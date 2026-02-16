# n8n ETL Workflow - Node Flow Diagram

```mermaid
flowchart LR
    subgraph Trigger["1. Schedule"]
        T["⏰ 6AM Daily<br/>Schedule Trigger"]
    end

    subgraph Products["2. Products Branch"]
        GP["🛒 Get Many<br/>Products"]
        TP["🐍 Transform<br/>Products"]
        UP[("🐘 Upsert<br/>Products")]
    end

    subgraph Inventory["3. Inventory Metrics"]
        CM["🐍 Calculate<br/>Inventory Metrics"]
        IS[("🐘 Insert Inventory<br/>Snapshot")]
    end

    subgraph Alerts["4. Alert Pipeline"]
        IF{"IF<br/>reorder_needed<br/>= true"}
        BA["🐍 Build Alert<br/>Message"]
        EM["📧 Send Email<br/>Gmail"]
        SL["💬 Send Slack<br/>Webhook"]
        WJ["📱 Send WhatsApp<br/>JS Code Node"]
    end

    subgraph Orders["5. Orders Branch"]
        GO["🌐 HTTP Request<br/>Get Orders"]
        TO["🐍 Transform<br/>Orders"]
        UO[("🐘 Upsert<br/>Orders")]
    end

    %% Trigger splits into two branches
    T -->|"1 item"| GP
    T -->|"1 item"| GO

    %% Products branch
    GP -->|"20 items"| TP
    TP -->|"20 items"| UP
    TP -->|"20 items"| CM

    %% Inventory metrics branch
    CM --> IS
    CM --> IF

    %% Alert pipeline
    IF -->|"true"| BA
    IF -.->|"false"| X["✋ Stop"]
    BA --> EM
    BA --> SL
    BA --> WJ

    %% Orders branch
    GO -->|"10 items"| TO
    TO -->|"10 items"| UO

    %% Styling
    classDef trigger fill:#00C4B4,stroke:#009688,color:white
    classDef python fill:#FF6D00,stroke:#E65100,color:white
    classDef postgres fill:#336791,stroke:#1A3A5C,color:white
    classDef woo fill:#96588A,stroke:#6D3F65,color:white
    classDef alert fill:#E53E3E,stroke:#C53030,color:white
    classDef condition fill:#F6E05E,stroke:#D69E2E,color:#333
    classDef stop fill:#A0AEC0,stroke:#718096,color:white
    classDef js fill:#F7DF1E,stroke:#C9B800,color:#333

    class T trigger
    class TP,TO,CM,BA python
    class UP,IS,UO postgres
    class GP woo
    class GO woo
    class EM,SL alert
    class WJ js
    class IF condition
    class X stop
```

## Node Configuration Reference

| Node | Type | Script / Key Settings |
|------|------|----------------------|
| 6AM Daily | Schedule Trigger | Every day at 6:00 AM |
| Get Many Products | WooCommerce | Resource: Product, Get All |
| HTTP Request (Get Orders) | HTTP Request | WooCommerce REST API, GET orders |
| Transform Products | Code (Python) | `scripts/n8n_transform_products.py` — Maps WooCommerce product fields to schema |
| Transform Orders | Code (Python) | `scripts/n8n_transform_orders.py` — Maps WooCommerce order fields to schema |
| Upsert Products | PostgreSQL | Table: `dim_products`, On Conflict: `woo_product_id` |
| Upsert Orders | PostgreSQL | Table: `fact_orders`, On Conflict: `woo_order_id` |
| Calculate Inventory Metrics | Code (Python) | `scripts/n8n_calculate_inventory_metrics.py` — Separates products/orders, computes avg_daily_sales from order data |
| Insert Inventory Snapshot | PostgreSQL | `scripts/n8n_insert_inventory_snapshot.sql` — Table: `fact_inventory_snapshots` |
| If Reorder Needed | IF | `{{ $json.reorder_needed }}` equals `true` |
| Build Alert Message | Code (Python) | `scripts/n8n_build_alert_message.py` — Builds HTML email, Slack text, WhatsApp payload |
| Send Email | Gmail | Subject: `{{ $json.email_subject }}`, Body: `{{ $json.email_html }}` |
| Slack Notification | HTTP Request | POST to Slack webhook, Body: `{{ $json.slack_text }}` |
| Send WhatsApp Alert | Code (JavaScript) | `scripts/n8n_send_whatsapp_alert.js` — JS workaround for n8n HTTP Request `json: false` bug |

## Key Split Points

1. **Schedule Trigger** → two parallel branches (products + orders)
2. **Transform Products** → Upsert Products + Calculate Inventory Metrics
3. **Calculate Inventory Metrics** → Insert Inventory Snapshot + IF Node
4. **Build Alert Message** → Send Email + Slack + Send WhatsApp Alert (JS Code Node)
