#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const assert = require('assert');

const root = path.resolve(__dirname, '..');

function runSnippet(relativePath, json) {
  const code = fs.readFileSync(path.join(root, relativePath), 'utf8');
  const input = { all: () => [{ json }] };
  const fn = new Function('$json', '$input', 'require', code);
  return fn(json, input, require);
}

const invoice = {
  customer_name: 'PT Nusa Horizon Wisata',
  payment_type: 'FULL_PAYMENT',
  items: [
    {
      trip_date: '2026-08-15',
      vehicle_type: 'Medium Bus',
      quantity: 2,
      pickup: 'Harapan Indah Bekasi',
      destination: 'Cisarua Puncak',
      unit_price: 2800000,
    },
    {
      trip_date: '2026-08-17',
      vehicle_type: 'Medium Bus',
      quantity: 2,
      pickup: 'Cisarua Puncak',
      destination: 'Jakarta',
      unit_price: 2600000,
    },
  ],
};

const calculated = runSnippet('n8n/code/calculate-invoice.js', invoice)[0].json;
assert.strictEqual(calculated.items[0].line_total, 5600000);
assert.strictEqual(calculated.items[1].line_total, 5200000);
assert.strictEqual(calculated.grand_total, 10800000);
assert.strictEqual(calculated.balance_due, 0);

const downPayment = runSnippet('n8n/code/calculate-invoice.js', {
  ...invoice,
  payment_type: 'DOWN_PAYMENT',
  down_payment_amount: 1000000,
})[0].json;
assert.strictEqual(downPayment.grand_total, 10800000);
assert.strictEqual(downPayment.down_payment_amount, 1000000);
assert.strictEqual(downPayment.balance_due, 9800000);

const fingerprintA = runSnippet('n8n/code/content-fingerprint.js', calculated)[0].json.content_fingerprint;
const fingerprintB = runSnippet('n8n/code/content-fingerprint.js', {
  ...calculated,
  customer_name: ' pt nusa horizon wisata ',
  items: [
    {
      trip_date: '2026-08-15',
      vehicle_type: ' medium   bus ',
      quantity: '2',
      pickup: 'harapan indah bekasi',
      destination: 'cisarua puncak',
      unit_price: '2.8 juta',
    },
    {
      trip_date: '2026-08-17',
      vehicle_type: 'medium bus',
      quantity: '2',
      pickup: 'cisarua puncak',
      destination: 'jakarta',
      unit_price: 'Rp2.600.000',
    },
  ],
})[0].json.content_fingerprint;
assert.strictEqual(fingerprintA, fingerprintB);

const preview = runSnippet('n8n/code/render-preview.js', {
  ...calculated,
  included: ['kendaraan', 'pengemudi', 'BBM'],
  excluded: ['tol', 'parkir', 'tips pengemudi'],
})[0].json.preview_text;
assert.match(preview, /PRATINJAU INVOICE/);
assert.match(preview, /Rp10\.800\.000/);

const paymentPreview = runSnippet('n8n/code/render-preview.js', downPayment)[0].json.preview_text;
assert.match(paymentPreview, /DP: Rp1\.000\.000/);
assert.match(paymentPreview, /Sisa pembayaran: Rp9\.800\.000/);

const patchedTrip = runSnippet('n8n/code/apply-patch.js', {
  active_draft: downPayment,
  patches: [{ target: 'item:return_trip', field: 'trip_date', value: '2026-08-18' }],
})[0].json;
assert.strictEqual(patchedTrip.items[1].trip_date, '2026-08-18');
assert.strictEqual(patchedTrip.revision_applied, true);

const patchedPayment = runSnippet('n8n/code/apply-patch.js', {
  active_draft: downPayment,
  patches: [
    { target: 'draft', field: 'payment_type', value: 'FULL_PAYMENT' },
    { target: 'draft', field: 'down_payment_amount', value: 0 },
  ],
})[0].json;
const recalculatedPayment = runSnippet('n8n/code/calculate-invoice.js', patchedPayment)[0].json;
assert.strictEqual(recalculatedPayment.payment_type, 'FULL_PAYMENT');
assert.strictEqual(recalculatedPayment.down_payment_amount, 0);
assert.strictEqual(recalculatedPayment.balance_due, 0);

const approvedInvoice = {
  invoice_id: 1,
  invoice_number: 'INV-0001/STA/VIII/2026',
  invoice_date: '2026-08-22',
  customer_name: calculated.customer_name,
  payment_type: calculated.payment_type,
  subtotal: calculated.subtotal,
  discount: calculated.discount,
  additional_fee: calculated.additional_fee,
  grand_total: calculated.grand_total,
  down_payment_amount: calculated.down_payment_amount,
  balance_due: calculated.balance_due,
  included: ['kendaraan', 'pengemudi', 'BBM'],
  excluded: ['tol', 'parkir', 'tips pengemudi'],
  items: calculated.items.map((item) => ({ ...item, uom: 'Unit' })),
};
const renderHandoff = runSnippet('n8n/code/prepare-render-request.js', {
  invoice: approvedInvoice,
  telegram_chat_id: '123456',
})[0].json;
assert.strictEqual(renderHandoff.renderer_contract, 'FULL_VALIDATED_INVOICE_PAYLOAD');
assert.strictEqual(renderHandoff.target_chat_id, '123456');
assert.strictEqual(renderHandoff.render_request.invoice.invoice_number, 'INV-0001/STA/VIII/2026');
assert.strictEqual(renderHandoff.render_request.invoice.status_label, 'LUNAS');

const delivery = runSnippet('n8n/code/telegram-delivery-result.js', {
  telegram_response: { ok: true, result: { message_id: 12345 } },
})[0].json;
assert.strictEqual(delivery.delivery_status, 'sent');
assert.strictEqual(delivery.provider_message_id, '12345');

console.log(JSON.stringify({ n8n_code_tests: 'PASS', grand_total: calculated.grand_total, fingerprint: fingerprintA }));
