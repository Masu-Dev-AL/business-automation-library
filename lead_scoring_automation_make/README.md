# AI Lead Scoring & Territory Routing

An automated lead scoring and routing system built with Make.com and Claude AI ("claude-haiku-4-5") that scores incoming leads from Typeform, assigns them to territory reps via Slack, logs everything to Airtable, and sends a personalised Gmail auto-reply.

## Overview

This project demonstrates how to build an AI-powered lead qualification pipeline using:
- **Make.com** - Visual workflow orchestration (native Typeform, Airtable, Gmail connectors)
- **Typeform** - Lead intake form with structured fields
- **Claude API (Anthropic)** - AI scoring of ICP fit, intent, and lead priority
- **Airtable** - Lead CRM database and audit trail
- **Slack Webhooks** - Territory-based channel routing with rep @mentions
- **Gmail** - Personalised auto-reply to every lead

## Architecture

```
Typeform Submission → Make.com Workflow → Claude AI ("claude-haiku-4-5") → Territory Decision
                                                             ↓
                                          ┌──────────────────┤
                                          ↓         ↓        ↓
                                       Airtable  Slack     Gmail
                                       (CRM log) (@rep)   (auto-reply)
```

## Features

- Typeform-native trigger (no manual webhook config)
- AI scoring: ICP fit (1–10), intent (1–10), priority tier (hot / warm / cold)
- Territory routing — North America, Europe, Asia-Pacific, Other
- Slack channel routing with @rep mention per territory
- Airtable CRM record with full AI reasoning stored per lead
- Personalised Gmail auto-reply to every lead

## Project Structure

```
├── scripts/
│   ├── mk_normalize_lead.js             # Step 2: field mapping reference
│   ├── mk_score_lead.js                 # Step 3: Claude API HTTP request config + prompt
│   ├── mk_build_routing_decision.js     # Step 4: territory routing + Slack message builder
│   ├── mk_log_to_airtable.js            # Step 5: Airtable field mapping reference
│   └── mk_send_reply_email.js           # Step 6: Gmail HTML auto-reply template
├── airtable/
│   └── schema.md                        # Airtable base and field definitions
├── config/
│   └── .env.example                     # Environment variable template
└── technical_guide/
    ├── lead_scoring_technical_guide.md
    ├── architecture.md
    └── make_workflow_diagram.md
```

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Masu-Dev-AL/business-automation-library.git
   cd business-automation-library/lead_scoring_automation_make
   ```

2. **Set up Airtable**
   - Create a new base using the schema in `airtable/schema.md`
   - Generate a Personal Access Token in Airtable account settings

3. **Set up Typeform**
   - Create a new form with the fields defined in the technical guide
   - Note your Form ID from the URL

4. **Set up Slack**
   - Create channels: `#sales-north-america`, `#sales-europe`, `#sales-asia`, `#sales-general`
   - Create incoming webhook URLs for each channel (Slack App settings)
   - Create fake rep accounts: @sarah.mitchell, @james.hartley, @priya.chen, @manager

5. **Configure Make.com**
   - Sign up at [make.com](https://make.com) (free — 1,000 ops/month)
   - Create a new scenario with a Typeform trigger
   - Add modules following the technical guide
   - Store credentials via Make's Connections panel

6. **Connect Gmail**
   - In Make, add a Gmail module and authenticate via OAuth (no API key needed)

## Technologies

- **Orchestration:** Make.com (free tier — 1,000 ops/month)
- **Lead intake:** Typeform (free tier)
- **AI:** Anthropic Claude API (claude-haiku-4-5 for cost efficiency)
- **CRM:** Airtable (free tier — 1,000 records/base)
- **Notifications:** Slack Webhooks
- **Email:** Gmail via Make native connector (OAuth)

## Cost

- Development: Free (Make free tier + Anthropic free credits + Airtable free tier)
- Production (~500 leads/month): ~$1–3/month (Claude API only)

## License

This project is provided for educational purposes.

---

*Part of the Business Automation Library — Code examples for building real-world automation solutions.*
