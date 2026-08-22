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

Static config validation is included in `test-local` and can be run directly:

```bash
./scripts/validate-config-static.py
```

Database bootstrap validation, when credentials are available:

```bash
./scripts/validate-db.sh
```

Renderer container tests:

```bash
./scripts/test-renderer-container.sh
```

GitHub Actions CI runs:

- host-safe tests
- renderer container PDF validation
- MySQL bootstrap validation

Generated test PDFs are uploaded as CI artifacts and remain ignored by Git.

Because GitHub may reject workflow-file pushes from tokens without `workflow` scope, the workflow is stored as `ci/github-actions-invoice-bot-v2-ci.yml`. Copy it to `.github/workflows/invoice-bot-v2-ci.yml` from an account/token with workflow permission to activate it.

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

Offline acceptance simulator:

```bash
PYTHONPATH=services/invoice-core:services/llm-parser:services/workflow-sim \
  python3 -m unittest discover -s services/workflow-sim/tests -v
```
