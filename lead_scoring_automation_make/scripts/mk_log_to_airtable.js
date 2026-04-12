// Make.com — Module 6: Log Lead to Airtable
// Module type: Airtable > Create a Record
//
// Creates a new record in the Leads table with all lead data and AI scoring output.
//
// HOW TO USE:
// 1. Add an "Airtable > Create a Record" module
// 2. Connect your Airtable account (OAuth — no API key needed in Make UI)
// 3. Select your Base ID and table name ("Leads")
// 4. Map each Airtable field to the Make expression shown below
//
// All variable references follow this module numbering convention:
//   Module 2 = Normalize Lead (Set Multiple Variables)
//   Module 4 = JSON Parse (Claude response)
//   Module 5 = Routing Decision (Set Multiple Variables)
// ─────────────────────────────────────────────────────────────────────────────

// ── Airtable Field Mappings ───────────────────────────────────────────────────

const fieldMappings = {

  // Lead identity
  "Lead ID":            "{{2.lead_id}}",
  "Name":               "{{2.lead_name}}",
  "Email":              "{{2.lead_email}}",
  "Company":            "{{2.company}}",
  "Role":               "{{2.role}}",

  // Typeform answers
  "Company Size":       "{{2.company_size}}",
  "Budget Range":       "{{2.budget}}",
  "Country":            "{{2.country}}",
  "Primary Challenge":  "{{2.challenge}}",
  "Submitted At":       "{{2.submitted_at}}",

  // Territory routing
  "Territory":          "{{5.territory_label}}",
  "Assigned Rep":       "{{5.rep_name}}",

  // Claude AI scoring
  "ICP Score":          "{{4.icp_score}}",
  "Intent Score":       "{{4.intent_score}}",
  "Priority Tier":      "{{4.priority_tier}}",            // capitalise in Make: {{capitalize(4.priority_tier)}}
  "Recommended Action": "{{4.recommended_action}}",
  "AI Reasoning":       "{{4.reasoning}}",

  // Default status on creation
  "Status":             "New",
};

// ── Notes ─────────────────────────────────────────────────────────────────────
// - "Priority Tier" is a Single Select field. Make sure the value matches
//   one of the allowed options exactly: Hot, Warm, Cold (capitalised).
//   Use {{capitalize(4.priority_tier)}} in Make to auto-capitalise.
//
// - "Territory" is also a Single Select. Values must match exactly:
//   North America, Europe, Asia-Pacific, Other.
//
// - "Created At" is auto-populated by Airtable — do not map it manually.
