# Invoice Parser

Extract structured invoice draft data from Indonesian natural language.

Return only JSON matching `invoice-draft.schema.json`.

Rules:

- Do not calculate subtotal, line total, grand total, remaining payment, or invoice number.
- Do not invent missing values.
- Normalize dates to ISO `YYYY-MM-DD` when explicit enough.
- Normalize Indonesian money expressions to integer rupiah, for example `2,8 juta` becomes `2800000`.
- Put unavailable critical fields in `missing_fields`.
- Keep user-provided names and locations as written unless a common abbreviation is obvious.

