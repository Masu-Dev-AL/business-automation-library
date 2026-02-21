# E-commerce Inventory & Order Fulfillment Pipeline

An automated inventory monitoring and order fulfillment system for e-commerce businesses, built with n8n, PostgreSQL, and Streamlit.

## Overview

This project demonstrates how to build an end-to-end inventory management pipeline using:
- **n8n** - Workflow automation (scheduled ETL, webhooks, multi-channel alerts)
- **WooCommerce REST API** - E-commerce data source (products, orders, inventory)
- **PostgreSQL** - Star schema data warehouse (dimensions + facts)
- **Python** - Data transformation and business logic
- **Streamlit** - Interactive analytics dashboard

## Architecture

```
WooCommerce API → n8n ETL Workflow → Python Transforms → PostgreSQL
                                                              ↓
                                                    Streamlit Dashboard

WooCommerce Webhook → n8n Alert Workflow → Stock Check → IF Low Stock
                                                              ↓
                                                  Email + Slack + WhatsApp
```

## Features

- Automated daily ETL from WooCommerce to PostgreSQL star schema
- Real-time webhook-triggered stock monitoring on new orders
- Reorder point calculations with days-of-inventory tracking
- Multi-channel alerts (Gmail, Slack, WhatsApp Business API)
- Automated weekly summary reports with HTML email
- 5-page interactive Streamlit dashboard

## Project Structure

```
├── scripts/
│   ├── n8n_transform_products.py       # WooCommerce product transformation
│   ├── n8n_transform_orders.py         # WooCommerce order transformation
│   ├── n8n_calculate_inventory_metrics.py  # Stock level calculations
│   ├── n8n_evaluate_stock_alerts.py    # Alert threshold evaluation
│   ├── n8n_build_alert_message.py      # Multi-channel alert formatting
│   ├── n8n_build_weekly_report.py      # Weekly HTML report builder
│   ├── n8n_send_whatsapp_alert.js      # WhatsApp Business API integration
│   ├── n8n_*.sql                       # SQL queries for n8n PostgreSQL nodes
│   ├── generate_test_data.py           # WooCommerce test data generator
│   ├── seed_sample_orders.py           # Direct DB order seeding
│   └── verify_setup.py                 # Setup verification script
├── dashboard/
│   ├── app.py                          # Streamlit main app
│   ├── db.py                           # Database connection helper
│   └── pages/                          # Dashboard pages (5 views)
├── sql/
│   └── schema.sql                      # Star schema DDL + views + seed data
├── workflow_json/
│   ├── n8n_workflows_export.json       # Importable n8n workflow definitions
│   └── schema_export.sql               # Database schema export
├── config/
│   ├── .env.example                    # Environment variable template
│   └── docker-compose.yml              # n8n Docker deployment
├── technical_guide/                    # Complete implementation guide + diagrams
└── requirements.txt
```

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Masu-Dev-AL/business-automation-library.git
   cd business-automation-library/ecommerce_automation_n8n
   ```

2. **Set up the environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   pip install -r requirements.txt
   ```

3. **Configure credentials**
   ```bash
   cp config/.env.example config/.env
   # Edit .env with your WooCommerce API keys, database credentials, etc.
   ```

4. **Set up PostgreSQL**
   ```bash
   psql -U postgres -c "CREATE DATABASE ecommerce_inventory;"
   psql -U postgres -d ecommerce_inventory -f sql/schema.sql
   ```

5. **Generate test data**
   ```bash
   python scripts/generate_test_data.py
   ```

6. **Deploy n8n** (see technical guide for VPS setup)
   ```bash
   docker compose -f config/docker-compose.yml up -d
   ```
   Import workflows from `workflow_json/n8n_workflows_export.json`.

7. **Launch the dashboard**
   ```bash
   cd dashboard
   streamlit run app.py
   ```

## Documentation

See the [Technical Guide](technical_guide/) for complete step-by-step implementation instructions including:
- WooCommerce and Local WP setup
- PostgreSQL star schema design
- n8n workflow configuration (3 workflows)
- VPS deployment with Docker
- Notification channel setup (Gmail, Slack, WhatsApp)
- Dashboard walkthrough

## Technologies

- **Orchestration:** n8n (self-hosted on VPS)
- **Data Source:** WooCommerce REST API
- **Database:** PostgreSQL (star schema)
- **Dashboard:** Streamlit + Plotly
- **Language:** Python 3.13, JavaScript (n8n Code nodes)
- **Deployment:** Docker, Hostinger VPS
- **Notifications:** Gmail, Slack Webhooks, WhatsApp Business API

## Cost

- Development: Free (Local WP + local PostgreSQL + n8n Community)
- Production: ~$5-10/month (Hostinger VPS for n8n + PostgreSQL)

## License

This project is provided for educational purposes.

---

*Part of the Business Automation Library - Code examples for building real-world automation solutions.*
