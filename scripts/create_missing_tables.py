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
    # 1. Update vendors table - add missing columns
    print("Updating vendors table...")
    cursor.execute("""
        ALTER TABLE vendors 
        ADD COLUMN IF NOT EXISTS vendor_address TEXT,
        ADD COLUMN IF NOT EXISTS vendor_phone VARCHAR(50),
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """)
    
    # 2. Create customers table
    print("Creating customers table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id SERIAL PRIMARY KEY,
            customer_name VARCHAR(255),
            customer_address TEXT,
            customer_email VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 3. Update invoices table - add missing columns
    print("Updating invoices table...")
    cursor.execute("""
        ALTER TABLE invoices 
        ADD COLUMN IF NOT EXISTS customer_id INTEGER REFERENCES customers(customer_id),
        ADD COLUMN IF NOT EXISTS discount DECIMAL(12, 2) DEFAULT 0,
        ADD COLUMN IF NOT EXISTS payment_instructions TEXT,
        ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(5, 2),
        ADD COLUMN IF NOT EXISTS s3_bucket VARCHAR(255),
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """)
    
    # 4. Create bank_details table
    print("Creating bank_details table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bank_details (
            bank_id SERIAL PRIMARY KEY,
            vendor_id INTEGER REFERENCES vendors(vendor_id),
            bank_name VARCHAR(255),
            account_number VARCHAR(100),
            routing_number VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 5. Create bedrock_extraction_log table
    print("Creating bedrock_extraction_log table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bedrock_extraction_log (
            log_id SERIAL PRIMARY KEY,
            invoice_id INTEGER REFERENCES invoices(invoice_id),
            extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            model_version VARCHAR(100),
            overall_confidence DECIMAL(5, 2),
            raw_json JSONB,
            processing_time_ms INTEGER,
            success BOOLEAN DEFAULT true,
            error_message TEXT
        )
    """)
    
    conn.commit()
    print("\n✓ All tables created/updated successfully!")
    
    # Show final table list
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    
    print("\n=== All Tables ===")
    for row in cursor.fetchall():
        print(f"- {row[0]}")
    
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {str(e)}")

cursor.close()
conn.close()