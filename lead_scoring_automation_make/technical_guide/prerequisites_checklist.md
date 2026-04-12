# Prerequisites Checklist — Lead Scoring & Territory Routing

## Before You Build

Complete every item below before opening the Make.com scenario editor.
Each section maps directly to the corresponding step in `lead_scoring_technical_guide.md`.

---

### Make.com Account

- [ ] Sign up at [make.com](https://make.com) (free — no credit card required)
- [ ] Create a new scenario named: `lead-scoring-territory-routing`
- [ ] Note your plan tier (free = 1,000 ops/month, covers ~110 leads/month)

---

### Typeform

- [ ] Sign up at [typeform.com](https://www.typeform.com) (free)
- [ ] Create a new form named: `Lead Intake Form`
- [ ] Add all 8 questions with correct types and **References** (see Section 3.2)
- [ ] Publish the form
- [ ] Copy the **Form ID** from the URL (`https://admin.typeform.com/form/FORM_ID_HERE/...`)

---

### Anthropic API Key

- [ ] Sign up at [console.anthropic.com](https://console.anthropic.com)
- [ ] Create an API key named: `lead-scoring-automation`
- [ ] Copy the key — it starts with `sk-ant-...`
- [ ] Store it in Make as a Custom Variable named `ANTHROPIC_API_KEY` (see Section 3.8)

---

### Airtable

- [ ] Sign up at [airtable.com](https://airtable.com) (free)
- [ ] Create a base named: `Lead Scoring CRM`
- [ ] Create a table named: `Leads` with all fields from `airtable/schema.md`
- [ ] Copy the **Base ID** from the URL (`appXXXXXXXXXXXXXX`)
- [ ] Generate a Personal Access Token with scopes: `data.records:write`, `schema.bases:read`
- [ ] Copy the token — shown only once

---

### Slack

- [ ] Create four channels in your workspace:
  - [ ] `#sales-north-america`
  - [ ] `#sales-europe`
  - [ ] `#sales-asia`
  - [ ] `#sales-general`
- [ ] Create a Slack App named `Lead Router` at [api.slack.com/apps](https://api.slack.com/apps)
- [ ] Enable Incoming Webhooks on the app
- [ ] Add one webhook per channel (4 total) and copy all four URLs:
  - [ ] `#sales-north-america` webhook URL: `___________________________`
  - [ ] `#sales-europe` webhook URL: `___________________________`
  - [ ] `#sales-asia` webhook URL: `___________________________`
  - [ ] `#sales-general` webhook URL: `___________________________`
- [ ] Confirm rep handles exist in the workspace (or create placeholder accounts):
  - [ ] `@sarah.mitchell` (North America)
  - [ ] `@james.hartley` (Europe)
  - [ ] `@priya.chen` (Asia-Pacific)
  - [ ] `@manager` (General)

---

### Gmail

- [ ] Identify which Google account you will send auto-replies from
- [ ] Authenticate the Gmail connection in Make (Section 3.6) — OAuth only, no API key needed

---

### Make Custom Variables (Credential Storage)

Before building modules, store sensitive values in Make → Team Settings → Variables:

- [ ] `ANTHROPIC_API_KEY` — your `sk-ant-...` key
- [ ] `SLACK_WEBHOOK_NA` — North America webhook URL
- [ ] `SLACK_WEBHOOK_EU` — Europe webhook URL
- [ ] `SLACK_WEBHOOK_AP` — Asia-Pacific webhook URL
- [ ] `SLACK_WEBHOOK_GENERAL` — General webhook URL

---

### Ready to Build

When all items above are checked, open the Make.com scenario editor and follow **Section 3.7** of `lead_scoring_technical_guide.md` to build each module in order.
