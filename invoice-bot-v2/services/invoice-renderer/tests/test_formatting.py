from decimal import Decimal

from app.formatting import rupiah, terbilang


def test_rupiah_uses_indonesian_thousands_separator():
    assert rupiah(Decimal("10800000")) == "Rp10.800.000"


def test_terbilang_outputs_indonesian_words():
    assert terbilang(Decimal("10800000")) == "Sepuluh Juta Delapan Ratus Ribu Rupiah"

