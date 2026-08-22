from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PaymentType = Literal["FULL_PAYMENT", "DOWN_PAYMENT", "BALANCE_PAYMENT", "UNSPECIFIED"]


class InvoiceItem(BaseModel):
    sort_order: int = Field(ge=0)
    trip_date: date | None = None
    vehicle_type: str = Field(min_length=1, max_length=100)
    quantity: Decimal = Field(gt=0)
    uom: str = Field(default="Unit", min_length=1, max_length=20)
    pickup: str | None = Field(default=None, max_length=500)
    destination: str | None = Field(default=None, max_length=500)
    unit_price: Decimal = Field(ge=0)
    line_total: Decimal = Field(ge=0)
    description: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_line_total(self) -> "InvoiceItem":
        expected = self.quantity * self.unit_price
        if self.line_total != expected:
            raise ValueError(f"line_total must equal quantity * unit_price, expected {expected}")
        return self


class CompanyInfo(BaseModel):
    name: str = "STA Transport"
    tagline: str = "Sewa Bus Pariwisata"
    address: str = "Jl. Akses Tol Cimanggis No. 73, Leuwinanggung, Tapos, Depok 16456"
    phone: str = "Handphone: 0811-800-8613"
    whatsapp: str = "WhatsApp: 0812-840-21376"
    email: str = "statransdotcom@gmail.com"
    website: str = "www.statransport.co.id"
    signatory_city: str = "Depok"
    signatory_name: str = "Suhendi"
    signatory_position: str = "Marketing Executive"


class InvoicePayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    invoice_id: int | None = None
    invoice_number: str = Field(min_length=1, max_length=50)
    invoice_date: date
    customer_name: str = Field(min_length=1, max_length=255)
    payment_type: PaymentType
    subtotal: Decimal = Field(ge=0)
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    additional_fee: Decimal = Field(default=Decimal("0"), ge=0)
    grand_total: Decimal = Field(ge=0)
    down_payment_amount: Decimal = Field(default=Decimal("0"), ge=0)
    balance_due: Decimal = Field(default=Decimal("0"), ge=0)
    included: list[str] = Field(default_factory=list)
    excluded: list[str] = Field(default_factory=list)
    notes: str | None = None
    status_label: str = "LUNAS"
    items: list[InvoiceItem] = Field(min_length=1)
    company: CompanyInfo = Field(default_factory=CompanyInfo)

    @field_validator("included", "excluded")
    @classmethod
    def compact_strings(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()]

    @model_validator(mode="after")
    def validate_totals(self) -> "InvoicePayload":
        subtotal = sum((item.line_total for item in self.items), Decimal("0"))
        if self.subtotal != subtotal:
            raise ValueError(f"subtotal must equal item total, expected {subtotal}")
        expected_grand_total = self.subtotal - self.discount + self.additional_fee
        if self.grand_total != expected_grand_total:
            raise ValueError(f"grand_total must equal subtotal - discount + additional_fee, expected {expected_grand_total}")
        if self.down_payment_amount > self.grand_total:
            raise ValueError("down_payment_amount must not exceed grand_total")
        if self.payment_type == "FULL_PAYMENT" and self.down_payment_amount != 0:
            raise ValueError("down_payment_amount must be zero for FULL_PAYMENT")
        expected_balance = Decimal("0") if self.payment_type == "FULL_PAYMENT" else self.grand_total - self.down_payment_amount
        if self.balance_due != expected_balance:
            raise ValueError(f"balance_due must match payment type and down payment, expected {expected_balance}")
        return self


class RenderInvoiceRequest(BaseModel):
    invoice: InvoicePayload


class RenderInvoiceResponse(BaseModel):
    ok: bool
    file_path: str
    sha256: str
    size: int
