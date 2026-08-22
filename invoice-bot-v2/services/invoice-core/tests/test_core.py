import unittest

from invoice_core import (
    InvoiceItemInput,
    calculate_invoice_totals,
    content_fingerprint,
    format_invoice_number,
    is_natural_approval,
)


class InvoiceCoreTest(unittest.TestCase):
    def test_pt_nusa_calculation_is_deterministic_integer_math(self):
        result = calculate_invoice_totals(
            [
                InvoiceItemInput("2026-08-15", "Medium Bus", 2, "Harapan Indah Bekasi", "Cisarua Puncak", 2_800_000),
                InvoiceItemInput("2026-08-17", "Medium Bus", 2, "Cisarua Puncak", "Jakarta", 2_600_000),
            ],
            payment_type="FULL_PAYMENT",
        )

        self.assertEqual(result["items"][0]["line_total"], 5_600_000)
        self.assertEqual(result["items"][1]["line_total"], 5_200_000)
        self.assertEqual(result["grand_total"], 10_800_000)
        self.assertEqual(result["balance_due"], 0)

    def test_down_payment_balance_is_recalculated(self):
        result = calculate_invoice_totals(
            [
                InvoiceItemInput("2026-08-15", "Medium Bus", 2, "Harapan Indah Bekasi", "Cisarua Puncak", 2_800_000),
            ],
            payment_type="DOWN_PAYMENT",
            down_payment_amount=1_000_000,
        )

        self.assertEqual(result["grand_total"], 5_600_000)
        self.assertEqual(result["down_payment_amount"], 1_000_000)
        self.assertEqual(result["balance_due"], 4_600_000)

    def test_full_payment_ignores_down_payment_amount(self):
        result = calculate_invoice_totals(
            [
                InvoiceItemInput("2026-08-15", "Medium Bus", 1, "Harapan Indah Bekasi", "Cisarua Puncak", 2_800_000),
            ],
            payment_type="FULL_PAYMENT",
            down_payment_amount=1_000_000,
        )

        self.assertEqual(result["down_payment_amount"], 0)
        self.assertEqual(result["balance_due"], 0)

    def test_fingerprint_normalizes_semantic_business_data(self):
        base = {
            "customer_name": "PT Nusa Horizon Wisata",
            "payment_type": "FULL_PAYMENT",
            "items": [
                {
                    "trip_date": "2026-08-15",
                    "vehicle_type": "Medium Bus",
                    "quantity": 2,
                    "pickup": "Harapan Indah Bekasi",
                    "destination": "Cisarua Puncak",
                    "unit_price": 2_800_000,
                }
            ],
        }
        variant = {
            "customer_name": " pt nusa horizon wisata ",
            "payment_type": " full_payment ",
            "items": [
                {
                    "trip_date": "2026-08-15",
                    "vehicle_type": " medium   bus ",
                    "quantity": "2",
                    "pickup": "harapan indah bekasi",
                    "destination": "cisarua puncak",
                    "unit_price": "Rp2.800.000",
                }
            ],
        }

        self.assertEqual(content_fingerprint(base), content_fingerprint(variant))

    def test_fingerprint_includes_down_payment_amount(self):
        base = {
            "customer_name": "PT Nusa Horizon Wisata",
            "payment_type": "DOWN_PAYMENT",
            "down_payment_amount": 1_000_000,
            "items": [
                {
                    "trip_date": "2026-08-15",
                    "vehicle_type": "Medium Bus",
                    "quantity": 2,
                    "pickup": "Harapan Indah Bekasi",
                    "destination": "Cisarua Puncak",
                    "unit_price": 2_800_000,
                }
            ],
        }
        changed = {**base, "down_payment_amount": 2_000_000}

        self.assertNotEqual(content_fingerprint(base), content_fingerprint(changed))

    def test_invoice_number_format(self):
        self.assertEqual(format_invoice_number(1, "sta", 8, 2026), "INV-0001/STA/VIII/2026")

    def test_approval_requires_awaiting_approval_state(self):
        self.assertTrue(is_natural_approval("oke", "AWAITING_APPROVAL"))
        self.assertFalse(is_natural_approval("oke", "IDLE"))


if __name__ == "__main__":
    unittest.main()
