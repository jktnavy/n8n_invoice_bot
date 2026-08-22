const items = $json.items || [];
const discount = Number($json.discount || 0);
const additionalFee = Number($json.additional_fee || 0);
const paymentType = String($json.payment_type || $json.payment?.type || 'UNSPECIFIED').trim().toUpperCase();
const downPaymentAmount = Number($json.down_payment_amount || $json.payment?.down_payment_amount || 0);

if (discount < 0 || additionalFee < 0 || downPaymentAmount < 0) {
  throw new Error('discount, additional_fee, and down_payment_amount must be non-negative');
}

let subtotal = 0;
const calculatedItems = items.map((item, index) => {
  const quantity = Number(item.quantity);
  const unitPrice = Number(item.unit_price);
  if (!Number.isInteger(quantity) || quantity <= 0) {
    throw new Error(`item ${index + 1} quantity must be a positive integer`);
  }
  if (!Number.isInteger(unitPrice) || unitPrice < 0) {
    throw new Error(`item ${index + 1} unit_price must be a non-negative integer`);
  }
  const lineTotal = quantity * unitPrice;
  subtotal += lineTotal;
  return {
    ...item,
    sort_order: index + 1,
    quantity,
    unit_price: unitPrice,
    line_total: lineTotal,
  };
});

const grandTotal = subtotal - discount + additionalFee;
if (grandTotal < 0) {
  throw new Error('grand_total must be non-negative');
}
const effectiveDownPayment = paymentType === 'FULL_PAYMENT' ? 0 : downPaymentAmount;
if (effectiveDownPayment > grandTotal) {
  throw new Error('down_payment_amount must not exceed grand_total');
}

const balanceDue = paymentType === 'FULL_PAYMENT' ? 0 : grandTotal - effectiveDownPayment;

return [
  {
    json: {
      ...$json,
      items: calculatedItems,
      payment_type: paymentType,
      subtotal,
      discount,
      additional_fee: additionalFee,
      grand_total: grandTotal,
      down_payment_amount: effectiveDownPayment,
      balance_due: balanceDue,
    },
  },
];
