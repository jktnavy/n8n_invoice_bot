# Testing

## Unit

- currency formatting
- Indonesian date formatting
- terbilang
- calculation
- fingerprint
- JSON schema validation
- invoice sequence
- n8n deterministic Code node snippets
- static database schema invariants

Host-safe checks:

```bash
./scripts/test-local.sh
```

Database bootstrap validation, when credentials are available:

```bash
./scripts/validate-db.sh
```

Renderer container tests:

```bash
./scripts/test-renderer-container.sh
```

## Integration

- MySQL schema
- renderer health/render
- mocked LLM
- mocked Telegram

## E2E

- create invoice and approve
- revise draft
- retry failed delivery
- duplicate detection
- ambiguous request asks for missing data
