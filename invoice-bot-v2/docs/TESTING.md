# Testing

## Unit

- currency formatting
- Indonesian date formatting
- terbilang
- calculation
- fingerprint
- JSON schema validation
- invoice sequence

Host-safe checks:

```bash
./scripts/test-local.sh
```

Renderer container tests:

```bash
docker build --target test -t invoice-renderer-test services/invoice-renderer
docker run --rm invoice-renderer-test
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
