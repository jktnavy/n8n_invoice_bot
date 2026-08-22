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
- renderer payload/no-database contract

Host-safe checks:

```bash
./scripts/test-local.sh
```

Static config validation is included in `test-local` and can be run directly:

```bash
./scripts/validate-config-static.py
./scripts/validate-deploy-static.py
./scripts/validate-renderer-contract.py
./scripts/scan-secrets.py
./scripts/readiness-gate.py
```

Runtime evidence template:

```bash
cp docs/readiness-evidence.example.json readiness-evidence.json
./scripts/readiness-gate.py --evidence readiness-evidence.json
```

The actual `readiness-evidence.json` file is ignored by Git because it is a
local/live verification artifact.

LLM structured-output smoke check:

```bash
PYTHONPATH=services/llm-parser python3 -m llm_parser.cli structured-smoke
```

Use `LLM_PROVIDER=mock` for offline deterministic validation. With live
provider credentials, the same command exercises intent classification and
invoice draft extraction against the configured provider.

Database bootstrap validation, when credentials are available:

```bash
./scripts/validate-db.sh
```

Renderer container tests:

```bash
./scripts/test-renderer-container.sh
```

This builds the renderer test target, runs renderer unit tests inside the
container, renders the PT Nusa fixture through the runtime image, and verifies
the generated PDF filename, non-trivial size, `%PDF` signature, SHA-256, and
reported renderer metadata.

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

Acceptance JSON evidence:

```bash
PYTHONPATH=services/invoice-core:services/llm-parser:services/workflow-sim \
  python3 scripts/run-acceptance-sim.py
```

The JSON runner summarizes scenario A-E outcomes, invoice/delivery counts,
sequence usage, and audit event counts for CI logs or pre-live review.
