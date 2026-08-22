# LLM Parser

Initial provider: OpenAI.

Provider abstraction must allow DeepSeek, Gemini, or OpenRouter without changing business workflow.

Offline tests can use:

```text
LLM_PROVIDER=mock
```

The mock provider is deterministic and only exists for local/integration tests. It is not a production parser.

Schemas:

- `llm/schemas/intent.schema.json`
- `llm/schemas/invoice-draft.schema.json`
- `llm/schemas/invoice-patch.schema.json`

LLM output must be rejected when it does not match schema.
