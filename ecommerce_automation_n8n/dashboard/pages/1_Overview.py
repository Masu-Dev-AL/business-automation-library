import streamlit as st
import plotly.express as px
from db import run_query

st.header("Overview")

# ── Top KPIs ─────────────────────────────────────────────
kpi = run_query("""
    SELECT
        COALESCE(SUM(quantity_on_hand * sell_price), 0) AS inventory_value,
        COALESCE(SUM(quantity_on_hand), 0)              AS total_units,
        COUNT(*)                                         AS active_products,
        COALESCE(AVG(days_of_inventory), 0)             AS avg_days_inventory
    FROM vw_current_inventory
""")

c1, c2, c3, c4 = st.columns(4)
if not kpi.empty:
    c1.metric("Inventory Value", f"${kpi['inventory_value'].iloc[0]:,.0f}")
    c2.metric("Units in Stock", f"{kpi['total_units'].iloc[0]:,.0f}")
    c3.metric("Active Products", int(kpi["active_products"].iloc[0]))
    c4.metric("Avg Days of Inventory", f"{kpi['avg_days_inventory'].iloc[0]:.1f}")

# ── Stock Status Breakdown — donut ───────────────────────
col1, col2 = st.columns(2)

status_df = run_query("""
    SELECT stock_status, COUNT(*) AS count
    FROM vw_current_inventory
    GROUP BY stock_status
""")
if not status_df.empty:
    fig = px.pie(
        status_df,
        names="stock_status",
        values="count",
        title="Stock Status Breakdown",
        hole=0.45,
        color="stock_status",
        color_discrete_map={"Healthy": "#2ecc71", "Low": "#f39c12", "Critical": "#e74c3c"},
    )
    col1.plotly_chart(fig, use_container_width=True)

# ── Daily Orders Trend (last 30 days) ───────────────────
orders_df = run_query("""
    SELECT full_date, order_count, total_revenue
    FROM vw_daily_orders
    WHERE full_date >= CURRENT_DATE - 30
      AND full_date <= CURRENT_DATE
      AND order_count > 0
    ORDER BY full_date
""")
if not orders_df.empty:
    fig_line = px.line(
        orders_df,
        x="full_date",
        y="order_count",
        title="Daily Orders (Last 30 Days)",
        labels={"full_date": "Date", "order_count": "Orders"},
        markers=True,
    )
    col2.plotly_chart(fig_line, use_container_width=True)

# ── Top 5 Products by Revenue ────────────────────────────
top5 = run_query("""
    SELECT product_name, revenue_30d
    FROM vw_product_performance
    WHERE revenue_30d > 0
    ORDER BY revenue_30d DESC
    LIMIT 5
""")
if not top5.empty:
    fig_bar = px.bar(
        top5,
        x="revenue_30d",
        y="product_name",
        orientation="h",
        title="Top 5 Products by Revenue (30 days)",
        labels={"revenue_30d": "Revenue ($)", "product_name": "Product"},
    )
    fig_bar.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Recent Alerts ────────────────────────────────────────
st.subheader("Recent Alerts")
alerts = run_query("""
    SELECT
        a.alert_date,
        p.product_name,
        a.alert_type,
        a.current_quantity,
        a.threshold_quantity,
        a.is_resolved
    FROM inventory_alerts a
    JOIN dim_products p ON a.product_id = p.product_id
    ORDER BY a.alert_date DESC
    LIMIT 10
""")
if not alerts.empty:
    st.dataframe(alerts, use_container_width=True, hide_index=True)
else:
    st.info("No recent alerts.")
