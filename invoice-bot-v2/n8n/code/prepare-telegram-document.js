const invoiceId = $json.invoice_id;
const invoiceNumber = $json.invoice_number || $json.render_request?.invoice?.invoice_number || null;
const targetChatId = $json.target_chat_id;
const pdfPath = $json.pdf_path || $json.render_response?.file_path || null;

if (!invoiceId) {
  throw new Error('invoice_id is required');
}
if (!targetChatId || String(targetChatId).trim() === '') {
  throw new Error('target_chat_id is required');
}
if (!pdfPath || String(pdfPath).trim() === '') {
  throw new Error('pdf_path is required');
}
if (!String(pdfPath).toLowerCase().endsWith('.pdf')) {
  throw new Error('pdf_path must point to a PDF file');
}

const caption = invoiceNumber
  ? `Invoice ${invoiceNumber} - STA Transport`
  : 'Invoice STA Transport';

return [
  {
    json: {
      ...$json,
      invoice_id: Number(invoiceId),
      target_chat_id: String(targetChatId),
      pdf_path: String(pdfPath),
      telegram_method: 'sendDocument',
      telegram_document_payload: {
        chat_id: String(targetChatId),
        document_path: String(pdfPath),
        caption,
      },
      delivery_status: 'sending',
      delivery_payload_ready: true,
    },
  },
];
