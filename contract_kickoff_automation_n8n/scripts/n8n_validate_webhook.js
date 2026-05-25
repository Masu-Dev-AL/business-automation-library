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
