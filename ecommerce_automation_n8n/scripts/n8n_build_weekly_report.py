# n8n Code Node: Build Weekly Summary Report (HTML Email)
# Input: Three query results — order stats, inventory health, top products
# Output: Styled HTML email body + subject line

from datetime import datetime

items = _input.all()

# n8n passes all upstream node results — extract each
# Item 0: Weekly Order Stats
# Item 1: Inventory Health
# Item 2: Top Products (may be multiple rows)
order_stats = items[0].json
inventory = items[1].json
top_products = [item.json for item in items[2:]] if len(items) > 2 else []

# Parse order stats
order_count = order_stats.get("order_count", 0)
total_revenue = float(order_stats.get("total_revenue", 0))
avg_order_value = float(order_stats.get("avg_order_value", 0))
total_items_sold = order_stats.get("total_items_sold", 0)
period_start = str(order_stats.get("period_start", "N/A"))[:10]
period_end = str(order_stats.get("period_end", "N/A"))[:10]

# Parse inventory health
critical_count = int(inventory.get("critical_count", 0))
low_count = int(inventory.get("low_count", 0))
healthy_count = int(inventory.get("healthy_count", 0))
total_products = int(inventory.get("total_products", 0))
reorder_products = inventory.get("reorder_needed_products") or []
if isinstance(reorder_products, str):
    import json
    reorder_products = json.loads(reorder_products)

# Build top products table rows
top_product_rows = ""
for i, p in enumerate(top_products, 1):
    top_product_rows += f"""<tr>
        <td style="padding: 8px 12px; border: 1px solid #e2e8f0;">{i}</td>
        <td style="padding: 8px 12px; border: 1px solid #e2e8f0;">{p.get("product_name", "")}</td>
        <td style="padding: 8px 12px; border: 1px solid #e2e8f0;">{p.get("category", "")}</td>
        <td style="padding: 8px 12px; border: 1px solid #e2e8f0;">{p.get("units_sold", 0)}</td>
        <td style="padding: 8px 12px; border: 1px solid #e2e8f0;">${float(p.get("revenue", 0)):,.2f}</td>
    </tr>"""

if not top_product_rows:
    top_product_rows = '<tr><td colspan="5" style="padding: 12px; text-align: center; color: #718096;">No sales this week</td></tr>'

# Build reorder needed table rows
reorder_rows = ""
for p in reorder_products:
    status_color = "#ef4444" if p.get("stock_status") == "Critical" else "#f59e0b"
    reorder_rows += f"""<tr>
        <td style="padding: 8px 12px; border: 1px solid #e2e8f0;">{p.get("product_name", "")}</td>
        <td style="padding: 8px 12px; border: 1px solid #e2e8f0; color: {status_color}; font-weight: bold;">{p.get("stock_status", "")}</td>
        <td style="padding: 8px 12px; border: 1px solid #e2e8f0;">{p.get("quantity_on_hand", 0)}</td>
        <td style="padding: 8px 12px; border: 1px solid #e2e8f0;">{p.get("reorder_point", 0)}</td>
        <td style="padding: 8px 12px; border: 1px solid #e2e8f0;">{p.get("supplier_name", "N/A")}</td>
    </tr>"""

if not reorder_rows:
    reorder_rows = '<tr><td colspan="5" style="padding: 12px; text-align: center; color: #38a169;">All products above reorder point</td></tr>'

# Inventory health bar (visual percentages)
health_pct = round(healthy_count / total_products * 100) if total_products else 0
low_pct = round(low_count / total_products * 100) if total_products else 0
critical_pct = round(critical_count / total_products * 100) if total_products else 0

report_date = datetime.now().strftime("%B %d, %Y")
week_label = f"{period_start} to {period_end}"

email_html = f"""<html>
<body style="font-family: Arial, sans-serif; background-color: #f7fafc; padding: 20px; margin: 0;">
<div style="max-width: 700px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

    <!-- Header -->
    <div style="background: linear-gradient(135deg, #2c5282, #2b6cb0); padding: 24px 32px; color: white;">
        <h1 style="margin: 0; font-size: 22px;">Weekly Inventory Report</h1>
        <p style="margin: 4px 0 0; opacity: 0.85; font-size: 14px;">{week_label}</p>
    </div>

    <div style="padding: 24px 32px;">

    <!-- Order Summary -->
    <h2 style="color: #2d3748; font-size: 18px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">Order Summary</h2>
    <table style="width: 100%; margin-bottom: 24px;">
        <tr>
            <td style="padding: 12px; text-align: center; background: #ebf8ff; border-radius: 6px; margin: 4px;">
                <div style="font-size: 28px; font-weight: bold; color: #2b6cb0;">{order_count}</div>
                <div style="font-size: 12px; color: #718096;">Orders</div>
            </td>
            <td style="width: 8px;"></td>
            <td style="padding: 12px; text-align: center; background: #f0fff4; border-radius: 6px;">
                <div style="font-size: 28px; font-weight: bold; color: #38a169;">${total_revenue:,.2f}</div>
                <div style="font-size: 12px; color: #718096;">Revenue</div>
            </td>
            <td style="width: 8px;"></td>
            <td style="padding: 12px; text-align: center; background: #faf5ff; border-radius: 6px;">
                <div style="font-size: 28px; font-weight: bold; color: #805ad5;">${avg_order_value:,.2f}</div>
                <div style="font-size: 12px; color: #718096;">Avg Order</div>
            </td>
            <td style="width: 8px;"></td>
            <td style="padding: 12px; text-align: center; background: #fffbeb; border-radius: 6px;">
                <div style="font-size: 28px; font-weight: bold; color: #d69e2e;">{total_items_sold}</div>
                <div style="font-size: 12px; color: #718096;">Items Sold</div>
            </td>
        </tr>
    </table>

    <!-- Top Products -->
    <h2 style="color: #2d3748; font-size: 18px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">Top Products This Week</h2>
    <table style="border-collapse: collapse; width: 100%; margin-bottom: 24px;">
        <tr style="background-color: #2c5282; color: white;">
            <th style="padding: 8px 12px; border: 1px solid #2c5282;">#</th>
            <th style="padding: 8px 12px; border: 1px solid #2c5282;">Product</th>
            <th style="padding: 8px 12px; border: 1px solid #2c5282;">Category</th>
            <th style="padding: 8px 12px; border: 1px solid #2c5282;">Units</th>
            <th style="padding: 8px 12px; border: 1px solid #2c5282;">Revenue</th>
        </tr>
        {top_product_rows}
    </table>

    <!-- Inventory Health -->
    <h2 style="color: #2d3748; font-size: 18px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">Inventory Health</h2>
    <div style="display: flex; height: 24px; border-radius: 12px; overflow: hidden; margin-bottom: 12px;">
        <div style="width: {health_pct}%; background: #38a169;"></div>
        <div style="width: {low_pct}%; background: #f59e0b;"></div>
        <div style="width: {critical_pct}%; background: #ef4444;"></div>
    </div>
    <p style="font-size: 13px; color: #4a5568; margin-top: 4px;">
        <span style="color: #38a169;">&#9679;</span> Healthy: {healthy_count} ({health_pct}%)
        &nbsp;&nbsp;
        <span style="color: #f59e0b;">&#9679;</span> Low: {low_count} ({low_pct}%)
        &nbsp;&nbsp;
        <span style="color: #ef4444;">&#9679;</span> Critical: {critical_count} ({critical_pct}%)
    </p>

    <!-- Reorder Needed -->
    <h2 style="color: #2d3748; font-size: 18px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">Products Needing Reorder</h2>
    <table style="border-collapse: collapse; width: 100%; margin-bottom: 24px;">
        <tr style="background-color: #e53e3e; color: white;">
            <th style="padding: 8px 12px; border: 1px solid #e53e3e;">Product</th>
            <th style="padding: 8px 12px; border: 1px solid #e53e3e;">Status</th>
            <th style="padding: 8px 12px; border: 1px solid #e53e3e;">Stock</th>
            <th style="padding: 8px 12px; border: 1px solid #e53e3e;">Reorder Pt</th>
            <th style="padding: 8px 12px; border: 1px solid #e53e3e;">Supplier</th>
        </tr>
        {reorder_rows}
    </table>

    </div>

    <!-- Footer -->
    <div style="background: #f7fafc; padding: 16px 32px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #a0aec0;">
        Automated weekly report from E-commerce Inventory System | Generated {report_date}
    </div>

</div>
</body>
</html>"""

email_subject = f"Weekly Inventory Report — {week_label} | {order_count} orders, ${total_revenue:,.0f} revenue"

return [{
    "json": {
        "email_subject": email_subject,
        "email_html": email_html,
        "order_count": order_count,
        "total_revenue": total_revenue,
        "critical_count": critical_count,
        "low_count": low_count,
        "report_date": report_date
    }
}]
