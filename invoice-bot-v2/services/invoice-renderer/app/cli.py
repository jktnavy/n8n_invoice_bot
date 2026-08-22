import argparse
import json
from pathlib import Path

from app.renderer import render_invoice_pdf
from app.schemas import RenderInvoiceRequest


def main() -> int:
    parser = argparse.ArgumentParser(description="Render an STA invoice fixture to PDF.")
    parser.add_argument("payload", type=Path, help="Path to render request JSON")
    args = parser.parse_args()

    request = RenderInvoiceRequest.model_validate_json(args.payload.read_text())
    file_path, digest, size = render_invoice_pdf(request.invoice)
    print(json.dumps({"ok": True, "file_path": str(file_path), "sha256": digest, "size": size}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

