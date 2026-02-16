-- n8n PostgreSQL Node: Insert Inventory Snapshot
-- Operation: Execute Query
-- Runs once per item from Calculate Inventory Metrics output

INSERT INTO fact_inventory_snapshots (
    product_id,
    date_id,
    snapshot_date,
    quantity_on_hand,
    quantity_allocated,
    quantity_available,
    reorder_needed,
    days_of_inventory
)
SELECT
    p.product_id,
    d.date_id,
    '{{ $json.snapshot_date }}'::date,
    {{ $json.quantity_on_hand }},
    {{ $json.quantity_allocated }},
    {{ $json.quantity_available }},
    {{ $json.reorder_needed }},
    {{ $json.days_of_inventory }}
FROM dim_products p
JOIN dim_date d ON d.full_date = '{{ $json.snapshot_date }}'::date
WHERE p.woo_product_id = {{ $json.woo_product_id }}
ON CONFLICT (product_id, snapshot_date) DO UPDATE SET
    quantity_on_hand = EXCLUDED.quantity_on_hand,
    quantity_available = EXCLUDED.quantity_available,
    reorder_needed = EXCLUDED.reorder_needed,
    days_of_inventory = EXCLUDED.days_of_inventory;
