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

const webhookMessage = runSnippet('n8n/code/normalize-telegram-message.js', {
  body: {
    update_id: 123,
    message: {
      message_id: 456,
      text: 'Buat invoice PT Nusa',
      chat: { id: 789 },
      from: { id: 111 },
    },
  },
})[0].json;
assert.strictEqual(webhookMessage.raw_message, 'Buat invoice PT Nusa');
assert.strictEqual(webhookMessage.telegram_chat_id, '789');
assert.strictEqual(webhookMessage.telegram_user_id, '111');
assert.strictEqual(webhookMessage.telegram_message_id, '456');
assert.strictEqual(webhookMessage.telegram_update_id, '123');
assert.match(webhookMessage.correlation_id, /^[0-9a-f-]{36}$/);

const manualMessage = runSnippet('n8n/code/normalize-telegram-message.js', {
  text: 'status invoice',
  chat_id: 'chat-1',
})[0].json;
assert.strictEqual(manualMessage.raw_message, 'status invoice');
assert.strictEqual(manualMessage.telegram_chat_id, 'chat-1');

const routedIntent = runSnippet('n8n/code/intent-prefilter.js', webhookMessage)[0].json;
assert.strictEqual(routedIntent.intent, 'CREATE_INVOICE');
assert.strictEqual(routedIntent.intent_source, 'deterministic_prefilter');

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

const telegramDocument = runSnippet('n8n/code/prepare-telegram-document.js', {
  invoice_id: 1,
  invoice_number: 'INV-0001/STA/VIII/2026',
  target_chat_id: '123456',
  pdf_path: '/data/invoices/INV-0001.pdf',
})[0].json;
assert.strictEqual(telegramDocument.telegram_method, 'sendDocument');
assert.strictEqual(telegramDocument.delivery_status, 'sending');
assert.strictEqual(telegramDocument.telegram_document_payload.chat_id, '123456');
assert.strictEqual(telegramDocument.telegram_document_payload.document_path, '/data/invoices/INV-0001.pdf');
assert.match(telegramDocument.telegram_document_payload.caption, /INV-0001\/STA\/VIII\/2026/);

const resendDocument = runSnippet('n8n/code/prepare-telegram-document.js', {
  invoice_id: 1,
  invoice_number: 'INV-0001/STA/VIII/2026',
  target_chat_id: '123456',
  pdf_path: '/data/invoices/INV-0001.pdf',
  resend_requested: true,
})[0].json;
assert.strictEqual(resendDocument.telegram_method, 'sendDocument');
assert.strictEqual(resendDocument.telegram_document_payload.document_path, telegramDocument.telegram_document_payload.document_path);
assert.strictEqual(resendDocument.invoice_id, telegramDocument.invoice_id);
assert.strictEqual(resendDocument.resend_requested, true);

const delivery = runSnippet('n8n/code/telegram-delivery-result.js', {
  http_status: 200,
  telegram_response: { ok: true, result: { message_id: 12345 } },
})[0].json;
assert.strictEqual(delivery.delivery_status, 'sent');
assert.strictEqual(delivery.provider_message_id, '12345');
assert.strictEqual(delivery.http_status, 200);

const failedDelivery = runSnippet('n8n/code/telegram-delivery-result.js', {
  http_status: 400,
  telegram_response: { ok: false, error_code: 400, description: 'Bad Request: chat not found' },
})[0].json;
assert.strictEqual(failedDelivery.delivery_status, 'failed');
assert.strictEqual(failedDelivery.provider_message_id, null);
assert.strictEqual(failedDelivery.http_status, 400);
assert.strictEqual(failedDelivery.provider_error_code, '400');
assert.match(failedDelivery.provider_error_message, /chat not found/);

const missingMessageIdDelivery = runSnippet('n8n/code/telegram-delivery-result.js', {
  http_status: 200,
  telegram_response: { ok: true, result: {} },
})[0].json;
assert.strictEqual(missingMessageIdDelivery.delivery_status, 'failed');
assert.strictEqual(missingMessageIdDelivery.provider_message_id, null);

const sanitizedError = runSnippet('n8n/code/sanitize-error.js', {
  execution: { id: 'exec-1' },
  workflow: { name: '01-telegram-router' },
  node: { name: 'Normalize Telegram Message' },
  telegram_chat_id: '123456',
  error: {
    name: 'Error',
    message: 'request failed token=secret password=hunter2 api_key=sk-test authorization=Bearer-secret',
  },
})[0].json;
assert.strictEqual(sanitizedError.event_type, 'ERROR');
assert.strictEqual(sanitizedError.correlation_id, 'exec-1');
assert.strictEqual(sanitizedError.telegram_chat_id, '123456');
assert.doesNotMatch(sanitizedError.message, /secret|hunter2|sk-test|Bearer-secret/);
assert.match(sanitizedError.message, /token=\[redacted\]/);

console.log(JSON.stringify({ n8n_code_tests: 'PASS', grand_total: calculated.grand_total, fingerprint: fingerprintA }));
