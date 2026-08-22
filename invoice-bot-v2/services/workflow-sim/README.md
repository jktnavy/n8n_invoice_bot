# Workflow Simulator

This service is an offline executable contract for the n8n workflows.

It verifies deterministic behavior without external dependencies:

- draft creation from structured extraction
- preview before final invoice
- approval gated by `AWAITING_APPROVAL`
- draft revision without invoice number allocation
- transaction-style invoice number sequence behavior
- duplicate final invoice detection
- delivery failure separated from invoice creation
- resend reusing the same invoice and PDF path

It is not the production orchestrator. Production orchestration remains n8n.

