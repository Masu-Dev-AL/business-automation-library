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
    # Add missing columns to vendors table
    cursor.execute("""
        ALTER TABLE vendors 
        ADD COLUMN IF NOT EXISTS vendor_address TEXT,
        ADD COLUMN IF NOT EXISTS vendor_phone VARCHAR(50),
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """)
    
    # Add missing columns to customers table (if it exists)
    cursor.execute("""
        ALTER TABLE customers 
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """)
    
    # Add missing columns to invoices table
    cursor.execute("""
        ALTER TABLE invoices 
        ADD COLUMN IF NOT EXISTS customer_id INTEGER REFERENCES customers(customer_id),
        ADD COLUMN IF NOT EXISTS discount DECIMAL(12, 2) DEFAULT 0,
        ADD COLUMN IF NOT EXISTS payment_instructions TEXT,
        ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(5, 2),
        ADD COLUMN IF NOT EXISTS s3_bucket VARCHAR(255),
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """)
    
    conn.commit()
    print("✓ Schema updated successfully!")
    
    # Verify vendors table
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'vendors'
        ORDER BY ordinal_position
    """)
    
    print("\n=== Updated Vendors Table Columns ===")
    for row in cursor.fetchall():
        print(f"- {row[0]}")
    
except Exception as e:
    conn.rollback()
    print(f"Error: {str(e)}")

cursor.close()
conn.close()