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

Runtime structured-output smoke test:

```bash
PYTHONPATH=services/llm-parser python3 -m llm_parser.cli structured-smoke
```

With live `LLM_API_KEY` and `LLM_MODEL`, this classifies a PT Nusa invoice
creation message and extracts an invoice draft. It fails if the intent is not
`CREATE_INVOICE`, the draft schema is invalid, no customer/items are returned,
or the smoke fixture still reports missing fields. Without live credentials it
reports `skipped_live_credentials_missing`.

OpenAI provider implementation:

- Uses the Responses API endpoint.
- Sends schema-constrained `text.format` JSON Schema payloads with `strict: true`.
- Uses only stdlib HTTP so host-safe tests do not require SDK installation.
- Requires `LLM_API_KEY` and `LLM_MODEL` at runtime.

Provider switching:

- `LLM_PROVIDER=openai` uses the default OpenAI Responses endpoint.
- `LLM_PROVIDER=deepseek` or `LLM_PROVIDER=openrouter` uses the same
  Responses-compatible adapter and requires `LLM_BASE_URL` to be set to that
  provider's compatible `/responses` endpoint.
- `LLM_PROVIDER=gemini` is reserved behind the same interface but intentionally
  not enabled until a provider-specific structured output adapter is added.

This follows the official OpenAI Structured Outputs guidance: Structured Outputs are recommended over JSON mode when possible because they enforce schema adherence, and the Responses API supports schema-constrained output with `text.format`.
