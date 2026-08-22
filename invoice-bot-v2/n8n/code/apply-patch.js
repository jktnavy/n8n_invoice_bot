const draft = $json.active_draft || $json;
const patches = $json.patches || $json.patch?.patches || [];

if (!Array.isArray(patches) || patches.length === 0) {
  throw new Error('at least one patch is required');
}
if (!Array.isArray(draft.items) || draft.items.length === 0) {
  throw new Error('active draft items are required');
}

const updated = {
  ...draft,
  items: draft.items.map((item) => ({ ...item })),
};

for (const operation of patches) {
  if (operation.target === 'item:return_trip') {
    const item = updated.items[updated.items.length - 1];
    applyItemPatch(item, operation.field, operation.value);
  } else if (operation.target === 'draft') {
    applyDraftPatch(updated, operation.field, operation.value);
  } else {
    throw new Error(`unsupported patch target: ${operation.target}`);
  }
}

return [{ json: { ...$json, ...updated, revision_applied: true } }];

function applyItemPatch(item, field, value) {
  if (!['trip_date', 'unit_price'].includes(field)) {
    throw new Error(`unsupported item patch field: ${field}`);
  }
  if (field === 'unit_price') {
    const numericValue = Number(value);
    if (!Number.isInteger(numericValue) || numericValue < 0) {
      throw new Error('unit_price patch must be a non-negative integer');
    }
    item.unit_price = numericValue;
    return;
  }
  item[field] = value;
}

function applyDraftPatch(draft, field, value) {
  if (!['payment_type', 'down_payment_amount'].includes(field)) {
    throw new Error(`unsupported draft patch field: ${field}`);
  }
  if (field === 'payment_type') {
    draft.payment_type = String(value).trim().toUpperCase();
    return;
  }
  const numericValue = Number(value);
  if (!Number.isInteger(numericValue) || numericValue < 0) {
    throw new Error('down_payment_amount patch must be a non-negative integer');
  }
  draft.down_payment_amount = numericValue;
}
