// ─────────────────────────────────────────────────────────────────────────────
// A2 — Validate & Parse Webhook
// ─────────────────────────────────────────────────────────────────────────────

const body = $input.first().json.body;

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


// ─────────────────────────────────────────────────────────────────────────────
// A4 — Prepare PDF (reference only — actual workflow uses native Anthropic node)
// This snippet is for HTTP Request-based Claude calls. In the live workflow,
// A4 is the Anthropic "Analyze Document" node which accepts binary PDF input directly.
// ─────────────────────────────────────────────────────────────────────────────

const item = $input.all()[0];
const binaryKey = Object.keys(item.binary)[0];
const buffer = await this.helpers.getBinaryDataBuffer(0, binaryKey);
const pdfBase64 = buffer.toString('base64');

const claudeRequestBody = {
  model: "claude-sonnet-4-5",
  max_tokens: 4096,
  system: "You are a contract analyst for a business automation system. Extract structured project data from service contracts so tasks can be automatically created. Extract only what is explicitly stated. Return null for fields you cannot determine. Respond with valid JSON only — no explanation, no markdown.",
  messages: [{
    role: "user",
    content: [
      {
        type: "document",
        source: { type: "base64", media_type: "application/pdf", data: pdfBase64 }
      },
      {
        type: "text",
        text: "Extract structured data from this contract and return JSON with these fields: client_name, client_company, service_type, engagement_start_date, engagement_end_date, engagement_duration_days, contract_value, payment_terms, deliverables (array with name, description, due_date, due_days_from_start, owner_role, requires_client_input), team_members_mentioned, key_dates, special_conditions, extraction_notes."
      }
    ]
  }]
};

return [{
  json: {
    ...item.json,
    claude_request_body: JSON.stringify(claudeRequestBody)
  }
}];


// ─────────────────────────────────────────────────────────────────────────────
// A5b — Parse Claude Response
// ─────────────────────────────────────────────────────────────────────────────

const webhookData = $('A2 — Validate & Parse Webhook').first().json;
let text = $input.first().json.content[0].text;
text = text.replace(/^```json\s*/i, '').replace(/^```\s*/i, '').replace(/```\s*$/i, '').trim();
try {
  const extracted = JSON.parse(text);
  return [{ json: { ...webhookData, ...extracted } }];
} catch(e) {
  throw new Error(`Claude response could not be parsed as JSON. Preview: ${text.slice(0, 200)}`);
}


// ─────────────────────────────────────────────────────────────────────────────
// A6 — Assess Extraction Quality
// ─────────────────────────────────────────────────────────────────────────────

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

const clientCode = (extracted.client_company || extracted.client_name || 'UNK')
  .toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 6);
const dateCode = new Date().toISOString().slice(0, 10).replace(/-/g, '');
const contractId = `${clientCode}-${dateCode}-001`;

const startDate = extracted.engagement_start_date || new Date().toISOString().slice(0, 10);

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


// ─────────────────────────────────────────────────────────────────────────────
// A8b — Merge Project GID
// ─────────────────────────────────────────────────────────────────────────────

const prev = $('A6 - Assess Extraction Quality').first().json;
return [{ json: { ...prev, asana_project_gid: $input.first().json.gid } }];


// ─────────────────────────────────────────────────────────────────────────────
// A10 — Create Standard Onboarding Tasks
// ─────────────────────────────────────────────────────────────────────────────

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


// ─────────────────────────────────────────────────────────────────────────────
// A11b — Extract Email Body
// ─────────────────────────────────────────────────────────────────────────────

const prev = $('A8b - Merge Project GID').first().json;
const response = $input.first().json;
const emailText = response.text || response.content?.[0]?.text || '';
return [{ json: { ...prev, email_body: emailText } }];


// ─────────────────────────────────────────────────────────────────────────────
// A13a — Prepare Log Data (updated)
// ─────────────────────────────────────────────────────────────────────────────

const data = $input.first().json;
const fromFailure = data.extraction_quality === 'insufficient';

return [{
  json: {
    ...data,
    processing_status: fromFailure ? 'failed' : 'success',
    failure_reason: fromFailure ? `Extraction quality: ${data.extraction_quality}` : null,
    kickoff_email_sent: !fromFailure
  }
}];


// ─────────────────────────────────────────────────────────────────────────────
// A14a — Prepare Task Rows
// ─────────────────────────────────────────────────────────────────────────────

const contractData = $('A6 - Assess Extraction Quality').first().json;
const contractId = contractData.contract_id;

const deliverableTasks = contractData.deliverables.map((d, i) => ({
  contract_id: contractId,
  task_id: `${contractId}-D${i + 1}`,
  task_name: d.name,
  assignee_name: d.owner_role || 'Unassigned',
  due_date: d.due_date_resolved || d.due_date || '',
  deliverable_ref: d.name,
  task_source: 'extracted',
  created_at: new Date().toISOString()
}));

const standardTasks = $('A10 — Standard Onboarding Tasks').all().map((item, i) => ({
  contract_id: contractId,
  task_id: `${contractId}-S${i + 1}`,
  task_name: item.json.task_name,
  assignee_name: item.json.assignee_name,
  due_date: item.json.due_date,
  deliverable_ref: item.json.deliverable_ref,
  task_source: 'standard',
  created_at: new Date().toISOString()
}));

return [...deliverableTasks, ...standardTasks].map(task => ({ json: task }));


// ─────────────────────────────────────────────────────────────────────────────
// A13a — Prepare Log Data
// ─────────────────────────────────────────────────────────────────────────────

const data = $input.first().json;
const fromFailure = data.extraction_quality === 'insufficient' || !data.email_body;

return [{
  json: {
    ...data,
    processing_status: fromFailure ? 'failed' : 'success',
    failure_reason: fromFailure ? `Extraction quality: ${data.extraction_quality}` : null,
    kickoff_email_sent: !fromFailure
  }
}];
