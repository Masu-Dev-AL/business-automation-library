# Support Ticket Automation System

## Complete Technical Guide

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Implementation Guide](#3-implementation-guide)
   - [3.1 Pipedream Account & Project Setup](#31-pipedream-account--project-setup)
   - [3.2 PostgreSQL Database Setup (Neon)](#32-postgresql-database-setup-neon)
   - [3.3 Anthropic Claude API Setup](#33-anthropic-claude-api-setup)
   - [3.4 Slack Webhook Configuration](#34-slack-webhook-configuration)
   - [3.5 SendGrid Email Setup](#35-sendgrid-email-setup)
   - [3.6 Building the Pipedream Workflow](#36-building-the-pipedream-workflow)
   - [3.7 Environment Variables in Pipedream](#37-environment-variables-in-pipedream)
4. [Script Reference](#4-script-reference)
5. [Database Reference](#5-database-reference)
6. [Testing Procedures](#6-testing-procedures)
7. [Troubleshooting & Lessons Learned](#7-troubleshooting--lessons-learned)
8. [Cost Analysis](#8-cost-analysis)

---

## 1. Executive Summary

### Business Problem

Support teams at growing businesses waste significant time manually reading, sorting, and routing incoming tickets. A single inbox receives billing questions, technical bugs, shipping issues, and general enquiries — all mixed together. The result is slow response times, tickets landing with the wrong team, and no structured audit trail.

### Solution

This project implements an AI-powered support ticket classification and routing pipeline that:

- **Receives** support tickets via a webhook — compatible with any form tool, chat widget, or frontend
- **Classifies** each ticket using Claude AI: category (billing / technical / shipping / general), urgency (critical / high / medium / low), and sentiment
- **Routes** each ticket to the correct Slack channel with a formatted notification
- **Replies** automatically to the submitter with a ticket ID and SLA-based response time target
- **Logs** every ticket and its AI output to PostgreSQL for audit and future reporting

### System Capabilities

| Capability | Implementation |
|---|---|
| Ticket intake | Pipedream HTTP webhook trigger |
| AI classification | Claude API (`claude-haiku-4-5`) — category, urgency, sentiment, reasoning |
| Team routing | Dynamic Slack webhook — 4 channels based on AI category |
| Submitter auto-reply | SendGrid transactional email with ticket ID + SLA |
| Audit log | PostgreSQL `tickets` table with full AI output stored per row |
| End-to-end latency | ~3–5 seconds per ticket |

### Technologies

| Layer | Technology |
|---|---|
| Orchestration | Pipedream (cloud-hosted, no infrastructure required) |
| AI | Anthropic Claude API (`claude-haiku-4-5`) |
| Database | PostgreSQL via Neon (serverless, free tier) |
| Team Notifications | Slack Incoming Webhooks |
| Submitter Email | SendGrid Transactional Email API |
| Language | Python 3.x (Pipedream code steps) |

---

## 2. Architecture Overview

See `technical_guide/architecture.md` and `technical_guide/pipedream_workflow_diagram.md` for full Mermaid diagrams.

### Data Flow Summary

```
Submitter sends form/request
    |
    v
Pipedream HTTP Trigger (webhook URL)
    |
    v
Step 2 — Normalize: extract fields, generate ticket_id
    |
    v
Step 3 — Classify: Claude API returns category + urgency + sentiment + reasoning
    |
    v
Step 4 — Build Routing: map to Slack channel, compute SLA, build message content
    |
    +---> Step 5a: PostgreSQL — insert full ticket row (audit log)
    +---> Step 5b: Slack — POST to routed channel webhook
    +---> Step 5c: SendGrid — send HTML auto-reply to submitter
```

### Key Design Principles

1. **Single AI call** — All classification dimensions (category, urgency, sentiment) are extracted in one `claude-haiku-4-5` API call using structured output (Pydantic model). No chained prompts, no retries needed.

2. **Structured output via Pydantic** — `client.messages.parse()` with a `TicketClassification` Pydantic model guarantees the AI response always matches the expected schema. No JSON parsing errors.

3. **Routing logic is code, not AI** — Category → Slack channel mapping is a hardcoded dict in `pd_build_routing_decision.py`. AI classifies; Python routes. Clear separation of responsibilities.

4. **Parallel dispatch** — Steps 5a, 5b, 5c are independent. In Pipedream they can run in a parallel branch group, keeping end-to-end time under 5 seconds.

5. **Full audit trail** — `ai_reasoning` is stored per ticket in PostgreSQL so teams can inspect classification decisions without re-calling the API.

---

## 3. Implementation Guide

### 3.1 Pipedream Account & Project Setup

#### Create a Pipedream Account

1. Go to [pipedream.com](https://pipedream.com) and click **Sign Up**
2. Create a free account (GitHub login recommended)
3. You land on the **Projects** dashboard

#### Create a New Project

1. Click **New Project** (top right)
2. Name it: `support-ticket-automation`
3. Click **Create**

#### Create a New Workflow

1. Inside the project, click **New Workflow**
2. Name it: `ticket-intake-pipeline`
3. Click **Create Workflow** — the workflow editor opens

> **What is a workflow?** A Pipedream workflow is a sequence of steps. The first step is always a trigger (what starts the workflow). Every step after that runs in order and can access the output of all previous steps.

---

### 3.2 PostgreSQL Database Setup (Neon)

This project uses [Neon](https://neon.tech) — a free, serverless PostgreSQL provider that gives you a connection string with zero infrastructure to manage. Ideal for demos and small production workloads.

#### Create a Neon Account

1. Go to [neon.tech](https://neon.tech) and click **Sign Up**
2. Create a free account
3. Click **Create Project**
4. Name it: `support-tickets`
5. Select a region (choose one closest to your Pipedream deployment region — US East is a safe default)
6. Click **Create Project**

#### Get the Connection String

1. In the Neon dashboard, click your project → **Connection Details**
2. Select the **connection string** tab
3. Copy the full `postgresql://...` URL — you will need this for the `DATABASE_URL` environment variable

```
postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

> **Important:** The `?sslmode=require` at the end is required for Neon connections. Do not remove it.

#### Run the Schema

1. In the Neon dashboard, click **SQL Editor** (left sidebar)
2. Paste the full contents of `sql/schema.sql`
3. Click **Run** (or press Cmd/Ctrl + Enter)
4. Verify the output shows: `CREATE TABLE`, `CREATE INDEX` statements completing successfully

Alternatively, run from your local machine:

```bash
psql "postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require" -f sql/schema.sql
```

#### Verify the Table

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'tickets'
ORDER BY ordinal_position;
```

You should see 15 columns: `id`, `ticket_id`, `submitter_name`, `submitter_email`, `subject`, `body`, `category`, `urgency`, `sentiment`, `sentiment_score`, `ai_reasoning`, `assigned_channel`, `response_time_hours`, `created_at`, `processed_at`.

---

### 3.3 Anthropic Claude API Setup

#### Create an Anthropic Account

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up and verify your email
3. Navigate to **API Keys** (left sidebar)
4. Click **Create Key**
5. Name it: `support-ticket-automation`
6. Copy the key — it starts with `sk-ant-...`

> **Note:** You will need to add a payment method under **Billing** to use the API beyond the initial free credits. For demo/testing purposes, the free credits are sufficient.

#### Verify the Key (Optional)

```bash
curl https://api.anthropic.com/v1/messages \
  -H "content-type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-haiku-4-5","max_tokens":64,"messages":[{"role":"user","content":"Say OK"}]}'
```

Expected response includes `"content":[{"type":"text","text":"OK"}]`.

---

### 3.4 Slack Webhook Configuration

You need four Slack channels and one incoming webhook URL per channel. All four webhooks come from a single Slack App you create once.

#### Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App** → **From scratch**
3. App Name: `Support Ticket Router`
4. Select your workspace → **Create App**

#### Enable Incoming Webhooks

1. In the app settings, click **Incoming Webhooks** (left sidebar)
2. Toggle **Activate Incoming Webhooks** to **On**
3. Scroll down and click **Add New Webhook to Workspace**

#### Create the Four Channels

In Slack, create these four channels if they don't exist:

- `#support-billing`
- `#support-technical`
- `#support-shipping`
- `#support-general`

#### Add a Webhook for Each Channel

Repeat these steps **four times** — once per channel:

1. Click **Add New Webhook to Workspace**
2. Select the channel (e.g. `#support-billing`)
3. Click **Allow**
4. Copy the webhook URL (format: `https://hooks.slack.com/services/T.../B.../...`)

Save all four webhook URLs — you will add them as environment variables in step 3.7.

#### Test a Webhook

```bash
curl -X POST YOUR_SLACK_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"text": "Webhook test — support ticket router connected"}'
```

You should see the message appear in the corresponding Slack channel.

---

### 3.5 SendGrid Email Setup

SendGrid is a transactional email API. It sends auto-reply emails from your support address to ticket submitters.

#### Create a SendGrid Account

1. Go to [sendgrid.com](https://sendgrid.com) and click **Start For Free**
2. Create an account (free tier: 100 emails/day)
3. Complete the account setup wizard

#### Verify a Sender Identity

SendGrid requires you to verify the email address or domain you will send from.

**Option A — Single Sender (easier, good for demos):**
1. Go to **Settings → Sender Authentication → Single Sender Verification**
2. Click **Create New Sender**
3. Fill in: From Name (`Support Team`), From Email (your email), Reply To, Company, etc.
4. Click **Create** — SendGrid sends a verification email
5. Click the verification link in that email

**Option B — Domain Authentication (better for production):**
1. Go to **Settings → Sender Authentication → Domain Authentication**
2. Follow the DNS record setup for your domain

> For demos and testing, Option A is sufficient.

#### Create an API Key

1. Go to **Settings → API Keys**
2. Click **Create API Key**
3. Name: `support-ticket-automation`
4. Permission level: **Restricted Access** → enable **Mail Send → Full Access**
5. Click **Create & View**
6. Copy the key — it starts with `SG....`

> **Important:** The API key is only shown once. Save it immediately.

---

### 3.6 Building the Pipedream Workflow

This section walks through adding each step in the workflow editor. The step names you assign here must match exactly what the scripts reference via `pd.steps["step_name"]`.

#### Step 1 — Email Trigger

1. In the workflow editor, the first block says **Add a trigger**
2. Click it → select **Email**
3. Click **Save and continue**
4. Pipedream generates a unique `@pipedream.net` email address — copy it
5. Send a test email to this address to trigger the workflow

> The trigger step is always named `trigger` in Pipedream. No renaming needed.

> **How it works:** Any email sent to your `@pipedream.net` address fires the workflow. The sender's name, email address, subject line, and body are all captured automatically from the email headers and passed to the next step.

#### Step 2 — Normalize Ticket

1. Click **+** to add a step below the trigger
2. Select **Run Python code**
3. **Rename the step:** click the step name (default: `python_1`) → type `normalize_ticket` → press Enter
4. Paste the full contents of `scripts/pd_normalize_ticket.py` into the code editor
5. Click **Test** to verify — you should see the step execute and return a dict with `ticket_id`, `name`, `email`, `subject`, `body`, `received_at`

> **Why renaming matters:** Every downstream step accesses this step's output via `pd.steps["normalize_ticket"]["$return_value"]`. If the name is wrong, you will get a `KeyError`.

#### Step 3 — Classify Ticket

1. Click **+** → **Run Python code**
2. Rename to: `classify_ticket`
3. Paste the full contents of `scripts/pd_classify_ticket.py`
4. Pipedream will automatically install `anthropic` and `pydantic` on the first run — this takes ~20 seconds
5. Click **Test** — you should see output like:

```json
{
  "category": "technical",
  "urgency": "high",
  "sentiment": "negative",
  "sentiment_score": -0.7,
  "reasoning": "User reports a broken API integration causing revenue impact."
}
```

> **Package installation:** Pipedream detects `import anthropic` and `from pydantic import BaseModel` and auto-installs them. If the first test times out, click Test again — packages are cached after the first install.

#### Step 4 — Build Routing Decision

1. Click **+** → **Run Python code**
2. Rename to: `build_routing_decision`
3. Paste the full contents of `scripts/pd_build_routing_decision.py`
4. Click **Test** — output should include `slack_webhook_url`, `assigned_channel`, `response_time_hours`, `slack_text`, `email_html`

#### Step 5a — Log to PostgreSQL

1. Click **+** → **Run Python code**
2. Rename to: `log_to_postgres`
3. Paste the full contents of `scripts/pd_log_to_postgres.py`
4. Click **Test** — output should be `{"db_id": 1, "ticket_id": "TKT-XXXXXXXX"}`

> **Package:** Pipedream auto-installs `psycopg2-binary` from the `import psycopg2` statement.

#### Step 5b — Post to Slack

1. Click **+** → **Run Python code**
2. Rename to: `post_to_slack`
3. Paste the full contents of `scripts/pd_post_to_slack.py`
4. Click **Test** — verify the message appears in the correct Slack channel

#### Step 5c — Send Reply Email

1. Click **+** → **Run Python code**
2. Rename to: `send_reply_email`
3. Paste the full contents of `scripts/pd_send_reply_email.py`
4. Click **Test** — verify the auto-reply arrives in the submitter's inbox

#### Activate the Workflow

1. Click the **Deploy** button (top right)
2. Confirm the workflow is **Active**
3. The webhook URL is now live and accepting real requests

---

### 3.7 Environment Variables in Pipedream

All credentials are stored as Pipedream environment variables — never hardcoded in scripts.

#### Where to Set Them

1. In the Pipedream dashboard, click your project name → **Settings** (gear icon)
2. Click **Environment Variables**
3. Add each variable with **+ Add Variable**

#### Required Variables

| Variable | Where to get it | Example value |
|---|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys | `sk-ant-api03-...` |
| `DATABASE_URL` | Neon dashboard → Connection Details | `postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require` |
| `SLACK_WEBHOOK_BILLING` | api.slack.com → Your App → Incoming Webhooks | `https://hooks.slack.com/services/...` |
| `SLACK_WEBHOOK_TECHNICAL` | api.slack.com → Your App → Incoming Webhooks | `https://hooks.slack.com/services/...` |
| `SLACK_WEBHOOK_SHIPPING` | api.slack.com → Your App → Incoming Webhooks | `https://hooks.slack.com/services/...` |
| `SLACK_WEBHOOK_GENERAL` | api.slack.com → Your App → Incoming Webhooks | `https://hooks.slack.com/services/...` |
| `SENDGRID_API_KEY` | SendGrid → Settings → API Keys | `SG.xxx...` |
| `SENDGRID_FROM_EMAIL` | The verified sender email address | `support@yourdomain.com` |
| `SENDGRID_FROM_NAME` | Display name in the From field | `Support Team` |

> **Scope:** Variables set at the **project** level are available to all workflows in the project. Variables set at the **account** level are available to all projects. Either works — project-level is recommended to keep credentials scoped.

---

### 3.8 Connecting a Real Support Email Address

In production, customers should email a real address like `support@yourdomain.com` — not a `@pipedream.net` address. Use email forwarding to bridge the two.

#### Option A — Email Forwarding (Recommended for most setups)

Forward all mail from your support address to your Pipedream email trigger address. No DNS changes required.

**Gmail / Google Workspace:**
1. Go to **Settings → See all settings → Forwarding and POP/IMAP**
2. Click **Add a forwarding address**
3. Enter your `@pipedream.net` trigger address
4. Confirm the verification email Pipedream receives (check your workflow execution log — Pipedream captures it as a trigger event)
5. Set the rule to **Forward a copy** and optionally **keep a copy** in the inbox

**Result:** Customer emails `support@yourdomain.com` → Google forwards to Pipedream → workflow fires automatically.

#### Option B — MX Record Routing (Production / custom domain)

Point your domain's MX DNS records directly at Pipedream. Every email to `*@yourdomain.com` routes to Pipedream without forwarding.

1. In your domain registrar's DNS settings, add an MX record pointing to Pipedream's inbound mail servers
2. Refer to Pipedream's current documentation for the exact MX record values
3. Propagation takes up to 48 hours

> For demos and small production workloads, Option A is sufficient and takes under 5 minutes to set up.

---

## 4. Script Reference

| Script | Step Name | Input Steps | Purpose |
|---|---|---|---|
| `pd_normalize_ticket.py` | `normalize_ticket` | `trigger` | Extract fields from raw webhook body; generate `ticket_id` |
| `pd_classify_ticket.py` | `classify_ticket` | `normalize_ticket` | Call Claude API; return structured classification |
| `pd_build_routing_decision.py` | `build_routing_decision` | `normalize_ticket`, `classify_ticket` | Map category → channel; compute SLA; build Slack + email content |
| `pd_log_to_postgres.py` | `log_to_postgres` | `normalize_ticket`, `classify_ticket`, `build_routing_decision` | Insert full ticket row to PostgreSQL |
| `pd_post_to_slack.py` | `post_to_slack` | `normalize_ticket`, `build_routing_decision` | POST notification to routed Slack channel |
| `pd_send_reply_email.py` | `send_reply_email` | `normalize_ticket`, `build_routing_decision` | Send HTML auto-reply via SendGrid |

### Step Data Access Pattern

Each script accesses prior steps via:

```python
pd.steps["step_name"]["$return_value"]
```

The trigger body is accessed via:

```python
pd.steps["trigger"]["event"]["body"]
```

### Classification Schema (pd_classify_ticket.py)

Claude is prompted to return a strict Pydantic model:

```python
class TicketClassification(BaseModel):
    category:        str    # billing | technical | shipping | general
    urgency:         str    # critical | high | medium | low
    sentiment:       str    # positive | neutral | negative
    sentiment_score: float  # -1.0 to 1.0
    reasoning:       str    # one-sentence explanation
```

### SLA & Routing Table (pd_build_routing_decision.py)

| Urgency | SLA Target | Slack Channel (by category) |
|---|---|---|
| critical | 1 hour | all channels alerted |
| high | 4 hours | category channel |
| medium | 8 hours | category channel |
| low | 24 hours | category channel |

| Category | Slack Channel | Env Variable |
|---|---|---|
| billing | `#support-billing` | `SLACK_WEBHOOK_BILLING` |
| technical | `#support-technical` | `SLACK_WEBHOOK_TECHNICAL` |
| shipping | `#support-shipping` | `SLACK_WEBHOOK_SHIPPING` |
| general | `#support-general` | `SLACK_WEBHOOK_GENERAL` |

---

## 5. Database Reference

### tickets Table

Full DDL is in `sql/schema.sql`.

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL | Auto-increment primary key |
| `ticket_id` | VARCHAR(20) | Human-readable ID (e.g. `TKT-A3F2C1B9`) |
| `submitter_name` | VARCHAR(255) | Name from webhook payload |
| `submitter_email` | VARCHAR(255) | Email from webhook payload |
| `subject` | TEXT | Ticket subject |
| `body` | TEXT | Full ticket body text |
| `category` | VARCHAR(50) | AI output: `billing`, `technical`, `shipping`, `general` |
| `urgency` | VARCHAR(20) | AI output: `critical`, `high`, `medium`, `low` |
| `sentiment` | VARCHAR(20) | AI output: `positive`, `neutral`, `negative` |
| `sentiment_score` | DECIMAL(3,2) | AI output: `-1.00` to `1.00` |
| `ai_reasoning` | TEXT | AI output: one-sentence classification explanation |
| `assigned_channel` | VARCHAR(100) | Slack channel name (e.g. `#support-technical`) |
| `response_time_hours` | INTEGER | SLA target in hours |
| `created_at` | TIMESTAMP | Time ticket was received |
| `processed_at` | TIMESTAMP | Time AI processing completed |

### Useful Queries

**View all tickets:**
```sql
SELECT ticket_id, submitter_email, category, urgency, sentiment, assigned_channel, created_at
FROM tickets
ORDER BY created_at DESC;
```

**Count by category:**
```sql
SELECT category, COUNT(*) AS total
FROM tickets
GROUP BY category
ORDER BY total DESC;
```

**Average urgency distribution:**
```sql
SELECT urgency, COUNT(*) AS total,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct
FROM tickets
GROUP BY urgency
ORDER BY total DESC;
```

**Average sentiment score by category:**
```sql
SELECT category,
       ROUND(AVG(sentiment_score)::numeric, 2) AS avg_sentiment,
       COUNT(*) AS ticket_count
FROM tickets
GROUP BY category
ORDER BY avg_sentiment;
```

---

## 6. Testing Procedures

### 6.1 Sample Webhook Payload

Use this payload to test each step during build. Save to `sample_tickets/sample_payloads.json`.

```json
[
  {
    "name": "Sarah Chen",
    "email": "sarah.chen@example.com",
    "subject": "Charged twice for last month's subscription",
    "body": "Hi, I was charged twice on my credit card for my monthly plan this billing cycle. I can see two identical charges of $49.99 on October 3rd. Please refund the duplicate charge as soon as possible."
  },
  {
    "name": "Marcus Williams",
    "email": "marcus@example.com",
    "subject": "API returning 500 errors on /orders endpoint",
    "body": "Our integration with your API has been throwing 500 Internal Server Errors since this morning on the /orders endpoint. This is blocking our entire checkout flow. We are losing sales right now. Error: InternalServerError at line 42. Please escalate immediately."
  },
  {
    "name": "Priya Patel",
    "email": "priya.patel@gmail.com",
    "subject": "Order #84521 hasn't arrived yet",
    "body": "Hello, my order #84521 was supposed to arrive 5 days ago. The tracking page still shows 'In Transit' with no updates for the past 3 days. Could you look into this and let me know the status?"
  },
  {
    "name": "James Thompson",
    "email": "james.t@company.org",
    "subject": "Question about exporting data",
    "body": "Hi team, I was wondering if there's a way to export all my historical data as a CSV file. I've looked through the settings but can't find the option. Happy to wait for a response, no rush at all."
  }
]
```

### 6.2 Sending Test Requests

Replace `YOUR_WEBHOOK_URL` with the URL from Step 1 of the Pipedream workflow.

> **Common mistake:** `-X` sets the HTTP method — `POST` must come immediately after it, before the URL. `curl -X POST https://...` is correct. `curl -X https://...` will throw `no URL specified`.

**Single ticket (billing — should route to #support-billing):**
```bash
curl -X POST YOUR_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sarah Chen",
    "email": "sarah.chen@example.com",
    "subject": "Charged twice for last month",
    "body": "I was charged twice on my credit card. Please refund the duplicate charge."
  }'
```

**Critical technical issue (should be urgency=critical):**
```bash
curl -X POST YOUR_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Marcus Williams",
    "email": "marcus@example.com",
    "subject": "API returning 500 errors — checkout completely down",
    "body": "Our integration with your API has been throwing 500 errors since this morning. This is blocking our entire checkout flow. We are losing sales right now."
  }'
```

### 6.3 Verification Checklist

After sending each test request, verify all five outputs:

- [ ] **Pipedream workflow ran** — check the workflow execution log in the Pipedream dashboard
- [ ] **Step 2 (normalize)** — `ticket_id` is generated (format: `TKT-XXXXXXXX`)
- [ ] **Step 3 (classify)** — `category`, `urgency`, `sentiment`, `reasoning` all present
- [ ] **Step 4 (routing)** — correct `assigned_channel` for the category
- [ ] **Step 5a (postgres)** — row appears in the `tickets` table in Neon SQL Editor
- [ ] **Step 5b (slack)** — message appears in the correct Slack channel
- [ ] **Step 5c (email)** — auto-reply arrives in the submitter email inbox

### 6.4 Verify PostgreSQL Record

In the Neon SQL Editor:

```sql
SELECT * FROM tickets ORDER BY created_at DESC LIMIT 1;
```

Confirm all columns are populated, especially `category`, `urgency`, `ai_reasoning`, and `assigned_channel`.

---

## 7. Troubleshooting & Lessons Learned

> This section is updated as issues are discovered during the build. See `BUILD_LOG.md` for the full issue history.

### Package Install Timeout on First Run

**Symptom:** Step 3 (`classify_ticket`) times out on first test.

**Cause:** Pipedream is installing `anthropic` and `pydantic` for the first time. This can take 15–30 seconds and may exceed the default step timeout.

**Fix:** Click **Test** again. Packages are cached after the first install and subsequent runs are fast.

---

### `KeyError: 'step_name'` in pd.steps

**Symptom:** A script throws `KeyError: 'classify_ticket'` (or similar).

**Cause:** The step was not renamed correctly in Pipedream. The step name in the UI must exactly match the string used in `pd.steps["step_name"]`.

**Fix:**
1. Click the step name in the Pipedream workflow editor
2. Rename it to exactly match the required name (see Section 4 — Script Reference)
3. Re-test the failing step

---

### Neon Connection Timeout

**Symptom:** `pd_log_to_postgres.py` throws a connection error or times out.

**Cause:** Neon serverless PostgreSQL suspends inactive databases after 5 minutes on the free tier. The first connection after suspension takes 1–2 seconds to wake up.

**Fix:** Neon auto-wakes on connection — retry the test. For production use, consider keeping the connection alive with a scheduled ping or upgrading to Neon's paid tier.

---

### SendGrid 403 Forbidden

**Symptom:** `pd_send_reply_email.py` returns `status_code: 403`.

**Cause:** The `SENDGRID_FROM_EMAIL` address has not been verified as a sender identity.

**Fix:** Complete Single Sender Verification in the SendGrid dashboard (Section 3.5) and verify the email link sent to that address.

---

### Slack Webhook Returns 404

**Symptom:** `pd_post_to_slack.py` returns `status_code: 404`.

**Cause:** The webhook URL stored in the environment variable corresponds to a channel that has been deleted, or the wrong env variable is being used.

**Fix:** Regenerate the webhook URL for the channel in the Slack App settings and update the environment variable in Pipedream.

---

### Claude Returns Unexpected Category

**Symptom:** A billing ticket is classified as `general`.

**Cause:** The ticket body was too vague for Claude to identify a specific category confidently.

**Fix:** The system prompt in `pd_classify_ticket.py` provides clear definitions for each category. If misclassification is frequent, add more examples to the system prompt via few-shot prompting.

---

## 8. Cost Analysis

### Development / Testing

| Resource | Cost |
|---|---|
| Pipedream | Free (Pipedream free tier: 10,000 invocations/month) |
| Neon PostgreSQL | Free (Neon free tier: 0.5 GB storage, 1 compute unit) |
| Anthropic Claude API | ~$0.00001 per ticket (Opus 4.6 at ~500 tokens/call) |
| Slack Incoming Webhooks | Free |
| SendGrid | Free (100 emails/day free tier) |
| **Total (development)** | **~$0/month** |

### Production Estimate (1,000 tickets/month)

| Resource | Usage | Cost |
|---|---|---|
| Pipedream | 1,000 workflow executions | Free (within free tier) |
| Neon PostgreSQL | 1,000 rows (~1 MB) | Free (within free tier) |
| Anthropic Claude `claude-haiku-4-5` | ~500K tokens input + 50K output | ~$0.75/month |
| Slack | Unlimited webhooks | Free |
| SendGrid | 1,000 emails | Free (within free tier) |
| **Total (production, 1K tickets/month)** | | **~$1/month** |
