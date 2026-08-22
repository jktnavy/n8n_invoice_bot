import unittest

from llm_parser.mock_provider import MockProvider


class MockProviderTest(unittest.TestCase):
    def setUp(self):
        self.provider = MockProvider()

    def test_classifies_create_invoice(self):
        result = self.provider.classify_intent("buat invoice PT Nusa")
        self.assertEqual(result["intent"], "CREATE_INVOICE")

    def test_classifies_create_invoice_with_tanpa_dp_as_create(self):
        result = self.provider.classify_intent("buat invoice PT Nusa, lunas tanpa DP")
        self.assertEqual(result["intent"], "CREATE_INVOICE")

    def test_classifies_natural_approval(self):
        result = self.provider.classify_intent("oke gas")
        self.assertEqual(result["intent"], "APPROVE_DRAFT")

    def test_classifies_cancel_draft(self):
        result = self.provider.classify_intent("batalkan invoice ini")
        self.assertEqual(result["intent"], "CANCEL_DRAFT")

    def test_classifies_status_invoice_as_status(self):
        result = self.provider.classify_intent("status invoice")
        self.assertEqual(result["intent"], "GET_STATUS")

    def test_classifies_detail_invoice(self):
        result = self.provider.classify_intent("lihat detail invoice tadi")
        self.assertEqual(result["intent"], "GET_INVOICE")

    def test_extracts_pt_nusa_fixture(self):
        result = self.provider.extract_invoice(
            "Buat invoice PT Nusa Horizon, 2 medium tanggal 15 Harapan Indah ke Puncak 2,8 juta, tanggal 17 Puncak Jakarta 2,6 juta. Lunas."
        )
        self.assertEqual(result["customer"]["name"], "PT Nusa Horizon Wisata")
        self.assertEqual(result["items"][0]["unit_price"], 2800000)
        self.assertEqual(result["items"][1]["unit_price"], 2600000)
        self.assertEqual(result["missing_fields"], [])

    def test_extracts_revision_patch(self):
        result = self.provider.extract_patch("tanggal pulang ganti tanggal 18", {})
        self.assertEqual(result["patches"][0]["field"], "trip_date")
        self.assertEqual(result["patches"][0]["value"], "2026-08-18")

    def test_extracts_payment_revision_patch(self):
        result = self.provider.extract_patch("tidak usah DP, langsung pelunasan", {})
        self.assertEqual(result["missing_fields"], [])
        self.assertEqual(
            result["patches"],
            [
                {"target": "draft", "field": "payment_type", "value": "FULL_PAYMENT"},
                {"target": "draft", "field": "down_payment_amount", "value": 0},
            ],
        )


if __name__ == "__main__":
    unittest.main()
