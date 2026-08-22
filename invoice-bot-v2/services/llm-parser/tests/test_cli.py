import io
import json
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from llm_parser.cli import structured_smoke_provider, validate_structured_smoke, healthcheck_provider


class LLMParserCliTest(unittest.TestCase):
    def test_healthcheck_uses_offline_mock_provider(self):
        env = {"LLM_PROVIDER": "mock"}
        with patch.dict(os.environ, env, clear=True), io.StringIO() as buffer, redirect_stdout(buffer):
            exit_code = healthcheck_provider("buat invoice")
            payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["mode"], "offline_mock")
        self.assertEqual(payload["intent"], "CREATE_INVOICE")

    def test_healthcheck_skips_live_provider_without_credentials(self):
        env = {"LLM_PROVIDER": "openai"}
        with patch.dict(os.environ, env, clear=True), io.StringIO() as buffer, redirect_stdout(buffer):
            exit_code = healthcheck_provider("buat invoice")
            payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["mode"], "skipped_live_credentials_missing")
        self.assertEqual(payload["provider"], "openai")

    def test_healthcheck_does_not_instantiate_reserved_provider_without_credentials(self):
        env = {"LLM_PROVIDER": "gemini"}
        with patch.dict(os.environ, env, clear=True), io.StringIO() as buffer, redirect_stdout(buffer):
            exit_code = healthcheck_provider("buat invoice")
            payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["mode"], "skipped_live_credentials_missing")
        self.assertEqual(payload["provider"], "gemini")

    def test_structured_smoke_uses_mock_provider_for_intent_and_invoice(self):
        env = {"LLM_PROVIDER": "mock"}
        with patch.dict(os.environ, env, clear=True), io.StringIO() as buffer, redirect_stdout(buffer):
            exit_code = structured_smoke_provider(
                "Buat invoice PT Nusa Horizon, 2 medium tanggal 15 Harapan Indah ke Puncak 2,8 juta, tanggal 17 Puncak Jakarta 2,6 juta. Lunas."
            )
            payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["mode"], "offline_mock")
        self.assertEqual(payload["intent"], "CREATE_INVOICE")
        self.assertEqual(payload["invoice_schema_version"], "invoice-draft.v1")
        self.assertEqual(payload["item_count"], 2)
        self.assertEqual(payload["missing_fields"], [])

    def test_structured_smoke_skips_live_provider_without_credentials(self):
        env = {"LLM_PROVIDER": "openai"}
        with patch.dict(os.environ, env, clear=True), io.StringIO() as buffer, redirect_stdout(buffer):
            exit_code = structured_smoke_provider("buat invoice")
            payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["mode"], "skipped_live_credentials_missing")
        self.assertEqual(payload["checks"], ["intent", "invoice_draft"])

    def test_validate_structured_smoke_rejects_incomplete_invoice(self):
        failures = validate_structured_smoke(
            {"schema_version": "intent.v1", "intent": "CREATE_INVOICE", "confidence": 1},
            {
                "schema_version": "invoice-draft.v1",
                "customer": {"name": None},
                "items": [],
                "payment": {"type": "UNSPECIFIED", "down_payment_amount": None},
                "missing_fields": ["customer.name"],
            },
        )

        self.assertIn("customer.name is required", failures)
        self.assertIn("at least one invoice item is required", failures)
        self.assertIn("missing_fields must be empty for PT Nusa smoke", failures)


if __name__ == "__main__":
    unittest.main()
