# Support Ticket Automation - High-Level Architecture

```mermaid
flowchart TB
    subgraph Intake["Ticket Intake"]
        WH["🎫 HTTP Webhook<br/>Pipedream Trigger"]
    end

    subgraph Orchestration["Orchestration (Pipedream Cloud)"]
        PD["⚙️ Pipedream Workflow<br/>5-Step Pipeline"]
    end

    subgraph AI["AI Classification"]
        CL["🤖 Claude API<br/>Category + Urgency + Sentiment"]
    end

    subgraph Storage["Storage"]
        PG[("🐘 PostgreSQL<br/>tickets table")]
    end

    subgraph Routing["Routing & Notifications"]
        SL1["💬 #support-billing"]
        SL2["💬 #support-technical"]
        SL3["💬 #support-shipping"]
        SL4["💬 #support-general"]
        EM["📧 Auto-Reply Email<br/>SendGrid"]
    end

    WH -->|"POST payload"| PD
    PD <-->|"classify"| CL
    PD -->|"log ticket"| PG
    PD -->|"billing"| SL1
    PD -->|"technical"| SL2
    PD -->|"shipping"| SL3
    PD -->|"general"| SL4
    PD -->|"acknowledgement"| EM

    classDef intake   fill:#00C4B4,stroke:#009688,color:white
    classDef orch     fill:#FF6D00,stroke:#E65100,color:white
    classDef ai       fill:#7B61FF,stroke:#5A45CC,color:white
    classDef store    fill:#336791,stroke:#1A3A5C,color:white
    classDef notify   fill:#E53E3E,stroke:#C53030,color:white

    class WH intake
    class PD orch
    class CL ai
    class PG store
    class SL1,SL2,SL3,SL4,EM notify
```

## Data Flow Summary

```
HTTP Webhook (ticket payload)
    |
    v
Pipedream Step 1 — Normalize raw payload → structured ticket object
    |
    v
Pipedream Step 2 — Claude API → category, urgency, sentiment, reasoning
    |
    v
Pipedream Step 3 — Build routing decision → channel, SLA hours, reply content
    |
    +---> PostgreSQL  (audit log)
    +---> Slack       (team notification, routed by category)
    +---> SendGrid    (auto-reply to submitter)
```

## Key Design Principles

1. **Stateless steps** — Each Pipedream step receives data from the previous step via `steps.<step_name>.$return_value`. No shared state, no file system access.

2. **Single AI call** — Classification, urgency, and sentiment are all extracted in one Claude API call using a structured JSON output prompt. Minimizes latency and API cost.

3. **Category-driven routing** — The routing decision step maps the AI category to a Slack webhook URL and an SLA target. Adding a new category only requires updating a single lookup dict.

4. **Parallel dispatch** — PostgreSQL log, Slack post, and email reply are independent Pipedream steps that can run in parallel (async step group), keeping end-to-end time under 5 seconds.

5. **Full audit trail** — `ai_reasoning` is stored per ticket so teams can audit why a ticket was classified a certain way without re-calling the API.
```
