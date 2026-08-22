import unittest

from workflow_sim import InvoiceBotSimulator


CREATE_MESSAGE = (
    "Buat invoice PT Nusa Horizon, 2 medium tanggal 15 Harapan Indah ke Puncak "
    "2,8 juta per unit, tanggal 17 Puncak Jakarta 2,6 juta. Lunas tanpa DP."
)
SECOND_CREATE_MESSAGE = (
    "Buat invoice PT Nusa, 2 medium tanggal 15 Harapan Indah ke Puncak "
    "2,8 juta per unit, tanggal 17 Puncak Jakarta 2,6 juta. Lunas tanpa DP."
)
DP_CREATE_MESSAGE = (
    "Buat invoice PT Nusa Horizon, 2 medium tanggal 15 Harapan Indah ke Puncak "
    "2,8 juta per unit, tanggal 17 Puncak Jakarta 2,6 juta. DP 1 juta."
)


class AcceptanceSimulatorTest(unittest.TestCase):
    def test_scenario_a_create_preview_approval_invoice_delivery(self):
        bot = InvoiceBotSimulator()

        preview = bot.handle_message("chat-1", "user-1", CREATE_MESSAGE)
        self.assertEqual(preview["type"], "PREVIEW")
        self.assertIsNone(preview["invoice_number"])
        self.assertEqual(preview["grand_total"], 10_800_000)

        approved = bot.handle_message("chat-1", "user-1", "setuju")
        self.assertEqual(approved["type"], "INVOICE_SENT")
        self.assertEqual(approved["invoice_number"], "INV-0001/STA/VIII/2026")
        self.assertEqual(approved["grand_total"], 10_800_000)
        self.assertEqual(len(bot.store.invoices), 1)
        self.assertEqual(len(bot.store.deliveries), 1)
        self.assertEqual(bot.store.deliveries[0]["status"], "sent")

    def test_scenario_b_revision_updates_same_draft_before_approval(self):
        bot = InvoiceBotSimulator()
        preview = bot.handle_message("chat-1", "user-1", CREATE_MESSAGE)
        draft_id = preview["draft_id"]

        revised = bot.handle_message("chat-1", "user-1", "tanggal pulang ganti tanggal 18")
        self.assertEqual(revised["type"], "PREVIEW")
        self.assertEqual(revised["draft_id"], draft_id)
        self.assertEqual(len(bot.store.invoices), 0)
        self.assertEqual(bot.store.drafts[draft_id]["items"][1]["trip_date"], "2026-08-18")

        approved = bot.handle_message("chat-1", "user-1", "oke")
        self.assertEqual(approved["invoice_number"], "INV-0001/STA/VIII/2026")
        self.assertEqual(len(bot.store.invoices), 1)

    def test_scenario_c_delivery_failure_then_resend_reuses_invoice(self):
        bot = InvoiceBotSimulator()
        bot.handle_message("chat-1", "user-1", CREATE_MESSAGE)
        failed = bot.handle_message("chat-1", "user-1", "setuju", delivery_ok=False)

        self.assertEqual(failed["type"], "DELIVERY_FAILED")
        self.assertEqual(failed["invoice_number"], "INV-0001/STA/VIII/2026")
        self.assertEqual(len(bot.store.invoices), 1)
        self.assertEqual(len(bot.store.deliveries), 1)

        resent = bot.handle_message("chat-1", "user-1", "kirim ulang invoice tadi", delivery_ok=True)
        self.assertEqual(resent["type"], "INVOICE_RESENT")
        self.assertEqual(resent["invoice_number"], "INV-0001/STA/VIII/2026")
        self.assertEqual(len(bot.store.invoices), 1)
        self.assertEqual(len(bot.store.deliveries), 2)
        self.assertEqual(bot.store.deliveries[-1]["status"], "sent")

    def test_status_reports_last_invoice_and_delivery_state(self):
        bot = InvoiceBotSimulator()
        bot.handle_message("chat-1", "user-1", CREATE_MESSAGE)
        approved = bot.handle_message("chat-1", "user-1", "setuju")

        status = bot.handle_message("chat-1", "user-1", "status invoice")
        self.assertEqual(status["type"], "INVOICE_STATUS")
        self.assertEqual(status["invoice_number"], approved["invoice_number"])
        self.assertEqual(status["invoice_status"], "SENT")
        self.assertEqual(status["delivery_status"], "sent")
        self.assertEqual(status["provider_message_id"], "1001")

    def test_status_reports_failed_delivery_error(self):
        bot = InvoiceBotSimulator()
        bot.handle_message("chat-1", "user-1", CREATE_MESSAGE)
        failed = bot.handle_message("chat-1", "user-1", "setuju", delivery_ok=False)

        status = bot.handle_message("chat-1", "user-1", f"status {failed['invoice_number']}")
        self.assertEqual(status["type"], "INVOICE_STATUS")
        self.assertEqual(status["invoice_status"], "DELIVERY_FAILED")
        self.assertEqual(status["delivery_status"], "failed")
        self.assertEqual(status["provider_error_message"], "Bad Request: chat not found")

    def test_scenario_d_duplicate_final_invoice_does_not_auto_create_new(self):
        bot = InvoiceBotSimulator()
        bot.handle_message("chat-1", "user-1", CREATE_MESSAGE)
        bot.handle_message("chat-1", "user-1", "setuju")

        duplicate = bot.handle_message("chat-1", "user-1", CREATE_MESSAGE)
        self.assertEqual(duplicate["type"], "DUPLICATE_INVOICE")
        self.assertEqual(duplicate["invoice_number"], "INV-0001/STA/VIII/2026")
        self.assertEqual(len(bot.store.invoices), 1)

    def test_scenario_e_ambiguous_request_asks_missing_fields(self):
        bot = InvoiceBotSimulator()
        result = bot.handle_message("chat-1", "user-1", "buat invoice PT ABC medium bus ke Puncak")
        self.assertEqual(result["type"], "MISSING_FIELDS")
        self.assertIn("items.unit_price", result["missing_fields"])
        self.assertEqual(len(bot.store.drafts), 0)
        self.assertEqual(len(bot.store.invoices), 0)

    def test_approval_without_active_draft_does_not_create_invoice(self):
        bot = InvoiceBotSimulator()
        result = bot.handle_message("chat-1", "user-1", "setuju")
        self.assertEqual(result["type"], "NO_ACTIVE_DRAFT")
        self.assertEqual(len(bot.store.invoices), 0)

    def test_status_without_invoice_does_not_guess(self):
        bot = InvoiceBotSimulator()
        result = bot.handle_message("chat-1", "user-1", "status invoice")
        self.assertEqual(result["type"], "NO_INVOICE")

    def test_sequence_increments_only_after_distinct_draft_approval(self):
        bot = InvoiceBotSimulator()

        first_preview = bot.handle_message("chat-1", "user-1", CREATE_MESSAGE)
        self.assertEqual(first_preview["type"], "PREVIEW")
        self.assertEqual(bot.store.sequence_last_number, 0)
        first = bot.handle_message("chat-1", "user-1", "setuju")
        self.assertEqual(first["invoice_number"], "INV-0001/STA/VIII/2026")
        self.assertEqual(bot.store.sequence_last_number, 1)

        second_preview = bot.handle_message("chat-2", "user-2", SECOND_CREATE_MESSAGE)
        self.assertEqual(second_preview["type"], "PREVIEW")
        self.assertEqual(bot.store.sequence_last_number, 1)
        second = bot.handle_message("chat-2", "user-2", "setuju")
        self.assertEqual(second["invoice_number"], "INV-0002/STA/VIII/2026")
        self.assertEqual(bot.store.sequence_last_number, 2)
        self.assertEqual(len(bot.store.invoices), 2)

    def test_scenario_d_payment_down_payment_tracks_balance_due(self):
        bot = InvoiceBotSimulator()

        preview = bot.handle_message("chat-1", "user-1", DP_CREATE_MESSAGE)
        draft = bot.store.drafts[preview["draft_id"]]
        self.assertEqual(preview["type"], "PREVIEW")
        self.assertEqual(draft["payment_type"], "DOWN_PAYMENT")
        self.assertEqual(draft["down_payment_amount"], 1_000_000)
        self.assertEqual(draft["balance_due"], 9_800_000)

        approved = bot.handle_message("chat-1", "user-1", "setuju")
        invoice = bot.store.invoices[approved["invoice_id"]]
        self.assertEqual(invoice["payment_type"], "DOWN_PAYMENT")
        self.assertEqual(invoice["down_payment_amount"], 1_000_000)
        self.assertEqual(invoice["balance_due"], 9_800_000)

    def test_payment_revision_can_remove_down_payment_before_approval(self):
        bot = InvoiceBotSimulator()

        preview = bot.handle_message("chat-1", "user-1", DP_CREATE_MESSAGE)
        draft_id = preview["draft_id"]
        revised = bot.handle_message("chat-1", "user-1", "tidak usah DP, langsung pelunasan")
        draft = bot.store.drafts[draft_id]

        self.assertEqual(revised["type"], "PREVIEW")
        self.assertEqual(revised["draft_id"], draft_id)
        self.assertEqual(draft["payment_type"], "FULL_PAYMENT")
        self.assertEqual(draft["down_payment_amount"], 0)
        self.assertEqual(draft["balance_due"], 0)

        approved = bot.handle_message("chat-1", "user-1", "setuju")
        invoice = bot.store.invoices[approved["invoice_id"]]
        self.assertEqual(invoice["payment_type"], "FULL_PAYMENT")
        self.assertEqual(invoice["down_payment_amount"], 0)
        self.assertEqual(invoice["balance_due"], 0)


if __name__ == "__main__":
    unittest.main()
