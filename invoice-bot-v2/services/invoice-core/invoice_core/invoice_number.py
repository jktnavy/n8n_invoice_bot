ROMAN_MONTHS = {
    1: "I",
    2: "II",
    3: "III",
    4: "IV",
    5: "V",
    6: "VI",
    7: "VII",
    8: "VIII",
    9: "IX",
    10: "X",
    11: "XI",
    12: "XII",
}


def format_invoice_number(sequence_number: int, company_code: str, month: int, year: int) -> str:
    if sequence_number <= 0:
        raise ValueError("sequence_number must be positive")
    if month not in ROMAN_MONTHS:
        raise ValueError("month must be 1-12")
    return f"INV-{sequence_number:04d}/{company_code.upper()}/{ROMAN_MONTHS[month]}/{year}"

