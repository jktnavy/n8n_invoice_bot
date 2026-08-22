# Native Install

Native production is preferred. Do not use this as a blind script; perform read-only discovery first.

## Preflight

```bash
./scripts/discover-environment.sh
./scripts/preflight-readiness.sh
ss -lntup
systemctl --type=service --state=running
```

Choose ports only after the port audit. Recommended defaults when free:

```text
invoice-renderer: 127.0.0.1:8000
n8n: 127.0.0.1:5678 behind reverse proxy
mysql: existing localhost/private server
```

## Database

Use a scoped database and user:

```text
database: invoice_bot_v2
user: invoice_bot_v2
```

Never use MySQL root for runtime.

## Renderer

```bash
python3 -m venv /opt/invoice-bot-v2/venv
/opt/invoice-bot-v2/venv/bin/pip install -r /opt/invoice-bot-v2/services/invoice-renderer/requirements.txt
```

Install `deploy/systemd/invoice-renderer.service` only after adjusting the environment file path and chosen port.

## n8n

Before installing n8n, check whether n8n already exists. Reuse an existing safe instance only if credentials/workflows can be isolated.

Do not install PM2 or change global Node.js unless the server standard already uses it.

## Reverse Proxy

If using Nginx:

```bash
nginx -t
systemctl reload nginx
```

Only add isolated config. Do not replace global config or restart unrelated services.
