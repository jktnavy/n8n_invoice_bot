import json
import mimetypes
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib import error, request


@dataclass(frozen=True)
class TelegramResult:
    ok: bool
    http_status: int | None
    provider_message_id: str | None
    provider_error_code: str | None
    provider_error_message: str | None
    provider_response: dict

    @property
    def delivery_status(self) -> str:
        return "sent" if self.ok and self.provider_message_id else "failed"


class TelegramClient:
    def __init__(
        self,
        bot_token: str,
        base_url: str = "https://api.telegram.org",
        transport: Callable[[str, bytes | None, dict[str, str]], tuple[int, dict]] | None = None,
    ):
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        self.bot_token = bot_token
        self.base_url = base_url.rstrip("/")
        self.transport = transport or self._default_transport

    def get_me(self) -> TelegramResult:
        return self._request_json("getMe")

    def send_document(self, chat_id: str | int | None, pdf_path: str | Path, caption: str | None = None) -> TelegramResult:
        if chat_id is None or str(chat_id).strip() == "":
            raise ValueError("Telegram chat_id is required")
        path = Path(pdf_path)
        if not path.is_file():
            raise FileNotFoundError(str(path))

        boundary = f"----invoicebotv2{uuid.uuid4().hex}"
        fields = {"chat_id": str(chat_id)}
        if caption:
            fields["caption"] = caption
        body = _multipart_body(fields, "document", path, boundary)
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        return self._request_json("sendDocument", body, headers)

    def _request_json(self, method: str, body: bytes | None = None, headers: dict[str, str] | None = None) -> TelegramResult:
        url = f"{self.base_url}/bot{self.bot_token}/{method}"
        http_status, response_body = self.transport(url, body, headers or {})
        return _telegram_result(http_status, response_body)

    def _default_transport(self, url: str, body: bytes | None, headers: dict[str, str]) -> tuple[int, dict]:
        try:
            req = request.Request(url, data=body, headers=headers, method="POST" if body is not None else "GET")
            with request.urlopen(req, timeout=60) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {"ok": False, "description": raw}
            return exc.code, parsed


def _telegram_result(http_status: int | None, response: dict) -> TelegramResult:
    ok = response.get("ok") is True
    result = response.get("result") if isinstance(response.get("result"), dict) else {}
    message_id = result.get("message_id")
    return TelegramResult(
        ok=ok and message_id is not None,
        http_status=http_status,
        provider_message_id=str(message_id) if message_id is not None else None,
        provider_error_code=None if ok else str(response.get("error_code", "")) or None,
        provider_error_message=None if ok else response.get("description", "Telegram request failed"),
        provider_response=response,
    )


def _multipart_body(fields: dict[str, str], file_field: str, path: Path, boundary: str) -> bytes:
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                str(value).encode(),
                b"\r\n",
            ]
        )

    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    chunks.extend(
        [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{file_field}"; filename="{path.name}"\r\n'.encode(),
            f"Content-Type: {mime_type}\r\n\r\n".encode(),
            path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return b"".join(chunks)


def redact_url(url: str) -> str:
    return re.sub(r"/bot[^/]+/", "/bot[redacted-token]/", url)
