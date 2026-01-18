import json
import psycopg2
import boto3
import os
from datetime import datetime

secretsmanager = boto3.client('secretsmanager')

def get_db_credentials():
    """Retrieve database credentials from Secrets Manager"""
    try:
        response = secretsmanager.get_secret_value(
            SecretId='invoice-automation/db-credentials'
        )
        return json.loads(response['SecretString'])
    except Exception as e:
        print(f"Error retrieving credentials: {str(e)}")
        raise

def lambda_handler(event, context):
    """
    Approve or reject an invoice
    Called via API Gateway with query parameters: invoice_id and action
    """
    
    try:
        # Parse query parameters
        params = event.get('queryStringParameters', {})
        invoice_id = params.get('invoice_id')
        action = params.get('action')  # 'approve' or 'reject'
        
        if not invoice_id or not action:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'text/html'},
                'body': '<html><body><h1>Error: Missing invoice_id or action</h1></body></html>'
            }
        
        if action not in ['approve', 'reject']:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'text/html'},
                'body': '<html><body><h1>Error: Action must be approve or reject</h1></body></html>'
            }
        
        # Connect to database
        db_creds = get_db_credentials()
        conn = psycopg2.connect(
            host=db_creds['host'],
            port=db_creds['port'],
            database=db_creds['dbname'],
            user=db_creds['username'],
            password=db_creds['password']
        )
        
        cursor = conn.cursor()
        
        # Get invoice details
        cursor.execute("""
            SELECT i.invoice_number, v.vendor_name, i.total_amount, i.status
            FROM invoices i
            JOIN vendors v ON i.vendor_id = v.vendor_id
            WHERE i.invoice_id = %s
        """, (invoice_id,))
        
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            conn.close()
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'text/html'},
                'body': '<html><body><h1>Error: Invoice not found</h1></body></html>'
            }
        
        invoice_number, vendor_name, total_amount, current_status = result
        
        # Update status
        new_status = 'approved' if action == 'approve' else 'rejected'
        
        cursor.execute("""
            UPDATE invoices 
            SET status = %s, processed_at = %s
            WHERE invoice_id = %s
        """, (new_status, datetime.now(), invoice_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Invoice {invoice_number} {new_status}")
        
        # Return success page
        action_text = 'Approved' if action == 'approve' else 'Rejected'
        color = 'green' if action == 'approve' else 'red'
        
        html = f"""
        <html>
        <head>
            <title>Invoice {action_text}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 50px; }}
                .success {{ color: {color}; font-size: 24px; font-weight: bold; }}
                .details {{ margin-top: 20px; background: #f5f5f5; padding: 20px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1 class="success">&#10003; Invoice {action_text}</h1>
            <div class="details">
                <p><strong>Invoice Number:</strong> {invoice_number}</p>
                <p><strong>Vendor:</strong> {vendor_name}</p>
                <p><strong>Amount:</strong> ${total_amount:,.2f}</p>
                <p><strong>Previous Status:</strong> {current_status}</p>
                <p><strong>New Status:</strong> {new_status}</p>
                <p><strong>Action Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <p style="margin-top: 30px;">You can close this window.</p>
        </body>
        </html>
        """
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/html'},
            'body': html
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/html'},
            'body': f'<html><body><h1>Error: {str(e)}</h1></body></html>'
        }