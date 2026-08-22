#!/usr/bin/env python3
"""Render 3 alternatif desain invoice (review saja, bukan produksi).

Mengisi placeholder {{FONT4xx}} / {{LOGO}} / {{STAMP}} dengan data URI,
lalu render ke PDF (WeasyPrint) di docs/designs/.
"""
import base64
import mimetypes
from pathlib import Path

from weasyprint import HTML

BASE = Path('/home/heden/projects/n8n_invoice')
ASSETS = BASE / 'skills' / 'invoice-sta' / 'assets'
FONTS = ASSETS / 'fonts'
STAMP = Path.home() / '.hermes' / 'invoices' / 'stamp_signature_merged.png'
OUT = BASE / 'docs' / 'designs'


def data_uri(p: Path) -> str:
    mime = mimetypes.guess_type(str(p))[0] or 'image/png'
    return f'data:{mime};base64,' + base64.b64encode(p.read_bytes()).decode()


def main() -> None:
    repl = {f'FONT{w}': data_uri(FONTS / f'inter-{w}.woff2')
            for w in ('400', '500', '600', '700', '800')}
    repl['LOGO'] = data_uri(ASSETS / 'Logo STA Trans.png')
    repl['STAMP'] = data_uri(STAMP)

    files = [
        '1-editorial-corporate.html',
        '2-classic-commercial.html',
        '3-modern-transport.html',
    ]
    for name in files:
        tpl = (OUT / name).read_text(encoding='utf-8')
        for k, v in repl.items():
            tpl = tpl.replace('{{' + k + '}}', v)
        pdf = OUT / name.replace('.html', '.pdf')
        HTML(string=tpl, base_url=str(BASE)).write_pdf(str(pdf))
        print('rendered', pdf)


if __name__ == '__main__':
    main()
