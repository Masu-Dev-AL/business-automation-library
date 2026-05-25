# Claude Contract Extraction Prompt

Used in n8n node **A5 — Claude API: Extract Contract Structure**.

Tune the user prompt's schema or instructions to match the specific contract formats you handle.
The model is called via HTTP Request POST to `https://api.anthropic.com/v1/messages`.

---

## System Prompt

```
You are a contract analyst for a business automation system. Your job is to extract structured project data from service contracts so that tasks can be automatically created in a project management tool.

Extract only what is explicitly stated or strongly implied in the contract. Do not invent deliverables, dates, or responsibilities. If a field cannot be determined with reasonable confidence, return null for that field.

Always respond with valid JSON only. No explanation, no preamble, no markdown — raw JSON only.
```

---

## User Prompt

```
Extract the following structured data from this service contract. Return JSON matching exactly this schema:

{
  "client_name": "string or null",
  "client_company": "string or null",
  "service_type": "string — short description of the engagement type e.g. 'Brand Strategy Project', 'Monthly SEO Retainer', 'Website Redesign'",
  "engagement_start_date": "ISO date string YYYY-MM-DD or null",
  "engagement_end_date": "ISO date string YYYY-MM-DD or null",
  "engagement_duration_days": "integer — infer from duration language if no explicit end date e.g. '30-day engagement' → 30, else null",
  "contract_value": "number in USD or null",
  "payment_terms": "string summary or null",
  "deliverables": [
    {
      "name": "string — concise deliverable name",
      "description": "string — one sentence description or null",
      "due_date": "ISO date string YYYY-MM-DD or null",
      "due_days_from_start": "integer — if no explicit date but relative timing stated e.g. 'within 2 weeks' → 14, else null",
      "owner_role": "string — responsible party role if stated e.g. 'Agency', 'Client', 'Designer', else null",
      "requires_client_input": "boolean — true if this deliverable needs something from the client first"
    }
  ],
  "team_members_mentioned": ["string — any named individuals or roles mentioned as responsible parties"],
  "key_dates": [
    {
      "label": "string — what this date is for",
      "date": "ISO date string YYYY-MM-DD"
    }
  ],
  "special_conditions": "string — any notable conditions, constraints, or dependencies worth flagging, or null",
  "extraction_notes": "string — anything ambiguous or worth flagging for human review, or null"
}

Contract text:
{{ $json.contract_text }}
```

---

## Tuning Notes

- **Adding deliverable categories:** Extend the `deliverables` array schema with a `category` field if contracts distinguish between phases or workstreams.
- **Currency handling:** The schema assumes USD. For multi-currency contracts, add a `currency` field alongside `contract_value`.
- **Retainer contracts:** Monthly retainers typically have no `engagement_end_date`. Rely on `engagement_duration_days` or leave both null — the system handles this as `partial` extraction quality.
- **Multi-phase SOWs:** Each phase can be a separate deliverable. The `description` field should capture phase scope.
- **Insufficient extraction:** If the contract is pure legal boilerplate with no scope detail, Claude will return empty `deliverables` and null dates — the A6 quality check will route this to the operator alert path.

---

## n8n Node Configuration

- Node type: `HTTP Request`
- Method: POST
- URL: `https://api.anthropic.com/v1/messages`
- Headers:
  - `x-api-key`: `{{ $env.ANTHROPIC_API_KEY }}`
  - `anthropic-version`: `2023-06-01`
  - `content-type`: `application/json`
- Body (JSON):
  ```json
  {
    "model": "claude-sonnet-4-6",
    "max_tokens": 2000,
    "system": "<system prompt above>",
    "messages": [
      { "role": "user", "content": "<user prompt above>" }
    ]
  }
  ```
