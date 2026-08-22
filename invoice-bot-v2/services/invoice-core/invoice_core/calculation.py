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
) -> dict:
    if discount < 0:
        raise ValueError("discount must be non-negative")
    if additional_fee < 0:
        raise ValueError("additional_fee must be non-negative")

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

    return {
        "items": calculated_items,
        "subtotal": subtotal,
        "discount": discount,
        "additional_fee": additional_fee,
        "grand_total": grand_total,
    }

