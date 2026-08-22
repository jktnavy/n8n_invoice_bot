# Telegram Gateway

Dependency-free Telegram Bot API helper.

Responsibilities:

- `getMe` health probing
- `sendDocument` request construction
- provider response mapping into delivery metadata
- preserving Telegram error code/description

Non-responsibilities:

- no invoice creation
- no invoice numbering
- no retry decisions
- no database writes
- no fallback destination chat

The caller must pass the source Telegram `chat.id` as `target_chat_id`.

