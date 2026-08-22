const text = ($json.raw_message || '').trim().toLowerCase();
const approvals = new Set(['setuju', 'iya', 'ya', 'oke', 'ok', 'gas', 'lanjut', 'sudah benar', 'sip']);

let intent = 'UNKNOWN';
if (approvals.has(text)) {
  intent = 'APPROVE_DRAFT';
} else if (/\b(help|bantuan|cara pakai|menu|panduan)\b/.test(text)) {
  intent = 'HELP';
} else if (/\b(batal|cancel|batalkan|void)\b/.test(text) && (/\binv-\d{4}\/sta\/[ivxlcdm]+\/\d{4}\b/.test(text) || /\b(final|sudah jadi|sudah dibuat)\b/.test(text))) {
  intent = 'CANCEL_INVOICE';
} else if (/\b(batal|cancel|batalkan)\b/.test(text)) {
  intent = 'CANCEL_DRAFT';
} else if (/kirim.*ulang|kirim.*lagi|resend/.test(text)) {
  intent = 'RESEND_INVOICE';
} else if (/lihat.*detail|detail.*invoice|tampilkan.*invoice/.test(text)) {
  intent = 'GET_INVOICE';
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
