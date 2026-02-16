items = _input.all()
transformed = []

for item in items:
    product = item.get('json', {})
    categories = product.get('categories', [])
    category_name = categories[0]['name'] if categories else 'Uncategorized'

    sell_price = float(product.get('regular_price') or 0)

    transformed.append({
        'json': {
            'woo_product_id': product.get('id'),
            'sku': product.get('sku') or f"SKU-{product.get('id')}",
            'product_name': product.get('name'),
            'category': category_name,
            'sell_price': sell_price,
            'cost_price': sell_price * 0.6,
            'is_active': product.get('status') == 'publish',
            'stock_quantity': product.get('stock_quantity')
        }
    })

return transformed
