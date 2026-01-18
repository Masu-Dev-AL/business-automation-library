# Portfolio Project 1: Complete Technical Guide Update Instructions

**For: Claude Code**  
**Date: January 11, 2026**  
**Project: Serverless Invoice Automation System**

---

## Overview

This document contains complete instructions to update the Portfolio Project 1 Technical Guide with the final, working architecture. The project was successfully completed using the **AWS-recommended simplified pattern** (not the original overcomplicated Step Functions approach).

---

## Key Changes from Original Plan

### ❌ What We DIDN'T Use (Original Plan)
- Step Functions (too complex for this use case)
- EventBridge for orchestration (unnecessary)
- 3 separate orchestrated Lambda functions

### ✅ What We BUILT (AWS Best Practice)
- **2 Main Lambda Functions** (simple, event-driven)
- **1 Approval Lambda Function** (API Gateway endpoint)
- S3 event triggers (native, simple)
- Direct Bedrock API calls from Lambda

### Why We Changed
- AWS samples and blog posts use this simpler pattern
- Less complexity, easier to debug
- Follows serverless best practices
- More cost-effective
- Just as powerful

---

## Final Architecture (IMPLEMENTED)

```
User uploads PDF
    ↓
S3 Incoming Bucket (invoice-automation-incoming-ag2026)
    ↓ [S3 Event Notification]
Lambda 1: BedrockTriggerFunction
    ↓ [Calls Bedrock API: invoke_data_automation_async]
Amazon Bedrock Data Automation
    ↓ [AI Processing with Custom Blueprint]
S3 Blueprint Bucket (invoice-automation-blueprint-ag2026)
    ↓ [S3 Event Notification on result.json]
Lambda 2: InvoiceProcessorFunction
    ↓ [Extract + Validate + Process]
RDS PostgreSQL Database
    ↓ [If amount > $50k]
SNS Email Notification with Approve/Reject Links
    ↓ [User clicks link]
API Gateway + Lambda 3: InvoiceApprovalFunction
    ↓ [Updates database]
Invoice Status Updated (approved/rejected)
```

---

## Complete Step-by-Step Implementation

### Step 1: AWS Account & IAM Setup

**1.1 Create AWS Account** (Standard)

**1.2 Create IAM User: `invoice-automation-dev`**

**1.3 Required IAM Policies:**
- AmazonS3FullAccess
- AmazonRDSFullAccess
- AWSLambda_FullAccess
- AmazonSNSFullAccess
- SecretsManagerReadWrite
- CloudWatchLogsFullAccess
- AmazonBedrockFullAccess
- AmazonEC2FullAccess (for VPC/RDS access)
- IAMFullAccess (for role creation)

**1.4 Create 3 Inline Policies:**

**EventBridgeAccess:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["events:*"],
      "Resource": "*"
    }
  ]
}
```

**APIGatewayAccess:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["apigateway:*"],
      "Resource": "*"
    }
  ]
}
```

**1.5 Configure AWS CLI**
```powershell
aws configure
# Access Key ID: [from IAM user]
# Secret Access Key: [from IAM user]
# Region: us-east-1
# Output format: json
```

---

### Step 2: Create S3 Buckets

**3 buckets needed:**

```powershell
$S3_SUFFIX = "ag2026"  # Use your initials + year

# 1. Incoming bucket (PDFs uploaded here)
aws s3api create-bucket --bucket invoice-automation-incoming-$S3_SUFFIX --region us-east-1

# 2. Blueprint bucket (Bedrock outputs here)
aws s3api create-bucket --bucket invoice-automation-blueprint-$S3_SUFFIX --region us-east-1

# 3. Processed bucket (successful invoices moved here)
aws s3api create-bucket --bucket invoice-automation-processed-$S3_SUFFIX --region us-east-1

# 4. Failed bucket (validation failures moved here)
aws s3api create-bucket --bucket invoice-automation-failed-$S3_SUFFIX --region us-east-1
```

**Enable versioning on blueprint bucket:**
```powershell
aws s3api put-bucket-versioning --bucket invoice-automation-blueprint-$S3_SUFFIX --versioning-configuration Status=Enabled
```

---

### Step 3: RDS PostgreSQL Database

**3.1 Create Database**

Via AWS Console (easier) or CLI:
- Engine: PostgreSQL 15.x
- Instance: db.t3.micro (Free Tier eligible)
- Storage: 20 GB GP3
- Database name: `invoice_automation`
- Master username: `postgres`
- Master password: [strong password]
- VPC: Default VPC
- Public access: Yes (for development)
- Security group: Allow PostgreSQL (5432) from your IP

**3.2 Store Credentials in Secrets Manager**

```powershell
$DB_PASSWORD = "YourStrongPassword"
$DB_HOST = "your-rds-endpoint.us-east-1.rds.amazonaws.com"

@"
{
  "username": "postgres",
  "password": "$DB_PASSWORD",
  "host": "$DB_HOST",
  "port": 5432,
  "dbname": "invoice_automation"
}
"@ | Set-Content -Path db-secret.json

aws secretsmanager create-secret --name invoice-automation/db-credentials --secret-string file://db-secret.json
```

**3.3 Complete Database Schema**

Create `sql/complete_schema.sql`:

```sql
-- Complete Invoice Automation Database Schema
-- Tested and Working as of January 11, 2026

-- Vendors table
CREATE TABLE IF NOT EXISTS vendors (
    vendor_id SERIAL PRIMARY KEY,
    vendor_name VARCHAR(255) UNIQUE NOT NULL,
    vendor_address TEXT,
    vendor_phone VARCHAR(50),
    vendor_email VARCHAR(255),
    payment_terms VARCHAR(255),
    is_approved BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255),
    customer_address TEXT,
    customer_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Invoices table
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(100) NOT NULL,
    vendor_id INTEGER REFERENCES vendors(vendor_id),
    customer_id INTEGER REFERENCES customers(customer_id),
    invoice_date DATE,
    due_date DATE,
    subtotal DECIMAL(12, 2),
    discount DECIMAL(12, 2) DEFAULT 0,
    tax_amount DECIMAL(12, 2),
    total_amount DECIMAL(12, 2),
    po_number VARCHAR(100),
    payment_terms VARCHAR(255),
    payment_instructions TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    confidence_score DECIMAL(5, 2),
    s3_key VARCHAR(500),
    s3_bucket VARCHAR(255),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(invoice_number, vendor_id)
);

-- Invoice line items table
CREATE TABLE IF NOT EXISTS invoice_line_items (
    line_item_id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    line_number INTEGER,
    description TEXT,
    quantity DECIMAL(10, 2),
    unit_price DECIMAL(12, 2),
    amount DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bank details table
CREATE TABLE IF NOT EXISTS bank_details (
    bank_id SERIAL PRIMARY KEY,
    vendor_id INTEGER REFERENCES vendors(vendor_id),
    bank_name VARCHAR(255),
    account_number VARCHAR(100),
    routing_number VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bedrock extraction log table (optional, for audit trail)
CREATE TABLE IF NOT EXISTS bedrock_extraction_log (
    log_id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES invoices(invoice_id),
    extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(100),
    overall_confidence DECIMAL(5, 2),
    raw_json JSONB,
    processing_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_invoices_vendor ON invoices(vendor_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date);
CREATE INDEX IF NOT EXISTS idx_line_items_invoice ON invoice_line_items(invoice_id);
```

**Apply schema:**
```powershell
psql -h $DB_HOST -U postgres -d invoice_automation -f sql/complete_schema.sql
```

---

### Step 4: Bedrock Data Automation

**4.1 Enable Bedrock Model Access**

In AWS Console → Bedrock → Model Access:
- Enable: Claude 3 Sonnet
- Enable: Claude 3 Haiku
- Wait for "Access granted"

**4.2 Create Bedrock Data Automation Project**

Via AWS Console (Bedrock → Data Automation):
1. Create new project: `invoice-extraction-project`
2. Project type: ASYNC
3. Stage: LIVE

**4.3 Create Custom Blueprint**

1. Upload sample invoice (invoice_0001.pdf)
2. Let Bedrock auto-generate schema from sample
3. Blueprint will extract:
   - invoice_number
   - company_name
   - company_address
   - company_contact_information
   - bill_to
   - client_email
   - invoice_date
   - due_date
   - po_number
   - subtotal
   - discount
   - tax
   - total_amount
   - payment_terms
   - payment_details (nested)
   - bank_details (nested)
   - invoice_items (array)

4. Save blueprint - you'll get a blueprint ARN

**Important ARNs to save:**
- Project ARN: `arn:aws:bedrock:us-east-1:{account}:data-automation-project/{project-id}`
- Blueprint ARN: `arn:aws:bedrock:us-east-1:{account}:blueprint/{blueprint-id}`
- Profile ARN: `arn:aws:bedrock:us-east-1:{account}:data-automation-profile/us.data-automation-v1`

**4.4 Bedrock Output Structure**

When Bedrock processes a PDF, it outputs to:
```
s3://invoice-automation-blueprint-ag2026/{job-id}/0/custom_output/0/result.json
```

Structure:
```json
{
  "matched_blueprint": {
    "confidence": 1.0,
    "name": "invoice_automation_blueprint"
  },
  "inference_result": {
    "invoice_number": "INV-0001",
    "company_name": "ACME CORPORATION",
    "total_amount": 26459.16,
    "invoice_items": [
      {
        "description": "Consulting Services",
        "quantity": 56,
        "unit_price": 75.93,
        "amount": 4251.92
      }
    ]
  }
}
```

**Key Points:**
- Fields are flat in `inference_result` (no nested "value" keys)
- Confidence is 0-1 scale (multiply by 100 for percentage)
- Output path is `{job-id}/0/custom_output/0/result.json` (not `inference_results/`)

---

### Step 5: Lambda Functions

**5.1 Create IAM Role for Lambda Functions**

```powershell
@"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@ | Set-Content -Path lambda-trust-policy.json

aws iam create-role --role-name InvoiceAutomationLambdaRole --assume-role-policy-document file://lambda-trust-policy.json
```

**Attach policies:**
```powershell
aws iam attach-role-policy --role-name InvoiceAutomationLambdaRole --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam attach-role-policy --role-name InvoiceAutomationLambdaRole --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
aws iam attach-role-policy --role-name InvoiceAutomationLambdaRole --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
```

**Add inline policies:**

**BedrockDataAutomationAccess:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeDataAutomationAsync",
        "bedrock:GetDataAutomationStatus",
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
```

**SNSPublishAccess:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["sns:Publish"],
      "Resource": "*"
    }
  ]
}
```

---

**5.2 Lambda Function 1: BedrockTriggerFunction**

**Purpose:** Triggered by S3 upload, invokes Bedrock API

**Location:** `lambda_v2/bedrock_trigger/`

**Code:** `lambda_function.py`
```python
import json
import boto3
import os
from datetime import datetime

def lambda_handler(event, context):
    """
    Triggered when PDF uploaded to incoming bucket
    Invokes Bedrock Data Automation to process the invoice
    """
    
    try:
        # Create client inside function with latest boto3
        bedrock_runtime = boto3.client('bedrock-data-automation-runtime', region_name='us-east-1')
        
        # Get S3 event details
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        print(f"New PDF uploaded: s3://{bucket}/{key}")
        
        # Invoke Bedrock Data Automation
        response = bedrock_runtime.invoke_data_automation_async(
            dataAutomationConfiguration={
                'dataAutomationProjectArn': os.environ['BEDROCK_PROJECT_ARN']
            },
            inputConfiguration={
                's3Uri': f's3://{bucket}/{key}'
            },
            outputConfiguration={
                's3Uri': os.environ['OUTPUT_BUCKET']
            },
            dataAutomationProfileArn=os.environ['BEDROCK_PROFILE_ARN']
        )
        
        invocation_arn = response['invocationArn']
        print(f"✓ Bedrock invocation started: {invocation_arn}")
        
        return {
            'statusCode': 200,
            'invocationArn': invocation_arn,
            'message': f'Processing started for {key}'
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'error': str(e)
        }
```

**requirements.txt:**
```
boto3>=1.35.0
```

**Deployment:**
```powershell
cd lambda_v2/bedrock_trigger
pip install -r requirements.txt -t . --upgrade
Compress-Archive -Path * -DestinationPath ..\bedrock_trigger.zip -Force
cd ..\..

aws lambda create-function \
  --function-name BedrockTriggerFunction \
  --runtime python3.11 \
  --handler lambda_function.lambda_handler \
  --role arn:aws:iam::{account}:role/InvoiceAutomationLambdaRole \
  --zip-file fileb://lambda_v2/bedrock_trigger.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables="{BEDROCK_PROJECT_ARN=arn:aws:bedrock:us-east-1:{account}:data-automation-project/{id},OUTPUT_BUCKET=s3://invoice-automation-blueprint-ag2026,BEDROCK_PROFILE_ARN=arn:aws:bedrock:us-east-1:{account}:data-automation-profile/us.data-automation-v1}"
```

---

**5.3 Lambda Function 2: InvoiceProcessorFunction**

**Purpose:** Processes Bedrock output, validates, writes to database

**Location:** `lambda_v2/invoice_processor/`

**Code:** See `/mnt/user-data/outputs/lambda_function_fixed.py` (the corrected version)

**Key Features:**
- Extracts data from Bedrock JSON
- Validates business rules
- Determines status based on amount ($50k threshold)
- Writes to PostgreSQL (vendors, customers, invoices, line items, bank details)
- Sends SNS notification for high-value invoices with approve/reject links
- Returns direct data (no statusCode wrapper)

**requirements.txt:**
```
boto3==1.34.22
psycopg2-binary==2.9.9
```

**Deployment (Windows-specific for psycopg2):**
```powershell
cd lambda_v2/invoice_processor
Remove-Item -Recurse -Force * -Exclude lambda_function.py,requirements.txt
pip install --platform manylinux2014_x86_64 --target . --implementation cp --python-version 3.11 --only-binary=:all: --upgrade psycopg2-binary
pip install boto3==1.34.22 -t .
Compress-Archive -Path * -DestinationPath ..\invoice_processor.zip -Force
cd ..\..

aws lambda create-function \
  --function-name InvoiceProcessorFunction \
  --runtime python3.11 \
  --handler lambda_function.lambda_handler \
  --role arn:aws:iam::{account}:role/InvoiceAutomationLambdaRole \
  --zip-file fileb://lambda_v2/invoice_processor.zip \
  --timeout 60 \
  --memory-size 512 \
  --environment Variables="{INCOMING_BUCKET=invoice-automation-incoming-ag2026,PROCESSED_BUCKET=invoice-automation-processed-ag2026,FAILED_BUCKET=invoice-automation-failed-ag2026,SNS_TOPIC_ARN={sns-arn},APPROVAL_API_ENDPOINT={api-endpoint}}"
```

---

**5.4 Lambda Function 3: InvoiceApprovalFunction**

**Purpose:** Handles approve/reject actions via API Gateway

**Location:** `lambda_v2/invoice_approval/`

**Code:** `lambda_function.py`
```python
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
```

**Deployment:**
```powershell
cd lambda_v2/invoice_approval
pip install --platform manylinux2014_x86_64 --target . --implementation cp --python-version 3.11 --only-binary=:all: --upgrade psycopg2-binary
Compress-Archive -Path * -DestinationPath ..\invoice_approval.zip -Force
cd ..\..

aws lambda create-function \
  --function-name InvoiceApprovalFunction \
  --runtime python3.11 \
  --handler lambda_function.lambda_handler \
  --role arn:aws:iam::{account}:role/InvoiceAutomationLambdaRole \
  --zip-file fileb://lambda_v2/invoice_approval.zip \
  --timeout 30 \
  --memory-size 256
```

---

### Step 6: Configure S3 Event Triggers

**6.1 Grant S3 Permission to Invoke Lambdas**

```powershell
# For BedrockTriggerFunction
aws lambda add-permission \
  --function-name BedrockTriggerFunction \
  --statement-id s3-trigger-incoming \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::invoice-automation-incoming-ag2026

# For InvoiceProcessorFunction
aws lambda add-permission \
  --function-name InvoiceProcessorFunction \
  --statement-id s3-trigger-blueprint \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::invoice-automation-blueprint-ag2026
```

**6.2 Configure S3 Notifications**

**Incoming bucket → BedrockTriggerFunction:**
```json
{
  "LambdaFunctionConfigurations": [
    {
      "Id": "InvoicePDFUpload",
      "LambdaFunctionArn": "arn:aws:lambda:us-east-1:{account}:function:BedrockTriggerFunction",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "suffix",
              "Value": ".pdf"
            }
          ]
        }
      }
    }
  ]
}
```

```powershell
aws s3api put-bucket-notification-configuration \
  --bucket invoice-automation-incoming-ag2026 \
  --notification-configuration file://s3-notification-incoming.json
```

**Blueprint bucket → InvoiceProcessorFunction:**
```json
{
  "LambdaFunctionConfigurations": [
    {
      "Id": "BedrockResultProcessing",
      "LambdaFunctionArn": "arn:aws:lambda:us-east-1:{account}:function:InvoiceProcessorFunction",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "suffix",
              "Value": "result.json"
            }
          ]
        }
      }
    }
  ]
}
```

```powershell
aws s3api put-bucket-notification-configuration \
  --bucket invoice-automation-blueprint-ag2026 \
  --notification-configuration file://s3-notification-blueprint.json
```

---

### Step 7: SNS Notifications

**7.1 Create SNS Topic**

```powershell
aws sns create-topic --name InvoiceApprovalNotifications
```

**7.2 Subscribe Email**

```powershell
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:{account}:InvoiceApprovalNotifications \
  --protocol email \
  --notification-endpoint your-email@example.com
```

**Check email and confirm subscription!**

---

### Step 8: API Gateway for Approvals

**8.1 Create REST API**

```powershell
$API_ID = (aws apigateway create-rest-api --name InvoiceApprovalAPI --description "API for approving/rejecting invoices" --query "id" --output text)

$ROOT_RESOURCE_ID = (aws apigateway get-resources --rest-api-id $API_ID --query "items[0].id" --output text)

$APPROVE_RESOURCE_ID = (aws apigateway create-resource --rest-api-id $API_ID --parent-id $ROOT_RESOURCE_ID --path-part approve --query "id" --output text)
```

**8.2 Create GET Method**

```powershell
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $APPROVE_RESOURCE_ID \
  --http-method GET \
  --authorization-type NONE \
  --request-parameters "method.request.querystring.invoice_id=true,method.request.querystring.action=true"
```

**8.3 Integrate with Lambda**

```powershell
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $APPROVE_RESOURCE_ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:{account}:function:InvoiceApprovalFunction/invocations"
```

**8.4 Grant API Gateway Permission**

```powershell
aws lambda add-permission \
  --function-name InvoiceApprovalFunction \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:{account}:$API_ID/*/*/approve"
```

**8.5 Deploy API**

```powershell
aws apigateway create-deployment --rest-api-id $API_ID --stage-name prod
```

**API Endpoint:**
```
https://{api-id}.execute-api.us-east-1.amazonaws.com/prod/approve
```

---

### Step 9: Testing

**9.1 End-to-End Test**

```powershell
# Upload invoice
aws s3 cp sample_invoices/invoice_0006.pdf s3://invoice-automation-incoming-ag2026/

# Wait 60-70 seconds for processing

# Check database
python scripts/query_invoices.py

# Should see invoice with status 'pending_review'

# Check email for approval notification with links

# Click APPROVE link

# Verify status changed to 'approved'
python scripts/query_invoices.py
```

**9.2 Test Low-Value Invoice (Auto-Approve)**

```powershell
# Upload invoice < $50k
aws s3 cp sample_invoices/invoice_0001.pdf s3://invoice-automation-incoming-ag2026/

# Wait 60-70 seconds

# Check database - should be 'approved' automatically
python scripts/query_invoices.py
```

---

## Key Differences from Original Guide

### Architecture Changes

| Original Plan | What We Built | Why |
|--------------|---------------|-----|
| Step Functions orchestration | Direct S3 → Lambda triggers | Simpler, AWS best practice |
| 3 orchestrated Lambdas | 2 event-driven Lambdas + 1 API Lambda | Less complexity |
| EventBridge for routing | Native S3 event notifications | Built-in, no extra service |
| Manual Bedrock triggering | Lambda calls Bedrock API | Fully automated |

### Critical Implementation Details

**1. Bedrock Output Structure (IMPORTANT!)**
- Output path: `{job-id}/0/custom_output/0/result.json` (NOT `inference_results/`)
- Fields are flat in `inference_result` (no nested "value" keys)
- Confidence is 0-1 (multiply by 100)
- Profile ARN required: `us.data-automation-v1`

**2. Lambda boto3 Version**
- Must use boto3 >= 1.35.0 for `bedrock-data-automation-runtime` client
- Package latest boto3 with Lambda deployment
- Create client inside function (not at module level)

**3. Windows psycopg2 Installation**
```powershell
pip install --platform manylinux2014_x86_64 --target . --implementation cp --python-version 3.11 --only-binary=:all: --upgrade psycopg2-binary
```

**4. Database Schema Completeness**
- Must include ALL columns used by Lambda
- Key missing columns in initial attempts:
  - vendors: vendor_address, vendor_phone
  - invoices: po_number, payment_terms, payment_instructions
  - invoice_line_items: line_number

**5. S3 Bucket Path Issues**
- Bedrock output configuration: Use `s3://bucket` NOT `s3://bucket/`
- Trailing slash causes double slash: `s3://bucket//job-id/`

**6. High-Value Threshold**
- $50,000 threshold for manual approval
- Status: `approved` (auto), `pending_review` (manual), `rejected`, `failed`

---

## Utility Scripts to Include

**scripts/query_invoices.py**
```python
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
    SELECT i.invoice_id, i.invoice_number, v.vendor_name, i.total_amount, i.status
    FROM invoices i
    JOIN vendors v ON i.vendor_id = v.vendor_id
    ORDER BY i.processed_at DESC
    LIMIT 10
""")

print("\n=== Recent Invoices ===")
for row in cursor.fetchall():
    print(f"ID: {row[0]} | Invoice: {row[1]} | Vendor: {row[2]} | Amount: ${row[3]:,.2f} | Status: {row[4]}")

cursor.close()
conn.close()
```

**scripts/clear_database.py**
```python
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
```

---

## Costs (Actual)

**Development (Free Tier):**
- S3: $0.50/month
- RDS db.t3.micro: Free for 12 months
- Lambda: Free (< 1M invocations)
- Bedrock: $0.30 per 10 test invoices
- SNS/API Gateway: < $1/month
- **Total: ~$2-5/month**

**Production (1,000 invoices/month):**
- S3: $2/month
- RDS: $15/month
- Lambda: $0.20/month
- Bedrock: $30/month
- SNS/API Gateway: $2/month
- **Total: ~$50/month**

---

## Success Metrics

**Achieved:**
- ✅ 100% extraction accuracy (Bedrock confidence)
- ✅ ~60 seconds processing time per invoice
- ✅ Fully automated end-to-end
- ✅ Zero manual data entry
- ✅ High-value approval workflow
- ✅ Complete audit trail
- ✅ Production-ready code

---

## Troubleshooting Guide

### Issue: Lambda can't find `bedrock-data-automation-runtime`
**Solution:** Install boto3 >= 1.35.0 in Lambda package

### Issue: Database column doesn't exist
**Solution:** Use complete schema from Step 3.3

### Issue: Bedrock output has double slash in path
**Solution:** Remove trailing slash from output bucket configuration

### Issue: EventBridge not triggering
**Solution:** We don't use EventBridge! Use S3 event notifications directly

### Issue: Approval links show "None"
**Solution:** Set APPROVAL_API_ENDPOINT environment variable in InvoiceProcessorFunction

---

## Final Project Structure

```
invoice-automation-aws/
├── lambda_v2/
│   ├── bedrock_trigger/
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   ├── invoice_processor/
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   └── invoice_approval/
│       ├── lambda_function.py
│       └── requirements.txt
├── scripts/
│   ├── load_env.ps1
│   ├── query_invoices.py
│   ├── query_full_invoice.py
│   └── clear_database.py
├── sql/
│   └── complete_schema.sql
├── config/
│   └── .env
├── sample_invoices/
│   └── invoice_*.pdf
└── README.md
```

---

## Summary

This project successfully demonstrates:
- Modern serverless architecture (AWS best practices)
- AI/ML integration (Bedrock Data Automation)
- Event-driven design (S3 triggers)
- Database design (PostgreSQL with complete schema)
- API design (REST API with API Gateway)
- Security (Secrets Manager, IAM roles)
- Business workflows (approval process)
- Production-ready code (error handling, logging)

**Total Development Time:** ~15-20 hours over 2 sessions
**Complexity:** Intermediate to Advanced
**Technologies:** 10+ AWS services, Python, PostgreSQL
**Result:** Fully functional, production-ready invoice automation system

---

## Instructions for Claude Code

1. Create a new comprehensive technical guide PDF using this information
2. Use clear section headers and step-by-step instructions
3. Include all code snippets exactly as shown
4. Add architecture diagrams (describe in text if you can't generate images)
5. Emphasize the simplified architecture vs original plan
6. Include troubleshooting section
7. Add cost analysis
8. Include testing procedures
9. Format for professional presentation
10. Save as: `Portfolio_Project_1_Complete_Technical_Guide.pdf`

The guide should be:
- Beginner-friendly but technically accurate
- Include Windows-specific commands (PowerShell)
- Highlight AWS best practices
- Include actual working code (tested)
- Show complete end-to-end flow
- Emphasize simplicity of final design

---

**End of Instructions**
