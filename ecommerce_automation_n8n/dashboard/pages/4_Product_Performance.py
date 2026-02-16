import streamlit as st
import pandas as pd
import plotly.express as px
from db import run_query

st.header("Product Performance")

perf = run_query("""
    SELECT product_name, category, sell_price, units_sold_30d, revenue_30d, order_count_30d
    FROM vw_product_performance
""")

if perf.empty:
    st.warning("No product performance data available.")
    st.stop()

for col in ["sell_price", "units_sold_30d", "revenue_30d", "order_count_30d"]:
    perf[col] = pd.to_numeric(perf[col], errors="coerce").fillna(0)

# ── Top 10 / Bottom 10 by Revenue ────────────────────────
col1, col2 = st.columns(2)

top10 = perf.nlargest(10, "revenue_30d")
bottom10 = perf[perf["revenue_30d"] > 0].nsmallest(10, "revenue_30d")

fig_top = px.bar(
    top10,
    x="revenue_30d",
    y="product_name",
    orientation="h",
    title="Top 10 Products by Revenue",
    labels={"revenue_30d": "Revenue ($)", "product_name": "Product"},
    color_discrete_sequence=["#2ecc71"],
)
fig_top.update_layout(yaxis=dict(autorange="reversed"))
col1.plotly_chart(fig_top, use_container_width=True)

if not bottom10.empty:
    fig_bot = px.bar(
        bottom10,
        x="revenue_30d",
        y="product_name",
        orientation="h",
        title="Bottom 10 Products by Revenue",
        labels={"revenue_30d": "Revenue ($)", "product_name": "Product"},
        color_discrete_sequence=["#e74c3c"],
    )
    fig_bot.update_layout(yaxis=dict(autorange="reversed"))
    col2.plotly_chart(fig_bot, use_container_width=True)

# ── Category Performance ─────────────────────────────────
cat_perf = perf.groupby("category", as_index=False).agg(
    units_sold=("units_sold_30d", "sum"),
    revenue=("revenue_30d", "sum"),
)
if not cat_perf.empty:
    import plotly.graph_objects as go

    fig_cat = go.Figure()
    fig_cat.add_trace(go.Bar(name="Units Sold", x=cat_perf["category"], y=cat_perf["units_sold"], marker_color="#3498db"))
    fig_cat.add_trace(go.Bar(name="Revenue ($)", x=cat_perf["category"], y=cat_perf["revenue"], marker_color="#e67e22"))
    fig_cat.update_layout(barmode="group", title="Category Performance (30 days)")
    st.plotly_chart(fig_cat, use_container_width=True)

# ── Product Profitability Scatter ────────────────────────
fig_scatter = px.scatter(
    perf[perf["units_sold_30d"] > 0],
    x="sell_price",
    y="units_sold_30d",
    size="revenue_30d",
    color="category",
    hover_name="product_name",
    title="Product Profitability (price vs units sold)",
    labels={"sell_price": "Sell Price ($)", "units_sold_30d": "Units Sold (30d)"},
)
st.plotly_chart(fig_scatter, use_container_width=True)

# ── Detailed Product Table ───────────────────────────────
st.subheader("Product Details")
search = st.text_input("Search products", "")
filtered = perf[perf["product_name"].str.contains(search, case=False, na=False)] if search else perf
st.dataframe(
    filtered.sort_values("revenue_30d", ascending=False),
    use_container_width=True,
    hide_index=True,
)
