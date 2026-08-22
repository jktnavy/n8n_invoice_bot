# LLM Parser Service Contract

This directory contains provider-neutral parser code and contracts for n8n usage.

Initial provider:

```text
OpenAI
```

Business workflow must call the parser through provider-neutral operations:

```text
classify_intent(message)
extract_invoice(message, context)
extract_patch(message, active_draft)
```

Provider output must match JSON schemas under `llm/schemas`.

