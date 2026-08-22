import unittest

from llm_parser.openai_provider import OpenAIProvider, _parse_structured_response, _validate_structured_payload
from llm_parser.providers import NotImplementedProvider, ProviderConfig, provider_from_env, validate_responses_base_url


class OpenAIProviderTest(unittest.TestCase):
    def test_provider_from_env_returns_openai_provider(self):
        import os

        previous = {key: os.environ.get(key) for key in ["LLM_PROVIDER", "LLM_MODEL", "LLM_API_KEY", "LLM_BASE_URL"]}
        try:
            os.environ["LLM_PROVIDER"] = "openai"
            os.environ["LLM_MODEL"] = "gpt-test"
            os.environ["LLM_API_KEY"] = "test-key"
            os.environ.pop("LLM_BASE_URL", None)
            self.assertIsInstance(provider_from_env(), OpenAIProvider)
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_openai_compatible_provider_uses_configured_base_url(self):
        import os

        previous = {key: os.environ.get(key) for key in ["LLM_PROVIDER", "LLM_MODEL", "LLM_API_KEY", "LLM_BASE_URL"]}
        try:
            os.environ["LLM_PROVIDER"] = "openrouter"
            os.environ["LLM_MODEL"] = "test-model"
            os.environ["LLM_API_KEY"] = "test-key"
            os.environ["LLM_BASE_URL"] = "https://llm.example.test/v1/responses"
            provider = provider_from_env()
            self.assertIsInstance(provider, OpenAIProvider)
            self.assertEqual(provider.base_url, "https://llm.example.test/v1/responses")
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_openai_compatible_provider_requires_base_url(self):
        import os

        previous = {key: os.environ.get(key) for key in ["LLM_PROVIDER", "LLM_MODEL", "LLM_API_KEY", "LLM_BASE_URL"]}
        try:
            os.environ["LLM_PROVIDER"] = "deepseek"
            os.environ["LLM_MODEL"] = "test-model"
            os.environ["LLM_API_KEY"] = "test-key"
            os.environ.pop("LLM_BASE_URL", None)
            with self.assertRaises(ValueError):
                provider_from_env()
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_openai_compatible_provider_rejects_invalid_base_url(self):
        invalid_urls = [
            "http://llm.example.test/v1/responses",
            "https://user:pass@llm.example.test/v1/responses",
            "https://llm.example.test/v1/chat/completions",
            "https://llm.example.test/v1/responses?token=secret",
            "not-a-url",
        ]
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    validate_responses_base_url(url, "openrouter")

    def test_openai_compatible_provider_allows_https_responses_url(self):
        validate_responses_base_url("https://llm.example.test/v1/responses", "openrouter")
        validate_responses_base_url("https://llm.example.test/v1/responses/", "deepseek")

    def test_gemini_remains_reserved_provider(self):
        import os

        previous = {key: os.environ.get(key) for key in ["LLM_PROVIDER", "LLM_MODEL", "LLM_API_KEY", "LLM_BASE_URL"]}
        try:
            os.environ["LLM_PROVIDER"] = "gemini"
            os.environ["LLM_MODEL"] = "test-model"
            os.environ["LLM_API_KEY"] = "test-key"
            os.environ["LLM_BASE_URL"] = "https://unused.example.test"
            self.assertIsInstance(provider_from_env(), NotImplementedProvider)
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

    def test_structured_response_is_validated_against_schema(self):
        schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["schema_version", "intent", "confidence"],
            "properties": {
                "schema_version": {"const": "intent.v1"},
                "intent": {"type": "string", "enum": ["CREATE_INVOICE", "UNKNOWN"]},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            },
        }

        _validate_structured_payload(
            {"schema_version": "intent.v1", "intent": "CREATE_INVOICE", "confidence": 0.9},
            schema,
        )

        invalid_payloads = [
            {"schema_version": "intent.v1", "intent": "CREATE_INVOICE"},
            {"schema_version": "intent.v1", "intent": "DELETE_DATABASE", "confidence": 0.9},
            {"schema_version": "intent.v1", "intent": "UNKNOWN", "confidence": 2},
            {"schema_version": "intent.v1", "intent": "UNKNOWN", "confidence": 0.5, "sql": "DROP"},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    _validate_structured_payload(payload, schema)

    def test_provider_rejects_malformed_structured_output(self):
        def transport(payload, api_key):
            return {"output_text": '{"schema_version":"intent.v1","intent":"DELETE_DATABASE","confidence":0.9}'}

        provider = OpenAIProvider(ProviderConfig("openai", "gpt-test", "test-key"), transport=transport)
        with self.assertRaises(ValueError):
            provider.classify_intent("buat invoice")


if __name__ == "__main__":
    unittest.main()
