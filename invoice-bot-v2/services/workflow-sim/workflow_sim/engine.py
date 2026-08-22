from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from uuid import uuid4

from invoice_core import InvoiceItemInput, calculate_invoice_totals, content_fingerprint, format_invoice_number, is_natural_approval
from llm_parser.mock_provider import MockProvider


@dataclass
class MemoryStore:
    drafts: dict[str, dict] = field(default_factory=dict)
    invoices: dict[int, dict] = field(default_factory=dict)
    deliveries: list[dict] = field(default_factory=list)
    audit_logs: list[dict] = field(default_factory=list)
    conversations: dict[tuple[str, str | None], dict] = field(default_factory=dict)
    sequence_last_number: int = 0
    next_invoice_id: int = 1


class InvoiceBotSimulator:
    """Offline acceptance simulator for deterministic workflow behavior.

    This is not production orchestration. It exists to make the expected n8n
    behavior executable without Telegram, MySQL, renderer, or LLM credentials.
    """

    def __init__(self, provider: MockProvider | None = None, store: MemoryStore | None = None):
        self.provider = provider or MockProvider()
        self.store = store or MemoryStore()

    def handle_message(self, chat_id: str, user_id: str | None, message: str, delivery_ok: bool = True) -> dict:
        correlation_id = str(uuid4())
        conversation = self._conversation(chat_id, user_id)
        self._audit(correlation_id, "MESSAGE_RECEIVED", "telegram_message", None, chat_id, user_id)
        intent = self.provider.classify_intent(message)["intent"]
        self._audit(correlation_id, "INTENT_DETECTED", "telegram_message", None, chat_id, user_id, metadata={"intent": intent})

        if intent == "CREATE_INVOICE":
            return self._create_draft(chat_id, user_id, message, conversation, correlation_id)
        if intent == "UPDATE_DRAFT":
            return self._update_draft(chat_id, user_id, message, conversation, correlation_id)
        if intent == "APPROVE_DRAFT":
            return self._approve(chat_id, user_id, message, conversation, delivery_ok, correlation_id)
        if intent == "CANCEL_DRAFT":
            return self._cancel_draft(chat_id, user_id, conversation, correlation_id)
        if intent == "CANCEL_INVOICE":
            return self._cancel_invoice(chat_id, user_id, message, conversation, correlation_id)
        if intent == "RESEND_INVOICE":
            return self._resend(chat_id, user_id, conversation, delivery_ok, correlation_id)
        if intent == "GET_INVOICE":
            return self._invoice_detail(chat_id, user_id, message, conversation, correlation_id)
        if intent == "GET_STATUS":
            return self._status(chat_id, user_id, message, conversation, correlation_id)
        self._audit(correlation_id, "ERROR", "telegram_message", None, chat_id, user_id, message="Unknown intent")
        return {"type": "UNKNOWN", "message": "Saya belum memahami permintaan itu."}

    def _create_draft(self, chat_id: str, user_id: str | None, message: str, conversation: dict, correlation_id: str) -> dict:
        extracted = self.provider.extract_invoice(message)
        if extracted["missing_fields"]:
            self._audit(
                correlation_id,
                "ERROR",
                "draft",
                None,
                chat_id,
                user_id,
                message="Missing required invoice fields",
                metadata={"missing_fields": extracted["missing_fields"]},
            )
            return {"type": "MISSING_FIELDS", "missing_fields": extracted["missing_fields"]}

        draft = self._draft_from_extraction(chat_id, user_id, message, extracted)
        duplicate_invoice = self._find_invoice_by_fingerprint(draft["content_fingerprint"])
        if duplicate_invoice:
            self._audit(
                correlation_id,
                "ERROR",
                "invoice",
                duplicate_invoice["id"],
                chat_id,
                user_id,
                message="Duplicate invoice request",
                metadata={"invoice_number": duplicate_invoice["invoice_number"]},
            )
            return {
                "type": "DUPLICATE_INVOICE",
                "invoice_number": duplicate_invoice["invoice_number"],
                "message": "Invoice dengan data sama sudah ada. Mau kirim ulang, lihat detail, atau benar-benar buat invoice baru?",
            }

        active_duplicate = self._find_active_draft(chat_id, draft["content_fingerprint"])
        if active_duplicate:
            conversation["active_draft_id"] = active_duplicate["id"]
            conversation["conversation_state"] = "AWAITING_APPROVAL"
            self._audit(correlation_id, "PREVIEW_SENT", "draft", active_duplicate["id"], chat_id, user_id)
            return {"type": "DRAFT_REUSED", "draft_id": active_duplicate["id"], "grand_total": active_duplicate["grand_total"]}

        self.store.drafts[draft["id"]] = draft
        conversation["active_draft_id"] = draft["id"]
        conversation["conversation_state"] = "AWAITING_APPROVAL"
        self._audit(correlation_id, "DRAFT_CREATED", "draft", draft["id"], chat_id, user_id)
        self._audit(correlation_id, "PREVIEW_SENT", "draft", draft["id"], chat_id, user_id)
        return {"type": "PREVIEW", "draft_id": draft["id"], "grand_total": draft["grand_total"], "invoice_number": None}

    def _update_draft(self, chat_id: str, user_id: str | None, message: str, conversation: dict, correlation_id: str) -> dict:
        if conversation.get("conversation_state") != "AWAITING_APPROVAL" or not conversation.get("active_draft_id"):
            self._audit(correlation_id, "ERROR", "draft", None, chat_id, user_id, message="No active draft to update")
            return {"type": "NO_ACTIVE_DRAFT"}
        draft = self.store.drafts[conversation["active_draft_id"]]
        patch = self.provider.extract_patch(message, draft)
        if patch["missing_fields"]:
            self._audit(
                correlation_id,
                "ERROR",
                "draft",
                draft["id"],
                chat_id,
                user_id,
                message="Draft patch not understood",
                metadata={"missing_fields": patch["missing_fields"]},
            )
            return {"type": "PATCH_NOT_UNDERSTOOD", "missing_fields": patch["missing_fields"]}

        for operation in patch["patches"]:
            if operation["target"] == "item:return_trip":
                item = draft["items"][-1]
                item[operation["field"]] = operation["value"]
            elif operation["target"] == "draft" and operation["field"] in {"payment_type", "down_payment_amount"}:
                draft[operation["field"]] = operation["value"]
        self._recalculate_draft(draft)
        draft["status"] = "AWAITING_APPROVAL"
        self._audit(correlation_id, "DRAFT_UPDATED", "draft", draft["id"], chat_id, user_id)
        self._audit(correlation_id, "PREVIEW_SENT", "draft", draft["id"], chat_id, user_id)
        return {"type": "PREVIEW", "draft_id": draft["id"], "grand_total": draft["grand_total"], "invoice_number": None}

    def _approve(self, chat_id: str, user_id: str | None, message: str, conversation: dict, delivery_ok: bool, correlation_id: str) -> dict:
        if not is_natural_approval(message, conversation.get("conversation_state", "IDLE")):
            self._audit(correlation_id, "ERROR", "draft", None, chat_id, user_id, message="Approval without awaiting draft")
            return {"type": "NO_ACTIVE_DRAFT", "message": "Tidak ada draft invoice yang sedang menunggu persetujuan."}
        draft = self.store.drafts[conversation["active_draft_id"]]
        self._audit(correlation_id, "APPROVAL_RECEIVED", "draft", draft["id"], chat_id, user_id)
        invoice = self._create_invoice_from_draft(draft)
        self._audit(correlation_id, "INVOICE_CREATED", "invoice", invoice["id"], chat_id, user_id, metadata={"invoice_number": invoice["invoice_number"]})
        self._audit(correlation_id, "PDF_GENERATED", "invoice", invoice["id"], chat_id, user_id, metadata={"pdf_path": invoice["pdf_path"]})
        draft["status"] = "APPROVED"
        conversation["active_draft_id"] = None
        conversation["last_invoice_id"] = invoice["id"]
        conversation["conversation_state"] = "DELIVERY_PENDING"
        delivery = self._send_invoice(invoice, chat_id, delivery_ok, correlation_id, user_id)
        conversation["conversation_state"] = "SENT" if delivery["status"] == "sent" else "ERROR"
        invoice["status"] = "SENT" if delivery["status"] == "sent" else "DELIVERY_FAILED"
        return {
            "type": "INVOICE_SENT" if delivery["status"] == "sent" else "DELIVERY_FAILED",
            "invoice_id": invoice["id"],
            "invoice_number": invoice["invoice_number"],
            "delivery_id": delivery["id"],
            "delivery_status": delivery["status"],
            "grand_total": invoice["grand_total"],
        }

    def _cancel_draft(self, chat_id: str, user_id: str | None, conversation: dict, correlation_id: str) -> dict:
        draft_id = conversation.get("active_draft_id")
        if conversation.get("conversation_state") != "AWAITING_APPROVAL" or not draft_id:
            self._audit(correlation_id, "ERROR", "draft", None, chat_id, user_id, message="No active draft to cancel")
            return {"type": "NO_ACTIVE_DRAFT"}

        draft = self.store.drafts[draft_id]
        draft["status"] = "CANCELLED"
        conversation["active_draft_id"] = None
        conversation["conversation_state"] = "IDLE"
        self._audit(correlation_id, "DRAFT_CANCELLED", "draft", draft_id, chat_id, user_id)
        return {"type": "DRAFT_CANCELLED", "draft_id": draft_id}

    def _resend(self, chat_id: str, user_id: str | None, conversation: dict, delivery_ok: bool, correlation_id: str) -> dict:
        invoice_id = conversation.get("last_invoice_id")
        if not invoice_id:
            self._audit(correlation_id, "ERROR", "invoice", None, chat_id, user_id, message="No invoice available to resend")
            return {"type": "NO_INVOICE"}
        invoice = self.store.invoices[invoice_id]
        if invoice["status"] == "VOID":
            self._audit(correlation_id, "ERROR", "invoice", invoice["id"], chat_id, user_id, message="Void invoice cannot be resent")
            return {"type": "NO_INVOICE"}
        delivery = self._send_invoice(invoice, chat_id, delivery_ok, correlation_id, user_id)
        invoice["status"] = "SENT" if delivery["status"] == "sent" else "DELIVERY_FAILED"
        if delivery["status"] == "sent":
            self._audit(correlation_id, "INVOICE_RESENT", "invoice", invoice["id"], chat_id, user_id, metadata={"delivery_id": delivery["id"]})
        return {
            "type": "INVOICE_RESENT" if delivery["status"] == "sent" else "DELIVERY_FAILED",
            "invoice_id": invoice["id"],
            "invoice_number": invoice["invoice_number"],
            "delivery_id": delivery["id"],
            "delivery_status": delivery["status"],
        }

    def _cancel_invoice(self, chat_id: str, user_id: str | None, message: str, conversation: dict, correlation_id: str) -> dict:
        invoice = self._find_invoice_for_message(message, conversation, include_void=True)
        if not invoice:
            self._audit(correlation_id, "ERROR", "invoice", None, chat_id, user_id, message="Invoice to void not found")
            return {"type": "NO_INVOICE"}
        if invoice["status"] == "VOID":
            self._audit(correlation_id, "ERROR", "invoice", invoice["id"], chat_id, user_id, message="Invoice already void")
            return {"type": "INVOICE_ALREADY_VOID", "invoice_id": invoice["id"], "invoice_number": invoice["invoice_number"]}

        invoice["status"] = "VOID"
        if conversation.get("last_invoice_id") == invoice["id"]:
            conversation["conversation_state"] = "IDLE"
        self._audit(correlation_id, "INVOICE_VOIDED", "invoice", invoice["id"], chat_id, user_id, metadata={"invoice_number": invoice["invoice_number"]})
        return {"type": "INVOICE_VOIDED", "invoice_id": invoice["id"], "invoice_number": invoice["invoice_number"]}

    def _status(self, chat_id: str, user_id: str | None, message: str, conversation: dict, correlation_id: str) -> dict:
        invoice = self._find_invoice_for_message(message, conversation)
        if not invoice:
            self._audit(correlation_id, "ERROR", "invoice", None, chat_id, user_id, message="Invoice status not found")
            return {"type": "NO_INVOICE"}
        delivery = self._latest_delivery(invoice["id"])
        return {
            "type": "INVOICE_STATUS",
            "invoice_id": invoice["id"],
            "invoice_number": invoice["invoice_number"],
            "invoice_status": invoice["status"],
            "delivery_status": delivery["status"] if delivery else None,
            "provider_message_id": delivery["provider_message_id"] if delivery else None,
            "provider_error_message": delivery["provider_error_message"] if delivery else None,
            "grand_total": invoice["grand_total"],
            "balance_due": invoice["balance_due"],
            "pdf_path": invoice["pdf_path"],
        }

    def _invoice_detail(self, chat_id: str, user_id: str | None, message: str, conversation: dict, correlation_id: str) -> dict:
        invoice = self._find_invoice_for_message(message, conversation)
        if not invoice:
            self._audit(correlation_id, "ERROR", "invoice", None, chat_id, user_id, message="Invoice detail not found")
            return {"type": "NO_INVOICE"}

        self._audit(correlation_id, "INVOICE_DETAIL_VIEWED", "invoice", invoice["id"], chat_id, user_id)
        return {
            "type": "INVOICE_DETAIL",
            "invoice_id": invoice["id"],
            "invoice_number": invoice["invoice_number"],
            "customer_name": invoice["customer_name"],
            "invoice_status": invoice["status"],
            "items": [item.copy() for item in invoice["items"]],
            "grand_total": invoice["grand_total"],
            "balance_due": invoice["balance_due"],
            "pdf_path": invoice["pdf_path"],
        }

    def _draft_from_extraction(self, chat_id: str, user_id: str | None, raw_input: str, extracted: dict) -> dict:
        item_inputs = [
            InvoiceItemInput(
                item.get("trip_date"),
                item["vehicle_type"],
                int(item["quantity"]),
                item.get("pickup"),
                item.get("destination"),
                int(item["unit_price"]),
            )
            for item in extracted["items"]
        ]
        payment_type = extracted["payment"]["type"]
        down_payment_amount = int(extracted["payment"].get("down_payment_amount") or 0)
        totals = calculate_invoice_totals(item_inputs, payment_type=payment_type, down_payment_amount=down_payment_amount)
        draft = {
            "id": str(uuid4()),
            "telegram_chat_id": chat_id,
            "telegram_user_id": user_id,
            "customer_name": extracted["customer"]["name"],
            "payment_type": payment_type,
            "included": extracted["notes"]["included"],
            "excluded": extracted["notes"]["excluded"],
            "notes": extracted["notes"]["free_text"],
            "raw_input": raw_input,
            "status": "AWAITING_APPROVAL",
            **totals,
        }
        draft["content_fingerprint"] = content_fingerprint(draft)
        return draft

    def _recalculate_draft(self, draft: dict) -> None:
        item_inputs = [
            InvoiceItemInput(
                item.get("trip_date"),
                item["vehicle_type"],
                int(item["quantity"]),
                item.get("pickup"),
                item.get("destination"),
                int(item["unit_price"]),
            )
            for item in draft["items"]
        ]
        totals = calculate_invoice_totals(
            item_inputs,
            payment_type=draft["payment_type"],
            down_payment_amount=int(draft.get("down_payment_amount") or 0),
        )
        draft.update(totals)
        draft["content_fingerprint"] = content_fingerprint(draft)

    def _create_invoice_from_draft(self, draft: dict) -> dict:
        self.store.sequence_last_number += 1
        invoice_id = self.store.next_invoice_id
        self.store.next_invoice_id += 1
        invoice = {
            "id": invoice_id,
            "invoice_number": format_invoice_number(self.store.sequence_last_number, "STA", 8, 2026),
            "invoice_date": date(2026, 8, 22).isoformat(),
            "customer_name": draft["customer_name"],
            "payment_type": draft["payment_type"],
            "items": [item.copy() for item in draft["items"]],
            "subtotal": draft["subtotal"],
            "discount": draft["discount"],
            "additional_fee": draft["additional_fee"],
            "grand_total": draft["grand_total"],
            "down_payment_amount": draft["down_payment_amount"],
            "balance_due": draft["balance_due"],
            "content_fingerprint": draft["content_fingerprint"],
            "source_draft_id": draft["id"],
            "pdf_path": f"/data/invoices/INV-{self.store.sequence_last_number:04d}.pdf",
            "status": "GENERATED",
        }
        self.store.invoices[invoice_id] = invoice
        return invoice

    def _send_invoice(self, invoice: dict, chat_id: str, delivery_ok: bool, correlation_id: str, user_id: str | None) -> dict:
        delivery = {
            "id": len(self.store.deliveries) + 1,
            "invoice_id": invoice["id"],
            "target_chat_id": chat_id,
            "status": "sent" if delivery_ok else "failed",
            "attempt_count": 1,
            "provider_message_id": str(1000 + len(self.store.deliveries) + 1) if delivery_ok else None,
            "provider_error_message": None if delivery_ok else "Bad Request: chat not found",
        }
        self.store.deliveries.append(delivery)
        self._audit(correlation_id, "DELIVERY_STARTED", "delivery", delivery["id"], chat_id, user_id, metadata={"invoice_id": invoice["id"]})
        self._audit(
            correlation_id,
            "DELIVERY_SENT" if delivery_ok else "DELIVERY_FAILED",
            "delivery",
            delivery["id"],
            chat_id,
            user_id,
            metadata={"invoice_id": invoice["id"], "provider_message_id": delivery["provider_message_id"]},
        )
        return delivery

    def _audit(
        self,
        correlation_id: str,
        event_type: str,
        entity_type: str | None,
        entity_id: str | int | None,
        chat_id: str,
        user_id: str | None,
        message: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        self.store.audit_logs.append(
            {
                "correlation_id": correlation_id,
                "event_type": event_type,
                "entity_type": entity_type,
                "entity_id": str(entity_id) if entity_id is not None else None,
                "telegram_chat_id": chat_id,
                "telegram_user_id": user_id,
                "message": message,
                "metadata": metadata or {},
            }
        )

    def _conversation(self, chat_id: str, user_id: str | None) -> dict:
        key = (chat_id, user_id)
        if key not in self.store.conversations:
            self.store.conversations[key] = {
                "telegram_chat_id": chat_id,
                "telegram_user_id": user_id,
                "active_draft_id": None,
                "last_invoice_id": None,
                "conversation_state": "IDLE",
            }
        return self.store.conversations[key]

    def _find_invoice_by_fingerprint(self, fingerprint: str) -> dict | None:
        for invoice in sorted(self.store.invoices.values(), key=lambda value: value["id"], reverse=True):
            if invoice["content_fingerprint"] == fingerprint and invoice["status"] != "VOID":
                return invoice
        return None

    def _find_active_draft(self, chat_id: str, fingerprint: str) -> dict | None:
        for draft in self.store.drafts.values():
            if (
                draft["telegram_chat_id"] == chat_id
                and draft["content_fingerprint"] == fingerprint
                and draft["status"] in {"DRAFT", "AWAITING_APPROVAL"}
            ):
                return draft
        return None

    def _find_invoice_for_message(self, message: str, conversation: dict, include_void: bool = False) -> dict | None:
        text = message.upper()
        for invoice in self.store.invoices.values():
            if invoice["invoice_number"].upper() in text and (include_void or invoice["status"] != "VOID"):
                return invoice
        invoice_id = conversation.get("last_invoice_id")
        if invoice_id:
            invoice = self.store.invoices.get(invoice_id)
            if invoice and (include_void or invoice["status"] != "VOID"):
                return invoice
        return None

    def _latest_delivery(self, invoice_id: int) -> dict | None:
        deliveries = [delivery for delivery in self.store.deliveries if delivery["invoice_id"] == invoice_id]
        return deliveries[-1] if deliveries else None
