-- =============================================
-- E-commerce Inventory Star Schema
-- PostgreSQL Database Schema
-- =============================================

-- =============================================
-- DIMENSION TABLES
-- =============================================

-- Date dimension for time-based analysis
CREATE TABLE IF NOT EXISTS dim_date (
    date_id SERIAL PRIMARY KEY,
    full_date DATE UNIQUE NOT NULL,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name VARCHAR(20),
    week INTEGER,
    day_of_week INTEGER,
    day_name VARCHAR(20),
    is_weekend BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers dimension
CREATE TABLE IF NOT EXISTS dim_suppliers (
    supplier_id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    lead_time_days INTEGER DEFAULT 7,
    reliability_score DECIMAL(3,2) DEFAULT 0.95,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products dimension
CREATE TABLE IF NOT EXISTS dim_products (
    product_id SERIAL PRIMARY KEY,
    woo_product_id INTEGER UNIQUE,
    sku VARCHAR(100),
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    cost_price DECIMAL(10,2),
    sell_price DECIMAL(10,2),
    reorder_point INTEGER DEFAULT 10,
    reorder_quantity INTEGER DEFAULT 50,
    safety_stock INTEGER DEFAULT 5,
    supplier_id INTEGER REFERENCES dim_suppliers(supplier_id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customers dimension
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id SERIAL PRIMARY KEY,
    woo_customer_id INTEGER UNIQUE,
    email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    segment VARCHAR(50) DEFAULT 'Regular',
    lifetime_value DECIMAL(12,2) DEFAULT 0,
    total_orders INTEGER DEFAULT 0,
    customer_since DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- FACT TABLES
-- =============================================

-- Orders fact table
CREATE TABLE IF NOT EXISTS fact_orders (
    order_fact_id SERIAL PRIMARY KEY,
    woo_order_id INTEGER UNIQUE,
    customer_id INTEGER REFERENCES dim_customers(customer_id),
    date_id INTEGER REFERENCES dim_date(date_id),
    order_date TIMESTAMP,
    status VARCHAR(50),
    total_amount DECIMAL(12,2),
    item_count INTEGER,
    fulfillment_time_hours INTEGER,
    shipping_cost DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order line items (bridge table)
CREATE TABLE IF NOT EXISTS fact_order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_fact_id INTEGER REFERENCES fact_orders(order_fact_id),
    product_id INTEGER REFERENCES dim_products(product_id),
    quantity INTEGER,
    unit_price DECIMAL(10,2),
    line_total DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily inventory snapshots
CREATE TABLE IF NOT EXISTS fact_inventory_snapshots (
    snapshot_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES dim_products(product_id),
    date_id INTEGER REFERENCES dim_date(date_id),
    snapshot_date DATE,
    quantity_on_hand INTEGER,
    quantity_allocated INTEGER DEFAULT 0,
    quantity_available INTEGER,
    reorder_needed BOOLEAN DEFAULT FALSE,
    days_of_inventory DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, snapshot_date)
);

-- Inventory movements (receipts, sales, adjustments)
CREATE TABLE IF NOT EXISTS fact_inventory_movements (
    movement_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES dim_products(product_id),
    date_id INTEGER REFERENCES dim_date(date_id),
    movement_date TIMESTAMP,
    movement_type VARCHAR(50),  -- 'sale', 'receipt', 'adjustment', 'return'
    quantity INTEGER,           -- negative for outbound
    reason VARCHAR(255),
    reference_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- OPERATIONAL TABLES
-- =============================================

-- ETL run history
CREATE TABLE IF NOT EXISTS etl_run_history (
    run_id SERIAL PRIMARY KEY,
    run_type VARCHAR(50),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(20),
    records_processed INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data quality log
CREATE TABLE IF NOT EXISTS data_quality_log (
    log_id SERIAL PRIMARY KEY,
    check_name VARCHAR(100),
    check_date TIMESTAMP,
    status VARCHAR(20),
    records_checked INTEGER,
    records_failed INTEGER,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory alerts
CREATE TABLE IF NOT EXISTS inventory_alerts (
    alert_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES dim_products(product_id),
    alert_type VARCHAR(50),     -- 'low_stock', 'out_of_stock', 'slow_moving'
    alert_date TIMESTAMP,
    current_quantity INTEGER,
    threshold_quantity INTEGER,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- INDEXES FOR PERFORMANCE
-- =============================================

CREATE INDEX IF NOT EXISTS idx_orders_date ON fact_orders(date_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON fact_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON fact_orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON fact_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_inventory_product ON fact_inventory_snapshots(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_date ON fact_inventory_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_movements_product ON fact_inventory_movements(product_id);
CREATE INDEX IF NOT EXISTS idx_movements_type ON fact_inventory_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_products_category ON dim_products(category);
CREATE INDEX IF NOT EXISTS idx_products_sku ON dim_products(sku);
CREATE INDEX IF NOT EXISTS idx_alerts_product ON inventory_alerts(product_id);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON inventory_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON inventory_alerts(is_resolved);

-- =============================================
-- POPULATE DATE DIMENSION
-- =============================================

-- Populate dim_date for 2 years (past year + next year)
INSERT INTO dim_date (full_date, year, quarter, month, month_name, week, day_of_week, day_name, is_weekend)
SELECT
    d::date as full_date,
    EXTRACT(year FROM d) as year,
    EXTRACT(quarter FROM d) as quarter,
    EXTRACT(month FROM d) as month,
    TO_CHAR(d, 'Month') as month_name,
    EXTRACT(week FROM d) as week,
    EXTRACT(dow FROM d) as day_of_week,
    TO_CHAR(d, 'Day') as day_name,
    EXTRACT(dow FROM d) IN (0, 6) as is_weekend
FROM generate_series(
    DATE '2025-01-01',
    DATE '2026-12-31',
    '1 day'::interval
) d
ON CONFLICT (full_date) DO NOTHING;

-- =============================================
-- SEED DATA: SAMPLE SUPPLIERS
-- =============================================

INSERT INTO dim_suppliers (supplier_name, contact_email, contact_phone, lead_time_days, reliability_score)
VALUES
    ('TechSource Inc', 'orders@techsource.com', '555-0101', 5, 0.98),
    ('Fashion Forward Ltd', 'supply@fashionforward.com', '555-0102', 7, 0.95),
    ('HomeGoods Wholesale', 'orders@homegoodswholesale.com', '555-0103', 4, 0.97),
    ('Global Electronics', 'purchasing@globalelec.com', '555-0104', 10, 0.92),
    ('Quick Ship Apparel', 'orders@quickshipapparel.com', '555-0105', 3, 0.99)
ON CONFLICT DO NOTHING;

-- =============================================
-- USEFUL VIEWS
-- =============================================

-- View: Current inventory status
CREATE OR REPLACE VIEW vw_current_inventory AS
SELECT
    p.product_id,
    p.woo_product_id,
    p.sku,
    p.product_name,
    p.category,
    p.sell_price,
    p.reorder_point,
    p.safety_stock,
    s.quantity_on_hand,
    s.quantity_available,
    s.days_of_inventory,
    s.reorder_needed,
    CASE
        WHEN s.quantity_on_hand <= p.safety_stock THEN 'Critical'
        WHEN s.quantity_on_hand <= p.reorder_point THEN 'Low'
        ELSE 'Healthy'
    END as stock_status,
    sup.supplier_name,
    sup.lead_time_days
FROM dim_products p
LEFT JOIN fact_inventory_snapshots s ON p.product_id = s.product_id
    AND s.snapshot_date = (SELECT MAX(snapshot_date) FROM fact_inventory_snapshots)
LEFT JOIN dim_suppliers sup ON p.supplier_id = sup.supplier_id
WHERE p.is_active = true;

-- View: Order summary by date
CREATE OR REPLACE VIEW vw_daily_orders AS
SELECT
    d.full_date,
    d.day_name,
    d.is_weekend,
    COUNT(DISTINCT o.woo_order_id) as order_count,
    SUM(o.total_amount) as total_revenue,
    AVG(o.total_amount) as avg_order_value,
    SUM(o.item_count) as total_items
FROM dim_date d
LEFT JOIN fact_orders o ON d.date_id = o.date_id
WHERE d.full_date >= CURRENT_DATE - 90
GROUP BY d.date_id, d.full_date, d.day_name, d.is_weekend
ORDER BY d.full_date DESC;

-- View: Product performance
CREATE OR REPLACE VIEW vw_product_performance AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.sell_price,
    COALESCE(SUM(oi.quantity), 0) as units_sold_30d,
    COALESCE(SUM(oi.line_total), 0) as revenue_30d,
    COUNT(DISTINCT o.order_fact_id) as order_count_30d
FROM dim_products p
LEFT JOIN fact_order_items oi ON p.product_id = oi.product_id
LEFT JOIN fact_orders o ON oi.order_fact_id = o.order_fact_id
    AND o.order_date >= CURRENT_DATE - 30
WHERE p.is_active = true
GROUP BY p.product_id, p.product_name, p.category, p.sell_price
ORDER BY revenue_30d DESC;

COMMENT ON TABLE dim_products IS 'Product dimension table containing product attributes';
COMMENT ON TABLE dim_customers IS 'Customer dimension table for customer analytics';
COMMENT ON TABLE dim_date IS 'Date dimension for time-based analysis';
COMMENT ON TABLE dim_suppliers IS 'Supplier dimension for inventory management';
COMMENT ON TABLE fact_orders IS 'Order fact table containing order transactions';
COMMENT ON TABLE fact_order_items IS 'Order line items bridge table';
COMMENT ON TABLE fact_inventory_snapshots IS 'Daily inventory level snapshots';
COMMENT ON TABLE fact_inventory_movements IS 'Inventory movement transactions';
