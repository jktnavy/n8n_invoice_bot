const response = $json.telegram_response || $json;
const ok = response.ok === true && response.result && response.result.message_id;
const errorCode = response.error_code ?? $json.http_status ?? null;

return [
  {
    json: {
      ...$json,
      delivery_status: ok ? 'sent' : 'failed',
      provider_message_id: ok ? String(response.result.message_id) : null,
      http_status: $json.http_status ?? response.http_status ?? null,
      provider_error_code: ok || errorCode === null ? null : String(errorCode),
      provider_error_message: ok ? null : String(response.description || 'Telegram delivery failed'),
      provider_response: response,
    },
  },
];
