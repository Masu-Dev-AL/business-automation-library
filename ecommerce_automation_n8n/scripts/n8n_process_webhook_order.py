# n8n Code Node: Process WooCommerce Webhook Order
# Input: WooCommerce order.created webhook payload
# Output: List of ordered product IDs + quantities for stock lookup

items = _input.all()

webhook_data = items[0].json

# Webhook wraps payload under "body" — unwrap it
order_data = webhook_data.get("body", webhook_data)

line_items = order_data.get("line_items", [])

product_ids = []
products = []

for item in line_items:
    product_id = item.get("product_id")
    quantity = item.get("quantity", 1)
    name = item.get("name", "Unknown")

    if product_id:
        product_ids.append(str(product_id))
        products.append({
            "woo_product_id": product_id,
            "product_name": name,
            "quantity_ordered": quantity
        })

return [{
    "json": {
        "order_id": order_data.get("id"),
        "order_number": order_data.get("number"),
        "order_date": order_data.get("date_created"),
        "product_ids": ",".join(product_ids),
        "product_count": len(products),
        "products": products
    }
}]
