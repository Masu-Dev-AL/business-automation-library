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

try:
    cursor.execute("""
        ALTER TABLE invoices 
        ADD COLUMN IF NOT EXISTS po_number VARCHAR(100),
        ADD COLUMN IF NOT EXISTS payment_terms VARCHAR(255)
    """)
    
    conn.commit()
    print("✓ Added po_number and payment_terms to invoices table")
    
except Exception as e:
    conn.rollback()
    print(f"Error: {str(e)}")

cursor.close()
conn.close()