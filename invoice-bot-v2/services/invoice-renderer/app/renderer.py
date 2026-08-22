import base64
import hashlib
import mimetypes
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.config import settings
from app.formatting import date_long, rupiah, terbilang
from app.schemas import InvoicePayload


def render_invoice_pdf(invoice: InvoicePayload) -> tuple[Path, str, int]:
    settings.invoice_output_dir.mkdir(parents=True, exist_ok=True)
    html = render_invoice_html(invoice)
    filename = safe_filename(invoice.invoice_number) + ".pdf"
    output_path = settings.invoice_output_dir / filename
    HTML(string=html, base_url=str(Path(__file__).resolve().parent)).write_pdf(output_path)
    digest = sha256_file(output_path)
    return output_path, digest, output_path.stat().st_size


def render_invoice_html(invoice: InvoicePayload) -> str:
    env = Environment(
        loader=FileSystemLoader(Path(__file__).resolve().parent / "templates"),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("invoice.html")
    items = sorted(invoice.items, key=lambda item: item.sort_order)
    first_date = min((item.trip_date for item in items if item.trip_date), default=None)
    last_date = max((item.trip_date for item in items if item.trip_date), default=None)
    return template.render(
        invoice=invoice,
        items=items,
        invoice_date=date_long(invoice.invoice_date),
        period=format_period(first_date, last_date),
        trip_meta=f"{len(items)} perjalanan",
        grand_total=rupiah(invoice.grand_total),
        amount_words=terbilang(invoice.grand_total),
        logo_data_uri=data_uri(settings.assets_dir / "logo" / "Logo STA Trans.png"),
        stamp_data_uri=data_uri(settings.assets_dir / "stamp" / "Cap STA Trans.gif"),
        signature_data_uri=data_uri(settings.assets_dir / "signature" / "Tanda Tangan Suhendi.gif"),
        rupiah=rupiah,
        date_long=date_long,
    )


def format_period(first_date, last_date) -> str:
    if first_date is None:
        return "-"
    if last_date is None or first_date == last_date:
        return date_long(first_date)
    return f"{date_long(first_date)} - {date_long(last_date)}"


def data_uri(path: Path) -> str:
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")

