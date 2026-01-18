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

# Get the latest invoice
cursor.execute("""
    SELECT 
        i.invoice_number,
        v.vendor_name,
        i.invoice_date,
        i.due_date,
        i.subtotal,
        i.discount,
        i.tax_amount,
        i.total_amount,
        i.status,
        i.confidence_score,
        i.po_number,
        i.payment_terms
    FROM invoices i
    JOIN vendors v ON i.vendor_id = v.vendor_id
    ORDER BY i.processed_at DESC
    LIMIT 1
""")

invoice = cursor.fetchone()
if invoice:
    print("\n=== Invoice Details ===")
    print(f"Invoice #: {invoice[0]}")
    print(f"Vendor: {invoice[1]}")
    print(f"Invoice Date: {invoice[2]}")
    print(f"Due Date: {invoice[3]}")
    print(f"PO Number: {invoice[10]}")
    print(f"Payment Terms: {invoice[11]}")
    print(f"")
    print(f"Subtotal: ${invoice[4]:,.2f}")
    print(f"Discount: -${abs(invoice[5]):,.2f}")
    print(f"Tax: ${invoice[6]:,.2f}")
    print(f"Total: ${invoice[7]:,.2f}")
    print(f"")
    print(f"Status: {invoice[8]}")
    print(f"Confidence: {invoice[9]}%")
    
    # Get line items
    cursor.execute("""
        SELECT description, quantity, unit_price, amount
        FROM invoice_line_items
        WHERE invoice_id = (
            SELECT invoice_id FROM invoices 
            ORDER BY processed_at DESC LIMIT 1
        )
        ORDER BY line_number
    """)
    
    print("\n=== Line Items ===")
    total_check = 0
    for item in cursor.fetchall():
        print(f"{item[0]}: {item[1]} x ${item[2]:,.2f} = ${item[3]:,.2f}")
        total_check += item[3]
    
    print(f"\nLine items total: ${total_check:,.2f}")
    
    # Get bank details
    cursor.execute("""
        SELECT bank_name, account_number, routing_number
        FROM bank_details
        WHERE vendor_id = (
            SELECT vendor_id FROM invoices 
            ORDER BY processed_at DESC LIMIT 1
        )
        LIMIT 1
    """)
    
    bank = cursor.fetchone()
    if bank:
        print("\n=== Bank Details ===")
        print(f"Bank: {bank[0]}")
        print(f"Account: {bank[1]}")
        print(f"Routing: {bank[2]}")

else:
    print("No invoices found")

cursor.close()
conn.close()