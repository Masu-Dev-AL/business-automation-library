import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
from db import get_connection, run_query

st.header("Alerts & Data Quality")

# ── Active Alerts by Type ────────────────────────────────
st.subheader("Active Alerts")
alert_counts = run_query("""
    SELECT alert_type, COUNT(*) AS count
    FROM inventory_alerts
    WHERE is_resolved = false
    GROUP BY alert_type
    ORDER BY count DESC
""")

if not alert_counts.empty:
    c1, c2, c3 = st.columns(3)
    type_map = {"low_stock": c1, "out_of_stock": c2, "slow_moving": c3}
    for _, row in alert_counts.iterrows():
        col = type_map.get(row["alert_type"])
        if col:
            col.metric(row["alert_type"].replace("_", " ").title(), int(row["count"]))
else:
    st.success("No active alerts.")

# ── Alert History Timeline ───────────────────────────────
alert_history = run_query("""
    SELECT a.alert_date, a.alert_type, p.product_name, a.is_resolved
    FROM inventory_alerts a
    JOIN dim_products p ON a.product_id = p.product_id
    ORDER BY a.alert_date DESC
    LIMIT 100
""")
if not alert_history.empty:
    fig_timeline = px.scatter(
        alert_history,
        x="alert_date",
        y="alert_type",
        color="is_resolved",
        hover_data=["product_name"],
        title="Alert History Timeline",
        labels={"alert_date": "Date", "alert_type": "Alert Type", "is_resolved": "Resolved"},
        color_discrete_map={True: "#2ecc71", False: "#e74c3c"},
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

# ── Data Quality Checks ─────────────────────────────────
st.subheader("Data Quality Log")
quality = run_query("""
    SELECT check_name, check_date, status, records_checked, records_failed, details
    FROM data_quality_log
    ORDER BY check_date DESC
    LIMIT 20
""")
if not quality.empty:
    st.dataframe(quality, use_container_width=True, hide_index=True)
else:
    st.info("No data quality checks recorded yet.")

# ── ETL Run History ──────────────────────────────────────
st.subheader("ETL Run History")
etl = run_query("""
    SELECT run_type, start_time, end_time, status, records_processed, error_message
    FROM etl_run_history
    ORDER BY start_time DESC
    LIMIT 20
""")
if not etl.empty:
    st.dataframe(etl, use_container_width=True, hide_index=True)
else:
    st.info("No ETL runs recorded yet.")

# ── Manual Quality Check ─────────────────────────────────
st.subheader("Run Quality Check")
if st.button("Run Basic Quality Checks"):
    conn = get_connection()
    if conn is None:
        st.error("No database connection.")
    else:
        checks = [
            ("Products without price", "SELECT COUNT(*) FROM dim_products WHERE sell_price IS NULL AND is_active = true"),
            ("Products without supplier", "SELECT COUNT(*) FROM dim_products WHERE supplier_id IS NULL AND is_active = true"),
            ("Orders without customer", "SELECT COUNT(*) FROM fact_orders WHERE customer_id IS NULL"),
            ("Negative inventory", "SELECT COUNT(*) FROM fact_inventory_snapshots WHERE quantity_on_hand < 0"),
            ("Duplicate orders", "SELECT COUNT(*) - COUNT(DISTINCT woo_order_id) FROM fact_orders"),
        ]
        results = []
        for name, sql in checks:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    count = cur.fetchone()[0]
                results.append({"Check": name, "Issues Found": count, "Status": "PASS" if count == 0 else "FAIL"})
            except Exception as e:
                results.append({"Check": name, "Issues Found": "-", "Status": f"ERROR: {e}"})

        results_df = pd.DataFrame(results)
        st.dataframe(results_df, use_container_width=True, hide_index=True)

        passed = sum(1 for r in results if r["Status"] == "PASS")
        st.info(f"{passed}/{len(results)} checks passed.")
