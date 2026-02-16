-- =============================================
-- Data Verification Queries
-- Run from VPS: psql -U n8n_user -d ecommerce_inventory -f verify_data.sql
-- Or connect first: psql -U n8n_user -d ecommerce_inventory
-- Then paste queries one at a time
-- =============================================

-- 1. Check row counts across all tables
SELECT 'dim_date' AS table_name, COUNT(*) AS rows FROM dim_date
UNION ALL SELECT 'dim_suppliers', COUNT(*) FROM dim_suppliers
UNION ALL SELECT 'dim_products', COUNT(*) FROM dim_products
UNION ALL SELECT 'dim_customers', COUNT(*) FROM dim_customers
UNION ALL SELECT 'fact_orders', COUNT(*) FROM fact_orders
UNION ALL SELECT 'fact_order_items', COUNT(*) FROM fact_order_items
UNION ALL SELECT 'fact_inventory_snapshots', COUNT(*) FROM fact_inventory_snapshots
UNION ALL SELECT 'fact_inventory_movements', COUNT(*) FROM fact_inventory_movements
UNION ALL SELECT 'inventory_alerts', COUNT(*) FROM inventory_alerts
ORDER BY table_name;

-- 2. Verify dim_products has WooCommerce data
SELECT woo_product_id, sku, product_name, category, sell_price
FROM dim_products
ORDER BY woo_product_id
LIMIT 10;

-- 3. Verify fact_orders has WooCommerce orders
SELECT woo_order_id, order_date, status, total_amount, item_count, fulfillment_time_hours
FROM fact_orders
ORDER BY order_date DESC
LIMIT 10;

-- 4. Verify fact_inventory_snapshots from today's run
SELECT
    s.snapshot_date,
    p.product_name,
    s.quantity_on_hand,
    s.quantity_available,
    s.reorder_needed,
    s.days_of_inventory
FROM fact_inventory_snapshots s
JOIN dim_products p ON s.product_id = p.product_id
WHERE s.snapshot_date = CURRENT_DATE
ORDER BY s.quantity_on_hand ASC;

-- 5. Check for products needing reorder (what the IF node should catch)
SELECT
    p.product_name,
    p.category,
    s.quantity_on_hand,
    p.reorder_point,
    s.days_of_inventory,
    CASE
        WHEN s.quantity_on_hand <= p.safety_stock THEN 'Critical'
        WHEN s.quantity_on_hand <= p.reorder_point THEN 'Low'
        ELSE 'Healthy'
    END AS stock_status
FROM dim_products p
JOIN fact_inventory_snapshots s ON p.product_id = s.product_id
WHERE s.snapshot_date = CURRENT_DATE
  AND s.reorder_needed = true
ORDER BY s.quantity_on_hand ASC;

-- 6. Quick sanity check: do date_ids match correctly?
SELECT
    o.woo_order_id,
    o.order_date,
    d.full_date,
    d.day_name
FROM fact_orders o
JOIN dim_date d ON o.date_id = d.date_id
LIMIT 5;
