items = _input.all()
transformed = []

for item in items:
    order = item.get('json', {})

    # Parse order date
    order_date = order.get('date_created', '')

    # Calculate fulfillment time if completed
    fulfillment_hours = None
    if order.get('date_completed'):
        # Would need datetime parsing for actual calculation
        fulfillment_hours = 24  # Placeholder

    transformed.append({
        'json': {
            'woo_order_id': order.get('id'),
            'order_date': order_date,
            'status': order.get('status'),
            'total_amount': float(order.get('total') or 0),
            'item_count': len(order.get('line_items', [])),
            'fulfillment_time_hours': fulfillment_hours,
            'shipping_cost': float(order.get('shipping_total') or 0)
        }
    })

return transformed
