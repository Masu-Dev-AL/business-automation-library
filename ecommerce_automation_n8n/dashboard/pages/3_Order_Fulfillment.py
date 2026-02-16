import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from db import run_query

st.header("Order Fulfillment")

# ── KPIs ─────────────────────────────────────────────────
kpi = run_query("""
    SELECT
        COUNT(*)                              AS total_orders,
        COALESCE(AVG(total_amount), 0)        AS avg_order_value,
        COALESCE(AVG(fulfillment_time_hours), 0) AS avg_fulfillment_hours
    FROM fact_orders
    WHERE order_date >= CURRENT_DATE - 30
""")

status_counts = run_query("""
    SELECT status, COUNT(*) AS count
    FROM fact_orders
    WHERE order_date >= CURRENT_DATE - 30
    GROUP BY status
    ORDER BY count DESC
""")

c1, c2, c3, c4 = st.columns(4)
if not kpi.empty:
    c1.metric("Total Orders (30d)", int(kpi["total_orders"].iloc[0]))
    c2.metric("Avg Order Value", f"${kpi['avg_order_value'].iloc[0]:,.2f}")
    avg_hrs = float(kpi["avg_fulfillment_hours"].iloc[0])
    c3.metric("Avg Fulfillment Time", f"{avg_hrs:.1f} hrs")
if not status_counts.empty:
    c4.metric("Order Statuses", ", ".join(f"{r['status']}: {r['count']}" for _, r in status_counts.iterrows()))

# ── Orders by Status — donut ─────────────────────────────
col1, col2 = st.columns(2)

if not status_counts.empty:
    fig_donut = px.pie(
        status_counts,
        names="status",
        values="count",
        title="Orders by Status (30 days)",
        hole=0.45,
    )
    col1.plotly_chart(fig_donut, use_container_width=True)

# ── Daily Order Volume + Revenue — dual axis ─────────────
daily = run_query("""
    SELECT full_date, order_count, total_revenue
    FROM vw_daily_orders
    WHERE full_date >= CURRENT_DATE - 30
      AND full_date <= CURRENT_DATE
      AND order_count > 0
    ORDER BY full_date
""")

if not daily.empty:
    fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
    fig_dual.add_trace(
        go.Bar(x=daily["full_date"], y=daily["order_count"], name="Orders", marker_color="#3498db"),
        secondary_y=False,
    )
    fig_dual.add_trace(
        go.Scatter(x=daily["full_date"], y=daily["total_revenue"], name="Revenue ($)", mode="lines+markers",
                   line=dict(color="#e74c3c")),
        secondary_y=True,
    )
    fig_dual.update_layout(title="Daily Orders & Revenue (30 days)")
    fig_dual.update_yaxes(title_text="Order Count", secondary_y=False)
    fig_dual.update_yaxes(title_text="Revenue ($)", secondary_y=True)
    col2.plotly_chart(fig_dual, use_container_width=True)

# ── Fulfillment Time Distribution ────────────────────────
fulfill = run_query("""
    SELECT fulfillment_time_hours
    FROM fact_orders
    WHERE fulfillment_time_hours IS NOT NULL
      AND order_date >= CURRENT_DATE - 30
""")
if not fulfill.empty:
    fig_hist = px.histogram(
        fulfill,
        x="fulfillment_time_hours",
        nbins=20,
        title="Fulfillment Time Distribution (hours)",
        labels={"fulfillment_time_hours": "Hours"},
    )
    st.plotly_chart(fig_hist, use_container_width=True)

# ── Recent Orders Table ──────────────────────────────────
st.subheader("Recent Orders")
recent = run_query("""
    SELECT
        o.woo_order_id AS "Order ID",
        o.order_date   AS "Date",
        o.status       AS "Status",
        o.total_amount AS "Total ($)",
        o.item_count   AS "Items",
        o.fulfillment_time_hours AS "Fulfillment (hrs)"
    FROM fact_orders o
    ORDER BY o.order_date DESC
    LIMIT 20
""")
if not recent.empty:
    st.dataframe(recent, use_container_width=True, hide_index=True)
