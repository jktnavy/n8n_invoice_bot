import unittest

from llm_parser.openai_provider import OpenAIProvider, _parse_structured_response
from llm_parser.providers import ProviderConfig, provider_from_env


class OpenAIProviderTest(unittest.TestCase):
    def test_provider_from_env_returns_openai_provider(self):
        import os

        previous = {key: os.environ.get(key) for key in ["LLM_PROVIDER", "LLM_MODEL", "LLM_API_KEY"]}
        try:
            os.environ["LLM_PROVIDER"] = "openai"
            os.environ["LLM_MODEL"] = "gpt-test"
            os.environ["LLM_API_KEY"] = "test-key"
            self.assertIsInstance(provider_from_env(), OpenAIProvider)
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_classify_intent_uses_strict_json_schema_payload(self):
        captured = {}

        def transport(payload, api_key):
            captured["payload"] = payload
            captured["api_key"] = api_key
            return {
                "output": [
                    {
                        "content": [
                            {
                                "type": "output_text",
                                "text": '{"schema_version":"intent.v1","intent":"CREATE_INVOICE","confidence":0.99,"reason":"test"}',
                            }
                        ]
                    }
                ]
            }

        provider = OpenAIProvider(ProviderConfig("openai", "gpt-test", "test-key"), transport=transport)
        result = provider.classify_intent("buat invoice PT Nusa")

        self.assertEqual(result["intent"], "CREATE_INVOICE")
        self.assertEqual(captured["api_key"], "test-key")
        self.assertEqual(captured["payload"]["model"], "gpt-test")
        text_format = captured["payload"]["text"]["format"]
        self.assertEqual(text_format["type"], "json_schema")
        self.assertTrue(text_format["strict"])
        self.assertEqual(text_format["schema"]["required"], ["schema_version", "intent", "confidence"])

    def test_missing_credentials_are_rejected_before_transport(self):
        provider = OpenAIProvider(ProviderConfig("openai", "", ""), transport=lambda payload, api_key: {})
        with self.assertRaises(ValueError):
            provider.classify_intent("buat invoice")

    def test_parse_output_text_shortcut(self):
        result = _parse_structured_response({"output_text": '{"ok": true}'})
        self.assertEqual(result, {"ok": True})

    def test_parse_raises_when_no_text(self):
        with self.assertRaises(ValueError):
            _parse_structured_response({"output": []})


if __name__ == "__main__":
    unittest.main()

