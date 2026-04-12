# AI Lead Scoring & Territory Routing

## Complete Technical Guide

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Implementation Guide](#3-implementation-guide)
   - [3.1 Make.com Account & Scenario Setup](#31-makecom-account--scenario-setup)
   - [3.2 Typeform Setup](#32-typeform-setup)
   - [3.3 Anthropic Claude API Setup](#33-anthropic-claude-api-setup)
   - [3.4 Airtable Setup](#34-airtable-setup)
   - [3.5 Slack Webhook Configuration](#35-slack-webhook-configuration)
   - [3.6 Gmail Connection](#36-gmail-connection)
   - [3.7 Building the Make.com Scenario](#37-building-the-makecom-scenario)
   - [3.8 Connections & Credentials in Make](#38-connections--credentials-in-make)
   - [3.9 Exporting the Scenario Blueprint](#39-exporting-the-scenario-blueprint)
   - [3.10 Error Handling in Make](#310-error-handling-in-make)

4. [Script Reference](#4-script-reference)
5. [Airtable Reference](#5-airtable-reference)
6. [Testing Procedures](#6-testing-procedures)
7. [Troubleshooting & Lessons Learned](#7-troubleshooting--lessons-learned)
8. [Cost Analysis](#8-cost-analysis)
9. [Customizing for Your Use Case](#9-customizing-for-your-use-case)

---

## 1. Executive Summary

### Business Problem

Sales teams at growing companies receive inbound leads from contact forms but have no automated way to qualify them, assign them to the right rep, or acknowledge the lead instantly. Leads sit in a shared inbox, get manually copy-pasted into a spreadsheet, and are routed by gut feel rather than data. The result is slow response times, missed hot leads, and reps working the wrong accounts.

### Solution

This project implements an AI-powered lead scoring and territory routing pipeline that:

- **Captures** leads via Typeform — a structured form with company, budget, and challenge fields
- **Scores** each lead using Claude AI ("claude-haiku-4-5"): ICP fit (1–10), intent (1–10), and priority tier (hot / warm / cold)
- **Routes** each lead to the correct territory Slack channel with a rep @mention
- **Logs** every lead and its AI scoring output to Airtable for CRM tracking
- **Replies** automatically to the lead with a personalised Gmail confirmation

### System Capabilities

| Capability | Implementation |
|---|---|
| Lead intake | Typeform native Make.com trigger |
| AI scoring | Claude AI ("claude-haiku-4-5") — ICP score, intent score, priority tier, reasoning |
| Territory routing | Make.com Router — 4 Slack channels based on country |
| Rep notification | Slack HTTP webhook with @rep mention per territory |
| Lead auto-reply | Gmail native Make.com module — personalised HTML email |
| CRM logging | Airtable — full lead record + AI output per row |
| End-to-end latency | ~5–8 seconds per lead |

### Technologies

| Layer | Technology |
|---|---|
| Orchestration | Make.com (cloud-hosted, visual scenario builder) |
| Lead intake | Typeform (native Make connector) |
| AI | Anthropic Claude API ("claude-haiku-4-5") |
| CRM | Airtable (native Make connector) |
| Team notifications | Slack Incoming Webhooks (via HTTP module) |
| Lead email | Gmail (native Make connector, OAuth) |

---

## 2. Architecture Overview

See `technical_guide/architecture.md` and `technical_guide/make_workflow_diagram.md` for full Mermaid diagrams.

### Data Flow Summary

```
Lead submits Typeform
    |
    v
Make.com — Module 1: Typeform Trigger (Watch Responses)
    |
    v
Module 2 — Normalize: map Typeform answers to clean named variables
    |
    v
Module 3 — Score: HTTP POST to Anthropic API → Claude returns JSON scores
    |
    v
Module 4 — Parse: JSON module extracts icp_score, intent_score, priority_tier, reasoning
    |
    v
Module 5 — Route: Set Multiple Variables → territory_label, rep_handle, slack_message
    |
    v
Module 6 — Deduplicate: Airtable Search Records by email → filter if 0 results
    |
    +---> Module 7: Airtable — Create a Record (CRM log)
    +---> Module 8: Gmail — Send auto-reply to lead
    +---> Module 9: Router → 4 paths → HTTP POST to Slack (territory channel)
```

### Prerequisites

See `technical_guide/prerequisites_checklist.md` for a one-page checklist of every account, credential, and configuration item to complete before building the Make.com scenario.

---

### Key Design Principles

1. **Single AI call** — ICP score, intent score, priority tier, and reasoning are all returned in one `claude-haiku-4-5` call. No chained prompts.

2. **Structured JSON output from Claude** — the prompt instructs Claude to return only a JSON object. The JSON Parse module (Module 4) extracts all fields cleanly for downstream use.

3. **Territory routing is AI-assisted** — Claude classifies the territory directly as part of the scoring call, returning a `territory_label` field (`North America`, `Europe`, `Asia`, `General`) alongside the scores. This handles abbreviations, country codes, and spelling variations that a hardcoded `switch()` expression would miss. Module 5 reads `territory_label` directly from the parsed Claude output.

4. **Deduplication before insert** — Module 6 searches Airtable by email before creating a record. A filter blocks the rest of the pipeline if a matching record already exists, preventing duplicate leads.

5. **Unconditional outputs first** — Airtable logging and Gmail auto-reply (Modules 7 and 8) run before the Router. Every new lead is logged and acknowledged regardless of territory. The Router (Module 9) handles only the Slack notification.

6. **Credentials via Make Connections** — API keys and OAuth tokens are stored in Make's Connections panel, never hardcoded in module configurations.

---

## 3. Implementation Guide

### 3.1 Make.com Account & Scenario Setup

#### Create a Make.com Account

1. Go to [make.com](https://make.com) and click **Get started free**
2. Sign up with your email (no credit card required)
3. You land on the **Scenarios** dashboard

#### Create a New Scenario

1. Click **Create a new scenario** (top right)
2. Make opens the visual scenario editor — a blank canvas
3. Click the large **+** in the centre of the canvas to add your first module
4. You will name the scenario after adding the trigger — click the scenario name at the top (defaults to "New scenario") and rename it: `lead-scoring-territory-routing`

> **What is a scenario?** In Make.com, a scenario is the equivalent of a workflow. It is a visual chain of modules connected by arrows. Each module performs one action (trigger, transform, API call, send email, etc.). Scenarios run automatically when triggered, or on a schedule.

---

### 3.2 Typeform Setup

You need a Typeform account and a published form before connecting it to Make.

#### Create a Typeform Account

1. Go to [typeform.com](https://www.typeform.com) and click **Sign up free**
2. Create a free account
3. You land on the **My workspace** dashboard

#### Build the Lead Form

1. Click **+ Create typeform**
2. Select **Start from scratch** — Typeform opens the form editor and immediately shows an **Add form elements** panel
3. Name it: `Lead Intake Form`
4. Add the following questions in order. For each question, click **+** to open the element picker, select the type from the panel (see the **Type** column below — names match exactly what appears in the picker under **Text & Video**, **Contact info**, or **Choice**), then set the **Reference** (found in the question settings panel → scroll to the bottom):

| # | Question text | Type | Reference |
|---|---|---|---|
| 1 | What is your name? | Short text | `name` |
| 2 | What is your work email? | Email | `email` |
| 3 | What is your company name? | Short text | `company` |
| 4 | What is your role? | Short text | `role` |
| 5 | How large is your company? | Dropdown | `company_size` |
| 6 | What is your monthly budget for this? | Dropdown | `budget` |
| 7 | What is the primary challenge you are trying to solve? | Long text | `challenge` |
| 8 | Where is your business based? | Address | `location` |

**Dropdown options for Company Size (Question 5):**
- 1–10
- 11–50
- 51–200
- 201–1,000
- 1,000+

**Dropdown options for Budget (Question 6):**
- Under $1k
- $1k–$5k
- $5k–$20k
- $20k–$50k
- $50k+

> **Question 8 — Address field:** Typeform's Address element (found under **Contact info** in the element picker) collects a structured address and returns a `Country` sub-field automatically. This avoids maintaining a country dropdown and eliminates spelling mismatches. Typeform returns country as a full name (e.g. `United States`, `United Kingdom`) which the `switch()` expression in Module 5 uses directly.

> **Setting References:** References are critical. Make's Typeform module identifies each answer by its `field.ref` value. If the reference is wrong or missing, the mapping in Module 2 will return empty values. Double-check each question's reference in Typeform before moving on.

#### Publish the Form

1. Click **Share** (top right) in Typeform — this publishes the form and generates a shareable link
2. Copy the form URL — you will need it to submit test leads later

#### Note Your Form ID

The Form ID appears in the Typeform URL:
```
https://admin.typeform.com/form/FORM_ID_HERE/create
```
Copy it — Make will ask for it when you configure the trigger.

---

### 3.3 Anthropic Claude API Setup

#### Create an Anthropic Account

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up and verify your email
3. Navigate to **API Keys** (left sidebar)
4. Click **Create Key**
5. Name it: `lead-scoring-automation`
6. Copy the key — it starts with `sk-ant-...`

> **Note:** You may need to add a payment method under **Billing** to use the API beyond the initial free credits. For demo and testing, free credits are sufficient.

#### Verify the Key (Optional)

```bash
curl https://api.anthropic.com/v1/messages \
  -H "content-type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-haiku-4-5-20251001","max_tokens":64,"messages":[{"role":"user","content":"Say OK"}]}'
```

Expected response includes `"content":[{"type":"text","text":"OK"}]`.

---

### 3.4 Airtable Setup

#### Create an Airtable Account

1. Go to [airtable.com](https://airtable.com) and click **Sign up for free**
2. Create a free account
3. You land on your **Home** workspace

#### Create the Base

1. Click **+ Add a base**
2. Select **Start from scratch**
3. Name it: `Lead Scoring CRM`
4. Click **Create base**

#### Build the Leads Table

Airtable opens with a default empty table. Rename it:

1. Double-click the tab at the bottom that says `Table 1`
2. Rename it to: `Leads`
3. Press Enter

Now add all fields from `airtable/schema.md`. For each field:

1. Click the **+** at the end of the column headers to add a new field
2. Set the field name and type as specified in the schema
3. For Single Select fields, add all allowed options (listed in `airtable/schema.md`)

> **Primary field:** Airtable's first column (primary field) defaults to type Single line text. Rename it to `Lead ID` — this will hold your generated `LEAD-XXXXXXXXXX` identifier.

> **Tip:** Use the dictionary below as a reference while updating field types manually. Set each field to the type shown.

```
{
  "Lead ID":             "Single line text (primary field)",
  "Name":                "Single line text",
  "Email":               "Email",
  "Company":             "Single line text",
  "Role":                "Single line text",
  "Company Size":        "Single line text",
  "Budget Range":        "Single line text",
  "Country":             "Single line text",
  "Territory":           "Single line text",
  "Primary Challenge":   "Long text",
  "ICP Score":           "Number",
  "Intent Score":        "Number",
  "Priority Tier":       "Single line text",
  "Recommended Action":  "Single line text",
  "AI Reasoning":        "Long text",
  "Assigned Rep":        "Single line text",
  "Status":              "Single select",
  "Submitted At":        "Single line text",
  "Created At":          "Created time"
}
```

> **Field types — avoid Single Select for AI-generated values:** `Company Size`, `Budget Range`, `Territory`, and `Priority Tier` are set to **Single line text** rather than Single Select. Airtable's API rejects values that don't exactly match a pre-configured option (`422 Insufficient permissions to create new select option`). Since these values come from freeform Typeform answers or AI output, Single line text is more robust. Only `Status` uses Single Select because it is always hardcoded to `New`.

#### Get Your Base ID

1. Open your base in the browser
2. The URL format is: `https://airtable.com/appXXXXXXXXXXXXXX/...`
3. Copy the `appXXXXXXXXXXXXXX` portion — this is your **Base ID**

#### Generate a Personal Access Token

1. Go to [airtable.com/create/tokens/new](https://airtable.com/create/tokens/new)
2. Click **Create new token**
3. Name: `make-lead-scoring`
4. Scopes: add the following three only
   - `data.records:read` — allows Make to search for existing records (deduplication)
   - `data.records:write` — allows Make to create records
   - `schema.bases:read` — allows Make to read the table structure
5. Access: select your `Lead Scoring CRM` base
6. Click **Create token**
7. Copy the token — it is shown only once

---

### 3.5 Slack Webhook Configuration

You need four Slack channels and one incoming webhook URL per channel.

#### Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App** → **From scratch**
3. App Name: `Lead Router`
4. Select your workspace → **Create App**

#### Enable Incoming Webhooks

1. In the app settings, click **Incoming Webhooks** (left sidebar)
2. Toggle **Activate Incoming Webhooks** to **On**

#### Create the Four Channels

In Slack, create these channels:

- `#sales-north-america`
- `#sales-europe`
- `#sales-asia`
- `#sales-general`

#### Territory Rep Display Names

The pipeline uses plain text rep names by default — no real Slack accounts are needed. The Slack message will show the assigned rep's name without pinging anyone:

- `Sarah Mitchell` — North America
- `James Hartley` — Europe
- `Priya Chen` — Asia
- `Manager` — General / Other

> **Upgrading to real @mentions:** Once you have real Slack users, get each person's member ID (Slack profile → three dots → **Copy member ID**, format: `U0123456789`). Replace each rep_handle value in Module 5 with `<@U0123456789>`. Slack renders this as a live @mention that notifies the person.

#### Add a Webhook for Each Channel

Repeat these steps four times — once per channel:

1. Click **Add New Webhook to Workspace**
2. Select the channel (e.g. `#sales-north-america`)
3. Click **Allow**
4. Copy the webhook URL (format: `https://hooks.slack.com/services/T.../B.../...`)

Save all four URLs — you will paste them directly into Make's HTTP modules in Section 3.7.

#### Test a Webhook

```bash
curl -X POST YOUR_SLACK_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"text": "Webhook test — lead router connected"}'
```

You should see the message appear in the corresponding Slack channel.

---

### 3.6 Gmail Connection

No API key is required. Make authenticates with Gmail via OAuth.

1. In Make, open the **Connections** panel (left sidebar → Connections)
2. Click **+ Create a connection**
3. Search for **Gmail**
4. Click **Continue** → Make opens a Google OAuth consent screen
5. Select the Google account you want to send emails from
6. Grant the requested permissions
7. Click **Save**

The connection is now stored and can be selected in any Gmail module in your scenario.

---

### 3.7 Building the Make.com Scenario

This section walks through adding each module to the canvas. Modules are added by clicking the **+** that appears on the right side of each existing module (or the centre **+** for the first module).

> **Make.com UI tip:** Click any module on the canvas to open its settings panel on the right. Save each module's settings before clicking away — Make does not auto-save in-progress module configurations.

---

#### Module 1 — Typeform Trigger

1. Click the centre **+** on the blank canvas
2. Search for `Typeform` in the module picker
3. Select **Watch Responses**
4. In the settings panel:
   - **Connection:** click **Add** → authenticate with your Typeform account via OAuth
   - **Form:** select `Lead Intake Form` from the dropdown (or paste the Form ID)
5. Click **OK**

> **How it works:** Make polls Typeform for new responses on your scenario's schedule. On the free tier, the minimum interval is 15 minutes. For testing, you can trigger the scenario manually using **Run once** (see Section 6).

---

#### Module 2 — Normalize Lead (Set Multiple Variables)

1. Click **+** to the right of Module 1
2. Search for `Tools` → select **Set Multiple Variables**
3. In the settings panel, click **Add item** for each variable below:

| Variable name | Value (Make expression) |
|---|---|
| `lead_id` | `LEAD-{{formatDate(now; "X")}}` |
| `lead_name` | *(map from the Typeform answer where field.ref = "name" — select from the dropdown that appears when you click the Value field)* |
| `lead_email` | *(map from Typeform answer, field.ref = "email")* |
| `company` | *(map from Typeform answer, field.ref = "company")* |
| `role` | *(map from Typeform answer, field.ref = "role")* |
| `company_size` | *(map from Typeform answer, field.ref = "company_size")* |
| `budget` | *(map from Typeform answer, field.ref = "budget")* |
| `challenge` | *(map from Typeform answer, field.ref = "challenge")* |
| `country` | *(map from Typeform answer, field.ref = "location" → expand `Address` → select `Country`)* |
| `submitted_at` | `{{1.submitted_at}}` |

> **Mapping Typeform fields:** When you click the Value field, Make shows a data tree from Module 1 (Typeform). Expand `Answers` → find the answer whose `Field > Reference` matches the ref you set in Typeform. Select the `Text` or `Email` or `Choice > Label` sub-field as appropriate. For the Address field (`location`), expand `Address` and select `Country` specifically — not the top-level answer text.

> See `scripts/mk_normalize_lead.js` for the complete field-by-field reference.

4. Click **OK**

---

#### Module 3 — Score Lead with Claude AI ("claude-haiku-4-5")

1. Click **+** to the right of Module 2
2. Search for `Anthropic` → select **Create a Message**
3. In the settings panel:
   - **Connection:** create a new connection → paste your Anthropic API key
   - **Model:** `claude-haiku-4-5-20251001`
   - **Max tokens:** `512`
   - **Message role:** `user`
   - **Message content:** paste the full prompt from `scripts/mk_score_lead.js`, replacing the placeholder variables with Make expressions from Module 2:

| Placeholder | Make expression |
|---|---|
| `{{2.lead_name}}` | select `lead_name` from Module 2 |
| `{{2.company}}` | select `company` from Module 2 |
| `{{2.country}}` | select `country` from Module 2 |
| `{{2.role}}` | select `role` from Module 2 |
| `{{2.company_size}}` | select `company_size` from Module 2 |
| `{{2.budget}}` | select `budget` from Module 2 |
| `{{2.challenge}}` | select `challenge` from Module 2 |

4. Click **OK**

> The native Anthropic module handles authentication and headers automatically — no HTTP configuration needed. The full prompt with scoring criteria is in `scripts/mk_score_lead.js`.

> **Critical prompt formatting rules:** The Claude prompt must include the following instructions to ensure clean JSON output. Without them, Claude will intermittently wrap the response in markdown code fences (` ```json ``` `), which breaks the downstream JSON Parse module:
> - `Do not use markdown. Do not wrap the response in code fences. Do not use ``` or ```json.`
> - `Your response must begin with { and end with }. Any characters outside the JSON object will cause a system failure.`
>
> These instructions should appear at the top of the prompt (before `LEAD DETAILS`) and again immediately before `Return ONLY this JSON`.

> **Territory classification in the prompt:** Claude classifies the territory as part of the same API call. Include a `Territory rules` section in the prompt and add `territory_label` to the JSON schema Claude returns. This eliminates the need for a hardcoded `switch()` expression and handles country abbreviations, codes, and spelling variations automatically. See the Scoring Schema in Section 4 for the full JSON structure.

---

#### Module 3b — Clean Claude Response (Set Variable)

Before parsing, Claude's raw output must be cleaned to strip any accidental markdown code fences. Despite the prompt instructions, models occasionally wrap output in ` ```json ``` ` blocks — this module removes them defensively.

1. Click **+** to the right of Module 3
2. Search for `Tools` → select **Set Variable**
3. In the settings panel:
   - **Variable name:** `claude_clean`
   - **Variable lifetime:** One cycle
   - **Variable value:**
     ```
     {{trim(replace(replace(3.result; "```json"; " "); "```"; " "))}}
     ```
4. Click **OK**

> **Why spaces instead of empty strings:** Make.com's formula normalizer strips empty string arguments (`""`) from `replace()` calls when exporting blueprints. Using a space character `" "` as the replacement avoids this, and `trim()` removes any leading/trailing whitespace left behind.

---

#### Module 4 — Parse Claude Response (JSON)

Claude returns its response as a text string. This module extracts it as a structured object.

1. Click **+** to the right of Module 3b
2. Search for `JSON` → select **Parse JSON**
3. In the settings panel:
   - **JSON string:** `{{3b.claude_clean}}` (reference the Set Variable module, not Module 3 directly)
4. Click **OK**

> After saving, Make will ask you to provide a sample JSON structure so it knows what fields to expect. Paste the following:

```json
{
  "icp_score": 8,
  "intent_score": 9,
  "priority_tier": "hot",
  "recommended_action": "Call within 2 hours",
  "reasoning": "VP-level decision maker at a 200-person company with a clear budget and urgent pain point.",
  "territory_label": "North America"
}
```

> Click **Save** — Make now exposes all six fields as individual mappable fields from Module 4 in all downstream modules.

> **Important:** `territory_label` must be added to the data structure manually. If it is missing from the data structure, Make will discard it from Claude's output even if Claude returns it correctly. In Make, go to **Data Structures** in the left sidebar → open the data structure linked to this module → add a `territory_label` field of type **Text**.

---

#### Module 5 — Build Routing Decision (Set Multiple Variables)

1. Click **+** to the right of Module 4
2. Search for `Tools` → select **Set Multiple Variables**
3. Add the following variables:

**territory_label** — read directly from Claude's parsed output (Module 4). No `switch()` needed:
```
{{4.territory_label}}
```

> Claude classifies the territory as part of the scoring call. This handles country codes (`US`, `UK`), abbreviations, and unlisted countries automatically. The possible values are: `North America`, `Europe`, `Asia`, `General`.

**rep_handle** — switch on `{{4.territory_label}}`:
```
{{switch(4.territory_label; "North America"; "Sarah Mitchell"; "Europe"; "James Hartley"; "Asia"; "Priya Chen"; "Manager")}}
```

**priority_label:**
```
{{switch(4.priority_tier; "hot"; "🔥 HOT"; "warm"; "🟡 WARM"; "🔵 COLD")}}
```

**slack_webhook_url** — paste your actual webhook URLs:
```
{{switch(4.territory_label; "North America"; "https://hooks.slack.com/services/YOUR_NA_WEBHOOK"; "Europe"; "https://hooks.slack.com/services/YOUR_EU_WEBHOOK"; "Asia"; "https://hooks.slack.com/services/YOUR_AP_WEBHOOK"; "https://hooks.slack.com/services/YOUR_GENERAL_WEBHOOK")}}
```

**slack_message:**
```
{{5.rep_handle}} — New lead assigned {{4.priority_tier}}

*{{2.company}}* | {{2.role}}
📍 {{2.country}} ({{4.territory_label}})
💰 Budget: {{2.budget}} | 👥 Size: {{2.company_size}}
💬 _"{{2.challenge}}"_

📊 ICP Score: {{4.icp_score}}/10 | Intent Score: {{4.intent_score}}/10
✅ {{4.recommended_action}}
```

4. Click **OK**

> See `scripts/mk_build_routing_decision.js` for the full territory map and routing logic reference.

---

#### Module 6 — Deduplicate (Airtable Search Records)

1. Click **+** to the right of Module 5
2. Search for `Airtable` → select **Search Records**
3. In the settings panel:
   - **Connection:** select your Airtable connection
   - **Base:** select `Lead Scoring CRM`
   - **Table:** select `Leads`
   - **Formula:** `{Email} = "{{2.lead_email}}"`
   - **Max Records:** `1`
4. Click **OK**

**Add a filter on Module 7 (Create Record):**

The deduplication filter goes on the Create Record module itself, not on the connector after Search Records.

1. Click Module 7 (Airtable Create Record) to open its settings
2. Click the **filter tab** at the top of the settings panel
3. Set the condition:
   - **Label:** `No duplicate`
   - **Condition A:** `{{6.Email}}`
   - **Operator:** `Does not exist`
4. Click **OK**

> **How it works:** If Airtable Search (Module 6) finds a record with the same email, `{{6.Email}}` will have a value and the filter blocks the create. If no record exists, `{{6.Email}}` is empty/undefined and the filter passes.

> **Common mistake:** Do not use `{{6.total}} Equal to 0` — `total` is not a reliable output field of the Search Records module. Do not use `{{6.Email}} Equal to "0"` — a real email address will never equal the string `"0"`, so this condition always blocks the create step.

---

#### Module 7 — Log to Airtable

1. Click **+** to the right of Module 6
2. Search for `Airtable` → select **Create a Record**
3. In the settings panel:
   - **Connection:** select your Airtable connection (or create one via OAuth)
   - **Base:** select `Lead Scoring CRM`
   - **Table:** select `Leads`
4. Map each field using the reference in `scripts/mk_log_to_airtable.js`:

| Airtable field | Make expression |
|---|---|
| Lead ID | `{{2.lead_id}}` |
| Name | `{{2.lead_name}}` |
| Email | `{{2.lead_email}}` |
| Company | `{{2.company}}` |
| Role | `{{2.role}}` |
| Company Size | `{{2.company_size}}` |
| Budget Range | `{{2.budget}}` |
| Country | `{{2.country}}` |
| Territory | `{{5.territory_label}}` |
| Primary Challenge | `{{2.challenge}}` |
| ICP Score | `{{4.icp_score}}` |
| Intent Score | `{{4.intent_score}}` |
| Priority Tier | `{{capitalize(4.priority_tier)}}` |
| Recommended Action | `{{4.recommended_action}}` |
| AI Reasoning | `{{4.reasoning}}` |
| Assigned Rep | `{{5.rep_handle}}` |
| Status | `New` |
| Submitted At | `{{2.submitted_at}}` |

5. Click **OK**

---

#### Module 8 — Gmail Auto-Reply

1. Click **+** to the right of Module 7
2. Search for `Gmail` → select **Send an Email**
3. In the settings panel:
   - **Connection:** select your Gmail connection
   - **To:** `{{2.lead_email}}`
   - **Subject:** `Thanks for reaching out, {{2.lead_name}} — we'll be in touch`
   - **Content:** select **HTML** and paste the raw HTML from `scripts/mk_send_reply_email.js` — the content must start with `<!DOCTYPE html>` and end with `</html>`. Do not wrap it in any JavaScript (no `const EMAIL_BODY = \`...\`.trim()` wrapper — Make expects raw HTML, not JS code)
   - **From name:** `Sales Team`
4. Click **OK**

---

#### Module 9 — Router (Territory Branching)

1. Click **+** to the right of Module 8
2. Search for `Flow control` → select **Router**
3. The Router splits the canvas into multiple paths — you will add one path per territory

**Add Path 1 — North America:**
1. Click the first path output of the Router → click **+** to add a module → search `Slack` → select **Send a Message**
2. In the settings panel:
   - **Connection:** create a new Slack connection and authenticate with your workspace
   - **Channel:** `#sales-north-america`
   - **Text:** `{{5.slack_message}}`
3. Click **OK**
4. Click the filter icon on the path connector → add a filter condition:
   - **Label:** `North America`
   - **Condition:** `{{5.territory_label}}` `Text operator: Equal to` `North America`

**Repeat for Paths 2–4** — same steps, different channel per path:

| Path | Filter value | Slack channel |
|---|---|---|
| 2 | `Europe` | `#sales-europe` |
| 3 | `Asia` | `#sales-asia` |
| 4 | *(no filter — fallback path)* | `#sales-general` |

> The fourth path (Other / General) has no filter — it catches any lead whose territory did not match paths 1–3. In Make, leave the filter blank on the last Router path to make it a fallback.

> All four Slack modules can share the same Slack connection — you only need to authenticate once.

---

#### Activate the Scenario

1. Click **Save** (bottom of the canvas, or Cmd/Ctrl + S)
2. Toggle the scenario from **OFF** to **ON** (bottom left of the canvas)
3. The scenario is now live and will poll Typeform on your selected interval

---

### 3.8 Connections & Credentials in Make

Make uses two separate systems for credentials — **Connections** for OAuth services, and **Custom Variables** for API keys and webhook URLs. Never hardcode credentials directly in module fields.

#### OAuth Connections (Typeform, Airtable, Gmail)

1. In Make, click **Connections** in the left sidebar
2. All OAuth connections are listed here
3. To reconnect an expired connection, click the three dots → **Reconnect**
4. OAuth connections are created inline when you configure the first module for each service — Make prompts you to authenticate at that point

#### Custom Variables (Anthropic API Key & Slack Webhooks)

Make does not have a native Anthropic connector, so the API key is passed as an HTTP header. To avoid pasting it directly in the module (which makes it visible to anyone who opens the scenario), store it as a Custom Variable:

1. In Make, click your **Team name** in the top left → **Team Settings**
2. Click **Variables** in the left sidebar
3. Click **+ Add variable** for each entry below:

| Variable name | Value | Used in |
|---|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Module 3 — HTTP header `x-api-key` |
| `SLACK_WEBHOOK_NA` | `https://hooks.slack.com/services/...` | Module 5 — `slack_webhook_url` switch() |
| `SLACK_WEBHOOK_EU` | `https://hooks.slack.com/services/...` | Module 5 — `slack_webhook_url` switch() |
| `SLACK_WEBHOOK_AP` | `https://hooks.slack.com/services/...` | Module 5 — `slack_webhook_url` switch() |
| `SLACK_WEBHOOK_GENERAL` | `https://hooks.slack.com/services/...` | Module 5 — `slack_webhook_url` switch() |

4. In module fields, reference variables using: `{{teamVariable.VARIABLE_NAME}}`
   - Example in Module 3's `x-api-key` header value field: `{{teamVariable.ANTHROPIC_API_KEY}}`
   - Example in Module 5's switch() for `slack_webhook_url`: replace the hardcoded webhook URLs with `{{teamVariable.SLACK_WEBHOOK_NA}}` etc.

> **Why this matters:** Anyone with edit access to your scenario can see hardcoded values in module fields. Variables stored in Team Settings are masked and not exposed in the scenario editor or execution logs.

#### Required Credentials Summary

| Service | Storage type | Where to get it |
|---|---|---|
| Anthropic API key | Make Custom Variable (`ANTHROPIC_API_KEY`) | console.anthropic.com → API Keys |
| Typeform | OAuth (Make Connection) | Authenticate when adding Module 1 |
| Airtable | OAuth (Make Connection) | Authenticate when adding Module 6 (Search Records) |
| Gmail | OAuth (Make Connection) | Authenticate in Section 3.6 |
| Slack webhooks (×4) | Make Custom Variables (`SLACK_WEBHOOK_*`) | api.slack.com → Your App → Incoming Webhooks |

---

### 3.9 Exporting the Scenario Blueprint

Make allows you to export your entire scenario as a JSON blueprint file. This is the fastest way to share a working scenario — a recipient imports it, reconfigures their connections and custom variables, and the scenario is ready without manually recreating every module.

#### Export the Blueprint

1. Open your scenario in the Make canvas
2. Click the **three dots menu** (top right of the canvas) → **Export Blueprint**
3. Make downloads a `.json` file (e.g. `lead-scoring-territory-routing.json`)
4. Add this file to your repository at: `config/make_blueprint.json`

#### Import a Blueprint

1. In Make, create a new blank scenario
2. Click the **three dots menu** → **Import Blueprint**
3. Upload the `.json` file
4. Make recreates all modules exactly — connections and custom variables still need to be reconfigured per account
5. Click each module that shows a connection warning → select your connection from the dropdown

> **For automation studios:** Include the exported blueprint in every client deliverable. It eliminates the manual build step and reduces onboarding time from hours to minutes. The blueprint + `prerequisites_checklist.md` + this guide is a complete handoff package.

---

### 3.10 Error Handling in Make

By default, if any module fails (e.g. Claude returns a 429 rate limit, Airtable is temporarily down), Make marks the entire scenario execution as failed and stops. For a production deployment, configure error handlers so the scenario degrades gracefully.

#### Adding an Error Handler to Module 3 (Claude API call)

Module 3 is the most likely failure point — Claude can return `429 Too Many Requests` under load or `500` on rare API outages.

1. Right-click Module 3 on the canvas → **Add error handler**
2. Make adds a red error path branching from the module
3. Choose **Resume** — this tells Make to continue executing downstream modules even if Module 3 failed
4. On the error path, add an HTTP module that posts a fallback alert to `#sales-general` Slack channel with the message: `"Lead scoring failed for {{2.lead_email}} — manual review required"`

> With Resume configured: if Claude fails, the lead is still logged to Airtable (Module 7) and the lead still receives their Gmail auto-reply (Module 8). Only the AI scores will be empty. This is far better than losing the lead entirely.

#### Adding an Error Handler to Module 7 (Airtable)

1. Right-click Module 7 → **Add error handler** → **Resume**
2. On the error path, add a Slack HTTP notification to `#sales-general`: `"Airtable log failed for {{2.lead_id}} — record not saved"`

#### Make's Error Handler Options

| Option | Behaviour | When to use |
|---|---|---|
| **Resume** | Continue scenario execution from the next module | Non-critical failures (logging, notifications) |
| **Commit** | Stop the current run but mark as successful | When partial completion is acceptable |
| **Rollback** | Stop and mark as failed (default behaviour) | When all-or-nothing is required |
| **Ignore** | Skip the failed module silently | Logging-only modules where failure is acceptable |

> For this pipeline: use **Resume** on Modules 3, 7, and 8. Use **Rollback** (default) on Module 2 — if field normalization fails, there is no recoverable lead to process.

---

## 4. Script Reference

| Script | Module | Purpose |
|---|---|---|
| `mk_normalize_lead.js` | Module 2 | Documents all Typeform field refs and Set Multiple Variables mappings |
| `mk_score_lead.js` | Module 3 | Full Claude prompt and HTTP request body configuration |
| `mk_build_routing_decision.js` | Module 5 | Territory map, rep config, Make switch() expressions, Slack message template |
| `mk_log_to_airtable.js` | Module 7 | Airtable field-to-Make-expression mapping reference |
| `mk_send_reply_email.js` | Module 8 | Gmail HTML auto-reply template |

### Scoring Schema (mk_score_lead.js)

Claude is prompted to return exactly this JSON structure:

```json
{
  "icp_score": 8,
  "intent_score": 9,
  "priority_tier": "hot",
  "recommended_action": "Call within 2 hours",
  "reasoning": "VP-level role at a 200-person company with an urgent, specific pain point and $20k+ budget.",
  "territory_label": "North America"
}
```

### Priority Tier Rules

| Priority | ICP Score | Intent Score | Action |
|---|---|---|---|
| hot | >= 7 | >= 7 | Call within 2 hours |
| warm | >= 5 | >= 5 | Follow-up within 24 hours |
| cold | < 5 (either) | < 5 (either) | Add to nurture sequence |

### Territory Routing Table

| Territory | Countries | Channel | Rep |
|---|---|---|---|
| North America | US, Canada, Mexico | `#sales-north-america` | Sarah Mitchell |
| Europe | UK, Germany, France, Spain, Italy, NL, SE, NO, DK, CH, BE, AT, PT, PL, IE, FI | `#sales-europe` | James Hartley |
| Asia | India, Japan, China, Singapore, South Korea, Australia, NZ, Indonesia, Malaysia, Thailand, Philippines, Vietnam, HK, Taiwan | `#sales-asia` | Priya Chen |
| Other | Everything else | `#sales-general` | Manager |

---

## 5. Airtable Reference

Full field definitions are in `airtable/schema.md`.

### Key Fields

| Field | Type | Source |
|---|---|---|
| Lead ID | Single line text (primary) | Generated by Module 2 |
| Priority Tier | Single select | Claude AI ("claude-haiku-4-5") — capitalised via `capitalize()` |
| Territory | Single select | Make switch() expression in Module 5 |
| AI Reasoning | Long text | Claude's full reasoning text |
| Status | Single select | Always set to `New` on creation — update manually as lead progresses |

### Useful Airtable Views to Create

**Hot Leads view:**
- Filter: Priority Tier = Hot
- Sort: Created At descending

**By Territory view:**
- Group by: Territory
- Sort: ICP Score descending

---

## 6. Testing Procedures

### 6.1 Running the Scenario Manually

On the free tier, the Typeform trigger polls every 15 minutes. To test immediately:

1. Submit your Typeform with test data (see samples below)
2. In Make, open the scenario canvas
3. Click **Run once** (bottom left)
4. Make executes the scenario once using the most recent unprocessed Typeform response
5. Each module shows a green tick (success) or red X (error) after running
6. Click any module to inspect its input and output data

### 6.2 Sample Test Submissions

Submit these via your published Typeform URL to generate known test cases.

**Test Lead 1 — Hot lead, North America**

| Field | Value |
|---|---|
| Name | Alex Johnson |
| Email | alex.johnson@acmecorp.com |
| Company | Acme Corp |
| Role | VP of Operations |
| Company Size | 201–1,000 |
| Budget | $20k–$50k |
| Challenge | We are manually tracking 500 vendor invoices in spreadsheets. We need automation urgently before Q2. |
| Country | United States |

*Expected output: ICP Score 8–9, Intent Score 9–10, Priority Tier = Hot, Territory = North America, routed to Sarah Mitchell*

---

**Test Lead 2 — Warm lead, Europe**

| Field | Value |
|---|---|
| Name | Sophie Müller |
| Email | sophie.muller@techgmbh.de |
| Company | Tech GmbH |
| Role | Operations Manager |
| Company Size | 51–200 |
| Budget | $5k–$20k |
| Challenge | We are looking into automating our customer onboarding process at some point this year. |
| Country | Germany |

*Expected output: ICP Score 6–7, Intent Score 5–6, Priority Tier = Warm, Territory = Europe, routed to James Hartley*

---

**Test Lead 3 — Cold lead, Asia**

| Field | Value |
|---|---|
| Name | Rahul Sharma |
| Email | rahul@startup.in |
| Company | Startup.in |
| Role | Intern |
| Company Size | 1–10 |
| Budget | Under $1k |
| Challenge | Just curious about what automation can do. |
| Country | India |

*Expected output: ICP Score 2–3, Intent Score 2–3, Priority Tier = Cold, Territory = Asia, routed to Priya Chen*

---

### 6.3 Verification Checklist

After each test run, verify all outputs:

- [ ] **Module 1 (Typeform)** — trigger fired and response data is visible in module output
- [ ] **Module 2 (Normalize)** — all 10 variables populated (no empty values)
- [ ] **Module 3 (Claude)** — response visible in module output, raw text begins with `{` and ends with `}`
- [ ] **Module 3b (Set Variable)** — `claude_clean` variable populated, no code fences present
- [ ] **Module 4 (JSON Parse)** — all 6 fields extracted: `icp_score`, `intent_score`, `priority_tier`, `recommended_action`, `reasoning`, `territory_label`
- [ ] **Module 5 (Routing)** — `territory_label`, `rep_handle`, `priority_label`, `slack_message` all populated
- [ ] **Module 6 (Dedup)** — search returns `0` results for the test email, filter passes
- [ ] **Module 7 (Airtable)** — new record appears in your Leads table with all fields filled
- [ ] **Module 8 (Gmail)** — auto-reply arrives in the test email inbox
- [ ] **Module 9 (Router + Slack)** — message appears in the correct territory Slack channel with @rep mention

### 6.4 Verify the Airtable Record

Open your `Lead Scoring CRM` base and check the new row:
- `Lead ID` is in format `LEAD-XXXXXXXXXX`
- `Priority Tier` is `Hot`, `Warm`, or `Cold` (capitalised)
- `AI Reasoning` contains a readable sentence from Claude
- `Territory` matches the submitted country
- `Status` is `New`

---

## 7. Troubleshooting & Lessons Learned

> This section is updated as issues are discovered during the build. See `BUILD_LOG.md` for the full issue history.

### Module 3 Returns Status 400 (Bad Request)

**Symptom:** The HTTP module shows status `400` and an error from the Anthropic API.

**Likely cause:** The request body JSON is malformed — most often caused by unescaped newlines or quotes inside the `content` string when building the prompt in Make's interface.

**Fix:** Ensure the prompt string uses `\n` for line breaks rather than actual newlines inside the JSON body. Test the raw JSON in a tool like Postman before pasting into Make.

---

### Module 4 (JSON Parse) Fails or Returns Empty Fields

**Symptom:** The JSON Parse module errors, or downstream modules show empty values for `icp_score` etc.

**Likely cause:** Claude wrapped the JSON in markdown code fences (` ```json ... ``` `) despite the prompt instruction. This happens intermittently, especially with Haiku.

**Fix:** Add a Set Variable module (Module 3b) between the Claude module and ParseJSON to strip code fences:
```
{{trim(replace(replace(3.result; "```json"; " "); "```"; " "))}}
```
Use a space `" "` as the replacement — not an empty string. Make's formula normalizer strips empty string arguments from `replace()` on blueprint export, breaking the formula at runtime.

Also strengthen the prompt with explicit instructions:
- `Do not use markdown. Do not wrap the response in code fences. Do not use ``` or ```json.`
- `Your response must begin with { and end with }. Any characters outside the JSON object will cause a system failure.`

---

### territory_label Always Returns "General" (Wrong Territory)

**Symptom:** All leads are assigned territory `General` regardless of country, or a US lead is classified as `General` instead of `North America`.

**Likely cause:** The country field in the Claude prompt is mapped to the wrong Typeform answer UUID. The country UUID used in Module 3's prompt must match the UUID used in Module 2's `country` variable — they are different Typeform fields and the UUIDs are not interchangeable.

**Fix:** In Module 3's prompt, replace the hardcoded country UUID with `{{2.country}}` (referencing Module 2's normalized variable). This guarantees the same field is used consistently throughout the pipeline. Verify by checking Module 2's execution output to confirm `country` is populated with the expected value.

---

### Airtable Returns 422 — Insufficient Permissions to Create Select Option

**Symptom:** Module 7 (Airtable Create Record) fails with error `[422] Insufficient permissions to create new select option`.

**Cause:** A field configured as Single Select in Airtable is receiving a value that does not match any of its pre-configured options. This commonly affects `Company Size`, `Budget Range`, `Territory`, and `Priority Tier` when values come from freeform Typeform answers or AI output.

**Fix:** Change the affected Airtable fields from **Single Select** to **Single line text**. Field IDs are preserved when changing types — no changes needed in Make. See the field schema in Section 3.4 for the recommended types.

---

### Deduplication Filter Blocks All Records (Nothing Written to Airtable)

**Symptom:** Module 7 (Airtable Create Record) never runs — no records appear in Airtable despite the scenario executing successfully.

**Cause:** The filter condition on the Create Record module is incorrectly configured. Common mistakes:
- `{{6.Email}} text:equal "0"` — a real email address never equals the string `"0"`, so this always blocks
- `{{6.total}} equal 0` — `total` is not a reliable output of the Search Records module

**Fix:** Set the filter condition to `{{6.Email}}` → **Does not exist**. This passes when the search found no matching record (Email is undefined) and blocks when a duplicate was found (Email has a value).

---

### Typeform Answers Not Mapping (Empty Variables in Module 2)

**Symptom:** Module 2 sets variables but they are all empty or showing `undefined`.

**Likely cause:** The Typeform question `Reference` values do not match what Module 2 expects. Make identifies answers by `field.ref` — if the reference was not set in Typeform, or was set with a typo, the answer cannot be found.

**Fix:** In Typeform form builder, open each question → scroll to the bottom of the settings panel → verify the Reference field exactly matches the values in Section 3.2 (`name`, `email`, `company`, etc.). Re-publish the form after making changes.

---

### Router Path Not Triggering

**Symptom:** The Router runs but none of the Slack HTTP modules execute.

**Likely cause:** The filter condition on the Router path does not match the value of `{{5.territory_label}}`. This is usually a spacing or capitalisation mismatch.

**Fix:** In the Router path filter, ensure the comparison value matches exactly (e.g. `Asia` not `Asia Pacific` or `asia-pacific`). Check Module 5's output in the run log to see the exact string being produced.

---

### Slack Returns 404

**Symptom:** The Slack HTTP module returns status `404`.

**Cause:** The webhook URL is invalid, expired, or belongs to a deleted channel.

**Fix:** Regenerate the webhook URL in the Slack App settings (api.slack.com → Your App → Incoming Webhooks) and update the URL in Module 5's `slack_webhook_url` switch() expression.

---

### Gmail Auto-Reply Goes to Spam

**Symptom:** Module 8 shows success but the lead does not receive the email.

**Cause:** The receiving mail server flagged the email. Gmail-to-Gmail messages sent via OAuth rarely have this issue, but it can happen with strict spam filters.

**Fix:** Check the spam/junk folder — the email will typically be there. For production use, send from a custom domain Gmail account (Google Workspace) rather than a free `@gmail.com` address.

---

### Airtable Field Type Mismatch

**Symptom:** Module 7 (Airtable) errors with `INVALID_VALUE_FOR_COLUMN`.

**Likely cause:** A Single Select field is receiving a value that does not match one of its configured options. Common for `Priority Tier` (receiving `hot` instead of `Hot`) or `Territory` (receiving `Asia Pacific` instead of `Asia`).

**Fix:** Ensure `capitalize()` is wrapping `4.priority_tier` in the Airtable module mapping. For Territory, confirm the `switch()` expression in Module 5 uses exact spelling (`Asia` with a hyphen) and that the Airtable Single Select options use the same spelling.

---

## 8. Cost Analysis

### Development / Testing

| Resource | Cost |
|---|---|
| Make.com | Free (free tier: 1,000 ops/month) |
| Typeform | Free (free tier: 10 responses/month on basic) |
| Anthropic Claude API | ~$0.0001 per lead (~500 tokens/call at haiku-4-5 pricing) |
| Airtable | Free (free tier: 1,000 records/base) |
| Slack Incoming Webhooks | Free |
| Gmail | Free |
| **Total (development)** | **~$0/month** |

### Production Estimate (~500 leads/month)

| Resource | Usage | Cost |
|---|---|---|
| Make.com | ~4,500 ops (9 ops/run × 500 runs) | ~$10.59/month (Core plan) |
| Typeform | 500 responses | ~$25/month (Core plan) |
| Anthropic `claude-haiku-4-5` | ~250K tokens input + 50K output | ~$0.50/month |
| Airtable | 500 records | Free (within free tier) |
| Slack | Unlimited webhooks | Free |
| Gmail | 500 emails | Free |
| **Total (production, 500 leads/month)** | | **~$36/month** |

> **Make.com operations note:** Each module execution = 1 operation. A single scenario run uses modules 1–7 plus 1 active Router path = **9 operations per run**. At 500 leads/month = 4,500 ops total. The free tier (1,000 ops/month) covers approximately 110 leads/month. Beyond that, the Core plan (~$10.59/month, 10,000 ops) covers up to ~1,100 leads/month comfortably. The Core plan is also required to reduce the polling interval below 15 minutes.

---

## 9. Customizing for Your Use Case

This section consolidates every touch point that changes when adapting the pipeline — territories, scoring logic, routing, form fields, and swap-out options for each tool layer.

### 9.1 Changing the Territory Map

The country → territory mapping lives in **Module 5** (`territory_label` variable). The fallback label `Other` is the default case of the same `switch()`. To add or remove territories:

1. Open Module 5 → `territory_label` value field
2. Add or remove country entries in the `switch()` expression
3. Update `rep_handle` in the same module to add/remove rep names (or `<@MEMBER_ID>` for real mentions)
4. Update `slack_webhook_url` to add/remove webhook URLs (or update Custom Variables)
5. Add or remove Router paths in Module 9 and update the filter conditions to match

> **All five touch points must stay in sync.** A country in the territory map with no corresponding Router path will fall through to the fallback channel. A Router path with no matching territory label will never activate.

### 9.2 Changing the Scoring Criteria

The scoring criteria live in the Claude prompt inside **Module 3**. To adjust how Claude weights signals (e.g. prioritise budget over company size, or add a new field):

1. Open Module 3 → **Request content** field
2. Edit the prompt — specifically the instructions after `LEAD DETAILS:`
3. Example: `"Weight budget range heavily — a budget of $20k+ should push ICP score above 7 regardless of company size."`
4. Re-test with the sample leads in Section 6.2 to verify the updated scoring behaviour

The full prompt template is in `scripts/mk_score_lead.js`.

### 9.3 Changing the Routing Assignments

Rep assignments are set in **Module 5** (`rep_handle` variable). By default these are plain text names. To change who is assigned per territory (or upgrade to real @mentions):

1. Open Module 5 → `rep_handle` value field
2. Update the `switch()` expression with new `@handle` values
3. Verify each handle exists in the Slack workspace before activating

> **Slack @mention handles are case-sensitive and must match the member's display name exactly.** If a handle doesn't resolve, the message still sends — the mention just appears as plain text.

### 9.4 Adding or Changing Form Fields

To add new intake fields or change existing ones:

1. Add or update questions in Typeform and set a `Reference` on each new field
2. In Module 2, add a new variable for each field, mapped to the Typeform `field.ref`
3. Update the Claude prompt in Module 3 to include the new field under `LEAD DETAILS:`
4. Add the new field to the Airtable schema and to the Module 7 field mapping
5. Update the Gmail template in Module 8 if the field should appear in the auto-reply

### 9.5 Swapping the Intake Source

The pipeline is not Typeform-specific. The Module 1 trigger can be replaced with:

| Intake source | Make trigger module |
|---|---|
| Webflow form | Webhooks → Custom Webhook |
| HubSpot form | HubSpot → Watch Form Submissions |
| Gravity Forms (WordPress) | Webhooks → Custom Webhook |
| Tally | Webhooks → Custom Webhook |
| Any API / Zapier → Make | Webhooks → Custom Webhook |

When switching to a webhook trigger, Module 2's mapping changes — you map from `{{1.body.field_name}}` rather than Typeform's answer structure. Everything from Module 3 onwards is unchanged.

### 9.6 Swapping the Storage Layer

To replace Airtable with a different storage target, swap out Modules 6 and 7:

| Storage target | Make module |
|---|---|
| HubSpot | HubSpot → Create a Contact |
| Pipedrive | Pipedrive → Create a Person / Deal |
| Salesforce | Salesforce → Create a Record |
| Notion | Notion → Create a Database Item |
| PostgreSQL | HTTP → POST to a custom endpoint, or use a Pipedream step |

The field mapping logic from `scripts/mk_log_to_airtable.js` translates directly — only the module type and destination field names change.

### 9.7 Adaptation Checklist

When reconfiguring the pipeline for a new use case:

- [ ] Update territory map in Module 5 (`territory_label` switch)
- [ ] Update routing assignments in Module 5 (`rep_handle` switch)
- [ ] Update webhook URLs in Make Custom Variables
- [ ] Update Router paths in Module 9 (one path per territory)
- [ ] Update Claude prompt in Module 3 for updated scoring criteria
- [ ] Update Typeform questions and References
- [ ] Update Airtable schema for any new fields
- [ ] Update Module 2 variable mapping for new fields
- [ ] Update Module 7 field mapping for new fields
- [ ] Update Module 8 email template as needed
- [ ] Export and save updated scenario blueprint (`config/make_blueprint.json`)

