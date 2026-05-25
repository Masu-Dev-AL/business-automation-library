# Prerequisites Checklist

Complete each section before activating the workflow in n8n.

---

## 1. n8n Instance

- [ ] n8n self-hosted instance running (Docker recommended)
- [ ] n8n accessible via public URL (required for PandaDoc webhook delivery)
- [ ] `pdfminer.six` installed on the n8n host: `pip install pdfminer.six`

---

## 2. PandaDoc

- [ ] PandaDoc account created (free tier works)
- [ ] API key generated: **Settings → Integrations → API**
- [ ] Webhook configured:
  - Go to **Settings → Integrations → Webhooks**
  - URL: `https://your-n8n-instance.com/webhook/contract-signed`
  - Events: `document_state_changed`
  - Shared secret: generate a random string, save as `PANDADOC_WEBHOOK_SECRET`
- [ ] n8n credential added: **HTTP Header Auth** with header `x-pd-secret` = webhook secret
- [ ] Test: send a test webhook event from PandaDoc and confirm n8n receives it

---

## 3. Anthropic / Claude API

- [ ] Anthropic account created at console.anthropic.com
- [ ] API key generated: **API Keys → Create key**
- [ ] n8n credential added: **HTTP Header Auth** with header `x-api-key` = API key
- [ ] Model in use: `claude-sonnet-4-6`

---

## 4. Asana

- [ ] Asana account created (free tier — up to 15 users)
- [ ] Personal Access Token generated: **My Profile → Apps → Manage Developer Apps → Personal Access Token**
- [ ] Workspace GID noted: visible in Asana URL (`app.asana.com/0/{WORKSPACE_GID}/...`)
- [ ] Team GID noted: GET `https://app.asana.com/api/1.0/teams` with your token
- [ ] n8n credential added: **HTTP Header Auth** with header `Authorization` = `Bearer {token}`
- [ ] Test: manually POST to Asana Projects API to confirm token + workspace GID are valid

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
| `PANDADOC_WEBHOOK_SECRET` | The secret string you chose when configuring the PandaDoc webhook |
| `PANDADOC_API_KEY` | PandaDoc Settings → API |
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
- [ ] Send a test PandaDoc document through the full pipeline using `TEST-001` (web design contract)
- [ ] Confirm: Asana project created · kickoff email received · Google Sheets row appended
