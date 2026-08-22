const crypto = require('crypto');

function normalizeText(value) {
  if (value === null || value === undefined) return null;
  return String(value).normalize('NFKC').trim().toLowerCase().replace(/\s+/g, ' ');
}

function canonicalInt(value) {
  if (value === null || value === undefined || value === '') return 0;
  return Number.parseInt(String(value).replace(/[^\d-]/g, ''), 10);
}

const canonical = {
  customer: normalizeText($json.customer_name || $json.customer?.name),
  payment_type: String($json.payment_type || $json.payment?.type || '').trim().toUpperCase(),
  discount: canonicalInt($json.discount || 0),
  additional_fee: canonicalInt($json.additional_fee || 0),
  items: ($json.items || []).map((item) => ({
    trip_date: item.trip_date || null,
    vehicle_type: normalizeText(item.vehicle_type),
    quantity: canonicalInt(item.quantity),
    pickup: normalizeText(item.pickup),
    destination: normalizeText(item.destination),
    unit_price: canonicalInt(item.unit_price),
  })).sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b))),
};

const payload = JSON.stringify(canonical);
const contentFingerprint = crypto.createHash('sha256').update(payload).digest('hex');

return [{ json: { ...$json, canonical_business_data: canonical, content_fingerprint: contentFingerprint } }];

