import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from db import run_query

st.header("Inventory Health")

# ── Inventory Heatmap ────────────────────────────────────
inv = run_query("""
    SELECT product_name, category, stock_status, quantity_on_hand, reorder_point,
           days_of_inventory
    FROM vw_current_inventory
    ORDER BY category, product_name
""")

if not inv.empty:
    import pandas as pd
    inv["quantity_on_hand"] = pd.to_numeric(inv["quantity_on_hand"], errors="coerce").fillna(0).astype(int).clip(lower=0)
    inv["days_of_inventory"] = pd.to_numeric(inv["days_of_inventory"], errors="coerce")

    status_map = {"Critical": 0, "Low": 1, "Healthy": 2}
    inv["status_num"] = inv["stock_status"].map(status_map)

    fig_heat = px.scatter(
        inv,
        x="category",
        y="product_name",
        color="stock_status",
        size="quantity_on_hand",
        title="Inventory Heatmap (size = qty on hand)",
        color_discrete_map={"Healthy": "#2ecc71", "Low": "#f39c12", "Critical": "#e74c3c"},
    )
    fig_heat.update_layout(height=max(400, len(inv) * 22))
    st.plotly_chart(fig_heat, use_container_width=True)

    # ── Products Near Reorder Point ──────────────────────
    st.subheader("Products Near Reorder Point")
    near_reorder = inv[inv["stock_status"].isin(["Low", "Critical"])].sort_values("quantity_on_hand")
    if not near_reorder.empty:
        st.dataframe(
            near_reorder[["product_name", "category", "quantity_on_hand", "reorder_point", "stock_status"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("All products are above reorder point.")

    # ── Days of Inventory Distribution ───────────────────
    valid = inv.dropna(subset=["days_of_inventory"])
    if not valid.empty:
        fig_hist = px.histogram(
            valid,
            x="days_of_inventory",
            nbins=20,
            title="Days of Inventory Distribution",
            labels={"days_of_inventory": "Days of Inventory"},
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    # ── Slow Movers vs Fast Movers ───────────────────────
    col1, col2 = st.columns(2)
    slow = inv[inv["days_of_inventory"] > 60].sort_values("days_of_inventory", ascending=False)
    fast = inv[inv["days_of_inventory"] < 7].sort_values("days_of_inventory")

    with col1:
        st.subheader("Slow Movers (>60 days)")
        if not slow.empty:
            st.dataframe(
                slow[["product_name", "category", "days_of_inventory", "quantity_on_hand"]],
                use_container_width=True, hide_index=True,
            )
        else:
            st.info("No slow movers.")

    with col2:
        st.subheader("Fast Movers (<7 days)")
        if not fast.empty:
            st.dataframe(
                fast[["product_name", "category", "days_of_inventory", "quantity_on_hand"]],
                use_container_width=True, hide_index=True,
            )
        else:
            st.info("No fast movers.")

# ── Stock Level Trends (last 30 snapshots) ───────────────
st.subheader("Stock Level Trends")
products_list = run_query("SELECT DISTINCT product_name FROM dim_products WHERE is_active = true ORDER BY product_name")
if not products_list.empty:
    selected = st.multiselect("Select products", products_list["product_name"].tolist(), default=products_list["product_name"].tolist()[:3])
    if selected:
        placeholders = ", ".join(["%s"] * len(selected))
        trends = run_query(f"""
            SELECT s.snapshot_date, p.product_name, s.quantity_on_hand
            FROM fact_inventory_snapshots s
            JOIN dim_products p ON s.product_id = p.product_id
            WHERE p.product_name IN ({placeholders})
            ORDER BY s.snapshot_date DESC
            LIMIT {len(selected) * 30}
        """, tuple(selected))
        if not trends.empty:
            trends = trends.sort_values("snapshot_date")
            fig_trend = px.line(
                trends,
                x="snapshot_date",
                y="quantity_on_hand",
                color="product_name",
                title="Stock Levels Over Time",
                labels={"snapshot_date": "Date", "quantity_on_hand": "Qty on Hand"},
            )
            st.plotly_chart(fig_trend, use_container_width=True)
