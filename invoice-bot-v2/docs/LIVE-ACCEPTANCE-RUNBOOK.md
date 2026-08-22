# Live Acceptance Runbook

Run only after source readiness passes, runtime services are healthy, and the
Telegram webhook points to the V2 n8n path:

```bash
./scripts/preflight-readiness.sh
./scripts/healthcheck.sh
./scripts/telegram-webhook.sh info
```

The Telegram webhook URL must end with:

```text
/webhook/telegram/invoice-bot-v2
```

Do not paste bot tokens, LLM keys, passwords, customer private data, or full
Telegram provider payloads into readiness evidence.

## Scenario A: Create, Preview, Approve, Deliver

Send a complete invoice request:

```text
Buat invoice PT Nusa Horizon Wisata, 2 medium bus tanggal 15 Agustus 2026 Harapan Indah Bekasi ke Cisarua Puncak 2,8 juta per unit, tanggal 17 Agustus 2026 Cisarua Puncak ke Jakarta 2,6 juta per unit. Lunas tanpa DP.
```

Expected:

- bot returns preview before generating a final PDF;
- approval message creates exactly one invoice number;
- PDF is delivered to the same Telegram chat;
- database stores invoice, items, delivery, and audit records.

## Scenario B: Revise Before Approval

Create the same draft, then send:

```text
pulangnya ubah jadi tanggal 18 Agustus 2026
```

Expected:

- same draft is updated;
- no invoice number is allocated before approval;
- new preview shows the revised return date;
- approval creates one invoice and one PDF.

## Scenario C: Delivery Failure And Resend

Force or observe a failed delivery in a controlled test chat, then send:

```text
kirim ulang invoice PT Nusa yang tadi
```

Expected:

- resend uses the existing invoice record;
- invoice number and PDF identity are not regenerated;
- delivery history records both failed and resend attempts.

## Scenario D: Duplicate Request

After Scenario A succeeds, send the same invoice request again.

Expected:

- bot does not silently create a duplicate final invoice;
- user is guided to resend, view detail, or explicitly create a new invoice.

## Scenario E: Ambiguous, Help, Cancel, Payment Revision

Send an incomplete request:

```text
buat invoice PT Nusa
```

Then test:

```text
bantuan
tidak usah DP, langsung pelunasan
batal
setuju
```

Expected:

- bot asks only for missing critical fields;
- help does not mutate invoice state;
- payment revision recalculates preview;
- cancellation clears active draft;
- approval after cancellation does not create an invoice.

## Evidence

Record only short non-secret proof after every scenario passes:

```bash
./scripts/record-readiness-evidence.py \
  --gate live_acceptance \
  --command "manual Telegram scenario A-E runbook" \
  --evidence "PASS scenario_a=sent scenario_b=revised_once scenario_c=resend_reused scenario_d=duplicate_guarded scenario_e=cancel_guarded"
```

Then verify:

```bash
./scripts/readiness-gate.py
```
