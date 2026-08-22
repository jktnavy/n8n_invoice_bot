# LLM Parser

Initial provider: OpenAI.

Provider abstraction must allow DeepSeek, Gemini, or OpenRouter without changing business workflow.

Schemas:

- `llm/schemas/intent.schema.json`
- `llm/schemas/invoice-draft.schema.json`
- `llm/schemas/invoice-patch.schema.json`

LLM output must be rejected when it does not match schema.

