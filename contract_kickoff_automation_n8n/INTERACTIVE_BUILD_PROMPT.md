# Interactive Build Prompt — Smart Contract-to-Kickoff Automation

**How to use:** Copy everything below the horizontal rule and paste it as your first message in a new Claude Desktop conversation. Claude will guide you through the build one step at a time.

---

I'm building the **Smart Contract-to-Kickoff Automation** project and need your help walking me through the n8n workflow setup step by step. Wait for me to confirm each step is done before moving to the next. If I run into an error, help me troubleshoot it before continuing.

---

## What This Project Does

Listens for a PandaDoc webhook when a contract is signed. Downloads the PDF, extracts the engagement scope using Claude AI, creates an Asana project with tasks and deadlines, and sends a personalized kickoff email — all within 60 seconds of signature.

**Trigger:** PandaDoc `document_state_changed` → `status: completed`
**Stack:** n8n (self-hosted) · Claude API · Asana API · Gmail · Google Sheets

---

## Architecture

```
PandaDoc (signed contract webhook)
        ↓
n8n Workflow A
        ↓
A1. Receive webhook
A2. Validate secret · extract document_id, client fields
A3. Download signed PDF via PandaDoc API
A4. Convert PDF to plain text (pdfminer)
A5. Claude extracts deliverables, dates, client info → JSON
A6. Score extraction quality: complete / partial / insufficient
        ↓                    ↓
   [quality ok]        [insufficient]
        ↓                    ↓
A8. Create Asana project    A15. Operator alert email
A9. Create extracted tasks       ↓
A10. Create 5 standard tasks  A13. Log to Sheets
A11. Claude drafts kickoff email
A12. Gmail sends to client
        ↓
A13. Google Sheets — contracts tab
A14. Google Sheets — tasks tab
```

---

## What's Already Built

All scripts are in `contract_kickoff_automation_n8n/scripts/`. Nothing needs to be coded — just pasted into n8n Code nodes.

**n8n Code node scripts:**
- `scripts/n8n_validate_webhook.js` — paste into node A2
- `scripts/n8n_assess_extraction_quality.js` — paste into node A6
- `scripts/n8n_create_standard_tasks.js` — paste into node A10

**Config:**
- `config/.env.example` — all 14 environment variables
- `config/claude_extraction_prompt.md` — standalone extraction prompt for tuning

**Diagrams & docs:**
- `technical_guide/architecture.md` — full Mermaid diagram
- `technical_guide/workflow_a_diagram.md` — A1-A15 node-by-node
- `technical_guide/prerequisites_checklist.md` — complete setup checklist

**Sample test contracts (run `python scripts/generate_sample_contracts.py` to generate):**
- `TEST-001` — web design, explicit dates (use for Phase 1 test)
- `TEST-002` — monthly retainer, no end date
- `TEST-003` — multi-phase SOW
- `TEST-004` — legal boilerplate, thin scope (tests insufficient path)
- `TEST-005` — blank PDF (tests pdf_text_empty path)

---

## Build Phases (in order)

1. Google Sheets — create 3 tabs, add headers
2. PandaDoc — configure webhook + note API key
3. n8n credentials — PandaDoc, Anthropic, Asana, Gmail, Google Sheets OAuth2
4. Workflow A — build nodes A1–A15
5. Workflow B — build reprocess workflow (B1–B3)
6. End-to-end test with TEST-001

---

## n8n Code Node Scripts (copy-paste ready)

### `n8n_validate_webhook.js` — paste into node A2

```javascript
// n8n Code node: A2 — Validate & Parse Webhook
// Validates the PandaDoc webhook secret header, extracts key fields,
// and halts gracefully on non-signing events.

const secret = $input.first().headers['x-pd-secret'];
if (secret !== $env.PANDADOC_WEBHOOK_SECRET) {
  throw new Error('Invalid webhook secret');
}

const body = $input.first().json;
if (body.data?.status !== 'completed') {
  return []; // Non-signing event, halt gracefully
}

return [{
  json: {
    document_id: body.data.id,
    client_name: body.data.recipients?.[0]?.last_name
      ? `${body.data.recipients[0].first_name} ${body.data.recipients[0].last_name}`
      : body.data.recipients?.[0]?.first_name || 'Unknown',
    client_email: body.data.recipients?.[0]?.email || null,
    signed_at: body.data.date_completed || new Date().toISOString()
  }
}];
```

---

### `n8n_assess_extraction_quality.js` — paste into node A6

```javascript
// n8n Code node: A6 — Assess Extraction Quality
// Scores extraction as complete/partial/insufficient, generates contract_id,
// resolves start dates, and calculates due dates for relative deliverables.

const extracted = $input.first().json;
const deliverables = extracted.deliverables || [];

const hasClient = !!(extracted.client_name || extracted.client_company);
const hasServiceType = !!extracted.service_type;
const hasStartDate = !!extracted.engagement_start_date;
const hasDeliverables = deliverables.length > 0;
const deliverablesHaveDates = deliverables.some(d => d.due_date || d.due_days_from_start);

let quality;
if (hasClient && hasServiceType && hasStartDate && hasDeliverables && deliverablesHaveDates) {
  quality = 'complete';
} else if (hasDeliverables && (hasStartDate || extracted.engagement_duration_days)) {
  quality = 'partial';
} else {
  quality = 'insufficient';
}

// Generate contract_id: [CLIENT_CODE]-[YYYYMMDD]-001
const clientCode = (extracted.client_company || extracted.client_name || 'UNK')
  .toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 6);
const dateCode = new Date().toISOString().slice(0, 10).replace(/-/g, '');
const contractId = `${clientCode}-${dateCode}-001`;

// Resolve start date — fall back to today if not extracted
const startDate = extracted.engagement_start_date || new Date().toISOString().slice(0, 10);

// Calculate due dates for deliverables that only have relative timing
const resolvedDeliverables = deliverables.map((d, i) => {
  let dueDate = d.due_date;
  if (!dueDate && d.due_days_from_start) {
    const start = new Date(startDate);
    start.setDate(start.getDate() + d.due_days_from_start);
    dueDate = start.toISOString().slice(0, 10);
  }
  return { ...d, due_date_resolved: dueDate, sequence: i + 1 };
});

return [{
  json: {
    ...extracted,
    contract_id: contractId,
    start_date_resolved: startDate,
    deliverables: resolvedDeliverables,
    extraction_quality: quality
  }
}];
```

---

### `n8n_create_standard_tasks.js` — paste into node A10

```javascript
// n8n Code node: A10 — Create Standard Onboarding Tasks
// Always runs after extracted tasks (regardless of extraction quality).
// Returns the 5 baseline onboarding tasks with due dates relative to start_date_resolved.
// Each task is tagged task_source: standard for the audit log.

const data = $input.first().json;
const startDate = new Date(data.start_date_resolved);

function addDays(date, days) {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result.toISOString().slice(0, 10);
}

const standardTasks = [
  {
    task_name: 'Send welcome packet to client',
    due_date: addDays(startDate, 1),
    assignee_name: 'Account Manager',
    task_source: 'standard',
    contract_id: data.contract_id,
    deliverable_ref: 'Onboarding',
    notes: 'Auto-generated standard onboarding task'
  },
  {
    task_name: 'Schedule kickoff call',
    due_date: addDays(startDate, 2),
    assignee_name: 'Account Manager',
    task_source: 'standard',
    contract_id: data.contract_id,
    deliverable_ref: 'Onboarding',
    notes: 'Auto-generated standard onboarding task'
  },
  {
    task_name: 'Set up client workspace/folder',
    due_date: addDays(startDate, 1),
    assignee_name: 'Project Manager',
    task_source: 'standard',
    contract_id: data.contract_id,
    deliverable_ref: 'Onboarding',
    notes: 'Auto-generated standard onboarding task'
  },
  {
    task_name: 'Confirm deliverable timeline with client',
    due_date: addDays(startDate, 3),
    assignee_name: 'Project Manager',
    task_source: 'standard',
    contract_id: data.contract_id,
    deliverable_ref: 'Onboarding',
    notes: 'Auto-generated standard onboarding task'
  },
  {
    task_name: 'Internal project briefing',
    due_date: addDays(startDate, 2),
    assignee_name: 'Full Team',
    task_source: 'standard',
    contract_id: data.contract_id,
    deliverable_ref: 'Onboarding',
    notes: 'Auto-generated standard onboarding task'
  }
];

return standardTasks.map(task => ({ json: task }));
```

---

## Claude API Prompts

### A5 — Contract Extraction

**System prompt:**
```
You are a contract analyst for a business automation system. Your job is to extract structured project data from service contracts so that tasks can be automatically created in a project management tool.

Extract only what is explicitly stated or strongly implied in the contract. Do not invent deliverables, dates, or responsibilities. If a field cannot be determined with reasonable confidence, return null for that field.

Always respond with valid JSON only. No explanation, no preamble, no markdown — raw JSON only.
```

**User prompt:**
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

### A11 — Kickoff Email Draft

**System prompt:**
```
You are a professional client success manager drafting a kickoff email on behalf of a service business. Write in a warm, confident, professional tone. Be specific — reference the actual project details. Keep it concise: under 200 words. No filler phrases like "We're excited to work with you." Lead with substance.
```

**User prompt:**
```
Draft a kickoff email to a new client. Use only the details provided — do not invent information that isn't here.

Client name: {{ $json.client_name || $json.client_company }}
Service type: {{ $json.service_type }}
Project start date: {{ $json.start_date_resolved }}
Project end date: {{ $json.engagement_end_date || 'TBD' }}
Key deliverables:
{{ $json.deliverables.map(d => `- ${d.name}${d.due_date_resolved ? ' (due ' + d.due_date_resolved + ')' : ''}`).join('\n') }}
Special conditions: {{ $json.special_conditions || 'None' }}

The email should:
1. Confirm the engagement is underway
2. Briefly summarize the key deliverables and timeline
3. State the immediate next step (kickoff call or first action)
4. Invite questions

Return only the email body — no subject line, no sender signature block.
```

---

## Google Sheets — Tab & Column Reference

Create a single Google Sheet with exactly these 3 tab names.

**Tab: `contracts`**
```
contract_id | pandadoc_document_id | client_name | client_email | service_type | engagement_start_date | engagement_end_date | contract_value | deliverable_count | task_count | asana_project_id | asana_project_url | kickoff_email_sent | extraction_quality | processing_status | failure_reason | processed_at
```

**Tab: `tasks`**
```
contract_id | task_id | asana_task_gid | task_name | assignee_name | due_date | deliverable_ref | task_source | created_at
```

**Tab: `errors`**
```
timestamp | contract_id | workflow_node | error_type | error_detail | recoverable
```

---

## Workflow A — Node-by-Node Build Guide

### A1. Webhook Trigger
- Node type: `Webhook`
- HTTP Method: `POST`
- Path: `contract-signed`
- Authentication: `Header Auth` — select the PandaDoc credential (header: `x-pd-secret`)
- Response mode: `When last node finishes`

### A2. Validate & Parse Webhook
- Node type: `Code`
- Language: JavaScript
- Paste `n8n_validate_webhook.js` (above)
- Connect from: A1

### A3. Download PDF
- Node type: `HTTP Request`
- Method: `GET`
- URL: `https://api.pandadoc.com/public/v1/documents/{{ $json.document_id }}/download`
- Authentication: `Header Auth` — PandaDoc credential (header: `Authorization`, value: `API-Key {{ $env.PANDADOC_API_KEY }}`)
- Response format: `File`
- Timeout: `30000` (30s)
- Connect from: A2

### A4. Convert PDF to Text
- Node type: `Execute Command`
- Command:
```bash
python3 -c "
import sys
from pdfminer.high_level import extract_text
from io import BytesIO
pdf_bytes = sys.stdin.buffer.read()
text = extract_text(BytesIO(pdf_bytes))
print(text or '')
" < {{ $binary.data }}
```
- If output is empty or under 100 characters: route to A15 (operator alert), log `pdf_text_empty`
- Add a Code node after A4 to expose the text: `return [{ json: { ...($input.first().json), contract_text: $input.first().json.stdout } }]`
- Connect from: A3

### A5. Claude API — Extract Contract
- Node type: `HTTP Request`
- Method: `POST`
- URL: `https://api.anthropic.com/v1/messages`
- Authentication: `Header Auth` — Anthropic credential (header: `x-api-key`)
- Headers (add manually): `anthropic-version: 2023-06-01`, `content-type: application/json`
- Body (JSON):
```json
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 2000,
  "system": "<paste A5 system prompt>",
  "messages": [
    { "role": "user", "content": "<paste A5 user prompt>" }
  ]
}
```
- After A5, add a Code node to parse the response:
```javascript
const text = $input.first().json.content[0].text;
return [{ json: JSON.parse(text) }];
```
- Connect from: A4

### A6. Assess Extraction Quality
- Node type: `Code`
- Language: JavaScript
- Paste `n8n_assess_extraction_quality.js` (above)
- Connect from: A5 parse node

### A7. IF — Quality Check
- Node type: `IF`
- Condition: `{{ $json.extraction_quality }}` · `is not equal to` · `insufficient`
- True branch → A8
- False branch → A15
- Connect from: A6

### A8. Asana — Create Project
- Node type: `HTTP Request`
- Method: `POST`
- URL: `https://app.asana.com/api/1.0/projects`
- Authentication: `Header Auth` — Asana credential (header: `Authorization`, value: `Bearer {{ $env.ASANA_ACCESS_TOKEN }}`)
- Headers: `content-type: application/json`
- Body (JSON):
```json
{
  "data": {
    "name": "{{ $json.client_name || $json.client_company }} — {{ $json.service_type }}",
    "workspace": "{{ $env.ASANA_WORKSPACE_GID }}",
    "team": "{{ $env.ASANA_TEAM_GID }}",
    "notes": "Auto-created from signed contract {{ $json.contract_id }}. Start: {{ $json.start_date_resolved }}. Extraction quality: {{ $json.extraction_quality }}.",
    "color": "light-green",
    "default_view": "list"
  }
}
```
- After A8, add a Code node to merge the project GID back:
```javascript
const prev = $('A6 node name').first().json;
return [{ json: { ...prev, asana_project_gid: $input.first().json.data.gid } }];
```
- Connect from: A7 (true branch)

### A9. Asana — Create Tasks from Deliverables
- Node type: `Loop Over Items` — iterate over `{{ $json.deliverables }}`
- Inside the loop, add an `HTTP Request` node:
  - Method: `POST`
  - URL: `https://app.asana.com/api/1.0/tasks`
  - Body (JSON):
```json
{
  "data": {
    "name": "{{ $json.name }}",
    "notes": "{{ $json.description || '' }}\n\nOwner role: {{ $json.owner_role || 'Unassigned' }}.\nClient input required: {{ $json.requires_client_input }}.",
    "projects": ["{{ $('A8 node name').first().json.asana_project_gid }}"],
    "due_on": "{{ $json.due_date_resolved || '' }}",
    "workspace": "{{ $env.ASANA_WORKSPACE_GID }}"
  }
}
```
- Connect from: A8

### A10. Asana — Standard Onboarding Tasks
- Node type: `Code` — paste `n8n_create_standard_tasks.js` (above)
- This outputs 5 items. Add a `Loop Over Items` → `HTTP Request` after it (same Asana task POST as A9, using `$json.task_name` as `name` and `$json.due_date` as `due_on`)
- Connect from: A9

### A11. Claude API — Draft Kickoff Email
- Node type: `HTTP Request`
- Method: `POST`
- URL: `https://api.anthropic.com/v1/messages`
- Same auth and headers as A5
- Body (JSON):
```json
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 800,
  "system": "<paste A11 system prompt>",
  "messages": [
    { "role": "user", "content": "<paste A11 user prompt>" }
  ]
}
```
- After A11, add a Code node to extract the email body:
```javascript
return [{ json: { ...$('A6 node name').first().json, email_body: $input.first().json.content[0].text } }];
```
- Connect from: A10

### A12. Gmail — Send Kickoff Email
- Node type: `Gmail` → Send Email
- Credential: Gmail OAuth2
- To: `{{ $json.client_email }}`
- Subject: `Your {{ $json.service_type }} project is underway — next steps inside`
- Message: `{{ $json.email_body }}\n\n{{ $env.EMAIL_SIGNATURE }}`
- CC: `{{ $env.ACCOUNT_MANAGER_EMAIL }}`
- Connect from: A11

### A13. Google Sheets — Log to contracts tab
- Node type: `Google Sheets` → Append Row
- Credential: Google Sheets OAuth2
- Document: select your audit log sheet
- Sheet: `contracts`
- Map these columns from `$json`:
  - `contract_id`, `pandadoc_document_id` (= `document_id`), `client_name`, `client_email`, `service_type`, `engagement_start_date`, `engagement_end_date`, `contract_value`
  - `deliverable_count` = `{{ $json.deliverables.length }}`
  - `extraction_quality`, `processed_at` = `{{ new Date().toISOString() }}`
  - `processing_status` = `success` (or `partial_success` / `failed` based on prior node results)
  - `asana_project_id`, `asana_project_url`, `kickoff_email_sent`
- Connect from: A12 (and also A15 — this node always runs)

### A14. Google Sheets — Log to tasks tab
- Node type: `Loop Over Items` → `Google Sheets` → Append Row
- Sheet: `tasks`
- Iterate over all created tasks (extracted + standard), mapping:
  - `contract_id`, `task_name`, `assignee_name`, `due_date`, `deliverable_ref`, `task_source`
  - `task_id` = generate as `{{ $json.contract_id }}-T{{ $itemIndex + 1 }}`
  - `asana_task_gid` = from Asana response
  - `created_at` = `{{ new Date().toISOString() }}`
- Connect from: A13

### A15. Operator Alert (failure path)
- Node type: `Gmail` → Send Email
- To: `{{ $env.OPERATOR_EMAIL }}`
- Subject: `Contract processing failed — manual review needed [{{ $json.contract_id || 'unknown' }}]`
- Message: include `client_name`, `extraction_quality`, and a link to the errors tab
- Connect from: A7 (false branch), and from A4 PDF-empty check
- Connect to: A13 (so the failure is always logged)

---

## Workflow B — Manual Reprocess (3 nodes)

### B1. Manual Trigger
- Node type: `Manual Trigger` or `Execute Workflow Trigger`
- Add form fields: `contract_id` (string), `pdf_file_path` (string)

### B2. Read contracts sheet
- Node type: `Google Sheets` → Get Row(s)
- Filter: `contract_id` = `{{ $json.contract_id }}`

### B3. Re-run extraction
- Connect to A4 (Execute Command) — re-run the full pipeline from PDF extraction onward
- The contracts sheet row is overwritten (not appended) using `Google Sheets → Update Row`

---

## Environment Variables

Set in n8n: **Settings → Environment Variables** (or `.env` file if Docker-hosted).

| Variable | Description |
|----------|-------------|
| `PANDADOC_WEBHOOK_SECRET` | Shared secret from PandaDoc webhook config |
| `PANDADOC_API_KEY` | PandaDoc API key (Settings → API) |
| `ANTHROPIC_API_KEY` | Claude API key (console.anthropic.com) |
| `ASANA_ACCESS_TOKEN` | Asana personal access token |
| `ASANA_WORKSPACE_GID` | From Asana URL or GET /workspaces |
| `ASANA_TEAM_GID` | From GET /teams |
| `OPERATOR_EMAIL` | Your email — receives failure alerts |
| `ACCOUNT_MANAGER_EMAIL` | CC'd on every kickoff email |
| `EMAIL_SIGNATURE` | Plain text signature appended to client emails |
| `DOCUSIGN_ACCOUNT_ID` | Phase 4 only |
| `CLICKUP_API_KEY` | Phase 3 only |
| `CLICKUP_LIST_ID` | Phase 3 only |
| `NOTION_DATABASE_ID` | Phase 3 only |

---

## Start

I'm ready to begin. Start me at **Phase 1: Google Sheets Setup**. Tell me exactly what to do first.
