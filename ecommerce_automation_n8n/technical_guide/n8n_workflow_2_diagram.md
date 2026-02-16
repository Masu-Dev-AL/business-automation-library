# n8n Workflow 2: Real-Time Inventory Alerts (Webhook-Triggered)

```mermaid
flowchart LR
    subgraph Trigger["1. Webhook"]
        WH["🔔 Webhook<br/>woo-order-created"]
    end

    subgraph Process["2. Extract Order"]
        PO["🐍 Process<br/>Webhook Order"]
    end

    subgraph StockCheck["3. Stock Lookup"]
        CS[("🐘 Check Stock<br/>vw_current_inventory")]
        ES["🐍 Evaluate<br/>Stock Alerts"]
    end

    subgraph Decision["4. Alert Gate"]
        IF{"IF<br/>alert_count > 0"}
    end

    subgraph AlertPipeline["5. Log & Notify"]
        IA[("🐘 Insert Alerts<br/>inventory_alerts")]
        BA["🐍 Build Alert<br/>Message"]
        EM["📧 Send Email<br/>SMTP"]
        SL["💬 Send Slack<br/>Webhook"]
        WA["📱 Send WhatsApp<br/>Business API"]
    end

    subgraph NoAlert["6. No Action"]
        X["✋ Stop"]
    end

    %% Flow
    WH --> PO
    PO --> CS
    CS --> ES
    ES --> IF
    IF -->|"true"| IA
    IF -->|"true"| BA
    IF -.->|"false"| X
    BA --> EM
    BA --> SL
    BA --> WA

    %% Styling
    classDef trigger fill:#00C4B4,stroke:#009688,color:white
    classDef python fill:#FF6D00,stroke:#E65100,color:white
    classDef postgres fill:#336791,stroke:#1A3A5C,color:white
    classDef alert fill:#E53E3E,stroke:#C53030,color:white
    classDef condition fill:#F6E05E,stroke:#D69E2E,color:#333
    classDef stop fill:#A0AEC0,stroke:#718096,color:white

    class WH trigger
    class PO,ES,BA python
    class CS,IA postgres
    class EM,SL,WA alert
    class IF condition
    class X stop
```

## Node Configuration Reference

| Node | Type | Key Settings |
|------|------|-------------|
| Webhook | Webhook | Method: POST, Path: `woo-order-created` |
| Process Webhook Order | Code (Python) | `scripts/n8n_process_webhook_order.py` |
| Check Stock Levels | PostgreSQL | Query: `scripts/n8n_check_stock_query.sql` |
| Evaluate Stock Alerts | Code (Python) | `scripts/n8n_evaluate_stock_alerts.py` |
| IF: alert_count > 0 | IF | `{{ $json.alert_count }}` greater than `0` |
| Insert Alerts | PostgreSQL | Query: `scripts/n8n_insert_alert.sql` (run once per alert) |
| Build Alert Message | Code (Python) | `scripts/n8n_build_alert_message.py` (reused from Workflow 1) |
| Send Email | Email (SMTP) | Subject: `{{ $json.email_subject }}`, Body: `{{ $json.email_html }}` |
| Send Slack | Slack | Message: `{{ $json.slack_text }}` |
| Send WhatsApp | HTTP Request | POST to WhatsApp Business API, Body: `{{ $json.whatsapp_payload }}` |

## WooCommerce Webhook Setup

1. WooCommerce Admin → Settings → Advanced → Webhooks → Add
2. **Topic:** Order created
3. **Delivery URL:** `https://<n8n-host>/webhook/woo-order-created`
4. **Secret:** (optional, for payload signature verification)
5. **Status:** Active

## Data Flow

1. WooCommerce fires `order.created` → n8n Webhook receives payload
2. Python extracts product IDs + quantities from `line_items`
3. PostgreSQL queries `vw_current_inventory` for those products
4. Python evaluates stock vs reorder point, builds alert list
5. IF `alert_count > 0`:
   - Insert each alert into `inventory_alerts` table
   - Build alert message (reuses `n8n_build_alert_message.py`)
   - Send Email + Slack + WhatsApp notifications
