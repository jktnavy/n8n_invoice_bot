import tempfile
import unittest
from pathlib import Path

from telegram_gateway.client import TelegramClient, redact_url


class TelegramClientTest(unittest.TestCase):
    def test_send_document_success_maps_message_id(self):
        captured = {}

        def transport(url, body, headers):
            captured["url"] = url
            captured["body"] = body
            captured["headers"] = headers
            return 200, {"ok": True, "result": {"message_id": 123}}

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf = Path(tmpdir) / "invoice.pdf"
            pdf.write_bytes(b"%PDF fake")
            result = TelegramClient("token-secret", transport=transport).send_document("chat-1", pdf, "Invoice")

        self.assertTrue(result.ok)
        self.assertEqual(result.delivery_status, "sent")
        self.assertEqual(result.provider_message_id, "123")
        self.assertIn(b'name="chat_id"', captured["body"])
        self.assertIn(b"chat-1", captured["body"])
        self.assertIn("multipart/form-data", captured["headers"]["Content-Type"])

    def test_provider_error_is_preserved(self):
        def transport(url, body, headers):
            return 400, {"ok": False, "error_code": 400, "description": "Bad Request: chat not found"}

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf = Path(tmpdir) / "invoice.pdf"
            pdf.write_bytes(b"%PDF fake")
            result = TelegramClient("token-secret", transport=transport).send_document("missing-chat", pdf)

        self.assertFalse(result.ok)
        self.assertEqual(result.delivery_status, "failed")
        self.assertEqual(result.provider_error_code, "400")
        self.assertEqual(result.provider_error_message, "Bad Request: chat not found")

    def test_provider_error_is_redacted_before_persistence(self):
        def transport(url, body, headers):
            token_like_value = "123456789:" + "abcdefghijklmnopqrstuvwxyz"
            return 400, {
                "ok": False,
                "error_code": 400,
                "description": "Bad Request token=secret api_key=sk-test-12345678 Authorization: Bearer-secret",
                "parameters": {
                    "authorization": "authorization: Bearer-nested-secret",
                    "bot_token": token_like_value,
                },
            }

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf = Path(tmpdir) / "invoice.pdf"
            pdf.write_bytes(b"%PDF fake")
            result = TelegramClient("token-secret", transport=transport).send_document("chat-1", pdf)

        self.assertFalse(result.ok)
        self.assertNotIn("secret", result.provider_error_message)
        self.assertNotIn("sk-test", result.provider_error_message)
        self.assertIn("token=[redacted]", result.provider_error_message)
        self.assertNotIn("Bearer-secret", str(result.provider_response))
        self.assertNotIn("Bearer-nested-secret", str(result.provider_response))
        self.assertNotIn("123456789:" + "abcdefghijklmnopqrstuvwxyz", str(result.provider_response))

    def test_send_document_requires_provider_message_id(self):
        def transport(url, body, headers):
            return 200, {"ok": True, "result": {}}

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf = Path(tmpdir) / "invoice.pdf"
            pdf.write_bytes(b"%PDF fake")
            result = TelegramClient("token-secret", transport=transport).send_document("chat-1", pdf)

        self.assertFalse(result.ok)
        self.assertEqual(result.delivery_status, "failed")
        self.assertIsNone(result.provider_message_id)
        self.assertEqual(result.provider_error_message, "Telegram request failed")

    def test_missing_chat_id_is_rejected_before_transport(self):
        called = False

        def transport(url, body, headers):
            nonlocal called
            called = True
            return 200, {}

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf = Path(tmpdir) / "invoice.pdf"
            pdf.write_bytes(b"%PDF fake")
            with self.assertRaises(ValueError):
                TelegramClient("token-secret", transport=transport).send_document("", pdf)

        self.assertFalse(called)

    def test_get_me_uses_get_me_endpoint(self):
        captured = {}

        def transport(url, body, headers):
            captured["url"] = url
            return 200, {"ok": True, "result": {"message_id": 1}}

        result = TelegramClient("token-secret", transport=transport).get_me()
        self.assertIn("/getMe", captured["url"])
        self.assertTrue(result.ok)

    def test_webhook_methods_use_expected_endpoints(self):
        calls = []

        def transport(url, body, headers):
            calls.append((url, body, headers))
            return 200, {"ok": True, "result": True}

        client = TelegramClient("token-secret", transport=transport)
        self.assertTrue(client.set_webhook("https://example.com/webhook").ok)
        self.assertTrue(client.get_webhook_info().ok)
        self.assertTrue(client.delete_webhook().ok)

        self.assertIn("/setWebhook", calls[0][0])
        self.assertIn(b"https://example.com/webhook", calls[0][1])
        self.assertEqual(calls[0][2]["Content-Type"], "application/json")
        self.assertIn("/getWebhookInfo", calls[1][0])
        self.assertIn("/deleteWebhook", calls[2][0])

    def test_set_webhook_requires_https(self):
        with self.assertRaises(ValueError):
            TelegramClient("token-secret", transport=lambda url, body, headers: (200, {})).set_webhook("http://example.com")

    def test_redact_url_hides_token(self):
        redacted = redact_url("https://api.telegram.org/bot123456:secret/sendDocument")
        self.assertNotIn("123456:secret", redacted)
        self.assertIn("[redacted-token]", redacted)


if __name__ == "__main__":
    unittest.main()
