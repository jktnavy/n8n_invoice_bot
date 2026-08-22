import argparse
import json
import os
from urllib.parse import urlparse

from .client import TelegramClient

V2_N8N_WEBHOOK_PATH = "/webhook/telegram/invoice-bot-v2"


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe Telegram Bot API helper for Invoice Bot V2.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("get-me")
    subparsers.add_parser("get-webhook-info")

    set_webhook = subparsers.add_parser("set-webhook")
    set_webhook.add_argument("--url", required=True, help="HTTPS webhook URL")
    set_webhook.add_argument(
        "--allow-non-v2-path",
        action="store_true",
        help="Allow a webhook URL that does not end with the Invoice Bot V2 n8n path.",
    )
    set_webhook.add_argument(
        "--keep-pending-updates",
        action="store_true",
        help="Do not ask Telegram to drop pending updates while replacing the webhook.",
    )

    subparsers.add_parser("delete-webhook")

    args = parser.parse_args()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    client = TelegramClient(token)

    if args.command == "get-me":
        result = client.get_me()
    elif args.command == "get-webhook-info":
        result = client.get_webhook_info()
    elif args.command == "set-webhook":
        validate_v2_webhook_url(args.url, allow_non_v2_path=args.allow_non_v2_path)
        result = client.set_webhook(args.url, drop_pending_updates=not args.keep_pending_updates)
    elif args.command == "delete-webhook":
        result = client.delete_webhook()
    else:
        raise AssertionError(args.command)

    print(
        json.dumps(
            {
                "ok": result.ok,
                "http_status": result.http_status,
                "provider_message_id": result.provider_message_id,
                "provider_error_code": result.provider_error_code,
                "provider_error_message": result.provider_error_message,
                "provider_response": result.provider_response,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result.ok else 1


def validate_v2_webhook_url(url: str, allow_non_v2_path: bool = False) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Telegram webhook URL must be HTTPS")
    if any(character.isspace() for character in url):
        raise ValueError("Telegram webhook URL must not contain whitespace")
    if not allow_non_v2_path and parsed.path.rstrip("/") != V2_N8N_WEBHOOK_PATH:
        raise ValueError(f"Telegram webhook URL must end with {V2_N8N_WEBHOOK_PATH}")


if __name__ == "__main__":
    raise SystemExit(main())
