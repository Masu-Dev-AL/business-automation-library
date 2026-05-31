# Google Sheets Schema

Three tabs, all append-only. Create a single Google Sheet with these tab names exactly as written.

---

## Tab 1: `contracts`

Master log of every processed contract. One row per signed document. Written by node **A13**.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `contract_id` | string | Unique ID: `[CLIENT_CODE]-[YYYYMMDD]-[SEQ]` | `ACME-20250601-001` |
| `envelope_id` | string | DocuSign envelope ID from Connect webhook payload | `89ada3dd-d386-4e35-af42` |
| `client_name` | string | Extracted client/company name | `Sarah Chen` |
| `client_email` | string | Primary client contact email | `sarah@brightfield.com` |
| `service_type` | string | Extracted engagement type | `Website Redesign` |
| `engagement_start_date` | date | Extracted or inferred start date (ISO) | `2025-06-15` |
| `engagement_end_date` | date | Extracted or inferred end date (ISO), null if none | `2025-08-15` |
| `contract_value` | number | Total contract value in USD, null if not stated | `18500` |
| `deliverable_count` | number | Number of deliverables extracted | `4` |
| `asana_project_id` | string | Asana project GID, null if creation failed | `1209876543210` |
| `kickoff_email_sent` | boolean | `true` if kickoff email sent successfully | `true` |
| `extraction_quality` | string | `complete`, `partial`, or `insufficient` | `complete` |
| `processing_status` | string | `success`, `partial_success`, or `failed` | `success` |
| `failure_reason` | string | Populated if processing_status ≠ success, else null | `asana_api_failed` |
| `processed_at` | datetime | ISO timestamp when the workflow ran | `2025-06-01T14:23:11Z` |

---

## Tab 2: `tasks`

One row per task created. Written by node **A14**. Linked to `contracts` via `contract_id`.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `contract_id` | string | FK to contracts tab | `ACME-20250601-001` |
| `task_id` | string | Unique task ID: `[CONTRACT_ID]-T[SEQ]` | `ACME-20250601-001-T01` |
| `asana_task_gid` | string | Asana task GID, null if not created | `1209876543211` |
| `task_name` | string | Task title as created in Asana | `Discovery & Wireframes` |
| `assignee_name` | string | Assigned team member name/role, null if unknown | `Account Manager` |
| `due_date` | date | Calculated due date (ISO format) | `2025-06-30` |
| `deliverable_ref` | string | Which deliverable this task maps to | `Deliverable 1` |
| `task_source` | string | `extracted` (from contract) or `standard` (baseline template) | `extracted` |
| `created_at` | datetime | ISO timestamp of task creation | `2025-06-01T14:23:45Z` |

---

## Tab 3: `errors`

Append-only error log. Every failure surfaces here — the system never fails silently. Written throughout Workflow A on any error condition.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `timestamp` | datetime | When the error occurred | `2025-06-01T14:22:58Z` |
| `contract_id` | string | Contract ID if available, else `unknown` | `ACME-20250601-001` |
| `workflow_node` | string | Which n8n node failed | `Claude Extract` |
| `error_type` | string | Error category (see below) | `claude_extraction_failed` |
| `error_detail` | string | Raw error message or description | `JSON parse error: unexpected token` |
| `recoverable` | boolean | `true` if manual retry via Workflow B is viable | `true` |

### Error Types

| `error_type` | Cause | Recoverable |
|-------------|-------|-------------|
| `webhook_parse_failed` | Malformed DocuSign Connect payload | false |
| `invalid_webhook_secret` | Secret header mismatch | false |
| `pdf_download_failed` | DocuSign API unavailable or bad envelope ID | true |
| `pdf_text_empty` | Scanned/image-only PDF, no extractable text | true (with corrected PDF) |
| `claude_extraction_failed` | Malformed JSON response from Claude | true |
| `asana_api_failed` | Asana project/task creation error | true |
| `asana_task_failed` | Individual task creation failed within loop | true |
| `email_failed` | Gmail send failure | true |

---

## Setup Instructions

1. Create a new Google Sheet named `Contract Kickoff Audit Log`
2. Rename `Sheet1` → `contracts`
3. Add tabs: `tasks`, `errors`
4. Add column headers to row 1 of each tab (exact names from tables above)
5. In n8n, add Google Sheets credentials (OAuth2) and copy the Sheet ID from the URL
6. Set the Sheet ID in n8n's Google Sheets nodes for A13, A14, and any error logging nodes
