from dataclasses import dataclass


@dataclass(frozen=True)
class InvoiceItemInput:
    trip_date: str | None
    vehicle_type: str
    quantity: int
    pickup: str | None
    destination: str | None
    unit_price: int


def calculate_invoice_totals(
    items: list[InvoiceItemInput],
    discount: int = 0,
    additional_fee: int = 0,
    payment_type: str = "UNSPECIFIED",
    down_payment_amount: int = 0,
) -> dict:
    if discount < 0:
        raise ValueError("discount must be non-negative")
    if additional_fee < 0:
        raise ValueError("additional_fee must be non-negative")
    if down_payment_amount < 0:
        raise ValueError("down_payment_amount must be non-negative")

    calculated_items = []
    subtotal = 0
    for index, item in enumerate(items, start=1):
        if item.quantity <= 0:
            raise ValueError(f"item {index} quantity must be positive")
        if item.unit_price < 0:
            raise ValueError(f"item {index} unit_price must be non-negative")
        line_total = item.quantity * item.unit_price
        subtotal += line_total
        calculated_items.append(
            {
                "sort_order": index,
                "trip_date": item.trip_date,
                "vehicle_type": item.vehicle_type,
                "quantity": item.quantity,
                "pickup": item.pickup,
                "destination": item.destination,
                "unit_price": item.unit_price,
                "line_total": line_total,
            }
        )

    grand_total = subtotal - discount + additional_fee
    if grand_total < 0:
        raise ValueError("grand_total must be non-negative")
    normalized_payment_type = payment_type.strip().upper()
    effective_down_payment = 0 if normalized_payment_type == "FULL_PAYMENT" else down_payment_amount
    if effective_down_payment > grand_total:
        raise ValueError("down_payment_amount must not exceed grand_total")
    balance_due = grand_total - effective_down_payment if normalized_payment_type != "FULL_PAYMENT" else 0

    return {
        "items": calculated_items,
        "subtotal": subtotal,
        "discount": discount,
        "additional_fee": additional_fee,
        "grand_total": grand_total,
        "down_payment_amount": effective_down_payment,
        "balance_due": balance_due,
    }
