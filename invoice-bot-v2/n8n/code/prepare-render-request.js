const invoice = $json.invoice || $json.approved_invoice || $json;
const targetChatId = $json.target_chat_id || $json.telegram_chat_id || invoice.telegram_chat_id || null;

const requiredFields = [
  'invoice_id',
  'invoice_number',
  'invoice_date',
  'customer_name',
  'payment_type',
  'subtotal',
  'discount',
  'additional_fee',
  'grand_total',
  'down_payment_amount',
  'balance_due',
  'items',
];

for (const field of requiredFields) {
  if (invoice[field] === undefined || invoice[field] === null || invoice[field] === '') {
    throw new Error(`approved invoice missing ${field}`);
  }
}
if (!Array.isArray(invoice.items) || invoice.items.length === 0) {
  throw new Error('approved invoice requires at least one item');
}
if (!targetChatId) {
  throw new Error('target_chat_id is required for Telegram delivery');
}
if (!/^INV-\d{4}\/STA\/(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)\/\d{4}$/.test(String(invoice.invoice_number))) {
  throw new Error('approved invoice invoice_number has invalid format');
}

let subtotal = 0;
const items = invoice.items.map((item, index) => {
  for (const field of ['sort_order', 'vehicle_type', 'quantity', 'uom', 'unit_price', 'line_total']) {
    if (item[field] === undefined || item[field] === null || item[field] === '') {
      throw new Error(`approved invoice item ${index + 1} missing ${field}`);
    }
  }
  const quantity = Number(item.quantity);
  const unitPrice = Number(item.unit_price);
  const lineTotal = Number(item.line_total);
  if (quantity <= 0 || unitPrice < 0 || lineTotal !== quantity * unitPrice) {
    throw new Error(`approved invoice item ${index + 1} has invalid total`);
  }
  subtotal += lineTotal;
  return {
    ...item,
    sort_order: Number(item.sort_order),
    quantity,
    unit_price: unitPrice,
    line_total: lineTotal,
  };
});

const discount = Number(invoice.discount || 0);
const additionalFee = Number(invoice.additional_fee || 0);
const grandTotal = Number(invoice.grand_total);
const downPaymentAmount = Number(invoice.down_payment_amount || 0);
const balanceDue = Number(invoice.balance_due || 0);
const paymentType = String(invoice.payment_type).trim().toUpperCase();

if (Number(invoice.subtotal) !== subtotal) {
  throw new Error(`approved invoice subtotal expected ${subtotal}`);
}
if (grandTotal !== subtotal - discount + additionalFee) {
  throw new Error('approved invoice grand_total does not match subtotal - discount + additional_fee');
}
if (downPaymentAmount > grandTotal) {
  throw new Error('approved invoice down_payment_amount exceeds grand_total');
}
const expectedBalance = paymentType === 'FULL_PAYMENT' ? 0 : grandTotal - downPaymentAmount;
if (balanceDue !== expectedBalance) {
  throw new Error(`approved invoice balance_due expected ${expectedBalance}`);
}

const normalizedInvoice = {
  ...invoice,
  payment_type: paymentType,
  items,
  subtotal,
  discount,
  additional_fee: additionalFee,
  grand_total: grandTotal,
  down_payment_amount: downPaymentAmount,
  balance_due: balanceDue,
  status_label: balanceDue === 0 ? 'LUNAS' : 'BELUM LUNAS',
};

return [
  {
    json: {
      ...$json,
      invoice_id: Number(invoice.invoice_id),
      target_chat_id: String(targetChatId),
      render_request: { invoice: normalizedInvoice },
      renderer_contract: 'FULL_VALIDATED_INVOICE_PAYLOAD',
      delivery_payload_ready: true,
    },
  },
];
