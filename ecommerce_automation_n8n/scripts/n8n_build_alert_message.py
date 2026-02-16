from datetime import datetime

items = _input.all()

# Separate critical vs low stock items
critical_items = []
low_items = []

for item in items:
    data = item.json
    if data.get("stock_status") == "Critical":
        critical_items.append(data)
    elif data.get("stock_status") == "Low":
        low_items.append(data)

all_alert_items = critical_items + low_items

if not all_alert_items:
    return []

# Build HTML table rows for email
table_rows = ""
for p in all_alert_items:
    status_color = "#ef4444" if p["stock_status"] == "Critical" else "#f59e0b"
    table_rows += f"""<tr>
        <td style="padding: 10px; border: 1px solid #ddd;">{p["product_name"]}</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{p.get("stock_status")}</td>
        <td style="padding: 10px; border: 1px solid #ddd; color: {status_color}; font-weight: bold;">{p["quantity_on_hand"]}</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{p["reorder_point"]}</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{p["days_of_inventory"]} days</td>
    </tr>"""

email_html = f"""<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
<h2 style="color: #e53e3e;">Low Stock Alert</h2>
<p><strong>{len(all_alert_items)} products</strong> need attention
({len(critical_items)} critical, {len(low_items)} low stock)</p>
<table style="border-collapse: collapse; width: 100%;">
    <tr style="background-color: #2c5282; color: white;">
        <th style="padding: 10px; border: 1px solid #ddd;">Product</th>
        <th style="padding: 10px; border: 1px solid #ddd;">Status</th>
        <th style="padding: 10px; border: 1px solid #ddd;">Current Stock</th>
        <th style="padding: 10px; border: 1px solid #ddd;">Reorder Point</th>
        <th style="padding: 10px; border: 1px solid #ddd;">Days Remaining</th>
    </tr>
    {table_rows}
</table>
<p style="color: #718096; font-size: 12px; margin-top: 30px;">
    Automated alert from E-commerce Inventory System | {datetime.now().strftime("%Y-%m-%d %H:%M")}
</p>
</body>
</html>"""

# Build Slack message
slack_lines = []
for p in all_alert_items:
    emoji = "🔴" if p["stock_status"] == "Critical" else "🟡"
    slack_lines.append(f"{emoji} *{p['product_name']}* — {p['quantity_on_hand']} units ({p['days_of_inventory']} days left)")

slack_text = f"""*Low Stock Alert — {len(all_alert_items)} products need reorder*
{len(critical_items)} critical, {len(low_items)} low stock

{chr(10).join(slack_lines)}"""

# Build WhatsApp message (plain text, no markdown)
wa_lines = []
for p in all_alert_items:
    icon = "[!!]" if p["stock_status"] == "Critical" else "[!]"
    wa_lines.append(f"{icon} {p['product_name']} — {p['quantity_on_hand']} units ({p['days_of_inventory']} days left)")

whatsapp_text = f"""LOW STOCK ALERT — {len(all_alert_items)} products need reorder
{len(critical_items)} critical, {len(low_items)} low stock

{chr(10).join(wa_lines)}

— Inventory System {datetime.now().strftime("%Y-%m-%d %H:%M")}"""

import json

# Pre-build JSON payloads so n8n can pass them directly to HTTP Request nodes
slack_payload = json.dumps({"text": slack_text})
whatsapp_payload = json.dumps({
    "messaging_product": "whatsapp",
    "to": "15551234567",
    "type": "template",
    "template": {
        "name": "inventory_alert",
        "language": {"code": "en_US"},
        "components": [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": whatsapp_text}
                ]
            }
        ]
    }
})

return [{
    "json": {
        "email_subject": f"[ALERT] Low Stock - {len(all_alert_items)} products need attention",
        "email_html": email_html,
        "slack_text": slack_text,
        "slack_payload": slack_payload,
        "whatsapp_text": whatsapp_text,
        "whatsapp_payload": whatsapp_payload,
        "critical_count": len(critical_items),
        "low_count": len(low_items),
        "total_alert_count": len(all_alert_items)
    }
}]
