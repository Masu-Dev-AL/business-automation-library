-- n8n PostgreSQL Node: Weekly Inventory Health
-- Returns stock status breakdown + top products needing reorder

SELECT
    COUNT(*) FILTER (WHERE stock_status = 'Critical') AS critical_count,
    COUNT(*) FILTER (WHERE stock_status = 'Low') AS low_count,
    COUNT(*) FILTER (WHERE stock_status = 'Healthy') AS healthy_count,
    COUNT(*) AS total_products,
    (
        SELECT json_agg(reorder_products)
        FROM (
            SELECT
                product_name,
                category,
                quantity_on_hand,
                reorder_point,
                days_of_inventory,
                stock_status,
                supplier_name,
                lead_time_days
            FROM vw_current_inventory
            WHERE quantity_on_hand <= reorder_point
            ORDER BY quantity_on_hand ASC
            LIMIT 10
        ) reorder_products
    ) AS reorder_needed_products
FROM vw_current_inventory;
