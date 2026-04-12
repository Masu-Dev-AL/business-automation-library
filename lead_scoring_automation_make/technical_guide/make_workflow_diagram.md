# Make.com Scenario Diagram — Lead Scoring & Territory Routing

```mermaid
flowchart LR
    subgraph TRIGGER ["Trigger"]
        M1["📥 1 · Typeform\nWatch Responses"]
    end

    subgraph PROCESS ["Process"]
        M2["🔧 2 · Tools\nSet Multiple Variables\n─────────────────\nlead_id · lead_name · lead_email\ncompany · role · company_size\nbudget · challenge · country\nsubmitted_at"]

        M3["🌐 3 · HTTP\nMake a Request\n─────────────────\nPOST api.anthropic.com\n/v1/messages\nModel: claude-haiku-4-5"]

        M4["🔍 4 · JSON\nParse JSON\n─────────────────\nicp_score · intent_score\npriority_tier\nrecommended_action\nreasoning"]

        M5["🗺️ 5 · Tools\nSet Multiple Variables\n─────────────────\nterritory_label · rep_name\nrep_handle · priority_label\nslack_webhook_url\nslack_message"]
    end

    subgraph OUTPUT ["Unconditional Output"]
        M6["📊 6 · Airtable\nCreate a Record\n─────────────────\nLeads table"]

        M7["📬 7 · Gmail\nSend an Email\n─────────────────\nTo: lead_email\nHTML auto-reply"]
    end

    subgraph ROUTER ["Territory Router"]
        M8["🔀 8 · Flow Control\nRouter"]
        M8A["💬 8a · HTTP\nPost to Slack\n#sales-north-america\n@sarah.mitchell"]
        M8B["💬 8b · HTTP\nPost to Slack\n#sales-europe\n@james.hartley"]
        M8C["💬 8c · HTTP\nPost to Slack\n#sales-asia\n@priya.chen"]
        M8D["💬 8d · HTTP\nPost to Slack\n#sales-general\n@manager"]
    end

    M1 --> M2
    M2 --> M3
    M3 --> M4
    M4 --> M5
    M5 --> M6
    M5 --> M7
    M5 --> M8
    M8 -->|"territory = NA"| M8A
    M8 -->|"territory = EU"| M8B
    M8 -->|"territory = AP"| M8C
    M8 -->|"fallback"| M8D

    classDef trigger  fill:#f59e0b,stroke:#d97706,color:#000
    classDef process  fill:#6366f1,stroke:#4338ca,color:#fff
    classDef router   fill:#ec4899,stroke:#be185d,color:#fff
    classDef slack    fill:#4a154b,stroke:#3b0f3c,color:#fff
    classDef airtable fill:#3b82f6,stroke:#2563eb,color:#fff
    classDef gmail    fill:#10b981,stroke:#059669,color:#fff

    class M1 trigger
    class M2,M3,M4,M5 process
    class M8 router
    class M8A,M8B,M8C,M8D slack
    class M6 airtable
    class M7 gmail
```

## Module Reference

| # | Module | App | Purpose |
|---|--------|-----|---------|
| 1 | Watch Responses | Typeform | Triggers scenario on new form submission |
| 2 | Set Multiple Variables | Tools | Normalises Typeform fields into clean named variables |
| 3 | Make a Request | HTTP | Calls Claude AI ("claude-haiku-4-5") to score the lead |
| 4 | Parse JSON | JSON | Extracts scores and reasoning from Claude's response text |
| 5 | Set Multiple Variables | Tools | Determines territory, rep, and builds Slack message |
| 6 | Create a Record | Airtable | Logs full lead record + AI output to CRM (unconditional) |
| 7 | Send an Email | Gmail | Sends personalised HTML auto-reply to the lead (unconditional) |
| 8 | Router | Flow Control | Splits execution into territory-filtered paths |
| 8a–d | Make a Request | HTTP | Posts Slack message to the correct territory channel |

> **Why Airtable and Gmail come before the Router:** Design principle — every lead is logged and acknowledged regardless of territory. Modules 6 and 7 run unconditionally on every execution. Module 8 (Router) handles only the Slack notification, which is territory-specific.
