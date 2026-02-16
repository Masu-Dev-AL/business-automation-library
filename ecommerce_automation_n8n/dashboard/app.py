import streamlit as st
import plotly.express as px
from datetime import datetime
from db import get_connection, run_query

st.set_page_config(
    page_title="Inventory Dashboard",
    page_icon=":package:",
    layout="wide",
)

# ── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.title("Inventory Dashboard")

    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"Last updated: {datetime.now():%Y-%m-%d %H:%M:%S}")

    conn = get_connection()
    if conn and not conn.closed:
        st.success("DB connected")
    else:
        st.error("DB disconnected")

# ── KPI Metric Cards ────────────────────────────────────
st.header("Dashboard Overview")

snapshot_date = run_query("SELECT MAX(snapshot_date) AS snap_date FROM fact_inventory_snapshots")
if not snapshot_date.empty and snapshot_date["snap_date"].iloc[0] is not None:
    st.info(f"Inventory data from snapshot: **{snapshot_date['snap_date'].iloc[0]}**")
else:
    st.warning("No inventory snapshots found.")

inv = run_query("""
    SELECT
        COALESCE(SUM(quantity_on_hand * sell_price), 0) AS inventory_value,
        COALESCE(SUM(quantity_on_hand), 0)              AS total_units,
        COUNT(*) FILTER (WHERE stock_status = 'Critical') AS stockout_risk
    FROM vw_current_inventory
""")

pending = run_query("""
    SELECT COUNT(*) AS cnt FROM fact_orders WHERE status = 'pending'
""")

c1, c2, c3, c4 = st.columns(4)
if not inv.empty:
    c1.metric("Inventory Value", f"${inv['inventory_value'].iloc[0]:,.0f}")
    c2.metric("Units in Stock", f"{inv['total_units'].iloc[0]:,.0f}")
c3.metric("Pending Orders", int(pending["cnt"].iloc[0]) if not pending.empty else 0)
if not inv.empty:
    c4.metric("Stockout Risk", int(inv["stockout_risk"].iloc[0]))

# ── Quick Summary Charts ────────────────────────────────
col_left, col_right = st.columns(2)

# Stock status distribution — pie
status_df = run_query("""
    SELECT stock_status, COUNT(*) AS count
    FROM vw_current_inventory
    GROUP BY stock_status
""")
if not status_df.empty:
    fig_pie = px.pie(
        status_df,
        names="stock_status",
        values="count",
        title="Stock Status Distribution",
        color="stock_status",
        color_discrete_map={"Healthy": "#2ecc71", "Low": "#f39c12", "Critical": "#e74c3c"},
    )
    col_left.plotly_chart(fig_pie, use_container_width=True)

# Recent order trend — bar (last 14 days)
orders_df = run_query("""
    SELECT full_date, order_count
    FROM vw_daily_orders
    WHERE full_date >= CURRENT_DATE - 30
      AND full_date <= CURRENT_DATE
      AND order_count > 0
    ORDER BY full_date
""")
if not orders_df.empty:
    orders_df = orders_df.sort_values("full_date")
    fig_bar = px.bar(
        orders_df,
        x="full_date",
        y="order_count",
        title="Recent Orders (Last 14 Days)",
        labels={"full_date": "Date", "order_count": "Orders"},
    )
    col_right.plotly_chart(fig_bar, use_container_width=True)
