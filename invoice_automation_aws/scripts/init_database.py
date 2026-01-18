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
with open('sql/schema.sql', 'r') as f:
 schema_sql = f.read()
 cursor.execute(schema_sql)
conn.commit()
cursor.close()
conn.close()
print("Database schema created successfully!")