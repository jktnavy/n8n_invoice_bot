#!/usr/bin/env python3
import json
from pathlib import Path

from workflow_sim import InvoiceBotSimulator

ROOT_DIR = Path(__file__).resolve().parents[1]

CREATE_MESSAGE = (
    "Buat invoice PT Nusa Horizon, 2 medium tanggal 15 Harapan Indah ke Puncak "
    "2,8 juta per unit, tanggal 17 Puncak Jakarta 2,6 juta. Lunas tanpa DP."
)
DP_CREATE_MESSAGE = (
    "Buat invoice PT Nusa Horizon, 2 medium tanggal 15 Harapan Indah ke Puncak "
    "2,8 juta per unit, tanggal 17 Puncak Jakarta 2,6 juta. DP 1 juta."
)


def main() -> int:
    scenarios = [
        scenario_create_approve_delivery(),
        scenario_revision_before_approval(),
        scenario_delivery_failure_resend(),
        scenario_duplicate_detail_status(),
        scenario_ambiguous_help_cancel_payment(),
    ]
    failures = [failure for scenario in scenarios for failure in scenario["failures"]]
    payload = {
        "ok": not failures,
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "failures": failures,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


def scenario_create_approve_delivery() -> dict:
    bot = InvoiceBotSimulator()
    preview = bot.handle_message("chat-a", "user-a", CREATE_MESSAGE)
    approved = bot.handle_message("chat-a", "user-a", "setuju")

    failures = []
    expect(preview["type"] == "PREVIEW", "scenario_a preview must be returned", failures)
    expect(preview["invoice_number"] is None, "scenario_a draft must not allocate invoice number", failures)
    expect(approved["type"] == "INVOICE_SENT", "scenario_a approval must send invoice", failures)
    expect(approved["invoice_number"] == "INV-0001/STA/VIII/2026", "scenario_a invoice number mismatch", failures)
    expect(len(bot.store.invoices) == 1, "scenario_a must create one invoice", failures)
    expect(len(bot.store.deliveries) == 1, "scenario_a must create one delivery", failures)
    expect(bot.store.deliveries[0]["target_chat_id"] == "chat-a", "scenario_a delivery must use source chat", failures)
    return summarize("scenario_a_create_approve_delivery", bot, failures, approved)


def scenario_revision_before_approval() -> dict:
    bot = InvoiceBotSimulator()
    preview = bot.handle_message("chat-b", "user-b", CREATE_MESSAGE)
    revised = bot.handle_message("chat-b", "user-b", "tanggal pulang ganti tanggal 18")
    approved = bot.handle_message("chat-b", "user-b", "oke")

    draft = bot.store.drafts[preview["draft_id"]]
    failures = []
    expect(revised["draft_id"] == preview["draft_id"], "scenario_b revision must keep same draft", failures)
    expect(draft["items"][1]["trip_date"] == "2026-08-18", "scenario_b return date not updated", failures)
    expect(approved["invoice_number"] == "INV-0001/STA/VIII/2026", "scenario_b invoice number mismatch", failures)
    expect(len(bot.store.invoices) == 1, "scenario_b must create invoice only after approval", failures)
    return summarize("scenario_b_revision_before_approval", bot, failures, approved)


def scenario_delivery_failure_resend() -> dict:
    bot = InvoiceBotSimulator()
    bot.handle_message("chat-c", "user-c", CREATE_MESSAGE)
    failed = bot.handle_message("chat-c", "user-c", "setuju", delivery_ok=False)
    resent = bot.handle_message("chat-c", "user-c", "kirim ulang invoice tadi", delivery_ok=True)

    failures = []
    expect(failed["type"] == "DELIVERY_FAILED", "scenario_c initial delivery must fail", failures)
    expect(resent["type"] == "INVOICE_RESENT", "scenario_c resend must succeed", failures)
    expect(failed["invoice_number"] == resent["invoice_number"], "scenario_c resend must reuse invoice number", failures)
    expect(len(bot.store.invoices) == 1, "scenario_c resend must not create another invoice", failures)
    expect(len(bot.store.deliveries) == 2, "scenario_c resend must create second delivery attempt", failures)
    return summarize("scenario_c_delivery_failure_resend", bot, failures, resent)


def scenario_duplicate_detail_status() -> dict:
    bot = InvoiceBotSimulator()
    bot.handle_message("chat-d", "user-d", CREATE_MESSAGE)
    approved = bot.handle_message("chat-d", "user-d", "setuju")
    duplicate = bot.handle_message("chat-d", "user-d", CREATE_MESSAGE)
    detail = bot.handle_message("chat-d", "user-d", "lihat detail invoice tadi")
    status = bot.handle_message("chat-d", "user-d", "status invoice")

    failures = []
    expect(duplicate["type"] == "DUPLICATE_INVOICE", "scenario_d duplicate must not auto-create", failures)
    expect(detail["type"] == "INVOICE_DETAIL", "scenario_d detail must return invoice detail", failures)
    expect(status["type"] == "INVOICE_STATUS", "scenario_d status must return invoice status", failures)
    expect(status["provider_message_id"] == "1001", "scenario_d status must expose Telegram message id", failures)
    expect(len(bot.store.invoices) == 1, "scenario_d must still have one invoice", failures)
    return summarize("scenario_d_duplicate_detail_status", bot, failures, approved)


def scenario_ambiguous_help_cancel_payment() -> dict:
    bot = InvoiceBotSimulator()
    ambiguous = bot.handle_message("chat-e", "user-e", "buat invoice PT ABC medium bus ke Puncak")
    help_result = bot.handle_message("chat-e", "user-e", "bantuan cara pakai")
    dp_preview = bot.handle_message("chat-e", "user-e", DP_CREATE_MESSAGE)
    revised = bot.handle_message("chat-e", "user-e", "tidak usah DP, langsung pelunasan")
    cancelled = bot.handle_message("chat-e", "user-e", "batalkan invoice ini")
    approval_after_cancel = bot.handle_message("chat-e", "user-e", "setuju")

    draft = bot.store.drafts[dp_preview["draft_id"]]
    failures = []
    expect(ambiguous["type"] == "MISSING_FIELDS", "scenario_e ambiguous input must ask missing fields", failures)
    expect(help_result["type"] == "HELP", "scenario_e help must not change invoice state", failures)
    expect(revised["type"] == "PREVIEW", "scenario_e payment revision must return preview", failures)
    expect(draft["payment_type"] == "FULL_PAYMENT", "scenario_e payment revision must remove DP", failures)
    expect(draft["balance_due"] == 0, "scenario_e full payment must have zero balance", failures)
    expect(cancelled["type"] == "DRAFT_CANCELLED", "scenario_e cancel must cancel active draft", failures)
    expect(approval_after_cancel["type"] == "NO_ACTIVE_DRAFT", "scenario_e approval after cancel must not create invoice", failures)
    expect(len(bot.store.invoices) == 0, "scenario_e must not create invoice", failures)
    return summarize("scenario_e_ambiguous_help_cancel_payment", bot, failures, approval_after_cancel)


def summarize(name: str, bot: InvoiceBotSimulator, failures: list[str], last_result: dict) -> dict:
    return {
        "name": name,
        "ok": not failures,
        "failures": failures,
        "last_result_type": last_result.get("type"),
        "invoice_count": len(bot.store.invoices),
        "draft_count": len(bot.store.drafts),
        "delivery_count": len(bot.store.deliveries),
        "audit_event_count": len(bot.store.audit_logs),
        "sequence_last_number": bot.store.sequence_last_number,
    }


def expect(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


if __name__ == "__main__":
    raise SystemExit(main())
