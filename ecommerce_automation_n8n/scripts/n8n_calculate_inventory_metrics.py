from datetime import date

items = _input.all()

DEFAULT_REORDER_POINT = 10
DEFAULT_SAFETY_STOCK = 5
LOOKBACK_DAYS = 30

# Separate products from orders using fields visible in the transform output
# Products have "woo_product_id" + "sell_price", Orders have "woo_order_id"
products = []
orders = []

for item in items:
    data = item.json
    if "woo_order_id" in data:
        orders.append(data)
    elif "woo_product_id" in data:
        products.append(data)

# Estimate avg daily sales across all products
# Transformed orders don't have line_items, so use total item_count
total_items_sold = sum(int(o.get("item_count", 0) or 0) for o in orders)
num_products = max(len(products), 1)
avg_daily_sales_estimate = max((total_items_sold / num_products) / LOOKBACK_DAYS, 0.1)

# Calculate inventory metrics for each product
results = []

for data in products:
    woo_product_id = data.get("woo_product_id")
    product_name = data.get("product_name", "Unknown")

    # Use sell_price to estimate stock value if needed
    sell_price = float(data.get("sell_price", 0) or 0)

    # Stock quantity may not be in transform output - estimate from orders
    # If your Transform Products node includes stock_quantity, this uses it;
    # otherwise falls back to a default
    stock_quantity = int(data.get("stock_quantity", 0) or 0)

    # Avg daily sales: estimated from total order items spread across products
    avg_daily_sales = avg_daily_sales_estimate

    days_of_inventory = round(stock_quantity / avg_daily_sales, 2) if avg_daily_sales > 0 else 999

    reorder_point = int(data.get("reorder_point", DEFAULT_REORDER_POINT))
    safety_stock = int(data.get("safety_stock", DEFAULT_SAFETY_STOCK))
    reorder_needed = stock_quantity <= reorder_point

    if stock_quantity <= safety_stock:
        stock_status = "Critical"
    elif stock_quantity <= reorder_point:
        stock_status = "Low"
    else:
        stock_status = "Healthy"

    results.append({
        "json": {
            "woo_product_id": woo_product_id,
            "product_name": product_name,
            "snapshot_date": date.today().isoformat(),
            "quantity_on_hand": stock_quantity,
            "quantity_allocated": 0,
            "quantity_available": stock_quantity,
            "reorder_needed": reorder_needed,
            "days_of_inventory": days_of_inventory,
            "avg_daily_sales": round(avg_daily_sales, 2),
            "reorder_point": reorder_point,
            "safety_stock": safety_stock,
            "stock_status": stock_status
        }
    })

return results
