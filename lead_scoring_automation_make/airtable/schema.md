# Airtable Schema — Lead Scoring CRM

## Base name: Lead Scoring CRM
## Table name: Leads

Create these fields in the order shown. Set **Lead ID** as the primary field.

| Field Name | Field Type | Notes |
|---|---|---|
| Lead ID | Single line text | Primary field. Auto-generated (e.g. `LEAD-1712345678`) |
| Name | Single line text | From Typeform |
| Email | Email | From Typeform |
| Company | Single line text | From Typeform |
| Role | Single line text | From Typeform |
| Company Size | Single select | See options below |
| Budget Range | Single select | See options below |
| Country | Single line text | Extracted from Typeform Address field (`location` → Country) |
| Territory | Single select | See options below |
| Primary Challenge | Long text | From Typeform (open text answer) |
| ICP Score | Number | 1–10, output from Claude AI ("claude-haiku-4-5") |
| Intent Score | Number | 1–10, output from Claude AI ("claude-haiku-4-5") |
| Priority Tier | Single select | See options below |
| Recommended Action | Single line text | Output from Claude (e.g. "Call within 2 hours") |
| AI Reasoning | Long text | Claude's full reasoning stored per lead |
| Assigned Rep | Single line text | e.g. Sarah Mitchell |
| Status | Single select | See options below |
| Submitted At | Single line text | ISO timestamp from Typeform |
| Created At | Created time | Auto-populated by Airtable |

---

## Single Select Options

### Company Size
- 1–10
- 11–50
- 51–200
- 201–1,000
- 1,000+

### Budget Range
- Under $1k
- $1k–$5k
- $5k–$20k
- $20k–$50k
- $50k+

### Territory
- North America
- Europe
- Asia-Pacific
- Other

### Priority Tier
- Hot
- Warm
- Cold

### Status
- New
- Contacted
- Qualified
- Converted
- Lost
