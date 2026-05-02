# Business Automation Library
https://www.youtube.com/@Business_Automation_Library
A collection of production-ready automation projects demonstrating real-world business process automation using cloud services, AI/ML, and modern development practices.

## Projects

| Project | Description | Technologies |
|---------|-------------|--------------|
| [Invoice Automation](./invoice_automation_aws/) | Serverless invoice processing with AI data extraction | AWS Lambda, Bedrock, S3, RDS, API Gateway |
| [Support Ticket Automation](./support_ticket_automation_pipedream/) | Webhook-based ticket intake with Claude AI classification (billing/technical/shipping), urgency scoring, Slack routing by category, PostgreSQL audit trail, and SendGrid acknowledgement emails | Pipedream, Claude AI, PostgreSQL, Slack, SendGrid |
| [Lead Scoring & Routing](./lead_scoring_automation_make/) | Typeform-to-CRM pipeline that scores inbound leads with Claude AI (ICP fit + intent 1–10), routes to territory-based Slack channels with rep @mentions, logs AI reasoning to Airtable, and sends personalized Gmail replies | Make.com, Claude AI, Typeform, Airtable, Slack, Gmail |
| [E-commerce Inventory & Fulfillment](./ecommerce_automation_n8n/) | WooCommerce ETL into a PostgreSQL star schema with automated reorder-point alerts via Gmail, Slack, and WhatsApp when stock falls below thresholds, plus a Streamlit analytics dashboard | n8n, PostgreSQL, WooCommerce, Streamlit, Slack, Gmail |
| [Competitor Price Monitor](./competitor_price_monitor_n8n/) | Daily scraper that tracks vitamin product pricing across competitor sites, normalizes to cost-per-serving, logs snapshots to Google Sheets, and delivers weekly Claude AI trend-analysis digests | n8n, Python, FastAPI, Claude AI, Google Sheets |

## About

This repository contains code examples and complete implementations featured on my YouTube channel. Each project includes:

- Complete source code
- Step-by-step technical guide
- Sample data for testing
- Deployment instructions
- Architecture Diagram

## Getting Started

Navigate to any project folder and follow the README instructions for setup and deployment.

## License

These projects are provided for educational purposes.

---

*Subscribe to the channel for video walkthroughs and tutorials!*
