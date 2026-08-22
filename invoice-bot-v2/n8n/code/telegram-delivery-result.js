const response = $json.telegram_response || $json;
const ok = response.ok === true && response.result && response.result.message_id;
const errorCode = response.error_code ?? $json.http_status ?? null;
const redactSensitive = (value) => String(value).replace(
  /(token|password|api[_-]?key|authorization)=\S+/gi,
  '$1=[redacted]',
);
const sanitizeValue = (value) => {
  if (typeof value === 'string') return redactSensitive(value);
  if (Array.isArray(value)) return value.map(sanitizeValue);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, sanitizeValue(item)]));
  }
  return value;
};
const sanitizedResponse = sanitizeValue(response);

return [
  {
    json: {
      ...$json,
      delivery_status: ok ? 'sent' : 'failed',
      provider_message_id: ok ? String(response.result.message_id) : null,
      http_status: $json.http_status ?? response.http_status ?? null,
      provider_error_code: ok || errorCode === null ? null : String(errorCode),
      provider_error_message: ok ? null : redactSensitive(response.description || 'Telegram delivery failed'),
      provider_response: sanitizedResponse,
    },
  },
];
