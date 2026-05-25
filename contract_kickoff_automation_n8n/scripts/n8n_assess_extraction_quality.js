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
