import argparse
import json
import os

from .client import TelegramClient


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe Telegram Bot API helper for Invoice Bot V2.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("get-me")
    subparsers.add_parser("get-webhook-info")

    set_webhook = subparsers.add_parser("set-webhook")
    set_webhook.add_argument("--url", required=True, help="HTTPS webhook URL")

    subparsers.add_parser("delete-webhook")

    args = parser.parse_args()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    client = TelegramClient(token)

    if args.command == "get-me":
        result = client.get_me()
    elif args.command == "get-webhook-info":
        result = client.get_webhook_info()
    elif args.command == "set-webhook":
        result = client.set_webhook(args.url)
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


if __name__ == "__main__":
    raise SystemExit(main())
