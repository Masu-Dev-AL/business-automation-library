# Interactive Build Prompt — Smart Contract-to-Kickoff Automation

**How to use:** Copy everything below the horizontal rule and paste it as your first message in a new Claude Desktop conversation. Claude will guide you through the build one step at a time.

---

I'm building the **Smart Contract-to-Kickoff Automation** project and need your help walking me through the n8n workflow setup step by step. Wait for me to confirm each step is done before moving to the next. If I run into an error, help me troubleshoot it before continuing.

---

## What This Project Does

Listens for a DocuSign Connect webhook when a contract is signed. Downloads the PDF, passes it directly to Claude AI for extraction, creates an Asana project with tasks and deadlines, and sends a personalized kickoff email — all within 60 seconds of signature.

**Trigger:** DocuSign Connect `envelope-completed` → `status: completed`
**Stack:** n8n (self-hosted) · Claude API · Asana API · Gmail · Google Sheets

---

## Architecture

```
DocuSign Connect (envelope-completed webhook)
        ↓
n8n Workflow A
        ↓
A1. Receive webhook
A2. Validate & parse — extract envelope_id, client fields
A3. Download signed PDF via DocuSign REST API
A4. Claude Analyze Document — extracts deliverables, dates, client info → JSON
A5b. Parse Claude Response
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
- `config/.env.example` — all environment variables
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
- `TEST-005` — blank PDF (tests image-only path)

---

## Build Phases (in order)

1. Google Sheets — create 3 tabs, add headers
2. DocuSign — configure Connect webhook + note integration key and account ID
3. n8n credentials — DocuSign OAuth2, Anthropic, Asana, Gmail, Google Sheets OAuth2
4. Workflow A — build nodes A1–A15
5. Workflow B — build reprocess workflow (B1–B3)
6. End-to-end test with TEST-001

---

## n8n Code Node Scripts (copy-paste ready)

### `n8n_validate_webhook.js` — paste into node A2

```javascript
// n8n Code node: A2 — Validate & Parse Webhook (DocuSign)
// Extracts key fields from DocuSign Connect envelope-completed event.
// Halts gracefully on non-signing events.

const body = $input.first().json.body;

// Only process completed envelopes
const status = body.data?.envelopeSummary?.status;
if (status !== 'completed') {
  return [];
}

const summary = body.data.envelopeSummary;
const signer = summary.recipients?.signers?.[0];

return [{
  json: {
    document_id: body.data.envelopeId,
    client_name: signer?.name || 'Unknown',
    client_email: signer?.email || null,
    signed_at: summary.completedDateTime || new Date().toISOString()
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

const data = $('A6 - Assess Extraction Quality').first().json;
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
    notes: 'Assignee Placeholder: Account Manager'
  },
  {
    task_name: 'Schedule kickoff call',
    due_date: addDays(startDate, 2),
    assignee_name: 'Account Manager',
    task_source: 'standard',
    contract_id: data.contract_id,
    deliverable_ref: 'Onboarding',
    notes: 'Assignee Placeholder: Account Manager'
  },
  {
    task_name: 'Set up client workspace/folder',
    due_date: addDays(startDate, 1),
    assignee_name: 'Project Manager',
    task_source: 'standard',
    contract_id: data.contract_id,
    deliverable_ref: 'Onboarding',
    notes: 'Assignee Placeholder: Project Manager'
  },
  {
    task_name: 'Confirm deliverable timeline with client',
    due_date: addDays(startDate, 3),
    assignee_name: 'Project Manager',
    task_source: 'standard',
    contract_id: data.contract_id,
    deliverable_ref: 'Onboarding',
    notes: 'Assignee Placeholder: Project Manager'
  },
  {
    task_name: 'Internal project briefing',
    due_date: addDays(startDate, 2),
    assignee_name: 'Full Team',
    task_source: 'standard',
    contract_id: data.contract_id,
    deliverable_ref: 'Onboarding',
    notes: 'Assignee Placeholder: Full Team'
  }
];

return standardTasks.map(task => ({ json: task }));
```

---

## Claude API Prompts

### A4 — Contract Extraction (Analyze Document node)

Configure on the **Anthropic** node in n8n using the **Analyze Document** operation.

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
```

---

### A11 — Kickoff Email Draft

Configure on the **Anthropic** node in n8n using the **Message a Model** operation.

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
contract_id | envelope_id | client_name | client_email | service_type | engagement_start_date | engagement_end_date | contract_value | deliverable_count | asana_project_id | kickoff_email_sent | extraction_quality | processing_status | failure_reason | processed_at
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
- Authentication: None (DocuSign Connect sends a standard POST; validate the payload in A2)
- Response mode: `When last node finishes`

### A2. Validate & Parse Webhook
- Node type: `Code`
- Language: JavaScript
- Paste `n8n_validate_webhook.js` (above)
- Connect from: A1

### A3. Download PDF
- Node type: `HTTP Request`
- Method: `GET`
- URL: `https://demo.docusign.net/restapi/v2.1/accounts/{{ $env.DOCUSIGN_ACCOUNT_ID }}/envelopes/{{ $json.document_id }}/documents/combined`
- Authentication: `DocuSign OAuth2 API` credential
- Response format: `File`
- Timeout: `30000` (30s)
- Connect from: A2

### A4. Analyze Document (Claude extraction)
- Node type: `Anthropic`
- Operation: `Analyze Document`
- Credential: select your Anthropic API credential
- Model: `claude-sonnet-4-5`
- Max Tokens: `4096`
- Input type: Binary (point to the binary output from A3)
- System Prompt: paste the A4 system prompt above
- User Prompt: paste the A4 user prompt above
- Connect from: A3

### A5b. Parse Claude Response
- Node type: `Code`
- Language: JavaScript
- Code:
```javascript
let text = $input.first().json.content[0].text;
text = text.replace(/^```json\s*/i, '').replace(/^```\s*/i, '').replace(/```\s*$/i, '').trim();
try {
  return [{ json: JSON.parse(text) }];
} catch(e) {
  throw new Error(`Claude response could not be parsed as JSON. Preview: ${text.slice(0, 200)}`);
}
```
- Connect from: A4

### A6. Assess Extraction Quality
- Node type: `Code`
- Language: JavaScript
- Paste `n8n_assess_extraction_quality.js` (above)
- Connect from: A5b

### A7. IF — Quality Check
- Node type: `IF`
- Condition: `{{ $json.extraction_quality }}` · `is not equal to` · `insufficient`
- True branch → A8
- False branch → A15
- Connect from: A6

### A8. Asana — Create Project
- Node type: `Asana`
- Operation: `Create` → `Project`
- Credential: select your Asana credential
- Name: `{{ $json.client_name || $json.client_company }} — {{ $json.service_type }}`
- Workspace: `{{ $env.ASANA_WORKSPACE_GID }}`
- Team: `{{ $env.ASANA_TEAM_GID }}`
- After A8, add a Code node (A8b) to merge the project GID back:
```javascript
const prev = $('A6 - Assess Extraction Quality').first().json;
return [{ json: { ...prev, asana_project_gid: $input.first().json.gid } }];
```
- After A8b, add a **Split Out** node (A8c) to expand the deliverables array into individual items
- Connect from: A7 (true branch)

### A9. Asana — Create Tasks from Deliverables
- Node type: `splitInBatches` (Loop Over Items), batch size 1
- Inside the loop, add an `Asana` node:
  - Operation: `Create` → `Task`
  - Name: `{{ $json.name }}`
  - Projects: `{{ $json.asana_project_gid }}`
  - Due On: `{{ $json.due_date_resolved || '' }}`
  - Notes: `{{ $json.description || '' }}\n\nOwner role: {{ $json.owner_role || 'Unassigned' }}`
- Connect from: A8c

### A10. Asana — Standard Onboarding Tasks
- Node type: `Code` — paste `n8n_create_standard_tasks.js` (above)
- This outputs 5 items. Add a `splitInBatches` loop → `Asana` node after it (same task creation config as A9, using `$json.task_name` as name and `$json.due_date` as `due_on`)
- Connect from: A9 (done branch)

### A11. Claude — Draft Kickoff Email
- Node type: `Anthropic`
- Operation: `Message a Model`
- Credential: select your Anthropic API credential
- Model: `claude-sonnet-4-5`
- Max Tokens: `800`
- System Prompt: paste the A11 system prompt above
- User Prompt: paste the A11 user prompt above
- After A11, add a Code node (A11b) to extract the email body:
```javascript
const prev = $('A6 - Assess Extraction Quality').first().json;
return [{ json: { ...prev, email_body: $input.first().json.content[0].text } }];
```
- Connect from: A10 (done branch)

### A12. Gmail — Send Kickoff Email
- Node type: `Gmail` → Send Email
- Credential: Gmail OAuth2
- To: `{{ $json.client_email }}`
- Subject: `Your {{ $json.service_type }} project is underway — next steps inside`
- Message: `{{ $json.email_body }}\n\n{{ $env.EMAIL_SIGNATURE }}`
- CC: `{{ $env.ACCOUNT_MANAGER_EMAIL }}`
- Connect from: A11b

### A13. Google Sheets — Log to contracts tab
- Node type: `Google Sheets` → Append Row
- Credential: Google Sheets OAuth2
- Document: select your audit log sheet
- Sheet: `contracts`
- Map these columns from `$json`:
  - `contract_id`, `envelope_id` (= `document_id`), `client_name`, `client_email`, `service_type`, `engagement_start_date`, `engagement_end_date`, `contract_value`
  - `deliverable_count` = `{{ $json.deliverables.length }}`
  - `extraction_quality`, `processed_at` = `{{ new Date().toISOString() }}`
  - `processing_status` = from A13a prepare node
  - `asana_project_id`, `kickoff_email_sent`, `failure_reason`
- Connect from: A12 (and also A15 — this node always runs on both paths)

### A14. Google Sheets — Log to tasks tab
- Node type: `splitInBatches` loop → `Google Sheets` → Append Row
- Sheet: `tasks`
- Iterate over all created tasks (extracted + standard), mapping:
  - `contract_id`, `task_name`, `assignee_name`, `due_date`, `deliverable_ref`, `task_source`
  - `task_id` = `{{ $json.contract_id }}-D{{ $itemIndex + 1 }}` (extracted) or `{{ $json.contract_id }}-S{{ $itemIndex + 1 }}` (standard)
  - `asana_task_gid` = from Asana response
  - `created_at` = `{{ new Date().toISOString() }}`
- Connect from: A13

### A15. Operator Alert (failure path)
- Node type: `Gmail` → Send Email
- To: `{{ $env.OPERATOR_EMAIL }}`
- Subject: `Contract processing failed — manual review needed [{{ $json.contract_id || 'unknown' }}]`
- Message: include `client_name`, `extraction_quality`, and a link to the errors tab
- Connect from: A7 (false branch)
- Connect to: A13 (so the failure is always logged)

---

## Workflow B — Manual Reprocess (3 nodes)

### B1. Manual Trigger
- Node type: `Manual Trigger` or `Execute Workflow Trigger`
- Add form fields: `contract_id` (string), `envelope_id` (string)

### B2. Read contracts sheet
- Node type: `Google Sheets` → Get Row(s)
- Filter: `contract_id` = `{{ $json.contract_id }}`

### B3. Re-run extraction
- Download PDF again from DocuSign using the stored `envelope_id` (same A3 config)
- Connect to A4 (Analyze Document) — re-run the full pipeline from PDF extraction onward
- The contracts sheet row is overwritten (not appended) using `Google Sheets → Update Row`

---

## Environment Variables

Set in n8n: **Settings → Environment Variables** (or `.env` file if Docker-hosted).

| Variable | Description |
|----------|-------------|
| `DOCUSIGN_ACCOUNT_ID` | DocuSign account ID (Apps & Keys → API Account ID) |
| `DOCUSIGN_OAUTH_CLIENT_ID` | DocuSign integration key |
| `DOCUSIGN_OAUTH_CLIENT_SECRET` | DocuSign OAuth2 secret |
| `ANTHROPIC_API_KEY` | Claude API key (console.anthropic.com) |
| `ASANA_ACCESS_TOKEN` | Asana personal access token |
| `ASANA_WORKSPACE_GID` | From Asana URL or GET /workspaces |
| `ASANA_TEAM_GID` | From GET /teams |
| `OPERATOR_EMAIL` | Your email — receives failure alerts |
| `ACCOUNT_MANAGER_EMAIL` | CC'd on every kickoff email |
| `EMAIL_SIGNATURE` | Plain text signature appended to client emails |
| `CLICKUP_API_KEY` | Phase 3 only |
| `CLICKUP_LIST_ID` | Phase 3 only |
| `NOTION_DATABASE_ID` | Phase 3 only |

---

## Start

I'm ready to begin. Start me at **Phase 1: Google Sheets Setup**. Tell me exactly what to do first.
