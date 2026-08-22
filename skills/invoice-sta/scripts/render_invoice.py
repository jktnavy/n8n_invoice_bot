#!/usr/bin/env python3
"""Render invoice STA Transport (desain: Modern Transport Manifest) ke PDF + MySQL.

Usage:
    python3 render_invoice.py /tmp/invoice_draft.json
    python3 render_invoice.py /tmp/invoice_draft.json --pdf-only   # tanpa MySQL

Input JSON (struktur baru):
    {
      "invoice_date": "2026-08-14",
      "due_date": "2026-08-21",            // opsional
      "payment_status": "LUNAS",           // LUNAS|BELUM LUNAS|DP DITERIMA|DRAFT|DIBATALKAN
      "payment_type": "FULL_PAYMENT",
      "customer": {"name":"...","address":"...","phone":"...","email":"..."},
      "trip_summary": {"vehicle_type":"Medium Bus","total_units":2,
                       "departure_date":"2026-08-15","return_date":"2026-08-17",
                       "pickup_address":"...","destination":"...","duration":"3 hari"},
      "items": [ {"description":"...","vehicle_type":"Medium Bus","quantity":2,
                  "unit_price":2800000,"subtotal":5600000} ],
      "subtotal": 10800000, "discount": 0, "additional_fee": 0,
      "grand_total": 10800000, "paid_amount": 10800000, "remaining_balance": 0,
      "amount_in_words": "sepuluh juta delapan ratus ribu rupiah",
      "notes": ["Harga termasuk ...", "Harga belum termasuk ..."]
    }

Nomor invoice (dari DB): INV-0001/STA/VIII/2026 (seq 4 digit / STA / bulan Romawi / tahun).
"""
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
import uuid
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from format_indonesia import date_long  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_DIR / 'assets'
FONTS_DIR = ASSETS_DIR / 'fonts'
TEMPLATE_PATH = SKILL_DIR / 'templates' / 'invoice_template.html'
OUTPUT_DIR = Path.home() / '.hermes' / 'invoices'

CFG = {
    'company_name': os.environ.get('STA_COMPANY_NAME', 'STA Transport'),
    'company_tagline': os.environ.get('STA_COMPANY_TAGLINE', 'Sewa Bus Pariwisata & Rent Cars'),
    'company_address': os.environ.get(
        'STA_COMPANY_ADDRESS',
        'Jl. Akses Tol Cimanggis No. 73, Leuwinanggung, Tapos, Depok 16456'),
    'company_email': os.environ.get('STA_COMPANY_EMAIL', 'statransdotcom@gmail.com'),
    'company_phone': os.environ.get('STA_COMPANY_PHONE', '0811-800-8613'),
    'company_whatsapp': os.environ.get('STA_COMPANY_WHATSAPP', '0812-840-21376'),
    'company_website': os.environ.get('STA_COMPANY_WEBSITE', 'www.statransport.co.id'),
    'bank_name': os.environ.get('STA_BANK_NAME', 'BCA'),
    'bank_account_number': os.environ.get('STA_BANK_ACCOUNT_NUMBER', '406 061 5352'),
    'bank_account_holder': os.environ.get('STA_BANK_ACCOUNT_HOLDER', 'Suhendi'),
    'signatory_name': os.environ.get('STA_SIGNATORY_NAME', 'Suhendi'),
    'signatory_position': os.environ.get('STA_SIGNATORY_POSITION', 'Marketing Executive'),
    'signatory_city': os.environ.get('STA_SIGNATORY_CITY', 'Jakarta'),
}

MONTHS_SHORT = {1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MEI', 6: 'JUN',
                7: 'JUL', 8: 'AGU', 9: 'SEP', 10: 'OKT', 11: 'NOV', 12: 'DES'}
ROMAN_MONTHS = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII',
                8: 'VIII', 9: 'IX', 10: 'X', 11: 'XI', 12: 'XII'}


def fmt_rp(amount) -> str:
    """Format Indonesia: Rp10.800.000 (tanpa spasi, tanpa ',-')."""
    value = float(amount or 0)
    return 'Rp' + f'{value:,.0f}'.replace(',', '.')


def _f(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _int_qty(value):
    v = _f(value)
    return int(v) if v == int(v) else v


def short_date(value: str) -> str:
    """'2026-08-15' -> '15 AGU 2026'."""
    try:
        d = date.fromisoformat(value)
        return f'{d.day} {MONTHS_SHORT[d.month]} {d.year}'
    except (ValueError, TypeError):
        return ''


# ---------------------------------------------------------------------------
# Gambar & font
# ---------------------------------------------------------------------------
def to_data_uri(path: Path) -> str:
    import mimetypes
    mime = mimetypes.guess_type(str(path))[0] or 'image/png'
    return f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode()


def merge_stamp_signature() -> Path:
    """Gabung tanda tangan (bawah) + cap (atas, opacity ~85%) jadi satu PNG."""
    from PIL import Image

    out = OUTPUT_DIR / 'stamp_signature_merged.png'
    if out.exists():
        return out

    sig = Image.open(ASSETS_DIR / 'Tanda Tangan Suhendi.gif').convert('RGBA')
    cap = Image.open(ASSETS_DIR / 'Cap STA Trans.gif').convert('RGBA')

    SIG_W, CAP_W = 220, 160
    if sig.width != SIG_W:
        sig = sig.resize((SIG_W, int(sig.height * SIG_W / sig.width)), Image.LANCZOS)
    if cap.width != CAP_W:
        cap = cap.resize((CAP_W, int(cap.height * CAP_W / cap.width)), Image.LANCZOS)

    w = max(sig.width, cap.width)
    h = max(sig.height, cap.height)
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    canvas.alpha_composite(sig, ((w - sig.width) // 2, (h - sig.height) // 2))
    r, g, b, a = cap.split()
    a = a.point(lambda x: int(x * 0.85))
    cap = Image.merge('RGBA', (r, g, b, a))
    canvas.alpha_composite(cap, ((w - cap.width) // 2, (h - cap.height) // 2))
    canvas.save(out)
    return out


def _font_uris() -> dict:
    uris = {}
    for w in ('400', '500', '600', '700', '800'):
        p = FONTS_DIR / f'inter-{w}.woff2'
        if p.exists():
            uris[f'FONT_{w}'] = to_data_uri(p)
    return uris


# ---------------------------------------------------------------------------
# Normalisasi data
# ---------------------------------------------------------------------------
def normalize(data: dict) -> dict:
    customer = data.get('customer') or {}
    if isinstance(customer, str):
        customer = {'name': customer}
    if not customer.get('name'):
        customer['name'] = data.get('customer_name', '')

    items = data.get('items') or []
    if items and 'unit_price' not in items[0] and 'price' in items[0]:
        new_items = []
        for it in items:
            desc = f"{it.get('vehicle_type', '')} — {it.get('trip_date', '')}"
            if it.get('pickup_address') or it.get('destination'):
                desc += (f" Jemput {it.get('pickup_address') or '-'} → "
                         f"Tujuan {it.get('destination') or '-'}")
            new_items.append({
                'description': desc.strip(' — '),
                'vehicle_type': it.get('vehicle_type', ''),
                'quantity': it.get('qty', 1),
                'unit_price': it.get('price', 0),
                'subtotal': it.get('line_total', 0),
            })
        items = new_items

    subtotal = _f(data.get('subtotal', data.get('sub_total', 0)))
    discount = _f(data.get('discount', data.get('discount_total', 0)))
    additional = _f(data.get('additional_fee', 0))
    grand = _f(data.get('grand_total', 0)) or (subtotal - discount + additional)
    paid = _f(data.get('paid_amount', data.get('paid_total', 0)))
    remaining = data.get('remaining_balance')
    remaining = _f(remaining) if remaining is not None else max(grand - paid, 0)

    return {
        'invoice_number': data.get('invoice_number', ''),
        'invoice_date': data.get('invoice_date') or date.today().isoformat(),
        'due_date': data.get('due_date'),
        'payment_status': str(data.get('payment_status') or '').upper(),
        'payment_type': data.get('payment_type', ''),
        'customer': customer,
        'trip_summary': data.get('trip_summary') or {},
        'items': items,
        'subtotal': subtotal,
        'discount': discount,
        'additional_fee': additional,
        'grand_total': grand,
        'paid_amount': paid,
        'remaining_balance': remaining,
        'amount_in_words': data.get('amount_in_words', data.get('terbilang', '')),
        'notes': data.get('notes') or [],
        'source_chat': data.get('source_chat'),
    }


def resolve_status(d: dict):
    if d['payment_status'] in ('LUNAS', 'BELUM LUNAS', 'DP DITERIMA', 'DRAFT', 'DIBATALKAN'):
        status = d['payment_status']
    else:
        if d['paid_amount'] >= d['grand_total'] > 0:
            status = 'LUNAS'
        elif d['paid_amount'] > 0:
            status = 'DP DITERIMA'
        else:
            status = 'BELUM LUNAS'
    return status, d['remaining_balance']


_DOT_CLASS = {
    'LUNAS': 'dot-lunas',
    'BELUM LUNAS': 'dot-belum-lunas',
    'DP DITERIMA': 'dot-dp',
    'DRAFT': 'dot-draft',
    'DIBATALKAN': 'dot-dibatalkan',
}


# ---------------------------------------------------------------------------
# Blok HTML
# ---------------------------------------------------------------------------
def build_status_html(status: str) -> str:
    cls = _DOT_CLASS.get(status, 'dot-belum-lunas')
    return f'<span class="dot {cls}"></span>{status}'


def _trip_meta(t: dict) -> str:
    parts = []
    if t.get('vehicle_type'):
        parts.append(f"{_int_qty(t.get('total_units', 1)) if t.get('total_units') else ''} "
                     f"{t['vehicle_type']}".strip())
    if t.get('duration'):
        parts.append(f'Durasi {t["duration"]}')
    return ' · '.join(parts) if parts else '-'


def _periode(t: dict) -> str:
    a, b = t.get('departure_date'), t.get('return_date')
    if not a:
        return '-'
    da, db = date.fromisoformat(a), date.fromisoformat(b) if b else None
    if db and da.year == db.year and da.month == db.month:
        return f'{da.day}–{db.day} {MONTHS_SHORT[db.month]} {db.year}'
    if db and da.year == db.year:
        return f'{da.day} {MONTHS_SHORT[da.month]} – {db.day} {MONTHS_SHORT[db.month]} {db.year}'
    if db:
        return f'{short_date(a)} – {short_date(b)}'
    return short_date(a)


def build_hero(t: dict) -> str:
    if not t:
        return ''
    dept = short_date(t.get('departure_date')) if t.get('departure_date') else ''
    arr = short_date(t.get('return_date')) if t.get('return_date') else ''
    dept_city = (t.get('pickup_address') or '').replace('<', '&lt;')
    arr_city = (t.get('destination') or '').replace('<', '&lt;')
    meta = ''
    bits = []
    if t.get('return_date') and t.get('destination'):
        bits.append(f"Kembali: {t['destination']}")
    if t.get('return_date') and t.get('pickup_address'):
        bits.append(f"Berangkat: {t['pickup_address']}")
    if bits:
        meta = ' &nbsp;·&nbsp; '.join(bits)
    return (
        '<div class="hero">'
        '<table class="dates" cellpadding="0" cellspacing="0"><tr>'
        f'<td class="dd d1"><div class="dt">{dept}</div><div class="dc">{dept_city}</div></td>'
        '<td class="arrow"><div class="l"></div></td>'
        f'<td class="dd d2"><div class="dt">{arr}</div><div class="dc">{arr_city}</div></td>'
        '</tr></table>'
        f'<div class="meta">{meta}</div>'
        '</div>'
    )


def build_item_rows(d: dict) -> str:
    rows = []
    for i, it in enumerate(d['items'], 1):
        veh = it.get('vehicle_type') or ''
        desc = it.get('description') or ''
        if veh and desc and veh.lower() in desc.lower():
            veh_html = f'<div class="i-veh">{veh}</div>'
            desc_html = ''
        elif veh:
            veh_html = f'<div class="i-veh">{veh}</div>'
            desc_html = f'<div class="i-rt">{desc}</div>' if desc else ''
        else:
            veh_html = f'<div class="i-veh">{desc or "-"}</div>'
            desc_html = ''
        rows.append(
            f'<tr>'
            f'<td class="ref">TR-{i:02d}</td>'
            f'<td>{veh_html}{desc_html}</td>'
            f'<td class="ctr">{_int_qty(it.get("quantity", 1))}</td>'
            f'<td class="num">{fmt_rp(it.get("unit_price", 0))}</td>'
            f'<td class="num i-jml">{fmt_rp(it.get("subtotal", 0))}</td>'
            f'</tr>'
        )
    return '\n'.join(rows)


def build_notes(d: dict) -> str:
    if not d['notes']:
        return '<div class="note">—</div>'
    out = []
    for n in d['notes']:
        low = n.lower()
        if 'belum termasuk' in low or 'tidak termasuk' in low:
            out.append(f'<div class="note"><span class="mk minus">–</span>{n}</div>')
        else:
            out.append(f'<div class="note"><span class="mk">✓</span>{n}</div>')
    return '\n'.join(out)


def build_tot_sub(d: dict, status: str) -> str:
    pt = str(d.get('payment_type') or '').upper()
    if pt == 'FULL_PAYMENT' or (status == 'LUNAS'):
        return 'Pelunasan 100% &nbsp;·&nbsp; LUNAS'
    bits = []
    if d['paid_amount'] > 0:
        bits.append(f'Uang Muka (DP) {fmt_rp(d["paid_amount"])}')
    if d['remaining_balance'] > 0:
        bits.append(f'Sisa {fmt_rp(d["remaining_balance"])}')
    if not bits:
        bits.append(f'Sisa Tagihan {fmt_rp(d["remaining_balance"])}')
    return ' &nbsp;·&nbsp; '.join(bits)


def build_watermark(status: str) -> str:
    if status != 'DRAFT':
        return ''
    return '<div class="watermark">DRAFT</div>'


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------
def render_html(d: dict, status: str) -> str:
    tpl = TEMPLATE_PATH.read_text(encoding='utf-8')
    fonts = _font_uris()
    t = d.get('trip_summary') or {}
    repl = {
        '{{FONT_400}}': fonts.get('FONT_400', ''),
        '{{FONT_500}}': fonts.get('FONT_500', ''),
        '{{FONT_600}}': fonts.get('FONT_600', ''),
        '{{FONT_700}}': fonts.get('FONT_700', ''),
        '{{FONT_800}}': fonts.get('FONT_800', ''),
        '{{WATERMARK}}': build_watermark(status),
        '{{LOGO_DATA_URI}}': to_data_uri(ASSETS_DIR / 'Logo STA Trans.png'),
        '{{STAMP_DATA_URI}}': to_data_uri(merge_stamp_signature()),
        '{{COMPANY_TAGLINE}}': CFG['company_tagline'],
        '{{COMPANY_ADDRESS}}': CFG['company_address'],
        '{{INVOICE_NUMBER}}': d['invoice_number'],
        '{{INVOICE_DATE}}': date_long(d['invoice_date']),
        '{{TRIP_META}}': _trip_meta(t),
        '{{PERIODE}}': _periode(t),
        '{{STATUS_HTML}}': build_status_html(status),
        '{{HERO}}': build_hero(t),
        '{{ITEMS_ROWS}}': build_item_rows(d),
        '{{NOTES_HTML}}': build_notes(d),
        '{{GRAND_TOTAL}}': fmt_rp(d['grand_total']),
        '{{TOT_SUB}}': build_tot_sub(d, status),
        '{{AMOUNT_IN_WORDS}}': d['amount_in_words'],
        '{{SIGN_NOTE}}': 'Invoice ini sah sebagai bukti penagihan.<br>'
                         'Mohon lampirkan bukti transfer saat pembayaran.',
        '{{SIGNATORY_CITY}}': CFG['signatory_city'],
        '{{SIGNATORY_NAME}}': CFG['signatory_name'],
        '{{SIGNATORY_POSITION}}': CFG['signatory_position'],
        '{{COMPANY_PHONE}}': CFG['company_phone'],
        '{{COMPANY_WHATSAPP}}': CFG['company_whatsapp'],
        '{{COMPANY_EMAIL}}': CFG['company_email'],
        '{{COMPANY_WEBSITE}}': CFG['company_website'],
    }
    for k, v in repl.items():
        tpl = tpl.replace(k, str(v))
    return tpl


def to_pdf(html_str: str, pdf_path: Path) -> None:
    tmp = Path('/tmp') / f'invoice_{uuid.uuid4().hex}.html'
    tmp.write_text(html_str, encoding='utf-8')
    try:
        from weasyprint import HTML
        HTML(string=html_str, base_url=str(SKILL_DIR)).write_pdf(str(pdf_path))
    except ImportError:
        subprocess.run(
            ['chromium', '--headless', '--no-sandbox',
             f'--print-to-pdf={pdf_path}', str(tmp)],
            check=True)
    finally:
        tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# MySQL
# ---------------------------------------------------------------------------
def _db_conn():
    import pymysql
    return pymysql.connect(
        host=os.environ.get('INVOICE_DB_HOST', '127.0.0.1'),
        port=int(os.environ.get('INVOICE_DB_PORT', '3306')),
        user=os.environ.get('INVOICE_DB_USER', 'root'),
        password=os.environ.get('INVOICE_DB_PASSWORD', ''),
        database=os.environ.get('INVOICE_DB_NAME', 'invoice_bot'),
        charset='utf8mb4',
        autocommit=False,
    )


def next_invoice_number(cur) -> str:
    """Format: INV-0001/STA/VIII/2026 (seq 4 digit / STA / bulan Romawi / tahun)."""
    cur.execute(
        "SELECT MAX(invoice_number) FROM invoices "
        "WHERE invoice_number REGEXP '^INV-[0-9]+/STA/[IVX]+/[0-9]{4}$'")
    row = cur.fetchone()
    y, m = date.today().year, date.today().month
    if not row or not row[0]:
        seq = 1
    else:
        m_obj = re.match(r'^INV-(\d+)/STA/[IVX]+/\d{4}$', str(row[0]).strip())
        seq = (int(m_obj.group(1)) + 1) if m_obj else 1
    return f'INV-{seq:04d}/STA/{ROMAN_MONTHS[m]}/{y}'


def _status_to_db(status: str) -> str:
    mapping = {'LUNAS': 'paid', 'DRAFT': 'draft', 'DIBATALKAN': 'void'}
    return mapping.get(status, 'sent')


def save_mysql(d: dict, status: str, pdf_path: Path):
    """Insert invoice + items. Return (invoice_number, inv_id)."""
    conn = _db_conn()
    try:
        with conn.cursor() as cur:
            number = d['invoice_number'] or next_invoice_number(cur)
            notes = d['notes']
            included = next((n for n in notes if 'termasuk' in n.lower() and 'belum' not in n.lower()), None)
            excluded = next((n for n in notes if 'belum termasuk' in n.lower() or 'tidak termasuk' in n.lower()), None)
            cur.execute(
                """INSERT INTO invoices
                   (invoice_number, customer_name, invoice_date, payment_type,
                    dp, sub_total, discount_total, grand_total, terbilang,
                    included_text, excluded_text, status, pdf_path,
                    source_chat, raw_request, request_fingerprint,
                    content_fingerprint, delivery_status)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (number, d['customer']['name'], d['invoice_date'],
                 d.get('payment_type'),
                 1 if ('DP' in str(d.get('payment_type') or '').upper()
                       or (d['paid_amount'] > 0 and d['paid_amount'] < d['grand_total'])) else 0,
                 d['subtotal'], d['discount'], d['grand_total'], d['amount_in_words'],
                 included, excluded, _status_to_db(status), str(pdf_path),
                 d.get('source_chat'), json.dumps(d, ensure_ascii=False),
                 d.get('request_fingerprint'), d.get('content_fingerprint'),
                 'pending'))
            inv_id = cur.lastrowid
            for i, it in enumerate(d['items'], 1):
                cur.execute(
                    """INSERT INTO invoice_items
                       (invoice_id, sort_order, description, trip_date,
                        vehicle_type, qty, uom, pickup_address, destination,
                        price, line_total)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (inv_id, i, it.get('description') or it.get('vehicle_type', ''),
                     None, it.get('vehicle_type'), it.get('quantity', 1),
                     'Unit', None, None, it.get('unit_price', 0),
                     it.get('subtotal', 0)))
            conn.commit()
            return number, inv_id
    finally:
        conn.close()


def update_delivery_status(inv_id, delivery_status: str, message_id=None,
                           chat_id=None, error=None) -> None:
    conn = _db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE invoices SET delivery_status=%s, telegram_message_id=%s, "
                "telegram_chat_id=%s, delivery_error=%s WHERE id=%s",
                (delivery_status, message_id, chat_id, error, inv_id))
            conn.commit()
    finally:
        conn.close()


def request_fingerprint(d: dict) -> str:
    """Fingerprint unik utk deteksi duplikat request (idempotency)."""
    parts = [
        str((d.get('customer') or {}).get('name', '')),
        str((d.get('trip_summary') or {}).get('departure_date', '')),
        str((d.get('trip_summary') or {}).get('return_date', '')),
        str((d.get('trip_summary') or {}).get('vehicle_type', '')),
        str((d.get('trip_summary') or {}).get('total_units', '')),
        str(d.get('subtotal', 0)),
        str(d.get('grand_total', 0)),
        str(d.get('source_chat', '')),
    ]
    return hashlib.sha256('|'.join(parts).encode('utf-8')).hexdigest()


def content_fingerprint(d: dict) -> str:
    """Fingerprint isi invoice (tanpa source_chat) — fallback deteksi duplikat
    jika agent lupa mengisi source_chat."""
    parts = [
        str((d.get('customer') or {}).get('name', '')),
        str((d.get('trip_summary') or {}).get('departure_date', '')),
        str((d.get('trip_summary') or {}).get('return_date', '')),
        str((d.get('trip_summary') or {}).get('vehicle_type', '')),
        str((d.get('trip_summary') or {}).get('total_units', '')),
        str(d.get('subtotal', 0)),
        str(d.get('grand_total', 0)),
    ]
    return hashlib.sha256('|'.join(parts).encode('utf-8')).hexdigest()


def find_existing_by_fingerprint(fp: str, cfp: str):
    """Cek apakah request yang sama sudah pernah dibuat (full atau content),
    melewati invoice yang statusnya void. Return (id, invoice_number) atau None."""
    conn = _db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, invoice_number FROM invoices "
                "WHERE (request_fingerprint=%s OR content_fingerprint=%s) "
                "AND invoice_number IS NOT NULL AND status != 'void' "
                "ORDER BY id DESC LIMIT 1", (fp, cfp))
            return cur.fetchone()
    finally:
        conn.close()


def get_invoice_by_number(inv_no: str):
    """Return (id, invoice_number, pdf_path) untuk nomor invoice, atau None."""
    conn = _db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, invoice_number, pdf_path FROM invoices "
                "WHERE invoice_number=%s LIMIT 1", (inv_no,))
            return cur.fetchone()
    finally:
        conn.close()


def validate_chat_id(chat_id: str) -> bool:
    """Cek validitas chat via getChat. Return True jika chat ada & dapat dikirim."""
    import urllib.error
    _load_env_file()
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    if not token or not re.match(r'^-?\d+$', str(chat_id).strip()):
        return False
    try:
        req = urllib.request.Request(
            f'https://api.telegram.org/bot{token}/getChat',
            data=json.dumps({'chat_id': str(chat_id).strip()}).encode(),
            headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
            return bool(data.get('ok'))
    except Exception:
        return False


def pick_valid_chat(candidate: str) -> str:
    """Prioritaskan kandidat; jika tidak valid, fallback ke grup allowlist
    (TELEGRAM_GROUP_ALLOWED_CHATS). Return chat id valid atau ''."""
    _load_env_file()
    if candidate and re.match(r'^-?\d+$', str(candidate).strip()) and validate_chat_id(candidate):
        return str(candidate).strip()
    allowed = os.environ.get('TELEGRAM_GROUP_ALLOWED_CHATS', '').strip()
    for fb in [x.strip() for x in allowed.split(',') if x.strip()]:
        if validate_chat_id(fb):
            return fb
    return ''


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def _load_env_file():
    """Baca ~/.hermes/.env langsung (agar token & chat id selalu tersedia,
    bahkan ketika script dijalankan di sandbox agent yang tidak mewarisi env)."""
    env_file = os.path.join(str(Path.home()), '.hermes', '.env')
    if not os.path.exists(env_file):
        return
    for line in open(env_file, encoding='utf-8'):
        line = line.strip()
        if line and '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())


def send_telegram_document(chat_id: str, pdf_path: Path) -> dict:
    """Kirim PDF ke chat Telegram via Bot API.

    Return dict: {"ok": bool, "chat_id": str, "message_id": int|None,
                  "http_status": int|None, "error_code": int|None,
                  "description": str}
    """
    import urllib.error
    _load_env_file()
    result = {'ok': False, 'chat_id': str(chat_id), 'message_id': None,
              'http_status': None, 'error_code': None, 'description': ''}
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    if not token:
        result['description'] = 'TELEGRAM_BOT_TOKEN kosong'
        return result
    if not re.match(r'^-?\d+$', str(chat_id).strip()):
        result['description'] = f'chat_id tidak numerik: {chat_id!r}'
        return result
    boundary = '----HermesBoundary' + uuid.uuid4().hex
    fields = [('chat_id', str(chat_id).strip())]
    body = b''
    for k, v in fields:
        body += (f'--{boundary}\r\n'
                 f'Content-Disposition: form-data; name="{k}"\r\n\r\n'
                 f'{v}\r\n').encode('utf-8')
    fname = pdf_path.name
    body += (f'--{boundary}\r\n'
             f'Content-Disposition: form-data; name="document"; filename="{fname}"\r\n'
             f'Content-Type: application/pdf\r\n\r\n').encode('utf-8')
    body += pdf_path.read_bytes()
    body += f'\r\n--{boundary}--\r\n'.encode('utf-8')

    url = f'https://api.telegram.org/bot{token}/sendDocument'
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result['http_status'] = resp.status
            data = json.loads(resp.read().decode())
            if data.get('ok'):
                result['ok'] = True
                result['message_id'] = (data.get('result') or {}).get('message_id')
                return result
            result['error_code'] = data.get('error_code')
            result['description'] = data.get('description') or 'sendDocument gagal'
            return result
    except urllib.error.HTTPError as exc:
        result['http_status'] = exc.code
        raw = exc.read().decode('utf-8', errors='replace')
        try:
            j = json.loads(raw)
            result['error_code'] = j.get('error_code')
            result['description'] = j.get('description') or raw
        except Exception:
            result['description'] = raw[:500]
        return result
    except Exception as exc:
        result['description'] = f'exception: {exc}'
        return result


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python3 render_invoice.py /tmp/invoice_draft.json [--pdf-only] [--chat <id>]')
        print('       python3 render_invoice.py --retry-send INV-0007/STA/VIII/2026 --chat <id>')
        sys.exit(1)

    pdf_only = '--pdf-only' in sys.argv
    chat_arg = ''
    if '--chat' in sys.argv:
        i = sys.argv.index('--chat')
        if i + 1 < len(sys.argv):
            chat_arg = sys.argv[i + 1]

    # ---- MODE RETRY DELIVERY (tanpa membuat invoice baru) ----
    if '--retry-send' in sys.argv:
        _load_env_file()
        j = sys.argv.index('--retry-send')
        inv_no = sys.argv[j + 1] if j + 1 < len(sys.argv) else ''
        if not inv_no:
            print('INVOICE_RESULT=FAILED (--retry-send butuh nomor invoice)')
            sys.exit(1)
        print(f'RETRY_SEND_INVOICE={inv_no}')
        row = get_invoice_by_number(inv_no)
        if not row:
            print('INVOICE_RESULT=FAILED (invoice tidak ditemukan di DB)')
            sys.exit(20)
        inv_id, inv_number, db_pdf = row
        pdf_path = Path(db_pdf) if db_pdf else (OUTPUT_DIR / f"{inv_number.replace('/', '-')}.pdf")
        if not pdf_path.exists():
            print(f'INVOICE_RESULT=FAILED (PDF tidak ada: {pdf_path})')
            sys.exit(20)
        print(f'RETRY_PDF={pdf_path}')
        chat = pick_valid_chat(chat_arg)
        print(f'TARGET_CHAT_ID={chat or "(tidak valid)"}')
        if not chat:
            print('INVOICE_RESULT=FAILED (chat id tidak valid)')
            sys.exit(20)
        result = send_telegram_document(chat, pdf_path)
        print(f"TELEGRAM_HTTP_STATUS={result.get('http_status')}")
        print(f"TELEGRAM_SEND_OK={'true' if result['ok'] else 'false'}")
        print(f"TELEGRAM_CHAT_ID={result['chat_id']}")
        if result['message_id'] is not None:
            print(f"TELEGRAM_MESSAGE_ID={result['message_id']}")
        if result.get('error_code') is not None:
            print(f"TELEGRAM_ERROR_CODE={result['error_code']}")
        if result.get('description'):
            print(f"TELEGRAM_DESCRIPTION={result['description']}")
        update_delivery_status(inv_id, 'sent' if result['ok'] else 'failed',
                               result['message_id'], result['chat_id'],
                               None if result['ok'] else result['description'])
        if result['ok']:
            print('INVOICE_RESULT=OK (retry delivery)')
            sys.exit(0)
        print('INVOICE_RESULT=FAILED (Telegram delivery gagal pada retry)')
        sys.exit(20)

    data = normalize(json.load(open(sys.argv[1])))
    request_id = str(data.get('request_id') or '').strip() or uuid.uuid4().hex[:12]
    print(f'REQUEST_ID={request_id}')
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _load_env_file()

    def _resolve_chat():
        chat = chat_arg or str(data.get('source_chat') or '').strip()
        if not re.match(r'^-?\d+$', chat):
            m = re.search(r'-?\d+', chat)
            chat = m.group(0) if m else ''
        if not chat:
            allowed = os.environ.get('TELEGRAM_GROUP_ALLOWED_CHATS', '').strip()
            if allowed:
                chat = allowed.split(',')[0].strip()
        return chat

    # --- Idempotency: deteksi duplikat request (jangan buat nomor baru) ---
    data['request_fingerprint'] = request_fingerprint(data)
    data['content_fingerprint'] = content_fingerprint(data)
    print(f'FINGERPRINT={data["request_fingerprint"]}')

    if not pdf_only:
        existing = find_existing_by_fingerprint(data['request_fingerprint'],
                                                data['content_fingerprint'])
        if existing:
            exist_id, exist_number = existing
            print('POTENTIAL_DUPLICATE=true')
            print(f'EXISTING_INVOICE={exist_number}')
            pdf_path = OUTPUT_DIR / f"{exist_number.replace('/', '-')}.pdf"
            if not pdf_path.exists():
                print('EXISTING_PDF=missing')
                print('INVOICE_RESULT=FAILED (invoice duplikat tapi PDF lama tidak ada)')
                sys.exit(20)
            chat = pick_valid_chat(_resolve_chat())
            print(f"TARGET_CHAT_ID={chat or '(tidak valid)'}")
            if not chat:
                print('INVOICE_RESULT=FAILED (chat id tidak valid)')
                sys.exit(20)
            result = send_telegram_document(chat, pdf_path)
            print(f"TELEGRAM_HTTP_STATUS={result.get('http_status')}")
            print(f"TELEGRAM_SEND_OK={'true' if result['ok'] else 'false'}")
            print(f"TELEGRAM_CHAT_ID={result['chat_id']}")
            if result['message_id'] is not None:
                print(f"TELEGRAM_MESSAGE_ID={result['message_id']}")
            if result.get('error_code') is not None:
                print(f"TELEGRAM_ERROR_CODE={result['error_code']}")
            if result.get('description'):
                print(f"TELEGRAM_DESCRIPTION={result['description']}")
            update_delivery_status(exist_id,
                                   'sent' if result['ok'] else 'failed',
                                   result['message_id'], result['chat_id'],
                                   None if result['ok'] else result['description'])
            if result['ok']:
                print('INVOICE_RESULT=OK (delivery ulang invoice yang sama)')
                sys.exit(0)
            print('INVOICE_RESULT=FAILED (Telegram delivery gagal pada retry)')
            sys.exit(20)

    # --- Invoice baru ---
    if not data['invoice_number'] and not pdf_only:
        conn = _db_conn()
        try:
            with conn.cursor() as cur:
                data['invoice_number'] = next_invoice_number(cur)
        finally:
            conn.close()
    elif not data['invoice_number']:
        data['invoice_number'] = f'INV-0000/STA/{ROMAN_MONTHS[date.today().month]}/{date.today().year}-TEST'

    status, remaining = resolve_status(data)
    data['remaining_balance'] = remaining

    pdf_path = OUTPUT_DIR / f"{data['invoice_number'].replace('/', '-')}.pdf"
    html = render_html(data, status)
    to_pdf(html, pdf_path)

    if pdf_only:
        print('PDF (tanpa MySQL):')
        print(pdf_path)
        print('PDF_CREATED=true')
        sys.exit(0)

    saved_number, inv_id = save_mysql(data, status, pdf_path)
    print('Invoice tersimpan:')
    print(pdf_path)
    print(f'Nomor: {saved_number}')
    print(f'RECORD_ID={inv_id}')

    # --- Kirim PDF langsung ke Telegram (error handling ketat) ---
    chat = pick_valid_chat(_resolve_chat())
    print(f"TARGET_CHAT_ID={chat or '(tidak valid)'}")
    if not chat:
        print('⚠️ Chat id tidak valid (getChat gagal / fallback kosong)')
        update_delivery_status(inv_id, 'failed', None, None,
                               'chat id tidak valid')
        print('INVOICE_RESULT=FAILED (chat id tidak valid)')
        sys.exit(20)

    result = send_telegram_document(chat, pdf_path)
    print(f"TELEGRAM_HTTP_STATUS={result.get('http_status')}")
    print(f"TELEGRAM_SEND_OK={'true' if result['ok'] else 'false'}")
    print(f"TELEGRAM_CHAT_ID={result['chat_id']}")
    if result['message_id'] is not None:
        print(f"TELEGRAM_MESSAGE_ID={result['message_id']}")
    if result.get('error_code') is not None:
        print(f"TELEGRAM_ERROR_CODE={result['error_code']}")
    if result.get('description'):
        print(f"TELEGRAM_DESCRIPTION={result['description']}")

    if result['ok']:
        update_delivery_status(inv_id, 'sent', result['message_id'],
                               result['chat_id'], None)
        print('INVOICE_RESULT=OK')
        sys.exit(0)

    update_delivery_status(inv_id, 'failed', None, result['chat_id'],
                           result['description'])
    print('INVOICE_RESULT=FAILED (Telegram delivery gagal)')
    sys.exit(20)


if __name__ == '__main__':
    main()
