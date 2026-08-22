# Deployment

Local development:

```bash
docker compose up -d
```

Docker is optional. Native production is preferred after environment discovery.

Production target:

```text
/opt/invoice-bot-v2/
```

Persistent data target:

```text
/var/lib/invoice-bot-v2/
```

V2 must not be deployed into `/home/invoicebot/.hermes/`.

Cutover happens only after local and live Telegram acceptance tests pass.
