import json
import boto3
import psycopg2
from datetime import datetime
import os

s3 = boto3.client('s3')
sns = boto3.client('sns')
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
    Triggered when Bedrock outputs result.json
    Extracts data, validates, and writes to database
    """
    
    try:
        # Get S3 event details
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        # Only process custom_output result.json files
        if 'custom_output' not in key or not key.endswith('result.json'):
            print(f"Skipping non-custom-output file: {key}")
            return {'statusCode': 200, 'message': 'Skipped'}
        
        print(f"Processing: s3://{bucket}/{key}")
        
        # 1. EXTRACT - Download and parse Bedrock output
        response = s3.get_object(Bucket=bucket, Key=key)
        bedrock_output = json.loads(response['Body'].read().decode('utf-8'))
        
        inference = bedrock_output.get('inference_result', {})
        
        invoice_data = {
            'invoice_number': inference.get('invoice_number'),
            'company_name': inference.get('company_name'),
            'company_address': inference.get('company_address'),
            'company_contact': inference.get('company_contact_information'),
            'bill_to': inference.get('bill_to'),
            'client_email': inference.get('client_email'),
            'invoice_date': inference.get('invoice_date'),
            'due_date': inference.get('due_date'),
            'po_number': inference.get('po_number'),
            'subtotal': inference.get('subtotal'),
            'discount': inference.get('discount'),
            'tax': inference.get('tax'),
            'total_amount': inference.get('total_amount'),
            'payment_terms': inference.get('payment_terms'),
            'payment_instructions': inference.get('payment_details', {}).get('payment_instructions'),
            'bank_name': inference.get('bank_details', {}).get('bank_name'),
            'account_number': inference.get('bank_details', {}).get('account_number'),
            'routing_number': inference.get('bank_details', {}).get('routing_number'),
            'line_items': inference.get('invoice_items', []),
            's3_key': key,
            's3_bucket': bucket,
        }
        
        confidence = bedrock_output.get('matched_blueprint', {}).get('confidence', 0) * 100
        invoice_data['confidence_score'] = round(confidence, 2)
        
        print(f"Extracted: {invoice_data['invoice_number']}, Confidence: {confidence}%")
        
        # 2. VALIDATE - Business rules
        validation_errors = []
        warnings = []
        
        # Required fields
        required_fields = ['invoice_number', 'company_name', 'total_amount', 'invoice_date']
        for field in required_fields:
            if not invoice_data.get(field):
                validation_errors.append(f"Missing required field: {field}")
        
        # Total amount must be positive
        total = invoice_data.get('total_amount')
        if total is not None and total != '':
            try:
                if float(total) <= 0:
                    validation_errors.append(f"Invalid total amount: {total}")
            except (ValueError, TypeError):
                validation_errors.append(f"Invalid total amount format: {total}")
        
        # Confidence threshold
        if confidence < 70:
            warnings.append(f"Low confidence: {confidence}%")
        
        is_valid = len(validation_errors) == 0
        needs_review = len(warnings) > 0

        # Determine status based on validation and amount
        total_amount_float = float(invoice_data.get('total_amount', 0))
        HIGH_VALUE_THRESHOLD = 50000  # $50,000

        if not is_valid:
            print(f"✗ Validation failed: {validation_errors}")
            status = 'failed'
        elif total_amount_float > HIGH_VALUE_THRESHOLD:
            print(f"💰 High-value invoice: ${total_amount_float:,.2f} - Requires approval")
            status = 'pending_review'
        elif needs_review:
            print(f"⚠ Needs review: {warnings}")
            status = 'pending_review'
        else:
            print(f"✓ Validation passed")
            status = 'approved'
        
        # 3. PROCESS - Write to database
        db_creds = get_db_credentials()
        conn = psycopg2.connect(
            host=db_creds['host'],
            port=db_creds['port'],
            database=db_creds['dbname'],
            user=db_creds['username'],
            password=db_creds['password']
        )
        
        cursor = conn.cursor()
        conn.autocommit = False
        
        try:
            # Insert vendor
            cursor.execute("""
                INSERT INTO vendors (vendor_name, vendor_address, vendor_phone, vendor_email, payment_terms, is_approved)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (vendor_name) DO UPDATE SET
                    vendor_address = EXCLUDED.vendor_address,
                    vendor_phone = EXCLUDED.vendor_phone
                RETURNING vendor_id
            """, (
                invoice_data.get('company_name'),
                invoice_data.get('company_address'),
                invoice_data.get('company_contact'),
                None,
                invoice_data.get('payment_terms'),
                True
            ))
            vendor_id = cursor.fetchone()[0]
            
            # Insert customer
            cursor.execute("""
                INSERT INTO customers (customer_name, customer_address, customer_email)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING customer_id
            """, (
                invoice_data.get('bill_to'),
                invoice_data.get('bill_to'),
                invoice_data.get('client_email')
            ))
            result = cursor.fetchone()
            customer_id = result[0] if result else None
            
            # Insert invoice
            cursor.execute("""
                INSERT INTO invoices (
                    invoice_number, vendor_id, customer_id,
                    invoice_date, due_date,
                    subtotal, discount, tax_amount, total_amount,
                    po_number, payment_terms, payment_instructions,
                    status, confidence_score,
                    s3_key, s3_bucket,
                    processed_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING invoice_id
            """, (
                invoice_data.get('invoice_number'),
                vendor_id,
                customer_id,
                invoice_data.get('invoice_date'),
                invoice_data.get('due_date'),
                invoice_data.get('subtotal'),
                abs(float(invoice_data.get('discount') or 0)),
                invoice_data.get('tax'),
                invoice_data.get('total_amount'),
                invoice_data.get('po_number'),
                invoice_data.get('payment_terms'),
                invoice_data.get('payment_instructions'),
                status,
                invoice_data.get('confidence_score'),
                invoice_data.get('s3_key'),
                invoice_data.get('s3_bucket'),
                datetime.now()
            ))
            invoice_id = cursor.fetchone()[0]
            
            # Insert line items
            line_items = invoice_data.get('line_items', [])
            if line_items:
                for idx, item in enumerate(line_items, 1):
                    cursor.execute("""
                        INSERT INTO invoice_line_items (
                            invoice_id, description, quantity, unit_price, amount, line_number
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        invoice_id,
                        item.get('description'),
                        item.get('quantity'),
                        item.get('unit_price'),
                        item.get('amount'),
                        idx
                    ))
            
            # Insert bank details
            if invoice_data.get('bank_name'):
                cursor.execute("""
                    INSERT INTO bank_details (vendor_id, bank_name, account_number, routing_number)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    vendor_id,
                    invoice_data.get('bank_name'),
                    invoice_data.get('account_number'),
                    invoice_data.get('routing_number')
                ))
            
            conn.commit()
            print(f"✓ Invoice {invoice_data.get('invoice_number')} saved (ID: {invoice_id})")
            
            # Send SNS notification for high-value invoices
            if total_amount_float > HIGH_VALUE_THRESHOLD:
                try:
                    approve_url = f"{os.environ.get('APPROVAL_API_ENDPOINT')}?invoice_id={invoice_id}&action=approve"
                    reject_url = f"{os.environ.get('APPROVAL_API_ENDPOINT')}?invoice_id={invoice_id}&action=reject"
                    
                    message = f"""
High-Value Invoice Requires Approval

Invoice Number: {invoice_data.get('invoice_number')}
Vendor: {invoice_data.get('company_name')}
Amount: ${total_amount_float:,.2f}
Date: {invoice_data.get('invoice_date')}
Due Date: {invoice_data.get('due_date')}
PO Number: {invoice_data.get('po_number')}

Confidence Score: {invoice_data.get('confidence_score')}%

This invoice exceeds the ${HIGH_VALUE_THRESHOLD:,.2f} threshold and requires manual approval.

----- ACTION REQUIRED -----

APPROVE: {approve_url}

REJECT: {reject_url}

Click one of the links above to approve or reject this invoice.
"""
                    
                    sns.publish(
                        TopicArn=os.environ['SNS_TOPIC_ARN'],
                        Subject=f'🔔 High-Value Invoice Approval Required: {invoice_data.get("invoice_number")}',
                        Message=message.strip()
                    )
                    print(f"✓ Approval notification sent via SNS")
                except Exception as e:
                    print(f"⚠ Failed to send SNS notification: {str(e)}")
            
            cursor.close()
            conn.close()
            
            # Move PDF to appropriate bucket based on status
            # Extract job_id from S3 key (format: /job-id/0/custom_output/0/result.json)
            parts = key.split('/')
            job_id = parts[1] if len(parts) > 1 and parts[0] == '' else parts[0]
            print(f"Extracted job_id: {job_id}")
            
            try:
                # Find the original PDF in incoming bucket by job_id tag
                incoming_bucket = os.environ['INCOMING_BUCKET']
                
                # List objects in incoming bucket and find the one with matching job_id tag
                response = s3.list_objects_v2(Bucket=incoming_bucket)
                
                original_pdf_key = None
                if 'Contents' in response:
                    for obj in response['Contents']:
                        try:
                            tags_response = s3.get_object_tagging(
                                Bucket=incoming_bucket,
                                Key=obj['Key']
                            )
                            for tag in tags_response.get('TagSet', []):
                                if tag['Key'] == 'bedrock_job_id' and tag['Value'] == job_id:
                                    original_pdf_key = obj['Key']
                                    break
                            if original_pdf_key:
                                break
                        except:
                            continue
                
                if original_pdf_key:
                    if status == 'approved':
                        # Move to processed bucket
                        dest_bucket = os.environ['PROCESSED_BUCKET']
                        s3.copy_object(
                            CopySource={'Bucket': incoming_bucket, 'Key': original_pdf_key},
                            Bucket=dest_bucket,
                            Key=original_pdf_key
                        )
                        s3.delete_object(Bucket=incoming_bucket, Key=original_pdf_key)
                        print(f"✓ Moved {original_pdf_key} to processed bucket")
                    else:
                        # Move to failed bucket (pending_review, rejected, or failed)
                        dest_bucket = os.environ['FAILED_BUCKET']
                        s3.copy_object(
                            CopySource={'Bucket': incoming_bucket, 'Key': original_pdf_key},
                            Bucket=dest_bucket,
                            Key=original_pdf_key
                        )
                        s3.delete_object(Bucket=incoming_bucket, Key=original_pdf_key)
                        print(f"⚠ Moved {original_pdf_key} to failed bucket (status: {status})")
                else:
                    print(f"⚠ Could not find original PDF for job_id: {job_id}")
                    
            except Exception as e:
                print(f"Could not move PDF: {str(e)}")
            
            return {
                'statusCode': 200,
                'invoice_id': invoice_id,
                'invoice_number': invoice_data.get('invoice_number'),
                'status': status
            }
            
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            raise e
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'error': str(e)
        }
