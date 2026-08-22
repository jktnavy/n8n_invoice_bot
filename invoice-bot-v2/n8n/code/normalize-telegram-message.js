const update = $json.body || $json;
const message = update.message || update.edited_message || {};
const text = String(message.text ?? message.caption ?? update.text ?? '').trim();
const chatId = message.chat?.id || update.chat_id || null;
const userId = message.from?.id || update.user_id || null;
const messageId = message.message_id || update.message_id || null;
const updateId = update.update_id || null;

if (!chatId) {
  throw new Error('Telegram chat.id is required');
}
if (text === '') {
  throw new Error('Telegram message text or caption is required');
}

return [
  {
    json: {
      raw_message: text,
      telegram_chat_id: String(chatId),
      telegram_user_id: userId ? String(userId) : null,
      telegram_message_id: messageId ? String(messageId) : null,
      telegram_update_id: updateId ? String(updateId) : null,
      correlation_id: crypto.randomUUID(),
    },
  },
];
