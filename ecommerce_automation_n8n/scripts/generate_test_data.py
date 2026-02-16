"""
Test Data Generator for WooCommerce
Creates sample products and orders for testing the inventory pipeline
"""
import os
import requests
from requests.auth import HTTPBasicAuth
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
import urllib3

# Disable SSL warnings for local development (self-signed certs)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv('config/.env')

# SSL verification - set to False for local development with self-signed certs
SSL_VERIFY = False

# WooCommerce API credentials
WC_URL = os.getenv('WC_URL', 'http://ecommerce-test.local/wp-json/wc/v3')
WC_KEY = os.getenv('WC_CONSUMER_KEY')
WC_SECRET = os.getenv('WC_CONSUMER_SECRET')

auth = HTTPBasicAuth(WC_KEY, WC_SECRET)

# Sample product categories with products
CATEGORIES = [
    {"name": "Electronics", "products": [
        {"name": "Wireless Earbuds Pro", "price": "79.99", "stock": 45, "sku": "ELEC-001"},
        {"name": "USB-C Hub 7-in-1", "price": "49.99", "stock": 30, "sku": "ELEC-002"},
        {"name": "Bluetooth Speaker", "price": "129.99", "stock": 25, "sku": "ELEC-003"},
        {"name": "Laptop Stand Aluminum", "price": "59.99", "stock": 50, "sku": "ELEC-004"},
        {"name": "Webcam HD 1080p", "price": "89.99", "stock": 20, "sku": "ELEC-005"},
        {"name": "Wireless Mouse", "price": "34.99", "stock": 60, "sku": "ELEC-006"},
        {"name": "Mechanical Keyboard", "price": "149.99", "stock": 15, "sku": "ELEC-007"},
        {"name": "USB Flash Drive 128GB", "price": "24.99", "stock": 100, "sku": "ELEC-008"},
        {"name": "Phone Charger Fast", "price": "29.99", "stock": 80, "sku": "ELEC-009"},
        {"name": "HDMI Cable 6ft", "price": "14.99", "stock": 120, "sku": "ELEC-010"},
    ]},
    {"name": "Apparel", "products": [
        {"name": "Cotton T-Shirt Classic", "price": "24.99", "stock": 100, "sku": "APRL-001"},
        {"name": "Denim Jeans Slim", "price": "69.99", "stock": 60, "sku": "APRL-002"},
        {"name": "Running Shoes Pro", "price": "119.99", "stock": 35, "sku": "APRL-003"},
        {"name": "Winter Jacket Warm", "price": "149.99", "stock": 25, "sku": "APRL-004"},
        {"name": "Baseball Cap Logo", "price": "19.99", "stock": 80, "sku": "APRL-005"},
        {"name": "Hoodie Zip-Up", "price": "54.99", "stock": 45, "sku": "APRL-006"},
        {"name": "Polo Shirt Premium", "price": "39.99", "stock": 55, "sku": "APRL-007"},
        {"name": "Shorts Athletic", "price": "29.99", "stock": 70, "sku": "APRL-008"},
        {"name": "Socks Pack 6", "price": "16.99", "stock": 150, "sku": "APRL-009"},
        {"name": "Belt Leather", "price": "34.99", "stock": 40, "sku": "APRL-010"},
    ]},
    {"name": "Home & Kitchen", "products": [
        {"name": "Coffee Maker 12-Cup", "price": "89.99", "stock": 40, "sku": "HOME-001"},
        {"name": "Throw Blanket Soft", "price": "39.99", "stock": 55, "sku": "HOME-002"},
        {"name": "LED Desk Lamp", "price": "34.99", "stock": 45, "sku": "HOME-003"},
        {"name": "Kitchen Scale Digital", "price": "29.99", "stock": 30, "sku": "HOME-004"},
        {"name": "Storage Bins Set 3", "price": "44.99", "stock": 65, "sku": "HOME-005"},
        {"name": "Cutting Board Bamboo", "price": "24.99", "stock": 50, "sku": "HOME-006"},
        {"name": "Water Bottle Insulated", "price": "27.99", "stock": 90, "sku": "HOME-007"},
        {"name": "Knife Set 5-Piece", "price": "79.99", "stock": 25, "sku": "HOME-008"},
        {"name": "Towel Set Bath", "price": "49.99", "stock": 35, "sku": "HOME-009"},
        {"name": "Candle Scented Large", "price": "22.99", "stock": 75, "sku": "HOME-010"},
    ]},
]

# Sample customer names for orders
FIRST_NAMES = ["John", "Jane", "Michael", "Sarah", "David", "Emma", "Chris", "Lisa", "James", "Amy",
               "Robert", "Emily", "William", "Jessica", "Daniel", "Ashley", "Thomas", "Nicole", "Mark", "Rachel"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Martinez", "Wilson",
              "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White", "Harris"]


def create_categories():
    """Create product categories in WooCommerce"""
    print("Creating categories...")
    category_ids = {}

    for category in CATEGORIES:
        try:
            response = requests.post(
                f"{WC_URL}/products/categories",
                auth=auth,
                json={"name": category["name"]},
                verify=SSL_VERIFY
            )
            if response.status_code in [200, 201]:
                cat_id = response.json().get("id")
                category_ids[category["name"]] = cat_id
                print(f"  Created category: {category['name']} (ID: {cat_id})")
            elif response.status_code == 400 and "term_exists" in response.text:
                # Category already exists, get its ID
                existing = requests.get(
                    f"{WC_URL}/products/categories",
                    auth=auth,
                    params={"search": category["name"]},
                    verify=SSL_VERIFY
                )
                if existing.status_code == 200:
                    cats = existing.json()
                    for cat in cats:
                        if cat["name"] == category["name"]:
                            category_ids[category["name"]] = cat["id"]
                            print(f"  Category exists: {category['name']} (ID: {cat['id']})")
                            break
            else:
                print(f"  Error creating category {category['name']}: {response.text}")
        except Exception as e:
            print(f"  Exception creating category: {e}")

    return category_ids


def create_products(category_ids):
    """Create sample products via WooCommerce API"""
    print("\nCreating products...")
    created_products = []

    for category in CATEGORIES:
        cat_id = category_ids.get(category["name"])
        if not cat_id:
            print(f"  Skipping {category['name']} - no category ID")
            continue

        for product in category["products"]:
            try:
                # Check if product already exists by SKU
                existing = requests.get(
                    f"{WC_URL}/products",
                    auth=auth,
                    params={"sku": product["sku"]},
                    verify=SSL_VERIFY
                )
                if existing.status_code == 200 and existing.json():
                    print(f"  Product exists: {product['name']}")
                    created_products.append(existing.json()[0])
                    continue

                response = requests.post(
                    f"{WC_URL}/products",
                    auth=auth,
                    json={
                        "name": product["name"],
                        "type": "simple",
                        "regular_price": product["price"],
                        "sku": product["sku"],
                        "manage_stock": True,
                        "stock_quantity": product["stock"],
                        "stock_status": "instock",
                        "categories": [{"id": cat_id}],
                        "description": f"High-quality {product['name']} from our {category['name']} collection.",
                        "short_description": f"Premium {product['name']}"
                    },
                    verify=SSL_VERIFY
                )
                if response.status_code in [200, 201]:
                    created_products.append(response.json())
                    print(f"  Created: {product['name']} (Stock: {product['stock']})")
                else:
                    print(f"  Error creating {product['name']}: {response.status_code}")
            except Exception as e:
                print(f"  Exception creating product: {e}")

    return created_products


def create_test_orders(products, num_orders=150):
    """Generate test orders over past 90 days"""
    print(f"\nCreating {num_orders} test orders...")

    if not products:
        print("  No products available to create orders!")
        return

    order_statuses = ["completed", "completed", "completed", "processing", "on-hold"]

    for i in range(num_orders):
        try:
            # Random date in past 90 days
            days_ago = random.randint(0, 90)
            order_date = datetime.now() - timedelta(days=days_ago)

            # Random products (1-4 items per order)
            num_items = random.randint(1, 4)
            selected_products = random.sample(products, min(num_items, len(products)))

            line_items = []
            for product in selected_products:
                line_items.append({
                    "product_id": product["id"],
                    "quantity": random.randint(1, 3)
                })

            # Random customer
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,99)}@example.com"

            # Create order
            order_data = {
                "status": random.choice(order_statuses),
                "date_created": order_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "line_items": line_items,
                "billing": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "address_1": f"{random.randint(100, 9999)} Main Street",
                    "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                    "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                    "postcode": str(random.randint(10000, 99999)),
                    "country": "US"
                },
                "shipping": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "address_1": f"{random.randint(100, 9999)} Main Street",
                    "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                    "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                    "postcode": str(random.randint(10000, 99999)),
                    "country": "US"
                }
            }

            response = requests.post(f"{WC_URL}/orders", auth=auth, json=order_data, verify=SSL_VERIFY)

            if response.status_code in [200, 201]:
                if (i + 1) % 25 == 0:
                    print(f"  Created {i + 1}/{num_orders} orders...")
            else:
                print(f"  Error creating order {i + 1}: {response.status_code}")

        except Exception as e:
            print(f"  Exception creating order {i + 1}: {e}")

    print(f"  Completed creating {num_orders} orders!")


def verify_connection():
    """Verify WooCommerce API connection"""
    print("Verifying WooCommerce connection...")
    print(f"  URL: {WC_URL}")

    try:
        response = requests.get(f"{WC_URL}/products", auth=auth, params={"per_page": 1}, verify=SSL_VERIFY)
        if response.status_code == 200:
            print("  Connection successful!")
            return True
        else:
            print(f"  Connection failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"  Connection error: {e}")
        return False


def get_existing_products():
    """Get list of existing products"""
    products = []
    page = 1

    while True:
        response = requests.get(
            f"{WC_URL}/products",
            auth=auth,
            params={"per_page": 100, "page": page},
            verify=SSL_VERIFY
        )
        if response.status_code != 200:
            break
        data = response.json()
        if not data:
            break
        products.extend(data)
        page += 1

    return products


def main():
    """Main function to generate test data"""
    print("=" * 60)
    print("WooCommerce Test Data Generator")
    print("=" * 60)

    # Verify connection
    if not verify_connection():
        print("\nPlease check your WooCommerce API credentials in config/.env")
        print("Make sure Local by Flywheel is running and WooCommerce is installed.")
        return

    # Create categories
    category_ids = create_categories()

    # Create products
    products = create_products(category_ids)

    # If no products were created, try to get existing ones
    if not products:
        print("\nNo products created, checking for existing products...")
        products = get_existing_products()

    print(f"\nTotal products available: {len(products)}")

    # Create test orders
    if products:
        create_test_orders(products, num_orders=150)

    print("\n" + "=" * 60)
    print("Test data generation complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Verify data in WooCommerce Admin > Products and Orders")
    print("2. Set up PostgreSQL database (run sql/schema.sql)")
    print("3. Run the ETL pipeline to populate the analytics database")


if __name__ == "__main__":
    main()
