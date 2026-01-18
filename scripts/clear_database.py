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
    # Delete in order to respect foreign key constraints
    cursor.execute("DELETE FROM bedrock_extraction_log")
    cursor.execute("DELETE FROM invoice_line_items")
    cursor.execute("DELETE FROM invoices")
    cursor.execute("DELETE FROM bank_details")
    cursor.execute("DELETE FROM customers")
    cursor.execute("DELETE FROM vendors")
    
    conn.commit()
    print("✓ All invoice data cleared from database")
    
except Exception as e:
    conn.rollback()
    print(f"Error: {str(e)}")

cursor.close()
conn.close()