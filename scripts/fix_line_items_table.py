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
    # Check current columns
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'invoice_line_items'
        ORDER BY ordinal_position
    """)
    
    print("\n=== Current Columns ===")
    for row in cursor.fetchall():
        print(f"- {row[0]}")
    
    # Add missing column
    cursor.execute("""
        ALTER TABLE invoice_line_items 
        ADD COLUMN IF NOT EXISTS line_number INTEGER
    """)
    
    conn.commit()
    print("\n✓ Added line_number column")
    
except Exception as e:
    conn.rollback()
    print(f"Error: {str(e)}")

cursor.close()
conn.close()