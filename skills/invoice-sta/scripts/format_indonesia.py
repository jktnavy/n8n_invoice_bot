#!/usr/bin/env python3
"""Format angka & tanggal Indonesia + terbilang.

Port dari helper aplikasi lama bus_invoice_app:
- app/Support/IndonesianFormat.php
- app/Support/Terbilang.php

Usage:
    python3 format_indonesia.py terbilang <angka>
    python3 format_indonesia.py rupiah   <angka>
    python3 format_indonesia.py date     <YYYY-MM-DD>
"""
import sys
from datetime import date

MONTHS = {
    1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni',
    7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November',
    12: 'Desember',
}


def rupiah(amount) -> str:
    """'Rp10.800.000' — format Indonesia tanpa spasi/tanpa ',-' (desain baru)."""
    value = float(amount or 0)
    return 'Rp' + f'{value:,.0f}'.replace(',', '.')


def date_long(value: str) -> str:
    """'2026-08-14' -> '14 Agustus 2026'."""
    d = date.fromisoformat(value)
    return f'{d.day} {MONTHS[d.month]} {d.year}'


def terbilang(value) -> str:
    """Angka -> kata Indonesia (lowercase), sesuai Terbilang.php."""
    n = int(float(value) // 1)
    if n == 0:
        return 'nol'
    if n < 0:
        return 'minus ' + _spell(abs(n))
    return _spell(n).strip()


def _spell(n: int) -> str:
    words = [
        '', 'satu', 'dua', 'tiga', 'empat', 'lima', 'enam', 'tujuh',
        'delapan', 'sembilan', 'sepuluh', 'sebelas',
    ]
    if n < 12:
        return words[n]
    if n < 20:
        return _spell(n - 10) + ' belas'
    if n < 100:
        return (_spell(n // 10) + ' puluh ' + _spell(n % 10)).strip()
    if n < 200:
        return ('seratus ' + _spell(n - 100)).strip()
    if n < 1000:
        return (_spell(n // 100) + ' ratus ' + _spell(n % 100)).strip()
    if n < 2000:
        return ('seribu ' + _spell(n - 1000)).strip()
    if n < 1_000_000:
        return (_spell(n // 1000) + ' ribu ' + _spell(n % 1000)).strip()
    if n < 1_000_000_000:
        return (_spell(n // 1_000_000) + ' juta ' + _spell(n % 1_000_000)).strip()
    if n < 1_000_000_000_000:
        return (_spell(n // 1_000_000_000) + ' miliar ' + _spell(n % 1_000_000_000)).strip()
    return (_spell(n // 1_000_000_000_000) + ' triliun ' + _spell(n % 1_000_000_000_000)).strip()


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'terbilang':
        print(terbilang(sys.argv[2]))
    elif cmd == 'rupiah':
        print(rupiah(float(sys.argv[2])))
    elif cmd == 'date':
        print(date_long(sys.argv[2]))
    else:
        print(__doc__)
