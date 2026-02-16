# n8n Code Node: Evaluate Stock Alerts
# Input: Stock level query results from vw_current_inventory
# Output: Alert list for products below reorder point

from datetime import datetime

items = _input.all()

alerts = []

for item in items:
    data = item.json
    quantity = int(data.get("quantity_on_hand", 0) or 0)
    reorder_point = int(data.get("reorder_point", 10))
    safety_stock = int(data.get("safety_stock", 5))

    if quantity <= reorder_point:
        if quantity <= safety_stock:
            alert_type = "out_of_stock" if quantity == 0 else "low_stock"
            stock_status = "Critical"
        else:
            alert_type = "low_stock"
            stock_status = "Low"

        alerts.append({
            "product_id": data.get("product_id"),
            "woo_product_id": data.get("woo_product_id"),
            "product_name": data.get("product_name"),
            "category": data.get("category"),
            "quantity_on_hand": quantity,
            "reorder_point": reorder_point,
            "safety_stock": safety_stock,
            "days_of_inventory": data.get("days_of_inventory", 0),
            "stock_status": stock_status,
            "alert_type": alert_type,
            "supplier_name": data.get("supplier_name"),
            "lead_time_days": data.get("lead_time_days"),
            "alert_date": datetime.now().isoformat()
        })

# Build summary counts
critical_count = sum(1 for a in alerts if a["stock_status"] == "Critical")
low_count = sum(1 for a in alerts if a["stock_status"] == "Low")

# Return each alert as a separate item so downstream nodes run once per alert
# Include summary counts on every item for the IF node and Build Alert Message
results = []
for alert in alerts:
    alert["alert_count"] = len(alerts)
    alert["critical_count"] = critical_count
    alert["low_count"] = low_count
    alert["checked_at"] = datetime.now().isoformat()
    results.append({"json": alert})

if not results:
    return [{"json": {"alert_count": 0, "critical_count": 0, "low_count": 0}}]

return results
