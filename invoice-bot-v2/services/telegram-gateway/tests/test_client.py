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

    def test_redact_url_hides_token(self):
        redacted = redact_url("https://api.telegram.org/bot123456:secret/sendDocument")
        self.assertNotIn("123456:secret", redacted)
        self.assertIn("[redacted-token]", redacted)


if __name__ == "__main__":
    unittest.main()

