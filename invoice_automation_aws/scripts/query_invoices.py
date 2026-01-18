import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('config/.env')

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=5432,
    database='invoice_automation',
    user='postgres',
    password=os.getenv('DB_PASSWORD')
)

cursor = conn.cursor()

# Query invoices
cursor.execute("""
    SELECT 
        i.invoice_id,
        i.invoice_number,
        v.vendor_name,
        i.total_amount,
        i.status,
        i.processed_at
    FROM invoices i
    JOIN vendors v ON i.vendor_id = v.vendor_id
    ORDER BY i.processed_at DESC
    LIMIT 10
""")

print("\n=== Recent Invoices ===")
for row in cursor.fetchall():
    print(f"ID: {row[0]} | Invoice: {row[1]} | Vendor: {row[2]} | Amount: ${row[3]} | Status: {row[4]}")

cursor.close()
conn.close()