const response = $json.telegram_response || $json;
const ok = response.ok === true && response.result && response.result.message_id;

return [
  {
    json: {
      ...$json,
      delivery_status: ok ? 'sent' : 'failed',
      provider_message_id: ok ? String(response.result.message_id) : null,
      provider_error_code: ok ? null : String(response.error_code || ''),
      provider_error_message: ok ? null : String(response.description || 'Telegram delivery failed'),
      provider_response: response,
    },
  },
];

