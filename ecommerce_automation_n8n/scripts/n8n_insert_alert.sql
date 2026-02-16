-- n8n PostgreSQL Node: Insert Inventory Alert
-- Operation: Execute Query
-- Runs once per alert item from Evaluate Stock Alerts output

INSERT INTO inventory_alerts (
    product_id,
    alert_type,
    alert_date,
    current_quantity,
    threshold_quantity,
    is_resolved
)
VALUES (
    {{ $json.product_id }},
    '{{ $json.alert_type }}',
    '{{ $json.alert_date }}'::timestamp,
    {{ $json.quantity_on_hand }},
    {{ $json.reorder_point }},
    false
);
