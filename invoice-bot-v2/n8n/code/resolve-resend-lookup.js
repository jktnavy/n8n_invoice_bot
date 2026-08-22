const invoiceNumber = String($json.invoice_number ?? '').trim() || null;
const explicitInvoiceId = $json.invoice_id || null;
const fallbackInvoiceId = $json.last_invoice_id || null;
const invoiceId = invoiceNumber ? null : (explicitInvoiceId || fallbackInvoiceId || null);

if (!invoiceId && !invoiceNumber) {
  throw new Error('invoice identifier is required');
}

return [
  {
    json: {
      ...$json,
      invoice_id: invoiceId,
      invoice_number: invoiceNumber,
      resend_requested: true,
    },
  },
];
