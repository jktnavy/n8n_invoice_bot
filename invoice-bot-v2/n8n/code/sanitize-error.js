const execution = $json.execution || {};
const workflow = $json.workflow || {};
const node = $json.node || {};
const error = $json.error || {};

const rawMessage = String(error.message || 'Unknown error');
const redactSensitive = (value) => String(value)
  .replace(/(token|password|api[_-]?key|authorization)\s*[:=]\s*\S+/gi, '$1=[redacted]')
  .replace(/\bsk-[A-Za-z0-9_-]{8,}\b/g, 'sk-[redacted]')
  .replace(/\b\d{6,}:[A-Za-z0-9_-]{20,}\b/g, '[redacted-telegram-token]');
const redactedMessage = redactSensitive(rawMessage);

return [
  {
    json: {
      correlation_id: $json.correlation_id || execution.id || crypto.randomUUID(),
      event_type: 'ERROR',
      entity_type: $json.entity_type || null,
      entity_id: $json.entity_id ? String($json.entity_id) : null,
      telegram_chat_id: $json.telegram_chat_id ? String($json.telegram_chat_id) : null,
      telegram_user_id: $json.telegram_user_id ? String($json.telegram_user_id) : null,
      workflow_name: workflow.name || null,
      node_name: node.name || null,
      message: redactedMessage,
      metadata: {
        error_type: error.name || 'Error',
        execution_id: execution.id || null,
      },
    },
  },
];
