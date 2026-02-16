-- n8n PostgreSQL Node: Check Stock Levels for Ordered Products
-- Operation: Execute Query
-- Runs after Process Webhook Order to get current stock vs reorder point

SELECT
    v.product_id,
    v.woo_product_id,
    v.product_name,
    v.category,
    v.quantity_on_hand,
    v.quantity_available,
    v.reorder_point,
    v.safety_stock,
    v.days_of_inventory,
    v.stock_status,
    v.supplier_name,
    v.lead_time_days
FROM vw_current_inventory v
WHERE v.woo_product_id IN ({{ $json.product_ids }});
