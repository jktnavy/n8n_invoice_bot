const text = ($json.raw_message || '').trim().toLowerCase();
const approvals = new Set(['setuju', 'iya', 'ya', 'oke', 'ok', 'gas', 'lanjut', 'buat', 'sudah benar', 'sip']);

let intent = 'UNKNOWN';
if (approvals.has(text)) {
  intent = 'APPROVE_DRAFT';
} else if (/kirim.*ulang|kirim.*lagi|resend/.test(text)) {
  intent = 'RESEND_INVOICE';
} else if (/status|sudah terkirim|invoice .* mana/.test(text)) {
  intent = 'GET_STATUS';
} else if (/ganti|ubah|revisi|jadi|tidak usah dp/.test(text) || (/tanpa dp/.test(text) && !/buat|invoice|tagihan/.test(text))) {
  intent = 'UPDATE_DRAFT';
} else if (/invoice|tagihan/.test(text)) {
  intent = 'CREATE_INVOICE';
}

return [
  {
    json: {
      ...$json,
      intent,
      confidence: intent === 'UNKNOWN' ? 0.2 : 0.7,
      intent_source: 'deterministic_prefilter',
    },
  },
];
