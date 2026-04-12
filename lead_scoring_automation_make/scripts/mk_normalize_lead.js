// Make.com — Module 2: Normalize Lead
// Module type: Tools > Set Multiple Variables
//
// Maps raw Typeform trigger output to clean, consistently named variables
// used by all downstream modules.
//
// HOW TO USE:
// 1. Add a "Tools > Set Multiple Variables" module after your Typeform trigger (Module 1)
// 2. For each entry below, create a variable with the given name and Make expression as the value
// 3. All subsequent modules reference these variable names (e.g. {{2.lead_name}})
//
// IMPORTANT: The Typeform field refs below (name, email, company, etc.) must match
// the "Reference" values you assign to each question in the Typeform form builder.
// Set these under: Question settings > Reference (bottom of the panel).
// ─────────────────────────────────────────────────────────────────────────────

// Variable: lead_id
// Make expression: LEAD-{{formatDate(now; "X")}}
// Generates a unique ID using the current Unix timestamp (e.g. LEAD-1712345678)

// Variable: lead_name
// Make expression: {{1.answers[].text}}  (filter: field.ref = "name")
// Typeform field type: Short text | ref: name

// Variable: lead_email
// Make expression: {{1.answers[].email}}  (filter: field.ref = "email")
// Typeform field type: Email | ref: email

// Variable: company
// Make expression: {{1.answers[].text}}  (filter: field.ref = "company")
// Typeform field type: Short text | ref: company

// Variable: role
// Make expression: {{1.answers[].text}}  (filter: field.ref = "role")
// Typeform field type: Short text | ref: role

// Variable: company_size
// Make expression: {{1.answers[].choice.label}}  (filter: field.ref = "company_size")
// Typeform field type: Dropdown | ref: company_size

// Variable: budget
// Make expression: {{1.answers[].choice.label}}  (filter: field.ref = "budget")
// Typeform field type: Dropdown | ref: budget

// Variable: challenge
// Make expression: {{1.answers[].text}}  (filter: field.ref = "challenge")
// Typeform field type: Long text | ref: challenge

// Variable: country
// Make expression: {{1.answers[].choice.label}}  (filter: field.ref = "country")
// Typeform field type: Dropdown | ref: country

// Variable: submitted_at
// Make expression: {{1.submitted_at}}
// ISO 8601 timestamp from Typeform (e.g. 2026-03-09T14:32:00Z)
