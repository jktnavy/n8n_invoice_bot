# STA Transport Invoice Bot V2

Greenfield conversational invoice bot for Telegram. V2 is isolated from the legacy Hermes implementation.

## Quick Start

1. Copy `.env.example` to `.env` and fill local secrets.
2. Start local services:

```bash
docker compose up -d
```

3. Open n8n at `http://localhost:5678`.
4. Expose the n8n webhook with Cloudflare Tunnel for local Telegram development.

## Architecture

```text
Telegram
-> n8n router
-> LLM structured intent/extraction
-> n8n deterministic workflow
-> MySQL invoice_bot_v2
-> FastAPI invoice-renderer
-> Telegram Bot API
```

LLM understands language. n8n orchestrates business workflow. MySQL stores truth. Python renders documents. Telegram confirms delivery.

## Directory Structure

```text
database/                 MySQL schema and migrations
docs/                     Architecture and operations notes
llm/                      Provider-neutral schemas, prompts, examples
n8n/workflows/            Exported n8n workflow JSON files
services/invoice-renderer FastAPI PDF renderer
scripts/                  Local operational scripts
tests/                    Cross-service fixtures and scenarios
```

## Local Setup

Local development can use Docker Compose for convenience:

```text
mysql
n8n
invoice-renderer
```

Host ports are configurable in `.env`. The default published MySQL port is `3307` to avoid colliding with a local MySQL/MariaDB on `3306`.

Telegram local development uses webhook via Cloudflare Tunnel. Polling/manual trigger is reserved for selected tests.

## Environment

Secrets live in `.env` and must not be committed. `.env.example` contains placeholders only.

## Run

```bash
docker compose up -d
docker compose logs -f invoice-renderer
```

## Test

Host-safe checks:

```bash
./scripts/test-local.sh
```

Renderer unit tests in container:

```bash
./scripts/test-renderer-container.sh
```

Healthcheck:

```bash
./scripts/healthcheck.sh
```

Read-only preflight:

```bash
./scripts/preflight-readiness.sh
```

Telegram webhook helper:

```bash
./scripts/telegram-webhook.sh info
```

CI workflow template: `ci/github-actions-invoice-bot-v2-ci.yml`

## Production Deployment

Production target:

```text
/opt/invoice-bot-v2/
```

Persistent data should be mounted under a clear production path such as:

```text
/var/lib/invoice-bot-v2/
```

Do not deploy V2 over the legacy Hermes runtime. Cutover happens only after acceptance tests pass.

Docker Compose is optional convenience for local development. Production deployment is native by default after read-only environment discovery.

## Troubleshooting

Check these first:

```text
docker compose ps
./scripts/healthcheck.sh
n8n execution logs
invoice_deliveries provider_error_message
audit_logs by correlation_id
```
