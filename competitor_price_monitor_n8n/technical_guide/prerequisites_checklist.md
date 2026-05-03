# Vitamin Price Monitor — Prerequisites Checklist

Print this page and work through each section before opening the [Build Guide](technical_guide.md#workflows--build-guide).

---

## 1. VPS / Docker

- [ ] VPS provisioned (Debian 12 or Ubuntu 22.04+ recommended, 2 GB RAM minimum)
- [ ] Docker Engine and Docker Compose v2 installed (`docker compose version` returns v2.x)
- [ ] Domain name pointing to VPS IP address (A record propagated)

> If using Traefik for SSL, confirm the Traefik container is running and `letsencrypt` volume exists before deploying n8n.

---

## 2. Google Cloud OAuth2

- [ ] Google Cloud project created (or existing project selected)
- [ ] Sheets API enabled: **APIs & Services → Enable APIs → Google Sheets API**
- [ ] Gmail API enabled: **APIs & Services → Enable APIs → Gmail API**
- [ ] OAuth 2.0 Client ID created: **APIs & Services → Credentials → Create Credentials → OAuth client ID** (type: Web application)
- [ ] Authorized redirect URI added: `https://n8n.your-domain.com/rest/oauth2-credential/callback`

Write credentials here:

```
Client ID:     ________________________________________________
Client Secret: ________________________________________________
```

> Both Google Sheets and Gmail use the same OAuth client — one client, two n8n credentials.

---

## 3. Google Sheets

- [ ] New Google Sheet created
- [ ] 4 tabs created (exact names): `products`, `snapshots`, `changes`, `analysis`
- [ ] Column headers added to row 1 of each tab (see `config/google_sheets_seed.md` for exact column lists)
- [ ] 5 Phase 1 seed rows added to `products` tab (`url`, `competitor_name`, `competitor_code`, `vitamin`, `vitamin_code` columns only — leave all other columns blank)
- [ ] Sheet ID copied from the URL: `docs.google.com/spreadsheets/d/**<SHEET_ID>**/edit`

Write Sheet ID here:

```
Sheet ID: ________________________________________________
```

---

## 4. Anthropic API Key

- [ ] Anthropic account created at [console.anthropic.com](https://console.anthropic.com)
- [ ] API key generated: **API Keys → Create Key** (copy immediately — shown once)
- [ ] API key added to `config/.env` as `ANTHROPIC_API_KEY=sk-ant-...`

---

## 5. n8n + Docker Stack

- [ ] `config/.env.example` copied to `config/.env` and all values filled in:
  - `N8N_HOST` — your n8n subdomain (e.g. `n8n.your-domain.com`)
  - `TIMEZONE` — your timezone (e.g. `America/New_York`)
  - `N8N_ENCRYPTION_KEY` — generate with `openssl rand -hex 16`
  - `ANTHROPIC_API_KEY` — from Step 4
  - `VITAMIN_MONITOR_SHEET_ID` — from Step 3
  - `VITAMIN_MONITOR_RECIPIENT` — email address for weekly digest
- [ ] Stack started: `docker compose -f config/docker-compose.yml up -d`
- [ ] n8n UI accessible at `https://n8n.your-domain.com`

---

## 6. n8n Credentials

- [ ] **Google Sheets OAuth2 API** credential created in n8n (Credentials → New → Google Sheets OAuth2 API → authorize)
- [ ] **Gmail OAuth2 API** credential created in n8n (same Client ID / Secret as Sheets credential)
- [ ] Both credentials show a green "Connected" status

---

## 7. Scraper Service

- [ ] Scraper container is running: `docker compose -f config/docker-compose.yml ps` shows `scraper-api` as `Up`
- [ ] Health check passes (run from inside n8n container or VPS):

```bash
docker compose -f config/docker-compose.yml exec n8n wget -qO- http://scraper-api:8000/health
# Expected: {"status":"ok","version":"1.0.0","playwright_available":true}
```

> First startup takes ~3 minutes while Playwright Chromium installs inside the scraper container.

---

## Ready to Build

All boxes checked? Open [Section 3 — Workflows Build Guide](technical_guide.md#workflows--build-guide) and build Workflow 1 (Onboarding) first, then Workflow 2 (Daily Capture), then Workflow 3 (Weekly Analysis).

Activate workflows in order: Onboarding → Daily Capture → Weekly Analysis.
