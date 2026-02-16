-- n8n PostgreSQL Node: Log ETL Run
-- Operation: Execute Query
-- Records the weekly report generation in etl_run_history

INSERT INTO etl_run_history (
    run_type,
    start_time,
    end_time,
    status,
    records_processed,
    error_message
)
VALUES (
    'weekly_report',
    '{{ $json.report_date }}'::timestamp,
    NOW(),
    'success',
    {{ $json.order_count }},
    NULL
);
