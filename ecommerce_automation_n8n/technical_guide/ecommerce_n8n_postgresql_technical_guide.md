# E-commerce Inventory & Order Fulfillment Pipeline

## Complete Technical Guide

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Implementation Guide](#3-implementation-guide)
   - [3.1 WordPress/WooCommerce Setup](#31-wordpresswoocommerce-setup)
   - [3.2 PostgreSQL Database Setup](#32-postgresql-database-setup)
   - [3.3 n8n Installation on Hostinger VPS](#33-n8n-installation-on-hostinger-vps)
   - [3.4 WooCommerce API Connection in n8n](#34-woocommerce-api-connection-in-n8n)
   - [3.5 n8n Workflows](#35-n8n-workflows)
   - [3.6 Streamlit Dashboard](#36-streamlit-dashboard)
   - [3.7 Alert Configuration](#37-alert-configuration)
4. [Script Reference](#4-script-reference)
5. [Database Reference](#5-database-reference)
6. [Testing Procedures](#6-testing-procedures)
7. [Troubleshooting & Lessons Learned](#7-troubleshooting--lessons-learned)
8. [Infrastructure Reference](#8-infrastructure-reference)
9. [Cost Analysis](#9-cost-analysis)
10. [Project Achievements](#10-project-achievements)

---

## 1. Executive Summary

### Business Problem

Small and medium e-commerce businesses lose revenue from two directions: stockouts cause lost sales, and overstock ties up working capital. Manual inventory monitoring does not scale, and most businesses lack the engineering resources to build automated monitoring systems.

### Solution

This project implements a fully automated e-commerce inventory and order fulfillment pipeline that:

- **Extracts** product and order data daily from WooCommerce via REST API
- **Transforms** raw data into inventory health metrics (days of inventory, reorder signals, stock velocity)
- **Loads** results into a PostgreSQL star schema optimized for analytics
- **Monitors** stock levels in real time via webhook-triggered alerts
- **Reports** weekly business summaries with styled HTML emails
- **Visualizes** inventory health, order fulfillment, and product performance on a 5-page Streamlit dashboard

### System Capabilities

| Capability | Implementation |
|---|---|
| Daily ETL pipeline | n8n Workflow 1 -- scheduled 6AM daily |
| Real-time stock alerts | n8n Workflow 2 -- WooCommerce webhook on new orders |
| Weekly summary reports | n8n Workflow 3 -- scheduled Monday 8AM |
| Multi-channel notifications | Email (Gmail), Slack (webhook), WhatsApp (Business API) |
| Interactive analytics | 5-page Streamlit dashboard with Plotly charts |
| Data quality monitoring | Automated checks + manual quality check UI |

### Technologies

| Layer | Technology |
|---|---|
| Data Source | WordPress + WooCommerce (20 products, REST API) |
| Orchestration | n8n (self-hosted on Hostinger VPS via Docker) |
| Processing | Python (n8n Code nodes -- no pandas, top-level execution) |
| Storage | PostgreSQL 16 (star schema with 4 dimensions, 4 facts, 3 views) |
| Visualization | Streamlit + Plotly |
| Infrastructure | Hostinger VPS, Docker, Traefik reverse proxy, SSL |
| Notifications | Gmail, Slack HTTP webhook, WhatsApp Business API |

---

## 2. Architecture Overview

### High-Level Architecture

```mermaid
flowchart TB
    subgraph DataSource["Data Source"]
        WC["🛒 WooCommerce<br/>WordPress Store"]
    end

    subgraph Orchestration["Orchestration (Hostinger VPS)"]
        N8N["⚙️ n8n<br/>Docker Container"]
        WF1["📅 WF1: Daily ETL"]
        WF2["🔔 WF2: Real-Time Alerts"]
        WF3["📊 WF3: Weekly Report"]
    end

    subgraph Storage["Storage (Hostinger VPS)"]
        PG[("🐘 PostgreSQL 16<br/>Star Schema")]
    end

    subgraph Visualization["Dashboard"]
        ST["📈 Streamlit<br/>5-Page Dashboard"]
    end

    subgraph Notifications["Notifications"]
        EM["📧 Gmail"]
        SL["💬 Slack"]
        WA["📱 WhatsApp"]
    end

    WC -->|"REST API"| N8N
    N8N --> WF1
    N8N --> WF2
    N8N --> WF3
    WF1 -->|"Products + Orders"| PG
    WF2 -->|"Alerts"| PG
    WF3 -->|"ETL Log"| PG
    PG -->|"SQL Queries"| ST
    WF1 --> EM
    WF1 --> SL
    WF1 --> WA
    WF2 --> EM
    WF2 --> SL
    WF3 --> EM

    classDef source fill:#96588A,stroke:#6D3F65,color:white
    classDef orch fill:#FF6D00,stroke:#E65100,color:white
    classDef store fill:#336791,stroke:#1A3A5C,color:white
    classDef viz fill:#FF4B4B,stroke:#CC3333,color:white
    classDef notify fill:#E53E3E,stroke:#C53030,color:white

    class WC source
    class N8N,WF1,WF2,WF3 orch
    class PG store
    class ST viz
    class EM,SL,WA notify
```

### Data Flow Summary

```
WooCommerce API
    |
    v
n8n Workflows (Extract + Transform)
    |
    v
PostgreSQL Star Schema
    |
    +---> Streamlit Dashboard (visualization)
    +---> n8n Alert Pipeline (notifications)
    +---> Weekly Report Email (reporting)
```

### Key Design Principles

1. **Star schema for analytics** -- Dimension tables (products, customers, suppliers, date) joined to fact tables (orders, order items, inventory snapshots, inventory movements) enable fast aggregation queries for the dashboard and reports.

2. **n8n Code nodes over standalone scripts** -- Python runs at top level inside n8n Code nodes using `_input.all()` for data input. No `load_dotenv()`, no local file access, no pandas. Credentials are handled by n8n's built-in node system.

3. **Parallel execution** -- Workflow 1 splits into products and orders branches; Workflow 3 runs three SQL queries in parallel then merges results. This minimizes total execution time.

4. **Reusable alert pipeline** -- The `n8n_build_alert_message.py` script is shared between Workflow 1 (daily reorder check) and Workflow 2 (real-time webhook alerts), producing Email HTML, Slack text, and WhatsApp payloads in a single output.

---

## 3. Implementation Guide

### 3.1 WordPress/WooCommerce Setup

#### Local Development Environment

Install **Local by Flywheel** (free) to run WordPress locally:

1. Download from [localwp.com](https://localwp.com/)
2. Create a new site (e.g., `ecommerce-test`)
3. Choose PHP 8.x, Apache, MySQL defaults
4. Once running, open the WordPress admin panel

#### WooCommerce Installation

1. WordPress Admin > Plugins > Add New > search "WooCommerce"
2. Install and activate WooCommerce
3. Skip the setup wizard (not needed for API-only usage)
4. Enable HTTPS in Local by Flywheel:
   - Click your site in Local > Overview tab > SSL section > click **Trust**

> **Important:** WooCommerce REST API requires HTTPS for Basic Authentication. HTTP connections return `401 Unauthorized`.

#### Generate API Keys

1. WooCommerce > Settings > Advanced > REST API
2. Click "Add Key"
3. Description: `n8n automation`
4. User: your admin user
5. Permissions: **Read/Write**
6. Click "Generate API Key"
7. Save the Consumer Key (`ck_...`) and Consumer Secret (`cs_...`)

#### Test Data

The project includes a test data generation script at `scripts/generate_test_data.py` that creates 20 realistic products across categories (Electronics, Apparel, Home & Garden, Sports) and generates sample orders. Run it locally with your WooCommerce API credentials:

```bash
pip install -r requirements.txt
python scripts/generate_test_data.py
```

You can also seed sample orders with `scripts/seed_sample_orders.py`.

#### Enable Permalinks

WordPress Admin > Settings > Permalinks > select **Post name** > Save Changes. This is required for the REST API to function.

---

### 3.2 PostgreSQL Database Setup

PostgreSQL must be installed on the **Hostinger VPS** (same server as n8n) so n8n can reach it over localhost.

#### Install PostgreSQL on VPS

```bash
# SSH into your Hostinger VPS
ssh root@your-hostinger-ip

# Install PostgreSQL
apt update && apt upgrade -y
apt install postgresql postgresql-contrib -y

# Start and enable service
systemctl start postgresql
systemctl enable postgresql
systemctl status postgresql
```

#### Create Database and User

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE ecommerce_inventory;
CREATE USER n8n_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ecommerce_inventory TO n8n_user;
\c ecommerce_inventory
GRANT ALL ON SCHEMA public TO n8n_user;
\q
```

#### Run the Schema

The complete schema is in `sql/schema.sql`. Copy it to the server and execute:

```bash
# From local machine
scp sql/schema.sql root@your-hostinger-ip:/root/

# On the server
sudo -u postgres psql -d ecommerce_inventory -f /root/schema.sql
```

This single file creates all dimension tables, fact tables, operational tables, indexes, views, populates the date dimension (2025-2026), and seeds 5 sample suppliers.

#### Configure Docker Access

Since n8n runs in Docker, it needs to reach PostgreSQL on the host. Add Docker network access to `pg_hba.conf`:

```bash
# Find the pg_hba.conf location
sudo -u postgres psql -c "SHOW hba_file;"

# Edit it (typically /etc/postgresql/16/main/pg_hba.conf)
# Add this line to allow Docker containers:
host    all    all    172.16.0.0/12    md5
```

Restart PostgreSQL:

```bash
systemctl restart postgresql
```

In n8n, use `172.17.0.1` (Docker bridge gateway) as the PostgreSQL host.

---

### 3.3 n8n Installation on Hostinger VPS

n8n is deployed via Docker with Traefik as a reverse proxy handling SSL certificates automatically.

#### Install Docker

```bash
ssh root@your-hostinger-ip

apt update && apt upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
apt install docker-compose -y
```

#### Create Docker Volumes

```bash
docker volume create traefik_data
docker volume create n8n_data
mkdir -p /local-files
```

#### Docker Compose Configuration

Create `/root/docker-compose.yml` -- the reference file is at `config/docker-compose.yml`:

```yaml
services:
  traefik:
    image: "traefik"
    restart: always
    command:
      - "--api=true"
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.web.http.redirections.entryPoint.to=websecure"
      - "--entrypoints.web.http.redirections.entryPoint.scheme=https"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.mytlschallenge.acme.tlschallenge=true"
      - "--certificatesresolvers.mytlschallenge.acme.email=${SSL_EMAIL}"
      - "--certificatesresolvers.mytlschallenge.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - traefik_data:/letsencrypt
      - /var/run/docker.sock:/var/run/docker.sock:ro

  n8n:
    image: docker.n8n.io/n8nio/n8n
    restart: always
    ports:
      - "127.0.0.1:5678:5678"
    labels:
      - traefik.enable=true
      - traefik.http.routers.n8n.rule=Host(`${SUBDOMAIN}.${DOMAIN_NAME}`)
      - traefik.http.routers.n8n.tls=true
      - traefik.http.routers.n8n.entrypoints=web,websecure
      - traefik.http.routers.n8n.tls.certresolver=mytlschallenge
      - traefik.http.middlewares.n8n.headers.SSLRedirect=true
      - traefik.http.middlewares.n8n.headers.STSSeconds=315360000
      - traefik.http.middlewares.n8n.headers.browserXSSFilter=true
      - traefik.http.middlewares.n8n.headers.contentTypeNosniff=true
      - traefik.http.middlewares.n8n.headers.forceSTSHeader=true
      - traefik.http.middlewares.n8n.headers.SSLHost=${DOMAIN_NAME}
      - traefik.http.middlewares.n8n.headers.STSIncludeSubdomains=true
      - traefik.http.middlewares.n8n.headers.STSPreload=true
      - traefik.http.routers.n8n.middlewares=n8n@docker
    environment:
      - N8N_HOST=${SUBDOMAIN}.${DOMAIN_NAME}
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - NODE_ENV=production
      - WEBHOOK_URL=https://${SUBDOMAIN}.${DOMAIN_NAME}/
      - GENERIC_TIMEZONE=${GENERIC_TIMEZONE}
      - N8N_PROXY_HOPS=1
    volumes:
      - n8n_data:/home/node/.n8n
      - /local-files:/files

volumes:
  traefik_data:
    external: true
  n8n_data:
    external: true
```

#### Environment File

Create `/root/.env`:

```
DOMAIN_NAME=your-hostinger-domain.hstgr.cloud
SUBDOMAIN=n8n
GENERIC_TIMEZONE=America/New_York
SSL_EMAIL=your-email@example.com
```

#### Start n8n

```bash
cd /root
docker-compose up -d
docker-compose ps   # Verify both containers are running
```

Access n8n at `https://n8n.your-hostinger-domain.hstgr.cloud`. Traefik handles SSL certificate provisioning automatically via Let's Encrypt.

> **Note:** The Docker container name will be `root-n8n-1` (not `n8n`). Use `docker exec -it root-n8n-1 sh` to access the container shell.

---

### 3.4 WooCommerce API Connection in n8n

#### Credential Setup

In n8n, go to Credentials > Add Credential > WooCommerce API:

| Field | Value |
|---|---|
| Consumer Key | `ck_your_woocommerce_key` |
| Consumer Secret | `cs_your_woocommerce_secret` |
| WooCommerce URL | `https://your-store-url` |
| Include Credentials in Query | **ON** |

> **Using n8n on VPS with Local WooCommerce:** n8n on the VPS cannot reach local domains like `ecommerce-test.local`. Enable **Live Link** in Local WP (bottom of site panel), then use the Live Link URL with embedded credentials: `https://USERNAME:PASSWORD@your-live-link.localsite.io`

#### Test the Connection

Create a test workflow:

1. Add a **Manual Trigger** node
2. Add a **WooCommerce** node
3. Set Resource: Product, Operation: **Get many products**
4. Execute -- you should see your 20 products returned

---

### 3.5 n8n Workflows

This project uses three n8n workflows. Each workflow's complete node-flow diagram is stored as a Mermaid file in `technical_guide/`. The workflow JSON export is at `workflow_json/n8n_workflows_export.json`.

---

#### Workflow 1: Daily Data Extraction + Reorder Notifications

**Trigger:** Schedule Trigger -- 6AM daily

**Diagram:** See `technical_guide/n8n_workflow_diagram.md`

```mermaid
flowchart LR
    subgraph Trigger["1. Schedule"]
        T["6AM Daily"]
    end

    subgraph Products["2. Products Branch"]
        GP["Get Many Products"]
        TP["Transform Products"]
        UP[("Upsert Products")]
    end

    subgraph Inventory["3. Inventory Metrics"]
        CM["Calculate Metrics"]
        IS[("Insert Snapshot")]
    end

    subgraph Alerts["4. Alert Pipeline"]
        IF{"Reorder Needed?"}
        BA["Build Alert Message"]
        EM["Gmail"]
        SL["Slack"]
        WJ["WhatsApp (JS)"]
    end

    subgraph Orders["5. Orders Branch"]
        GO["HTTP Get Orders"]
        TO["Transform Orders"]
        UO[("Upsert Orders")]
    end

    T --> GP
    T --> GO
    GP --> TP --> UP
    TP --> CM
    CM --> IS
    CM --> IF
    IF -->|"true"| BA
    BA --> EM
    BA --> SL
    BA --> WJ
    GO --> TO --> UO

    classDef trigger fill:#00C4B4,stroke:#009688,color:white
    classDef python fill:#FF6D00,stroke:#E65100,color:white
    classDef postgres fill:#336791,stroke:#1A3A5C,color:white
    classDef alert fill:#E53E3E,stroke:#C53030,color:white
    classDef condition fill:#F6E05E,stroke:#D69E2E,color:#333
    classDef js fill:#F7DF1E,stroke:#C9B800,color:#333

    class T trigger
    class TP,TO,CM,BA python
    class UP,IS,UO postgres
    class GP,GO trigger
    class EM,SL alert
    class WJ js
    class IF condition
```

##### Node-by-Node Configuration

**Schedule Trigger**
- Trigger interval: Every day at 6:00 AM
- Timezone: America/New_York

The trigger output splits into two parallel branches.

**Products Branch:**

1. **Get Many Products** (WooCommerce node)
   - Resource: Product
   - Operation: Get many products
   - Returns all 20 products with full WooCommerce metadata

2. **Transform Products** (Python Code node)
   - Script: `scripts/n8n_transform_products.py`
   - Maps WooCommerce fields to schema columns: `woo_product_id`, `sku`, `product_name`, `category`, `sell_price`, `cost_price` (estimated at 60% of sell price), `is_active`, `stock_quantity`
   - Input: raw WooCommerce product objects via `_input.all()`
   - Output: 20 transformed product items

3. **Upsert Products** (PostgreSQL node)
   - Table: `dim_products`
   - Operation: Upsert
   - On Conflict column: `woo_product_id`

**Orders Branch:**

1. **HTTP Request -- Get Orders** (HTTP Request node)
   - Method: GET
   - URL: WooCommerce REST API orders endpoint
   - Authentication: WooCommerce API credentials
   - Returns recent orders

2. **Transform Orders** (Python Code node)
   - Script: `scripts/n8n_transform_orders.py`
   - Maps: `woo_order_id`, `order_date`, `status`, `total_amount`, `item_count`, `fulfillment_time_hours`, `shipping_cost`

3. **Upsert Orders** (PostgreSQL node)
   - Table: `fact_orders`
   - Operation: Upsert
   - On Conflict column: `woo_order_id`

**Inventory Metrics (receives merged data from both branches):**

4. **Calculate Inventory Metrics** (Python Code node)
   - Script: `scripts/n8n_calculate_inventory_metrics.py`
   - This node receives the combined output of Transform Products and Transform Orders. It separates the two by checking for field names:

   ```python
   for item in items:
       data = item.json
       if "woo_order_id" in data:
           orders.append(data)
       elif "woo_product_id" in data:
           products.append(data)
   ```

   - Computes `avg_daily_sales` from total order `item_count` spread across products over a 30-day lookback
   - For each product, calculates: `quantity_on_hand`, `days_of_inventory`, `reorder_needed`, `stock_status` (Critical / Low / Healthy)

5. **Insert Inventory Snapshot** (PostgreSQL node)
   - Query: `scripts/n8n_insert_inventory_snapshot.sql`
   - Uses `ON CONFLICT (product_id, snapshot_date) DO UPDATE` for idempotent daily runs
   - Joins `dim_products` and `dim_date` to resolve foreign keys from `woo_product_id` and `snapshot_date`

**Alert Pipeline:**

6. **IF Reorder Needed** (IF node)
   - Condition: `{{ $json.reorder_needed }}` equals `true`
   - True branch: continues to Build Alert Message
   - False branch: stops

7. **Build Alert Message** (Python Code node)
   - Script: `scripts/n8n_build_alert_message.py`
   - Separates items into critical vs. low stock
   - Builds three outputs in a single return:
     - `email_html`: styled HTML table with color-coded stock status
     - `slack_text` / `slack_payload`: Markdown-formatted Slack message
     - `whatsapp_text` / `whatsapp_payload`: pre-built JSON for WhatsApp Business API

8. **Send Email** (Gmail node)
   - Subject: `{{ $json.email_subject }}`
   - Body: `{{ $json.email_html }}`

9. **Slack Notification** (HTTP Request node)
   - POST to Slack webhook URL
   - Body: `{{ $json.slack_payload }}`

10. **Send WhatsApp Alert** (JavaScript Code node)
    - Script: `scripts/n8n_send_whatsapp_alert.js`
    - Uses `this.helpers.httpRequest()` with `json: true` as a workaround for the n8n HTTP Request node bug (see [Troubleshooting](#7-troubleshooting--lessons-learned))

    ```javascript
    const response = await this.helpers.httpRequest({
      method: 'POST',
      url: 'https://graph.facebook.com/v24.0/<PHONE_NUMBER_ID>/messages',
      headers: {
        'Authorization': 'Bearer <WHATSAPP_API_TOKEN>',
        'Content-Type': 'application/json'
      },
      body: {
        messaging_product: 'whatsapp',
        to: '<RECIPIENT_NUMBER>',
        type: 'template',
        template: {
          name: 'inventory_alert',
          language: { code: 'en_US' },
          components: [{
            type: 'body',
            parameters: [{ type: 'text', text: $input.first().json.whatsapp_text }]
          }]
        }
      },
      json: true
    });
    return [{ json: response }];
    ```

> **Important:** Only the JavaScript Code node approach is reliable for WhatsApp alerts. The n8n HTTP Request node has a `json: false` bug that causes the WhatsApp API to reject the request. Always use the JS Code node with `this.helpers.httpRequest({ json: true })`.

---

#### Workflow 2: Real-Time Inventory Alerts (Webhook-Triggered)

**Trigger:** Webhook (POST to path `woo-order-created`)

**Diagram:** See `technical_guide/n8n_workflow_2_diagram.md`

```mermaid
flowchart LR
    WH["Webhook"] --> PO["Process Order"]
    PO --> CS[("Check Stock")]
    CS --> ES["Evaluate Alerts"]
    ES --> IF{"alert_count > 0?"}
    IF -->|"true"| IA[("Insert Alerts")]
    IF -->|"true"| BA["Build Message"]
    BA --> EM["Email"]
    BA --> SL["Slack"]

    classDef trigger fill:#00C4B4,stroke:#009688,color:white
    classDef python fill:#FF6D00,stroke:#E65100,color:white
    classDef postgres fill:#336791,stroke:#1A3A5C,color:white
    classDef alert fill:#E53E3E,stroke:#C53030,color:white
    classDef condition fill:#F6E05E,stroke:#D69E2E,color:#333

    class WH trigger
    class PO,ES,BA python
    class CS,IA postgres
    class EM,SL alert
    class IF condition
```

##### WooCommerce Webhook Setup

1. WooCommerce Admin > Settings > Advanced > Webhooks > Add Webhook
2. Topic: **Order created**
3. Delivery URL: `https://<n8n-host>/webhook/woo-order-created`
4. Status: Active

##### Node-by-Node Configuration

1. **Webhook** (Webhook node)
   - Method: POST
   - Path: `woo-order-created`
   - WooCommerce sends the full order payload when a new order is placed

2. **Process Webhook Order** (Python Code node)
   - Script: `scripts/n8n_process_webhook_order.py`
   - **Key lesson:** The webhook payload is wrapped under a `body` key by n8n. The script unwraps it:

   ```python
   webhook_data = items[0].json
   order_data = webhook_data.get("body", webhook_data)
   ```

   - Extracts `product_ids` (comma-separated) and `products` list from `line_items`
   - Output: single item with `product_ids`, `product_count`, `order_id`, `products` array

3. **Check Stock Levels** (PostgreSQL node)
   - Query: `scripts/n8n_check_stock_query.sql`
   - Queries `vw_current_inventory` for the ordered product IDs
   - Uses: `WHERE v.woo_product_id IN ({{ $json.product_ids }})`

4. **Evaluate Stock Alerts** (Python Code node)
   - Script: `scripts/n8n_evaluate_stock_alerts.py`
   - Checks each product's `quantity_on_hand` against `reorder_point` and `safety_stock`
   - Classifies alerts as `out_of_stock`, `low_stock` with `Critical` or `Low` status
   - **Key pattern:** Returns one item per alert so downstream INSERT iterates correctly:

   ```python
   results = []
   for alert in alerts:
       alert["alert_count"] = len(alerts)
       results.append({"json": alert})
   return results
   ```

5. **IF: alert_count > 0** (IF node)
   - Condition: `{{ $json.alert_count }}` greater than `0`

6. **Insert Alerts** (PostgreSQL node)
   - Query: `scripts/n8n_insert_alert.sql`
   - Runs once per alert item, inserting into `inventory_alerts` table

7. **Build Alert Message** (Python Code node)
   - Reuses `scripts/n8n_build_alert_message.py` from Workflow 1

8. **Send Email** + **Send Slack** -- same configuration as Workflow 1

---

#### Workflow 3: Weekly Summary Report

**Trigger:** Schedule Trigger -- Monday at 8:00 AM

**Diagram:** See `technical_guide/n8n_workflow_3_diagram.md`

```mermaid
flowchart LR
    ST["Monday 8AM"] --> QO[("Order Stats")]
    ST --> QI[("Inventory Health")]
    ST --> QT[("Top Products")]
    QO --> MG["Merge (Append)"]
    QI --> MG
    QT --> MG
    MG --> BR["Build Report HTML"]
    BR --> EM["Send Email"]
    BR --> LR[("Log ETL Run")]

    classDef trigger fill:#00C4B4,stroke:#009688,color:white
    classDef python fill:#FF6D00,stroke:#E65100,color:white
    classDef postgres fill:#336791,stroke:#1A3A5C,color:white
    classDef alert fill:#E53E3E,stroke:#C53030,color:white

    class ST trigger
    class BR python
    class QO,QI,QT,LR postgres
    class MG python
    class EM alert
```

##### Node-by-Node Configuration

The schedule trigger fires three parallel PostgreSQL queries:

1. **Weekly Order Stats** (PostgreSQL node)
   - Query: `scripts/n8n_weekly_order_stats.sql`
   - Returns: `order_count`, `total_revenue`, `avg_order_value`, `total_items_sold`, `period_start`, `period_end`
   - Filters: last 7 days, excludes cancelled/refunded orders

2. **Inventory Health** (PostgreSQL node)
   - Query: `scripts/n8n_weekly_inventory_health.sql`
   - Returns: `critical_count`, `low_count`, `healthy_count`, `total_products`, and a JSON array of `reorder_needed_products` (up to 10)
   - Uses `COUNT(*) FILTER (WHERE ...)` for status breakdown

3. **Top Products This Week** (PostgreSQL node)
   - Query: `scripts/n8n_weekly_top_products.sql`
   - Returns: top 5 products by revenue with `units_sold`, `revenue`, `order_count`

4. **Merge** (Merge node)
   - Mode: **Append**
   - Combines all three query results into a single item list
   - The Python script expects: Item 0 = order stats, Item 1 = inventory health, Items 2+ = top products

5. **Build Weekly Report HTML** (Python Code node)
   - Script: `scripts/n8n_build_weekly_report.py`
   - Generates a fully styled HTML email with:
     - Header with gradient background and week range
     - KPI cards (orders, revenue, avg order value, items sold)
     - Top products table
     - Inventory health bar (color-coded percentages)
     - Products needing reorder table
     - Footer with generation timestamp

6. **Send Email** (Gmail node)
   - Subject: `{{ $json.email_subject }}`
   - Body: `{{ $json.email_html }}`

7. **Log ETL Run** (PostgreSQL node)
   - Query: `scripts/n8n_log_etl_run.sql`
   - Inserts a record into `etl_run_history` with `run_type='weekly_report'`

---

### 3.6 Streamlit Dashboard

The dashboard provides 5 pages of interactive analytics, all powered by SQL queries against the PostgreSQL star schema.

#### File Structure

```
dashboard/
├── app.py                          # Main app + home page KPIs
├── db.py                           # Database connection + cached queries
└── pages/
    ├── 1_Overview.py               # KPIs, stock status donut, orders trend, top products
    ├── 2_Inventory_Health.py       # Heatmap, reorder table, days-of-inventory, slow/fast movers
    ├── 3_Order_Fulfillment.py      # Order KPIs, status donut, dual-axis volume/revenue, fulfillment histogram
    ├── 4_Product_Performance.py    # Top/bottom products, category performance, profitability scatter
    └── 5_Alerts_Quality.py         # Active alerts, alert timeline, data quality log, manual checks
```

#### Database Connection (`db.py`)

Uses `psycopg` (v3, not psycopg2) with Streamlit caching:

- `get_connection()` -- cached resource, reads `.env` for credentials, defaults to `172.17.0.1:5432`
- `run_query(sql, params)` -- cached for 5 minutes (TTL=300), returns pandas DataFrame

#### Page Descriptions

| Page | Key Visualizations |
|---|---|
| **app.py** (Home) | Inventory value, units in stock, pending orders, stockout risk; stock status pie chart; recent orders bar chart |
| **1_Overview** | Same KPIs + avg days of inventory; stock status donut; daily orders line chart (30 days); top 5 products by revenue; recent alerts table |
| **2_Inventory_Health** | Scatter heatmap (category x product, sized by qty, colored by status); products near reorder point; days-of-inventory histogram; slow movers (>60 days) vs fast movers (<7 days); stock level trends over time (multi-select) |
| **3_Order_Fulfillment** | Total orders, avg order value, avg fulfillment time; orders by status donut; dual-axis daily orders + revenue; fulfillment time histogram; recent orders table |
| **4_Product_Performance** | Top 10 / bottom 10 by revenue; category performance (grouped bar); profitability scatter (price vs units, sized by revenue); searchable product detail table |
| **5_Alerts_Quality** | Active alert counts by type; alert history timeline (scatter, colored by resolved status); data quality log; ETL run history; manual quality check button (5 checks) |

#### Running the Dashboard

```bash
cd dashboard
pip install -r ../requirements.txt
streamlit run app.py
```

For running on the VPS, ensure the `.env` file is configured at `config/.env` with the correct database credentials.

---

### 3.7 Alert Configuration

#### Gmail Setup

1. In n8n, add a Gmail credential (OAuth2 or App Password)
2. The Build Alert Message script provides `email_subject` and `email_html` fields
3. Configure the Gmail node with: To, Subject = `{{ $json.email_subject }}`, HTML Body = `{{ $json.email_html }}`

#### Slack Webhook

1. Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps)
2. Enable Incoming Webhooks
3. Add a webhook to your desired channel
4. Copy the webhook URL
5. In n8n, use an HTTP Request node: POST to the webhook URL with body `{{ $json.slack_payload }}`

#### WhatsApp Business API (via JavaScript Code Node)

WhatsApp alerts use the Meta Graph API with the WhatsApp Business platform:

1. Create a Meta Developer account and WhatsApp Business App
2. Get a Phone Number ID and permanent API token
3. Create a message template named `inventory_alert` in the WhatsApp Business dashboard
4. In n8n, use a **JavaScript Code node** (not HTTP Request) with the script at `scripts/n8n_send_whatsapp_alert.js`

> **Why JavaScript Code instead of HTTP Request?** The n8n HTTP Request node has a bug where `json: false` is sent even when you configure JSON body, causing the WhatsApp API to reject the request with a content-type error. The JS Code node's `this.helpers.httpRequest({ json: true })` correctly sends `Content-Type: application/json`.

---

## 4. Script Reference

All n8n scripts are stored in `scripts/` with the `n8n_` prefix.

| Script | Workflow | Node Name | Purpose |
|---|---|---|---|
| `n8n_transform_products.py` | WF1 | Transform Products | Maps WooCommerce product fields to `dim_products` schema |
| `n8n_transform_orders.py` | WF1 | Transform Orders | Maps WooCommerce order fields to `fact_orders` schema |
| `n8n_calculate_inventory_metrics.py` | WF1 | Calculate Inventory Metrics | Separates products/orders, computes avg daily sales, stock status |
| `n8n_insert_inventory_snapshot.sql` | WF1 | Insert Inventory Snapshot | Upserts daily snapshot into `fact_inventory_snapshots` |
| `n8n_build_alert_message.py` | WF1, WF2 | Build Alert Message | Builds HTML email, Slack text, and WhatsApp payload |
| `n8n_send_whatsapp_alert.js` | WF1 | Send WhatsApp Alert | JS Code node workaround for WhatsApp Business API |
| `n8n_process_webhook_order.py` | WF2 | Process Webhook Order | Unwraps webhook body, extracts product IDs from line items |
| `n8n_check_stock_query.sql` | WF2 | Check Stock Levels | Queries `vw_current_inventory` for ordered products |
| `n8n_evaluate_stock_alerts.py` | WF2 | Evaluate Stock Alerts | Evaluates stock vs reorder point, returns one item per alert |
| `n8n_insert_alert.sql` | WF2 | Insert Alerts | Inserts alert record into `inventory_alerts` |
| `n8n_build_weekly_report.py` | WF3 | Build Weekly Report HTML | Generates styled HTML email from 3 merged query results |
| `n8n_weekly_order_stats.sql` | WF3 | Weekly Order Stats | 7-day order count, revenue, avg order value |
| `n8n_weekly_inventory_health.sql` | WF3 | Inventory Health | Stock status breakdown + reorder products JSON |
| `n8n_weekly_top_products.sql` | WF3 | Top Products This Week | Top 5 products by revenue (7 days) |
| `n8n_log_etl_run.sql` | WF3 | Log ETL Run | Records report generation in `etl_run_history` |

**Utility scripts** (not used in n8n workflows):

| Script | Purpose |
|---|---|
| `scripts/generate_test_data.py` | Creates test products and orders in WooCommerce |
| `scripts/seed_sample_orders.py` | Seeds additional sample order data |
| `scripts/verify_setup.py` | Verifies database connection and schema |
| `scripts/verify_data.sql` | SQL queries to verify data integrity |

---

## 5. Database Reference

### Star Schema Diagram

```mermaid
erDiagram
    dim_date ||--o{ fact_orders : "date_id"
    dim_date ||--o{ fact_inventory_snapshots : "date_id"
    dim_date ||--o{ fact_inventory_movements : "date_id"
    dim_customers ||--o{ fact_orders : "customer_id"
    dim_products ||--o{ fact_order_items : "product_id"
    dim_products ||--o{ fact_inventory_snapshots : "product_id"
    dim_products ||--o{ fact_inventory_movements : "product_id"
    dim_products ||--o{ inventory_alerts : "product_id"
    dim_suppliers ||--o{ dim_products : "supplier_id"
    fact_orders ||--o{ fact_order_items : "order_fact_id"

    dim_products {
        int product_id PK
        int woo_product_id UK
        varchar sku
        varchar product_name
        varchar category
        decimal cost_price
        decimal sell_price
        int reorder_point
        int reorder_quantity
        int safety_stock
        int supplier_id FK
        boolean is_active
    }

    dim_customers {
        int customer_id PK
        int woo_customer_id UK
        varchar email
        varchar first_name
        varchar last_name
        varchar segment
        decimal lifetime_value
        int total_orders
    }

    dim_suppliers {
        int supplier_id PK
        varchar supplier_name
        varchar contact_email
        int lead_time_days
        decimal reliability_score
        boolean is_active
    }

    dim_date {
        int date_id PK
        date full_date UK
        int year
        int quarter
        int month
        varchar month_name
        int week
        int day_of_week
        boolean is_weekend
    }

    fact_orders {
        int order_fact_id PK
        int woo_order_id UK
        int customer_id FK
        int date_id FK
        timestamp order_date
        varchar status
        decimal total_amount
        int item_count
    }

    fact_order_items {
        int order_item_id PK
        int order_fact_id FK
        int product_id FK
        int quantity
        decimal unit_price
        decimal line_total
    }

    fact_inventory_snapshots {
        int snapshot_id PK
        int product_id FK
        int date_id FK
        date snapshot_date
        int quantity_on_hand
        int quantity_available
        boolean reorder_needed
        decimal days_of_inventory
    }

    fact_inventory_movements {
        int movement_id PK
        int product_id FK
        int date_id FK
        varchar movement_type
        int quantity
        varchar reason
    }
```

### Views

| View | Purpose |
|---|---|
| `vw_current_inventory` | Current stock status per product (latest snapshot), includes stock_status classification, supplier info |
| `vw_daily_orders` | Order count + revenue by date (last 90 days) |
| `vw_product_performance` | Units sold, revenue, order count per product (last 30 days) |

### Operational Tables

| Table | Purpose |
|---|---|
| `etl_run_history` | Tracks workflow executions (type, start/end time, status, records processed) |
| `data_quality_log` | Records data quality check results |
| `inventory_alerts` | Stores stock alerts with type, quantities, resolved status |

### Indexes

Performance indexes exist on: `fact_orders(date_id, customer_id, status, order_date)`, `fact_inventory_snapshots(product_id, snapshot_date)`, `fact_inventory_movements(product_id, movement_type)`, `dim_products(category, sku)`, `inventory_alerts(product_id, alert_type, is_resolved)`.

Full schema definition: `sql/schema.sql`

---

## 6. Testing Procedures

### Workflow 1: Daily ETL

1. Open Workflow 1 in n8n
2. Click **Execute Workflow** (manual trigger)
3. Verify each node's output:
   - Get Many Products returns 20 items
   - Transform Products outputs mapped fields
   - Upsert Products shows no errors
   - Calculate Inventory Metrics outputs stock metrics
   - Insert Inventory Snapshot completes without conflict errors
4. Check PostgreSQL:
   ```sql
   SELECT COUNT(*) FROM dim_products;                    -- Should be 20
   SELECT COUNT(*) FROM fact_inventory_snapshots
   WHERE snapshot_date = CURRENT_DATE;                   -- Should be 20
   ```

### Workflow 2: Webhook Alerts

Test from the VPS command line using curl:

```bash
# Use a real woo_product_id from dim_products
# Check existing products first:
sudo -u postgres psql -d ecommerce_inventory \
  -c "SELECT woo_product_id, product_name FROM dim_products LIMIT 5;"

# Fire a test webhook (use -k to skip SSL for localhost)
curl -k -X POST http://localhost:5678/webhook-test/woo-order-created \
  -H "Content-Type: application/json" \
  -d '{
    "id": 9999,
    "number": "9999",
    "date_created": "2026-02-14T10:00:00",
    "status": "processing",
    "line_items": [
      {
        "product_id": <REAL_WOO_PRODUCT_ID>,
        "name": "Test Product",
        "quantity": 5
      }
    ]
  }'
```

> **Important:** Use real `woo_product_id` values from `dim_products`. The stock check query joins on `woo_product_id`, so fake IDs will return no rows and no alerts will fire.

Verify in the n8n execution log that each node ran. Check `inventory_alerts`:

```sql
SELECT * FROM inventory_alerts ORDER BY alert_date DESC LIMIT 5;
```

### Workflow 3: Weekly Report

1. Open Workflow 3 in n8n
2. Click **Execute Workflow** (manual trigger)
3. Verify the email arrives with:
   - Order summary KPI cards
   - Top products table
   - Inventory health bar
   - Products needing reorder table
4. Check ETL log:
   ```sql
   SELECT * FROM etl_run_history ORDER BY start_time DESC LIMIT 5;
   ```

### Streamlit Dashboard

```bash
cd dashboard
streamlit run app.py
```

Verify:
- Database connection indicator shows green
- All 5 pages load without errors
- Charts render with data from the most recent snapshot
- Manual quality check button runs successfully

---

## 7. Troubleshooting & Lessons Learned

### n8n Webhook Wraps POST Body Under `body` Key

**Problem:** When WooCommerce sends a webhook POST to n8n, the payload appears nested under a `body` key in the n8n Webhook node output, not at the root level.

**Solution:** Always unwrap in your processing script:
```python
order_data = webhook_data.get("body", webhook_data)
```

### n8n Evaluate Scripts Must Return One Item Per Row

**Problem:** If an evaluate script returns a single item with an array of alerts, the downstream PostgreSQL INSERT node only runs once instead of once per alert.

**Solution:** Return each alert as a separate item in the results array:
```python
results = []
for alert in alerts:
    results.append({"json": alert})
return results
```

### n8n HTTP Request Node `json: false` Bug (WhatsApp)

**Problem:** The n8n HTTP Request node sends `json: false` to the WhatsApp Graph API even when you configure a JSON body. The API rejects the request because `Content-Type` is not set to `application/json`.

**Solution:** Use a JavaScript Code node with `this.helpers.httpRequest({ json: true })`. This correctly serializes the body and sets the Content-Type header. See `scripts/n8n_send_whatsapp_alert.js`.

### WhatsApp Graph API Requires Explicit Content-Type

The Meta Graph API for WhatsApp strictly requires `Content-Type: application/json`. Unlike Slack webhooks that are forgiving about content types, WhatsApp will reject requests without this header.

### Meta Auto-Upgrades Graph API Versions

Meta periodically deprecates older Graph API versions. If WhatsApp alerts suddenly stop working, check that your API version (e.g., `v24.0`) is still active. Update the URL in `n8n_send_whatsapp_alert.js` as needed.

### Testing Webhooks from VPS

Use `curl -k http://localhost:5678/webhook-test/...` directly on the VPS. The `-k` flag skips SSL verification for the localhost connection. The `webhook-test` path is n8n's test endpoint (vs. `webhook` for production).

### Use Real Product IDs When Testing

When testing Workflow 2 with curl, use actual `woo_product_id` values from `dim_products`. The check stock query uses `vw_current_inventory` which joins on `woo_product_id`. Fake IDs will return empty results and no alerts will fire.

### `pg_dump` With `-h localhost`

When backing up the database from the VPS, use `-h localhost` to force TCP connection instead of peer authentication:

```bash
pg_dump -U n8n_user -h localhost ecommerce_inventory > backup.sql
```

Without `-h localhost`, PostgreSQL defaults to Unix socket authentication (peer auth), which will fail for the `n8n_user` unless configured.

### Docker Container Naming

Hostinger's Docker setup creates container names with the directory prefix. The n8n container is named `root-n8n-1`, not `n8n`:

```bash
docker exec -it root-n8n-1 sh          # Correct
docker logs root-n8n-1 --tail 50       # Correct
```

### Python Code Nodes: No `load_dotenv`, No Pandas

n8n Python Code nodes run on the n8n server, not your local machine. They cannot access local `.env` files or import external packages like pandas. Use:
- `_input.all()` for data input
- Standard library only (datetime, json, etc.)
- `return` at top level (no function wrappers)

### psycopg v3 on Windows

The project uses `psycopg[binary]>=3.1.0` (v3) instead of `psycopg2-binary`, which has better Windows compatibility. Import as `import psycopg` (not `psycopg2`).

### WooCommerce API Requires HTTPS

Basic Authentication over HTTP returns `401 Unauthorized`. Always use HTTPS URLs. In Local by Flywheel, trust the SSL certificate. For self-signed certs in Python, add `verify=False` to requests (development only).

### n8n Operation Names Changed

Older n8n documentation references "Get All" for WooCommerce operations. Current versions use **"Get many products"**. The functionality is identical.

---

## 8. Infrastructure Reference

### VPS Access

```bash
# SSH into Hostinger VPS
ssh root@your-hostinger-ip
```

### Docker Commands

```bash
# Check running containers
docker-compose ps

# View n8n logs
docker logs root-n8n-1 --tail 100

# Restart n8n
cd /root && docker-compose restart n8n

# Restart everything
cd /root && docker-compose down && docker-compose up -d

# Access n8n container shell
docker exec -it root-n8n-1 sh
```

### PostgreSQL Commands

```bash
# Connect to database
sudo -u postgres psql -d ecommerce_inventory

# Connect as n8n_user (TCP)
psql -U n8n_user -h localhost -d ecommerce_inventory

# Backup database
pg_dump -U n8n_user -h localhost ecommerce_inventory > backup_$(date +%Y%m%d).sql

# Restore database
psql -U n8n_user -h localhost -d ecommerce_inventory < backup.sql

# Check PostgreSQL status
systemctl status postgresql
```

### Quick Resume Commands

After a VPS restart, verify everything is running:

```bash
# 1. Check Docker
docker-compose ps

# 2. If n8n is not running
cd /root && docker-compose up -d

# 3. Check PostgreSQL
systemctl status postgresql

# 4. If PostgreSQL is not running
systemctl start postgresql

# 5. Verify database
sudo -u postgres psql -d ecommerce_inventory -c "SELECT COUNT(*) FROM dim_products;"

# 6. Verify n8n is accessible
curl -k https://localhost:5678/healthz
```

### n8n PostgreSQL Credential Configuration

| Field | Value |
|---|---|
| Host | `172.17.0.1` (Docker bridge gateway) |
| Port | `5432` |
| Database | `ecommerce_inventory` |
| User | `n8n_user` |
| Password | (your password) |
| SSL | Disable (local connection) |

---

## 9. Cost Analysis

| Component | Cost | Notes |
|---|---|---|
| Hostinger VPS (KVM 1) | ~$6-10/month | Hosts n8n (Docker), PostgreSQL, Traefik |
| WooCommerce | Free | Open-source WordPress plugin |
| n8n (self-hosted) | Free | Community edition, unlimited workflows |
| PostgreSQL | Free | Open-source database |
| Streamlit | Free | Open-source dashboard framework |
| Local by Flywheel | Free | Local WordPress development |
| Gmail (notifications) | Free | Standard Gmail account |
| Slack (webhooks) | Free | Free tier includes incoming webhooks |
| WhatsApp Business API | Free tier | 1,000 free service conversations/month |
| **Total** | **~$6-10/month** | VPS is the only recurring cost |

---

## 10. Project Achievements

### Technical Skills Demonstrated

| Skill Area | Details |
|---|---|
| **Data Engineering** | Star schema design; ETL pipeline with idempotent upserts; date dimension generation; inventory movement tracking |
| **Workflow Automation** | 3 production n8n workflows (scheduled, webhook, report); parallel branch execution; conditional alert routing |
| **API Integration** | WooCommerce REST API consumption; Slack webhook integration; WhatsApp Business API via Meta Graph API |
| **Python** | Data transformation scripts for n8n Code nodes; HTML report generation; inventory metric calculations; no external dependencies |
| **SQL** | PostgreSQL views for real-time analytics; parameterized queries with n8n expressions; `ON CONFLICT` upserts; `FILTER` aggregation |
| **Dashboard Development** | 5-page Streamlit app with Plotly; cached database queries; interactive filters; dual-axis charts; manual quality checks |
| **DevOps / Infrastructure** | Docker + Docker Compose; Traefik reverse proxy with auto-SSL; PostgreSQL administration; VPS deployment |
| **Notification Systems** | Multi-channel alerts (Email + Slack + WhatsApp); HTML email templating; JS Code node workaround for API bugs |
| **Troubleshooting** | Documented 13+ setup issues with solutions; webhook payload quirks; Docker networking; API authentication patterns |

### System Metrics

- **20 products** monitored across 4 categories
- **3 automated workflows** running on schedule + webhook
- **5 dashboard pages** with 15+ chart types
- **3 notification channels** (Email, Slack, WhatsApp)
- **16 n8n scripts** (Python + SQL + JavaScript)
- **4 dimension tables**, **4 fact tables**, **3 views**, **15 indexes**

---

*Built for the Business Automation Library YouTube channel. All code is in the `ecommerce_automation_n8n/` directory of the [business-automation-library](https://github.com/your-repo) repository.*
