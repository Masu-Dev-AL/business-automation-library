# E-commerce Inventory & Order Fulfillment Pipeline - Project Brief

## Objective
Create a comprehensive technical implementation guide for building an automated e-commerce inventory and order fulfillment monitoring system using n8n, Python, PostgreSQL, and Streamlit. This project demonstrates real-world business automation for my YouTube channel "Business Automation Library."

## Business Value
Small/medium e-commerce businesses need automated inventory management to prevent stockouts (lost sales), reduce overstock (tied-up capital), and optimize fulfillment speed. This pipeline provides real-time inventory monitoring, automated reorder alerts, and fulfillment performance tracking.

## Technical Architecture
- **Data Source:** WooCommerce REST API (real WordPress e-commerce store)
- **Orchestration:** n8n workflow automation (scheduled ETL runs, alerts)
- **Processing:** Python scripts (pandas for transformations, business logic)
- **Storage:** PostgreSQL star schema (dimensions + facts)
- **Visualization:** Streamlit interactive dashboard
- **Alerting:** Email/Slack notifications for critical inventory events

## Core Features to Implement

### 1. Inventory Intelligence
- Stock level tracking across product catalog
- Reorder point calculations: `(avg_daily_sales × supplier_lead_time) + safety_stock`
- Stock velocity analysis (fast-moving vs. slow-moving products)
- Days of inventory remaining: `current_stock / avg_daily_sales`
- Automated low-stock alerts when inventory hits reorder threshold

### 2. Order Fulfillment Analytics
- Order processing time (order received → shipped)
- Fulfillment speed by product category
- Order volume trends and patterns
- Backorder tracking and management
- Customer order history and lifetime value

### 3. Business Automation (n8n Workflows)
- Daily scheduled data extraction from WooCommerce API
- Automated quality checks (missing data, negative inventory, duplicate orders)
- Alert triggers: low stock, out-of-stock, slow-moving inventory, large orders
- Weekly automated reports emailed to stakeholders
- Dashboard refresh triggers

## Database Schema (Star Schema)

**Dimensions:**
- `dim_products` (sku, name, category, cost_price, sell_price, reorder_point, reorder_quantity, supplier_id)
- `dim_customers` (customer_id, email, name, segment, lifetime_value, customer_since)
- `dim_suppliers` (supplier_id, name, lead_time_days, reliability_score)
- `dim_date` (date, year, quarter, month, week, day_of_week)

**Facts:**
- `fact_orders` (order_id, customer_id, product_id, date_id, quantity, total_amount, status, fulfillment_time_hours)
- `fact_inventory_snapshots` (product_id, date_id, quantity_on_hand, quantity_allocated, quantity_available, reorder_needed)
- `fact_inventory_movements` (product_id, date_id, movement_type, quantity, reason)

**Operational:**
- `data_quality_log`, `etl_run_history`, `inventory_alerts`

## Key Python Scripts Needed
1. `extract_woocommerce.py` - API data extraction (products, orders, inventory)
2. `transform_data.py` - Calculate metrics, clean data, apply business logic
3. `load_data.py` - Upsert to PostgreSQL dimensions and facts
4. `data_quality_checks.py` - Validation rules and anomaly detection
5. `calculate_reorder_points.py` - Inventory optimization logic
6. `dashboard/app.py` - Streamlit multi-page dashboard

## Streamlit Dashboard Pages
- **Overview:** KPIs (total inventory value, units in stock, pending orders, stockout risk count)
- **Inventory Health:** Products near reorder point, slow-movers, stock turns, days of inventory charts
- **Order Fulfillment:** Avg fulfillment time, orders by status, fulfillment trends
- **Product Performance:** Best/worst sellers, category analysis, profitability
- **Alerts & Quality:** Recent alerts, data quality check status

## WooCommerce Setup Approach
Use local WordPress with WooCommerce plugin, create 30-50 realistic products across categories (Electronics, Apparel, Home), generate 100-200 test orders over 90 days to simulate real business patterns. This provides authentic API data structure without needing a live production store.
