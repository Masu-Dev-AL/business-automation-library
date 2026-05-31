# Prerequisites Checklist

Complete each section before activating the workflow in n8n.

---

## 1. n8n Instance

- [ ] n8n self-hosted instance running (Docker recommended)
- [ ] n8n accessible via public URL (required for DocuSign Connect webhook delivery)

---

## 2. DocuSign

- [ ] DocuSign Developer Sandbox created (free at developers.docusign.com)
- [ ] Integration key created: **Apps & Keys → Add App and Integration Key**
- [ ] OAuth2 secret generated for the integration key
- [ ] DocuSign Connect webhook configured:
  - Go to **Admin → Connect**
  - Add a new configuration
  - URL: `https://your-n8n-instance.com/webhook/contract-signed`
  - Trigger events: `Envelope Completed`
  - Enable **Include Documents** so the PDF is accessible via the Documents API
- [ ] Account ID noted: found in **Apps & Keys** or the API account overview
- [ ] n8n credential added: **DocuSign OAuth2 API** with integration key, secret, and account ID
- [ ] Test: complete a test envelope in the DocuSign sandbox and confirm n8n receives the webhook

---

## 3. Anthropic / Claude API

- [ ] Anthropic account created at console.anthropic.com
- [ ] API key generated: **API Keys → Create key**
- [ ] n8n credential added: **Anthropic** — paste the API key
- [ ] Model in use: `claude-sonnet-4-5`

---

## 4. Asana

- [ ] Asana account created (free tier — up to 15 users)
- [ ] Personal Access Token generated: **My Profile → Apps → Manage Developer Apps → Personal Access Token**
- [ ] Workspace GID noted: visible in Asana URL (`app.asana.com/0/{WORKSPACE_GID}/...`)
- [ ] Team GID noted: GET `https://app.asana.com/api/1.0/teams` with your token
- [ ] n8n credential added: **Asana** — paste the Personal Access Token
- [ ] Test: manually create an Asana project via the n8n Asana node to confirm the token + workspace GID are valid

---

## 5. Gmail

- [ ] Google account with Gmail access
- [ ] n8n Gmail credential added: **OAuth2** (follow n8n's Gmail OAuth setup guide)
- [ ] Scopes required: `gmail.send`
- [ ] Test: send a test email via n8n Gmail node to confirm OAuth is working
- [ ] `OPERATOR_EMAIL` and `ACCOUNT_MANAGER_EMAIL` set in environment variables
- [ ] `EMAIL_SIGNATURE` set in environment variables (plain text, will be appended to emails)

---

## 6. Google Sheets

- [ ] Google Sheet created with 3 tabs: `contracts`, `tasks`, `errors`
- [ ] Column headers added to row 1 of each tab (see `google_sheets_schema.md`)
- [ ] Sheet ID noted (from URL: `docs.google.com/spreadsheets/d/{SHEET_ID}/edit`)
- [ ] n8n Google Sheets credential added: **OAuth2** (same Google account as Gmail)
- [ ] Scopes required: `spreadsheets`
- [ ] Sheet ID configured in n8n nodes A13, A14, and error logging nodes

---

## 7. Environment Variables in n8n

Set in n8n: **Settings → Environment Variables** (or via `.env` file if self-hosted with Docker).

| Variable | Where to find it |
|----------|-----------------|
| `DOCUSIGN_ACCOUNT_ID` | DocuSign Apps & Keys → API Account ID |
| `DOCUSIGN_OAUTH_CLIENT_ID` | DocuSign Apps & Keys → Integration Key |
| `DOCUSIGN_OAUTH_CLIENT_SECRET` | DocuSign Apps & Keys → Secret key for the integration |
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys |
| `ASANA_ACCESS_TOKEN` | Asana → Personal Access Token |
| `ASANA_WORKSPACE_GID` | Asana URL or API |
| `ASANA_TEAM_GID` | Asana API: `GET /teams` |
| `OPERATOR_EMAIL` | Your email for failure alerts |
| `ACCOUNT_MANAGER_EMAIL` | Email to CC on kickoff emails |
| `EMAIL_SIGNATURE` | Plain text signature block |

---

## 8. PM Tool Swap Notes (Phase 3)

When adding alternative PM tool outputs in Phase 3:

### ClickUp
- Create a ClickUp Space and List to receive tasks
- Generate API key: **Settings → Apps → API**
- Add `CLICKUP_API_KEY` and `CLICKUP_LIST_ID` to env vars
- Swap node A8 to POST `https://api.clickup.com/api/v2/list/{list_id}/task`
- ClickUp creates tasks directly (no project container needed)

### Notion
- Create a Notion database with columns matching the task schema
- Generate integration token: **Settings → Integrations → Develop**
- Share the database with your integration
- Add `NOTION_DATABASE_ID` to env vars
- Swap node A8 to POST `https://api.notion.com/v1/pages` with `parent.database_id`

### Trello
- Create a Trello board and copy the board short link ID
- Generate API key + token: `https://trello.com/power-ups/admin`
- Swap node A8 to POST `https://api.trello.com/1/boards` then create cards per deliverable
- Simplest swap — no task hierarchy, Kanban only

---

## 9. Final Verification

- [ ] Import `contract-kickoff-main.json` into n8n
- [ ] All credentials attached to correct nodes
- [ ] All environment variables set
- [ ] Workflow activated
- [ ] Complete a test DocuSign envelope using `TEST-001` (web design contract) sent through the full pipeline
- [ ] Confirm: Asana project created · kickoff email received · Google Sheets row appended
