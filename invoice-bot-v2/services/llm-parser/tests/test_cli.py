import io
import json
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from llm_parser.cli import healthcheck_provider


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


if __name__ == "__main__":
    unittest.main()
