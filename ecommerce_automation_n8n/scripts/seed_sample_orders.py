"""
Seed realistic order data for the last 30 days.
Run from project root: python scripts/seed_sample_orders.py
"""
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

conn = psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "5432")),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

cur = conn.cursor()

# ── Check current state ──────────────────────────────────
cur.execute("SELECT COUNT(*) FROM fact_orders")
print(f"Existing orders: {cur.fetchone()[0]}")

cur.execute("SELECT product_id, sell_price FROM dim_products WHERE is_active = true")
products = cur.fetchall()
print(f"Active products: {len(products)}")

cur.execute("SELECT customer_id FROM dim_customers")
customers = [r[0] for r in cur.fetchall()]
print(f"Customers: {len(customers)}")

if not products:
    print("No products found — cannot seed orders.")
    conn.close()
    exit(1)

# Seed customers if none exist
if not customers:
    print("No customers found — seeding 20 sample customers...")
    for i in range(1, 21):
        cur.execute("""
            INSERT INTO dim_customers (woo_customer_id, email, first_name, last_name, segment, customer_since)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (woo_customer_id) DO NOTHING
            RETURNING customer_id
        """, (
            1000 + i,
            f"customer{i}@example.com",
            f"First{i}",
            f"Last{i}",
            random.choice(["Regular", "VIP", "New"]),
            datetime.now().date() - timedelta(days=random.randint(30, 365)),
        ))
    conn.commit()
    cur.execute("SELECT customer_id FROM dim_customers")
    customers = [r[0] for r in cur.fetchall()]
    print(f"  Seeded {len(customers)} customers.")

# ── Generate orders for last 30 days ─────────────────────
statuses = ["completed", "completed", "completed", "processing", "pending", "on-hold"]
today = datetime.now().date()
order_id_start = 5000
orders_inserted = 0
items_inserted = 0

for day_offset in range(30, 0, -1):
    order_date = today - timedelta(days=day_offset)
    is_weekend = order_date.weekday() >= 5

    # Vary order volume: weekdays 8-20 orders, weekends 3-10
    if is_weekend:
        num_orders = random.randint(3, 10)
    else:
        num_orders = random.randint(8, 20)

    # Get date_id
    cur.execute("SELECT date_id FROM dim_date WHERE full_date = %s", (order_date,))
    row = cur.fetchone()
    if not row:
        continue
    date_id = row[0]

    for i in range(num_orders):
        order_id_start += 1
        woo_order_id = order_id_start
        customer_id = random.choice(customers)
        status = random.choice(statuses)
        num_items = random.randint(1, 5)

        # Pick random products for line items
        order_products = random.sample(products, min(num_items, len(products)))
        line_items = []
        total_amount = 0
        item_count = 0

        for prod_id, sell_price in order_products:
            qty = random.randint(1, 4)
            price = float(sell_price) if sell_price else random.uniform(10, 100)
            line_total = round(qty * price, 2)
            line_items.append((prod_id, qty, price, line_total))
            total_amount += line_total
            item_count += qty

        total_amount = round(total_amount, 2)
        shipping = round(random.uniform(0, 15), 2)
        fulfillment_hours = random.randint(2, 72) if status == "completed" else None

        # Add some time variation within the day
        hour = random.randint(6, 23)
        minute = random.randint(0, 59)
        order_datetime = datetime.combine(order_date, datetime.min.time().replace(hour=hour, minute=minute))

        # Insert order
        try:
            cur.execute("""
                INSERT INTO fact_orders (woo_order_id, customer_id, date_id, order_date, status,
                                         total_amount, item_count, fulfillment_time_hours, shipping_cost)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (woo_order_id) DO NOTHING
                RETURNING order_fact_id
            """, (woo_order_id, customer_id, date_id, order_datetime, status,
                  total_amount, item_count, fulfillment_hours, shipping))

            result = cur.fetchone()
            if result is None:
                continue
            order_fact_id = result[0]
            orders_inserted += 1

            # Insert line items
            for prod_id, qty, price, line_total in line_items:
                cur.execute("""
                    INSERT INTO fact_order_items (order_fact_id, product_id, quantity, unit_price, line_total)
                    VALUES (%s, %s, %s, %s, %s)
                """, (order_fact_id, prod_id, qty, price, line_total))
                items_inserted += 1

        except Exception as e:
            print(f"  Skipping order {woo_order_id}: {e}")
            conn.rollback()
            continue

conn.commit()
print(f"\nSeeded {orders_inserted} orders with {items_inserted} line items over the last 30 days.")

# ── Verify ───────────────────────────────────────────────
cur.execute("""
    SELECT full_date, order_count, total_revenue
    FROM vw_daily_orders
    WHERE order_count > 0
    ORDER BY full_date DESC
    LIMIT 10
""")
print("\nRecent daily orders (from view):")
for row in cur.fetchall():
    print(f"  {row[0]}  orders={row[1]}  revenue=${row[2]:.2f}")

cur.close()
conn.close()
print("\nDone!")
