# AI Support Ticket Classifier & Router

An automated support ticket classification and routing system built with Pipedream and Claude AI that categorizes incoming tickets, scores urgency, and routes them to the right Slack channel — with an auto-reply sent to the submitter.

## Overview

This project demonstrates how to build an AI-powered support automation pipeline using:
- **Pipedream** - Cloud-native workflow orchestration (webhook trigger, step chaining, parallel dispatch)
- **Claude API (Anthropic)** - AI classification of ticket category, urgency, and sentiment
- **PostgreSQL** - Ticket log and audit trail
- **Slack Webhooks** - Channel-based routing (billing, technical, shipping, general)
- **SendGrid** - Automated acknowledgement emails to submitters

## Architecture

```
HTTP Webhook → Pipedream Workflow → Claude AI → Route Decision
                                                      ↓
                              ┌───────────────────────┤
                              ↓           ↓            ↓
                         PostgreSQL   Slack Channel  Auto-Reply Email
```

## Features

- Webhook-based ticket intake (compatible with any form tool or frontend)
- AI classification: category (billing / technical / shipping / general), urgency (critical / high / medium / low), sentiment
- Dynamic Slack routing — each category posts to its own support channel
- Automated submitter acknowledgement with ticket ID and expected response time
- Full audit log in PostgreSQL with AI reasoning stored per ticket

## Project Structure

```
├── scripts/
│   ├── pd_normalize_ticket.py          # Step 2: normalize raw webhook payload
│   ├── pd_classify_ticket.py           # Step 3: Claude API classification prompt
│   ├── pd_build_routing_decision.py    # Step 4: map classification → channel + SLA
│   └── pd_build_reply_email.py         # Step 5: build HTML auto-reply email
├── sql/
│   └── schema.sql                      # tickets table DDL
├── config/
│   └── .env.example                    # Environment variable template
├── sample_tickets/
│   └── sample_payloads.json            # Test webhook payloads
└── technical_guide/
    ├── support_ticket_technical_guide.md
    ├── architecture.md
    └── pipedream_workflow_diagram.md
```

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Masu-Dev-AL/business-automation-library.git
   cd business-automation-library/support_ticket_automation_pipedream
   ```

2. **Set up PostgreSQL**
   ```bash
   psql -U postgres -c "CREATE DATABASE support_tickets;"
   psql -U postgres -d support_tickets -f sql/schema.sql
   ```

3. **Configure environment**
   ```bash
   cp config/.env.example config/.env
   # Edit .env with your API keys and DB credentials
   ```

4. **Create the Pipedream workflow**
   - Sign up at [pipedream.com](https://pipedream.com) (free)
   - Create a new workflow with an HTTP trigger
   - Add steps following the technical guide
   - Set environment variables in Pipedream project settings

5. **Test with sample payloads**
   ```bash
   curl -X POST <your-pipedream-webhook-url> \
     -H "Content-Type: application/json" \
     -d @sample_tickets/sample_payloads.json
   ```

## Documentation

See the [Technical Guide](technical_guide/support_ticket_technical_guide.md) for complete step-by-step implementation including:
- Pipedream account and workflow setup
- Claude API integration and prompt design
- PostgreSQL schema and connection
- Slack webhook configuration (per channel)
- SendGrid email setup
- Testing procedures

## Technologies

- **Orchestration:** Pipedream (cloud-hosted, no infrastructure required)
- **AI:** Anthropic Claude API (claude-haiku-4-5 for cost efficiency)
- **Database:** PostgreSQL
- **Notifications:** Slack Webhooks, SendGrid
- **Language:** Python 3.x (Pipedream code steps)

## Cost

- Development: Free (Pipedream free tier + Anthropic free credits)
- Production (1,000 tickets/month): ~$2-5/month (Claude API + SendGrid free tier)

## License

This project is provided for educational purposes.

---

*Part of the Business Automation Library - Code examples for building real-world automation solutions.*
