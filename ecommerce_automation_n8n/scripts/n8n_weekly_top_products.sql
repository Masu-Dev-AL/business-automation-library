-- n8n PostgreSQL Node: Weekly Top Products
-- Returns top 5 products by revenue for the past 7 days

SELECT
    p.product_name,
    p.category,
    SUM(oi.quantity) AS units_sold,
    SUM(oi.line_total) AS revenue,
    COUNT(DISTINCT o.order_fact_id) AS order_count
FROM fact_order_items oi
JOIN fact_orders o ON oi.order_fact_id = o.order_fact_id
JOIN dim_products p ON oi.product_id = p.product_id
WHERE o.order_date >= CURRENT_DATE - INTERVAL '7 days'
    AND o.status NOT IN ('cancelled', 'refunded')
GROUP BY p.product_id, p.product_name, p.category
ORDER BY revenue DESC
LIMIT 5;
