-- n8n PostgreSQL Node: Weekly Order Statistics
-- Returns order count, revenue, and avg order value for past 7 days

SELECT
    COUNT(DISTINCT o.woo_order_id) AS order_count,
    COALESCE(SUM(o.total_amount), 0) AS total_revenue,
    COALESCE(ROUND(AVG(o.total_amount), 2), 0) AS avg_order_value,
    COALESCE(SUM(o.item_count), 0) AS total_items_sold,
    MIN(o.order_date)::date AS period_start,
    MAX(o.order_date)::date AS period_end
FROM fact_orders o
WHERE o.order_date >= CURRENT_DATE - INTERVAL '7 days'
    AND o.status NOT IN ('cancelled', 'refunded');
