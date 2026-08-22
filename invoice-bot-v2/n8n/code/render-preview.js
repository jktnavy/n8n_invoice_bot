function rupiah(amount) {
  return 'Rp' + Number(amount || 0).toLocaleString('id-ID');
}

function formatDate(value) {
  if (!value) return '-';
  return new Intl.DateTimeFormat('id-ID', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(value));
}

const lines = [
  '📄 PRATINJAU INVOICE',
  '',
  'Kepada:',
  $json.customer_name,
  '',
];

for (const item of $json.items || []) {
  lines.push(formatDate(item.trip_date));
  lines.push(`${item.vehicle_type}`);
  lines.push(`${item.quantity} unit × ${rupiah(item.unit_price)}`);
  lines.push(`= ${rupiah(item.line_total)}`);
  lines.push(`${item.pickup || '-'} → ${item.destination || '-'}`);
  lines.push('');
}

lines.push('TOTAL');
lines.push(rupiah($json.grand_total));
lines.push('');
lines.push('Pembayaran:');
lines.push($json.payment_type === 'FULL_PAYMENT' ? 'LUNAS / FULL PAYMENT' : $json.payment_type);

if (($json.included || []).length) {
  lines.push('');
  lines.push('Termasuk:');
  for (const item of $json.included) lines.push(`✓ ${item}`);
}

if (($json.excluded || []).length) {
  lines.push('');
  lines.push('Tidak termasuk:');
  for (const item of $json.excluded) lines.push(`- ${item}`);
}

lines.push('');
lines.push('Sudah benar?');
lines.push('Balas: setuju atau tulis revisinya.');

return [{ json: { ...$json, preview_text: lines.join('\n') } }];

