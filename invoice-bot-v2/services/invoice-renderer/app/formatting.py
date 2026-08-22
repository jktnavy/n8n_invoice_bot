from datetime import date
from decimal import Decimal

MONTHS = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}


def rupiah(amount: Decimal | int | str) -> str:
    value = Decimal(str(amount or 0)).quantize(Decimal("1"))
    return "Rp" + f"{int(value):,}".replace(",", ".")


def date_long(value: date | None) -> str:
    if value is None:
        return "-"
    return f"{value.day} {MONTHS[value.month]} {value.year}"


def terbilang(value: Decimal | int | str) -> str:
    number = int(Decimal(str(value or 0)))
    if number == 0:
        return "Nol Rupiah"
    if number < 0:
        return "Minus " + _spell(abs(number)).title() + " Rupiah"
    return _spell(number).strip().title() + " Rupiah"


def _spell(number: int) -> str:
    words = [
        "",
        "satu",
        "dua",
        "tiga",
        "empat",
        "lima",
        "enam",
        "tujuh",
        "delapan",
        "sembilan",
        "sepuluh",
        "sebelas",
    ]
    if number < 12:
        return words[number]
    if number < 20:
        return _spell(number - 10) + " belas"
    if number < 100:
        return (_spell(number // 10) + " puluh " + _spell(number % 10)).strip()
    if number < 200:
        return ("seratus " + _spell(number - 100)).strip()
    if number < 1000:
        return (_spell(number // 100) + " ratus " + _spell(number % 100)).strip()
    if number < 2000:
        return ("seribu " + _spell(number - 1000)).strip()
    if number < 1_000_000:
        return (_spell(number // 1000) + " ribu " + _spell(number % 1000)).strip()
    if number < 1_000_000_000:
        return (_spell(number // 1_000_000) + " juta " + _spell(number % 1_000_000)).strip()
    if number < 1_000_000_000_000:
        return (_spell(number // 1_000_000_000) + " miliar " + _spell(number % 1_000_000_000)).strip()
    return (_spell(number // 1_000_000_000_000) + " triliun " + _spell(number % 1_000_000_000_000)).strip()

