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

cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'vendors'
    ORDER BY ordinal_position
""")

print("\n=== Vendors Table Columns ===")
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]}")

cursor.close()
conn.close()