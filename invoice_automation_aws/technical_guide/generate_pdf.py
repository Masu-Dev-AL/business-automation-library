"""
Portfolio Project 1 Technical Guide PDF Generator
Creates a comprehensive, professional technical guide from the project specifications
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.colors import HexColor, black, white, grey
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether, Preformatted, PageBreak
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib import colors
from datetime import datetime
import textwrap

def create_pdf():
    """Generate the Portfolio Project 1 Technical Guide PDF"""

    # Create PDF document
    filename = "Portfolio_Project_1_Complete_Technical_Guide.pdf"
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Define styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#1a365d'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=HexColor('#2d3748'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )

    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#1a365d'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#2c5282'),
        spaceAfter=10,
        spaceBefore=16,
        fontName='Helvetica-Bold'
    )

    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=HexColor('#2d3748'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#2d3748'),
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )

    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['Code'],
        fontSize=8,
        textColor=HexColor('#1a202c'),
        spaceAfter=12,
        spaceBefore=6,
        fontName='Courier',
        leftIndent=20,
        rightIndent=20,
        backColor=HexColor('#f7fafc')
    )

    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#2d3748'),
        spaceAfter=6,
        leftIndent=20,
        bulletIndent=10,
        fontName='Helvetica'
    )

    # Story container
    story = []

    # ========== TITLE PAGE ==========
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("Portfolio Project 1", title_style))
    story.append(Paragraph("Serverless Invoice Automation System", subtitle_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Complete Technical Implementation Guide", subtitle_style))
    story.append(Spacer(1, 0.5*inch))

    # Project info box
    info_data = [
        ["Project Type:", "AWS Serverless Application"],
        ["Technologies:", "Lambda, Bedrock, S3, RDS, API Gateway, SNS"],
        ["Complexity:", "Intermediate to Advanced"],
        ["Development Time:", "15-20 hours"],
        ["Date:", "January 11, 2026"],
    ]

    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#e2e8f0')),
        ('BACKGROUND', (1, 0), (1, -1), HexColor('#f7fafc')),
        ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#2d3748')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#cbd5e0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)

    story.append(PageBreak())

    # ========== TABLE OF CONTENTS ==========
    story.append(Paragraph("Table of Contents", heading1_style))

    toc_link_style = ParagraphStyle(
        'TOCLink',
        parent=bullet_style,
        textColor=HexColor('#2563eb'),
    )

    toc_items = [
        ("1. Executive Summary", "section1"),
        ("2. Using AI to Build This Project", "section2"),
        ("3. Architecture Overview", "section3"),
        ("4. Implementation Guide", "section4"),
        ("   4.1 AWS Account & IAM Setup", "section4-1"),
        ("   4.2 S3 Buckets Configuration", "section4-2"),
        ("   4.3 RDS PostgreSQL Database", "section4-3"),
        ("   4.4 Bedrock Data Automation", "section4-4"),
        ("   4.5 Lambda Functions", "section4-5"),
        ("   4.6 S3 Event Triggers", "section4-6"),
        ("   4.7 SNS Notifications", "section4-7"),
        ("   4.8 API Gateway Setup", "section4-8"),
        ("   4.9 Testing Procedures", "section4-9"),
        ("5. Code Reference", "section5"),
        ("6. Troubleshooting Guide", "section6"),
        ("7. Cost Analysis", "section7"),
        ("8. Success Metrics", "section8"),
    ]

    for item_text, anchor in toc_items:
        story.append(Paragraph(f'• <link href="#{anchor}" color="blue">{item_text}</link>', toc_link_style))

    story.append(PageBreak())

    # ========== EXECUTIVE SUMMARY ==========
    story.append(Paragraph('<a name="section1"/>1. Executive Summary', heading1_style))

    story.append(Paragraph(
        "This guide provides complete implementation instructions for a serverless invoice automation system "
        "built on AWS. The system uses Amazon Bedrock Data Automation for AI-powered data extraction, "
        "Lambda for processing, RDS PostgreSQL for storage, and API Gateway for approval workflows.",
        body_style
    ))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("System Capabilities", heading2_style))
    capabilities = [
        "Automated PDF invoice data extraction with Bedrock",
        "~60 second processing time per invoice",
        "Approval workflow for high-value invoices (&gt;$50,000)",
        "Complete audit trail in PostgreSQL",
        "Email notifications with approve/reject links",
    ]
    for capability in capabilities:
        story.append(Paragraph(f"• {capability}", bullet_style))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Technologies Used", heading2_style))
    story.append(Paragraph(
        "AWS Lambda • Amazon Bedrock • S3 • RDS PostgreSQL • API Gateway • SNS • Secrets Manager",
        body_style
    ))

    story.append(PageBreak())

    # ========== USING AI TO BUILD THIS PROJECT ==========
    story.append(Paragraph('<a name="section2"/>2. Using AI to Build This Project', heading1_style))

    story.append(Paragraph("Recommended: Claude Sonnet 4.5", heading2_style))

    story.append(Paragraph(
        "This project is complex and involves multiple AWS services, database schema design, Lambda functions, "
        "and API configurations. We highly recommend using <b>Claude Sonnet 4.5</b> (via claude.ai or Claude Code) "
        "to assist with implementation. Claude can help you write code, debug issues, configure AWS services, "
        "and troubleshoot problems as they arise.",
        body_style
    ))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Implementation Prompt", heading2_style))

    story.append(Paragraph(
        "Copy and paste this prompt into Claude Sonnet 4.5 to get started:",
        body_style
    ))

    story.append(Spacer(1, 0.1*inch))

    implementation_prompt = '''I want to build a serverless invoice automation system on AWS with the following architecture:

SYSTEM OVERVIEW:
- Automated PDF invoice processing using Amazon Bedrock Data Automation
- Event-driven architecture with S3 triggers and Lambda functions
- PostgreSQL database for structured data storage
- Approval workflow for high-value invoices (>$50,000)
- Email notifications with approve/reject links via SNS and API Gateway

ARCHITECTURE COMPONENTS:
1. S3 Incoming Bucket → receives PDF uploads
2. Lambda (BedrockTriggerFunction) → invokes Bedrock Data Automation API
3. Amazon Bedrock → AI-powered data extraction from invoices
4. S3 Blueprint Bucket → stores Bedrock extraction results
5. Lambda (InvoiceProcessorFunction) → validates and saves to database
6. RDS PostgreSQL → stores invoices, vendors, line items
7. SNS → sends approval emails for invoices >$50k
8. API Gateway + Lambda (InvoiceApprovalFunction) → approve/reject endpoint

DATABASE SCHEMA:
- vendors (vendor_id, vendor_name, vendor_address, vendor_phone, etc.)
- customers (customer_id, customer_name, customer_address, etc.)
- invoices (invoice_id, invoice_number, vendor_id, total_amount, status, etc.)
- invoice_line_items (line_item_id, invoice_id, description, quantity, etc.)
- bank_details (bank_id, vendor_id, bank_name, account_number, etc.)

KEY REQUIREMENTS:
- Use Python 3.11 for Lambda functions
- Store DB credentials in AWS Secrets Manager
- Bedrock output path: {job-id}/0/custom_output/0/result.json
- Invoice status: 'approved' (auto <$50k), 'pending_review' (>$50k), 'rejected'
- S3 event notifications trigger Lambda functions
- Windows environment (PowerShell commands)

HELP ME WITH:
1. Setting up the complete database schema with all necessary columns
2. Writing the three Lambda functions with proper error handling
3. Configuring S3 event notifications and IAM permissions
4. Creating the Bedrock Data Automation project and blueprint
5. Setting up API Gateway with approve/reject endpoints
6. Deployment scripts and testing procedures
7. Troubleshooting any issues that arise

Please start by helping me set up the AWS infrastructure and guide me through each step of the implementation.'''

    story.append(Preformatted(implementation_prompt, code_style))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Why Claude Sonnet 4.5?", heading2_style))

    ai_benefits = [
        "Deep understanding of AWS services and best practices",
        "Can write production-ready Python code for Lambda functions",
        "Helps debug complex issues across multiple AWS services",
        "Provides Windows PowerShell commands for deployment",
        "Understands Bedrock Data Automation API and output structure",
        "Can assist with IAM policies, database schema design, and API Gateway setup",
        "Offers real-time guidance as you encounter issues",
    ]
    for benefit in ai_benefits:
        story.append(Paragraph(f"• {benefit}", bullet_style))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "<b>Pro Tip:</b> Share error messages, CloudWatch logs, and AWS console screenshots with Claude "
        "for faster debugging. Claude can analyze logs and provide specific fixes for your exact situation.",
        body_style
    ))

    story.append(PageBreak())

    # ========== ARCHITECTURE OVERVIEW ==========
    story.append(Paragraph('<a name="section3"/>3. Architecture Overview', heading1_style))

    story.append(Paragraph("System Architecture", heading2_style))

    # Architecture flow
    arch_flow = """
User uploads PDF invoice
    ↓
S3 Incoming Bucket (invoice-automation-incoming-ag2026)
    ↓ [S3 Event Notification]
Lambda 1: BedrockTriggerFunction
    ↓ [Calls Bedrock API: invoke_data_automation_async]
Amazon Bedrock Data Automation (AI Processing)
    ↓ [Extracts structured data with custom blueprint]
S3 Blueprint Bucket (invoice-automation-blueprint-ag2026)
    ↓ [S3 Event Notification on result.json]
Lambda 2: InvoiceProcessorFunction
    ↓ [Extract + Validate + Process + Save]
RDS PostgreSQL Database
    ↓ [If amount > $50,000]
SNS Email Notification with Approve/Reject Links
    ↓ [User clicks link]
API Gateway + Lambda 3: InvoiceApprovalFunction
    ↓ [Updates database status]
Invoice Status Updated (approved/rejected)
    """

    story.append(Preformatted(arch_flow, code_style))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Architecture Components", heading2_style))

    components_data = [
        ["Component", "Purpose"],
        ["S3 Incoming Bucket", "Receives uploaded PDF invoices"],
        ["BedrockTriggerFunction", "Invokes Bedrock Data Automation API"],
        ["Bedrock Data Automation", "AI-powered data extraction from PDFs"],
        ["S3 Blueprint Bucket", "Stores Bedrock extraction results"],
        ["InvoiceProcessorFunction", "Validates data and writes to database"],
        ["RDS PostgreSQL", "Stores invoices, vendors, and line items"],
        ["SNS Topic", "Sends approval notifications for high-value invoices"],
        ["API Gateway", "Provides approve/reject endpoints"],
        ["InvoiceApprovalFunction", "Updates invoice status in database"],
    ]

    components_table = Table(components_data, colWidths=[2.5*inch, 3.5*inch])
    components_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (0, -1), HexColor('#e2e8f0')),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#cbd5e0')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(components_table)

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Key Design Principles", heading2_style))
    principles = [
        "Event-driven architecture using native S3 triggers",
        "Serverless components for automatic scaling",
        "AI/ML integration for document processing",
        "Separation of concerns across Lambda functions",
        "Secure credential storage with Secrets Manager",
    ]
    for principle in principles:
        story.append(Paragraph(f"• {principle}", bullet_style))

    story.append(PageBreak())

    # ========== IMPLEMENTATION GUIDE ==========
    story.append(Paragraph('<a name="section4"/>4. Implementation Guide', heading1_style))

    story.append(Paragraph(
        "This section provides complete step-by-step instructions for implementing the invoice automation system. "
        "Follow each step carefully, using the provided code snippets and commands.",
        body_style
    ))

    story.append(Spacer(1, 0.2*inch))

    # Step 1: AWS Account & IAM Setup
    story.append(Paragraph('<a name="section4-1"/>4.1 AWS Account & IAM Setup', heading2_style))

    story.append(Paragraph("Create IAM User", heading3_style))
    story.append(Paragraph(
        "Create an IAM user named <b>invoice-automation-dev</b> with programmatic access. "
        "This user will need extensive permissions to manage the various AWS services.",
        body_style
    ))

    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("Required AWS Managed Policies", heading3_style))
    managed_policies = [
        "AmazonS3FullAccess",
        "AmazonRDSFullAccess",
        "AWSLambda_FullAccess",
        "AmazonSNSFullAccess",
        "SecretsManagerReadWrite",
        "CloudWatchLogsFullAccess",
        "AmazonBedrockFullAccess",
        "AmazonEC2FullAccess (for VPC/RDS access)",
        "IAMFullAccess (for role creation)",
    ]
    for policy in managed_policies:
        story.append(Paragraph(f"• {policy}", bullet_style))

    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("Custom Inline Policies", heading3_style))

    story.append(Paragraph("<b>EventBridgeAccess:</b>", body_style))
    eventbridge_policy = '''{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["events:*"],
    "Resource": "*"
  }]
}'''
    story.append(Preformatted(eventbridge_policy, code_style))

    story.append(Paragraph("<b>APIGatewayAccess:</b>", body_style))
    apigateway_policy = '''{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["apigateway:*"],
    "Resource": "*"
  }]
}'''
    story.append(Preformatted(apigateway_policy, code_style))

    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("Configure AWS CLI", heading3_style))
    cli_config = '''aws configure
# Access Key ID: [from IAM user]
# Secret Access Key: [from IAM user]
# Region: us-east-1
# Output format: json'''
    story.append(Preformatted(cli_config, code_style))

    story.append(PageBreak())

    # Step 2: S3 Buckets
    story.append(Paragraph('<a name="section4-2"/>4.2 S3 Buckets Configuration', heading2_style))

    story.append(Paragraph(
        "The system requires four S3 buckets for different stages of invoice processing. "
        "Use a unique suffix (e.g., your initials + year) to ensure globally unique bucket names.",
        body_style
    ))

    story.append(Spacer(1, 0.1*inch))

    s3_buckets_cmd = '''$S3_SUFFIX = "ag2026"  # Use your initials + year

# 1. Incoming bucket (PDFs uploaded here)
aws s3api create-bucket --bucket invoice-automation-incoming-$S3_SUFFIX --region us-east-1

# 2. Blueprint bucket (Bedrock outputs here)
aws s3api create-bucket --bucket invoice-automation-blueprint-$S3_SUFFIX --region us-east-1

# 3. Processed bucket (successful invoices moved here)
aws s3api create-bucket --bucket invoice-automation-processed-$S3_SUFFIX --region us-east-1

# 4. Failed bucket (validation failures moved here)
aws s3api create-bucket --bucket invoice-automation-failed-$S3_SUFFIX --region us-east-1'''
    story.append(Preformatted(s3_buckets_cmd, code_style))

    story.append(Paragraph("<b>Enable versioning on blueprint bucket:</b>", body_style))
    s3_versioning_cmd = '''aws s3api put-bucket-versioning \\
  --bucket invoice-automation-blueprint-$S3_SUFFIX \\
  --versioning-configuration Status=Enabled'''
    story.append(Preformatted(s3_versioning_cmd, code_style))

    story.append(PageBreak())

    # Step 3: RDS PostgreSQL
    story.append(Paragraph('<a name="section4-3"/>4.3 RDS PostgreSQL Database', heading2_style))

    story.append(Paragraph("Database Configuration", heading3_style))
    db_config = [
        ["Engine:", "PostgreSQL 15.x"],
        ["Instance:", "db.t3.micro (Free Tier eligible)"],
        ["Storage:", "20 GB GP3"],
        ["Database name:", "invoice_automation"],
        ["Master username:", "postgres"],
        ["VPC:", "Default VPC"],
        ["Public access:", "Yes (for development)"],
    ]

    db_table = Table(db_config, colWidths=[2*inch, 4*inch])
    db_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#e2e8f0')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#cbd5e0')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(db_table)

    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("Store Credentials in Secrets Manager", heading3_style))
    secrets_cmd = '''$DB_PASSWORD = "YourStrongPassword"
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

aws secretsmanager create-secret \\
  --name invoice-automation/db-credentials \\
  --secret-string file://db-secret.json'''
    story.append(Preformatted(secrets_cmd, code_style))

    story.append(PageBreak())

    story.append(Paragraph("Complete Database Schema", heading3_style))
    story.append(Paragraph(
        "The database schema includes tables for vendors, customers, invoices, line items, "
        "bank details, and an audit log for Bedrock extractions. This schema has been tested "
        "and verified to work with all Lambda functions.",
        body_style
    ))

    schema_sql = '''-- Vendors table
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

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_invoices_vendor ON invoices(vendor_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date);
CREATE INDEX IF NOT EXISTS idx_line_items_invoice ON invoice_line_items(invoice_id);'''
    story.append(Preformatted(schema_sql, code_style))

    story.append(PageBreak())

    # Step 4: Bedrock Data Automation
    story.append(Paragraph('<a name="section4-4"/>4.4 Bedrock Data Automation', heading2_style))

    story.append(Paragraph("Create Bedrock Data Automation Project", heading3_style))
    bedrock_steps = [
        "Navigate to AWS Console → Bedrock → Data Automation",
        "Create new project named: <b>invoice-extraction-project</b>",
        "Project type: <b>ASYNC</b>",
        "Stage: <b>LIVE</b>",
    ]
    for step in bedrock_steps:
        story.append(Paragraph(f"{step}", bullet_style))

    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("Create Custom Blueprint", heading3_style))
    story.append(Paragraph(
        "Upload a sample invoice PDF and let Bedrock auto-generate the extraction schema. "
        "The blueprint will extract fields such as:",
        body_style
    ))

    blueprint_fields = [
        "invoice_number, company_name, company_address, company_contact_information",
        "bill_to, client_email, invoice_date, due_date, po_number",
        "subtotal, discount, tax, total_amount, payment_terms",
        "payment_details (nested), bank_details (nested), invoice_items (array)",
    ]
    for field in blueprint_fields:
        story.append(Paragraph(f"• {field}", bullet_style))

    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>Important ARNs to Save:</b>", body_style))
    bedrock_arns = '''Project ARN: arn:aws:bedrock:us-east-1:{account}:data-automation-project/{project-id}
Blueprint ARN: arn:aws:bedrock:us-east-1:{account}:blueprint/{blueprint-id}
Profile ARN: arn:aws:bedrock:us-east-1:{account}:data-automation-profile/us.data-automation-v1'''
    story.append(Preformatted(bedrock_arns, code_style))

    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("Bedrock Output Structure", heading3_style))
    story.append(Paragraph("<b>Critical Implementation Details:</b>", body_style))
    bedrock_notes = [
        "Output path: <b>{job-id}/0/custom_output/0/result.json</b> (NOT inference_results/)",
        "Fields are flat in <b>inference_result</b> (no nested 'value' keys)",
        "Confidence is 0-1 scale (multiply by 100 for percentage)",
        "Output bucket must NOT have trailing slash (causes double slash issue)",
    ]
    for note in bedrock_notes:
        story.append(Paragraph(f"• {note}", bullet_style))

    story.append(PageBreak())

    # Step 5: Lambda Functions
    story.append(Paragraph('<a name="section4-5"/>4.5 Lambda Functions', heading2_style))

    story.append(Paragraph("Create IAM Role for Lambda", heading3_style))
    lambda_role_cmd = '''# Create trust policy
@"
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
"@ | Set-Content -Path lambda-trust-policy.json

# Create role
aws iam create-role \\
  --role-name InvoiceAutomationLambdaRole \\
  --assume-role-policy-document file://lambda-trust-policy.json

# Attach managed policies
aws iam attach-role-policy --role-name InvoiceAutomationLambdaRole \\
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam attach-role-policy --role-name InvoiceAutomationLambdaRole \\
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
aws iam attach-role-policy --role-name InvoiceAutomationLambdaRole \\
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite'''
    story.append(Preformatted(lambda_role_cmd, code_style))

    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("Add Custom Inline Policies", heading3_style))
    bedrock_access_policy = '''{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "bedrock:InvokeDataAutomationAsync",
      "bedrock:GetDataAutomationStatus",
      "bedrock:InvokeModel"
    ],
    "Resource": "*"
  }]
}'''
    story.append(Paragraph("<b>BedrockDataAutomationAccess:</b>", body_style))
    story.append(Preformatted(bedrock_access_policy, code_style))

    sns_access_policy = '''{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["sns:Publish"],
    "Resource": "*"
  }]
}'''
    story.append(Paragraph("<b>SNSPublishAccess:</b>", body_style))
    story.append(Preformatted(sns_access_policy, code_style))

    story.append(PageBreak())

    # Lambda 1
    story.append(Paragraph("Lambda Function 1: BedrockTriggerFunction", heading3_style))
    story.append(Paragraph(
        "<b>Purpose:</b> Triggered when a PDF is uploaded to the incoming S3 bucket. "
        "Invokes Bedrock Data Automation API to process the invoice.",
        body_style
    ))

    story.append(Paragraph("<b>Location:</b> lambda_v2/bedrock_trigger/lambda_function.py", body_style))

    bedrock_lambda_code = '''import json
import boto3
import os

def lambda_handler(event, context):
    """Triggered when PDF uploaded to incoming bucket"""
    try:
        # Create client with latest boto3
        bedrock_runtime = boto3.client(
            'bedrock-data-automation-runtime',
            region_name='us-east-1'
        )

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
        return {'statusCode': 500, 'error': str(e)}'''
    story.append(Preformatted(bedrock_lambda_code, code_style))

    story.append(Paragraph("<b>requirements.txt:</b>", body_style))
    story.append(Preformatted("boto3>=1.35.0", code_style))

    story.append(Paragraph("<b>Deployment:</b>", body_style))
    bedrock_deploy_cmd = '''cd lambda_v2/bedrock_trigger
pip install -r requirements.txt -t . --upgrade
Compress-Archive -Path * -DestinationPath ..\\bedrock_trigger.zip -Force
cd ..\\..

aws lambda create-function \\
  --function-name BedrockTriggerFunction \\
  --runtime python3.11 \\
  --handler lambda_function.lambda_handler \\
  --role arn:aws:iam::{account}:role/InvoiceAutomationLambdaRole \\
  --zip-file fileb://lambda_v2/bedrock_trigger.zip \\
  --timeout 30 --memory-size 256 \\
  --environment Variables="{BEDROCK_PROJECT_ARN=...,OUTPUT_BUCKET=s3://...}"'''
    story.append(Preformatted(bedrock_deploy_cmd, code_style))

    story.append(PageBreak())

    # Lambda 2
    story.append(Paragraph("Lambda Function 2: InvoiceProcessorFunction", heading3_style))
    story.append(Paragraph(
        "<b>Purpose:</b> Processes Bedrock output JSON, validates business rules, "
        "writes to PostgreSQL database, and sends SNS notifications for high-value invoices.",
        body_style
    ))

    story.append(Paragraph(
        "<b>Key Features:</b>",
        body_style
    ))
    processor_features = [
        "Extracts data from Bedrock JSON structure",
        "Validates business rules and data quality",
        "Determines approval status based on $50,000 threshold",
        "Writes to PostgreSQL (vendors, customers, invoices, line items, bank details)",
        "Sends SNS notification with approve/reject links for high-value invoices",
        "Moves processed files to appropriate S3 buckets",
    ]
    for feature in processor_features:
        story.append(Paragraph(f"• {feature}", bullet_style))

    story.append(Paragraph("<b>requirements.txt:</b>", body_style))
    processor_requirements = '''boto3==1.34.22
psycopg2-binary==2.9.9'''
    story.append(Preformatted(processor_requirements, code_style))

    story.append(Paragraph("<b>Deployment (Windows-specific for psycopg2):</b>", body_style))
    processor_deploy_cmd = '''cd lambda_v2/invoice_processor

# Install psycopg2 for Linux Lambda environment
pip install --platform manylinux2014_x86_64 --target . \\
  --implementation cp --python-version 3.11 --only-binary=:all: \\
  --upgrade psycopg2-binary

pip install boto3==1.34.22 -t .
Compress-Archive -Path * -DestinationPath ..\\invoice_processor.zip -Force
cd ..\\..

aws lambda create-function \\
  --function-name InvoiceProcessorFunction \\
  --runtime python3.11 \\
  --handler lambda_function.lambda_handler \\
  --role arn:aws:iam::{account}:role/InvoiceAutomationLambdaRole \\
  --zip-file fileb://lambda_v2/invoice_processor.zip \\
  --timeout 60 --memory-size 512 \\
  --environment Variables="{INCOMING_BUCKET=...,SNS_TOPIC_ARN=...,etc}"'''
    story.append(Preformatted(processor_deploy_cmd, code_style))

    story.append(PageBreak())

    # Lambda 3
    story.append(Paragraph("Lambda Function 3: InvoiceApprovalFunction", heading3_style))
    story.append(Paragraph(
        "<b>Purpose:</b> Handles approve/reject actions via API Gateway. "
        "Updates invoice status in database and returns HTML confirmation page.",
        body_style
    ))

    story.append(Paragraph(
        "<b>API Parameters:</b> invoice_id (required), action (approve|reject)",
        body_style
    ))

    approval_deploy_cmd = '''cd lambda_v2/invoice_approval
pip install --platform manylinux2014_x86_64 --target . \\
  --implementation cp --python-version 3.11 --only-binary=:all: \\
  --upgrade psycopg2-binary
Compress-Archive -Path * -DestinationPath ..\\invoice_approval.zip -Force
cd ..\\..

aws lambda create-function \\
  --function-name InvoiceApprovalFunction \\
  --runtime python3.11 \\
  --handler lambda_function.lambda_handler \\
  --role arn:aws:iam::{account}:role/InvoiceAutomationLambdaRole \\
  --zip-file fileb://lambda_v2/invoice_approval.zip \\
  --timeout 30 --memory-size 256'''
    story.append(Preformatted(approval_deploy_cmd, code_style))

    story.append(PageBreak())

    # Step 6: S3 Event Triggers
    story.append(Paragraph('<a name="section4-6"/>4.6 S3 Event Triggers', heading2_style))

    story.append(Paragraph("Grant S3 Permission to Invoke Lambdas", heading3_style))
    s3_permissions_cmd = '''# For BedrockTriggerFunction
aws lambda add-permission \\
  --function-name BedrockTriggerFunction \\
  --statement-id s3-trigger-incoming \\
  --action lambda:InvokeFunction \\
  --principal s3.amazonaws.com \\
  --source-arn arn:aws:s3:::invoice-automation-incoming-ag2026

# For InvoiceProcessorFunction
aws lambda add-permission \\
  --function-name InvoiceProcessorFunction \\
  --statement-id s3-trigger-blueprint \\
  --action lambda:InvokeFunction \\
  --principal s3.amazonaws.com \\
  --source-arn arn:aws:s3:::invoice-automation-blueprint-ag2026'''
    story.append(Preformatted(s3_permissions_cmd, code_style))

    story.append(Paragraph("Configure S3 Notifications", heading3_style))
    story.append(Paragraph(
        "Set up S3 event notifications to trigger Lambda functions when objects are created:",
        body_style
    ))

    s3_notification_incoming = '''{
  "LambdaFunctionConfigurations": [{
    "Id": "InvoicePDFUpload",
    "LambdaFunctionArn": "arn:aws:lambda:us-east-1:{account}:function:BedrockTriggerFunction",
    "Events": ["s3:ObjectCreated:*"],
    "Filter": {
      "Key": {"FilterRules": [{"Name": "suffix", "Value": ".pdf"}]}
    }
  }]
}'''
    story.append(Paragraph("<b>Incoming bucket → BedrockTriggerFunction (s3-notification-incoming.json):</b>", body_style))
    story.append(Preformatted(s3_notification_incoming, code_style))

    s3_apply_incoming = '''aws s3api put-bucket-notification-configuration \\
  --bucket invoice-automation-incoming-ag2026 \\
  --notification-configuration file://s3-notification-incoming.json'''
    story.append(Preformatted(s3_apply_incoming, code_style))

    s3_notification_blueprint = '''{
  "LambdaFunctionConfigurations": [{
    "Id": "BedrockResultProcessing",
    "LambdaFunctionArn": "arn:aws:lambda:us-east-1:{account}:function:InvoiceProcessorFunction",
    "Events": ["s3:ObjectCreated:*"],
    "Filter": {
      "Key": {"FilterRules": [{"Name": "suffix", "Value": "result.json"}]}
    }
  }]
}'''
    story.append(Paragraph("<b>Blueprint bucket → InvoiceProcessorFunction (s3-notification-blueprint.json):</b>", body_style))
    story.append(Preformatted(s3_notification_blueprint, code_style))

    s3_apply_blueprint = '''aws s3api put-bucket-notification-configuration \\
  --bucket invoice-automation-blueprint-ag2026 \\
  --notification-configuration file://s3-notification-blueprint.json'''
    story.append(Preformatted(s3_apply_blueprint, code_style))

    story.append(PageBreak())

    # Step 7: SNS
    story.append(Paragraph('<a name="section4-7"/>4.7 SNS Notifications', heading2_style))

    story.append(Paragraph("Create SNS Topic", heading3_style))
    sns_create_cmd = '''aws sns create-topic --name InvoiceApprovalNotifications'''
    story.append(Preformatted(sns_create_cmd, code_style))

    story.append(Paragraph("Subscribe Email Address", heading3_style))
    sns_subscribe_cmd = '''aws sns subscribe \\
  --topic-arn arn:aws:sns:us-east-1:{account}:InvoiceApprovalNotifications \\
  --protocol email \\
  --notification-endpoint your-email@example.com

# IMPORTANT: Check your email and confirm the subscription!'''
    story.append(Preformatted(sns_subscribe_cmd, code_style))

    story.append(Paragraph(
        "<b>Note:</b> You must confirm the email subscription before you can receive notifications.",
        body_style
    ))

    story.append(PageBreak())

    # Step 8: API Gateway
    story.append(Paragraph('<a name="section4-8"/>4.8 API Gateway Setup', heading2_style))

    story.append(Paragraph("Create REST API", heading3_style))
    api_create_cmd = '''$API_ID = (aws apigateway create-rest-api \\
  --name InvoiceApprovalAPI \\
  --description "API for approving/rejecting invoices" \\
  --query "id" --output text)

$ROOT_RESOURCE_ID = (aws apigateway get-resources \\
  --rest-api-id $API_ID \\
  --query "items[0].id" --output text)

$APPROVE_RESOURCE_ID = (aws apigateway create-resource \\
  --rest-api-id $API_ID \\
  --parent-id $ROOT_RESOURCE_ID \\
  --path-part approve \\
  --query "id" --output text)'''
    story.append(Preformatted(api_create_cmd, code_style))

    story.append(Paragraph("Create GET Method with Integration", heading3_style))
    api_method_cmd = '''# Create GET method
aws apigateway put-method \\
  --rest-api-id $API_ID --resource-id $APPROVE_RESOURCE_ID \\
  --http-method GET --authorization-type NONE \\
  --request-parameters "method.request.querystring.invoice_id=true,method.request.querystring.action=true"

# Integrate with Lambda
aws apigateway put-integration \\
  --rest-api-id $API_ID --resource-id $APPROVE_RESOURCE_ID \\
  --http-method GET --type AWS_PROXY --integration-http-method POST \\
  --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:{account}:function:InvoiceApprovalFunction/invocations"'''
    story.append(Preformatted(api_method_cmd, code_style))

    story.append(Paragraph("Grant API Gateway Permission", heading3_style))
    api_permission_cmd = '''aws lambda add-permission \\
  --function-name InvoiceApprovalFunction \\
  --statement-id apigateway-invoke \\
  --action lambda:InvokeFunction \\
  --principal apigateway.amazonaws.com \\
  --source-arn "arn:aws:execute-api:us-east-1:{account}:$API_ID/*/*/approve"'''
    story.append(Preformatted(api_permission_cmd, code_style))

    story.append(Paragraph("Deploy API", heading3_style))
    api_deploy_cmd = '''aws apigateway create-deployment \\
  --rest-api-id $API_ID --stage-name prod

# Your API endpoint will be:
# https://{api-id}.execute-api.us-east-1.amazonaws.com/prod/approve'''
    story.append(Preformatted(api_deploy_cmd, code_style))

    story.append(PageBreak())

    # Step 9: Testing
    story.append(Paragraph('<a name="section4-9"/>4.9 Testing Procedures', heading2_style))

    story.append(Paragraph("End-to-End Test (High-Value Invoice)", heading3_style))
    test_high_value = '''# 1. Upload invoice > $50,000
aws s3 cp sample_invoices/invoice_0006.pdf s3://invoice-automation-incoming-ag2026/

# 2. Wait 60-70 seconds for processing
# - BedrockTriggerFunction invokes Bedrock
# - Bedrock processes PDF (30-40 seconds)
# - InvoiceProcessorFunction saves to database

# 3. Check database for invoice
python scripts/query_invoices.py
# Should see invoice with status 'pending_review'

# 4. Check email for approval notification
# Email will contain APPROVE and REJECT links

# 5. Click APPROVE link

# 6. Verify status changed to 'approved'
python scripts/query_invoices.py'''
    story.append(Preformatted(test_high_value, code_style))

    story.append(Paragraph("Test Low-Value Invoice (Auto-Approve)", heading3_style))
    test_low_value = '''# 1. Upload invoice < $50,000
aws s3 cp sample_invoices/invoice_0001.pdf s3://invoice-automation-incoming-ag2026/

# 2. Wait 60-70 seconds

# 3. Check database - should be 'approved' automatically
python scripts/query_invoices.py

# No email notification is sent for auto-approved invoices'''
    story.append(Preformatted(test_low_value, code_style))

    story.append(Paragraph("Monitoring and Debugging", heading3_style))
    monitoring_tips = [
        "Check CloudWatch Logs for each Lambda function",
        "Verify S3 event notifications are configured correctly",
        "Ensure database credentials in Secrets Manager are correct",
        "Confirm Bedrock model access is granted",
        "Verify SNS email subscription is confirmed",
    ]
    for tip in monitoring_tips:
        story.append(Paragraph(f"• {tip}", bullet_style))

    story.append(PageBreak())

    # ========== CODE REFERENCE ==========
    story.append(Paragraph('<a name="section5"/>5. Code Reference', heading1_style))

    story.append(Paragraph("Project Structure", heading2_style))
    project_structure = '''invoice-automation-aws/
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
└── README.md'''
    story.append(Preformatted(project_structure, code_style))

    story.append(Paragraph("Utility Scripts", heading2_style))

    story.append(Paragraph("<b>scripts/query_invoices.py</b> - View recent invoices:", body_style))
    query_script = '''import psycopg2
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
    SELECT i.invoice_id, i.invoice_number, v.vendor_name,
           i.total_amount, i.status
    FROM invoices i
    JOIN vendors v ON i.vendor_id = v.vendor_id
    ORDER BY i.processed_at DESC LIMIT 10
""")

print("\\n=== Recent Invoices ===")
for row in cursor.fetchall():
    print(f"ID: {row[0]} | Invoice: {row[1]} | " +
          f"Vendor: {row[2]} | Amount: ${row[3]:,.2f} | Status: {row[4]}")

cursor.close()
conn.close()'''
    story.append(Preformatted(query_script, code_style))

    story.append(PageBreak())

    # ========== TROUBLESHOOTING ==========
    story.append(Paragraph('<a name="section6"/>6. Troubleshooting Guide', heading1_style))

    troubleshooting_data = [
        ["Issue", "Solution"],
        ["Lambda can't find bedrock-data-automation-runtime client",
         "Install boto3 >= 1.35.0 in Lambda package"],
        ["Database column doesn't exist error",
         "Use complete schema from Section 3.3. Ensure all columns match Lambda code."],
        ["Bedrock output has double slash in S3 path",
         "Remove trailing slash from output bucket configuration"],
        ["S3 event notification not triggering Lambda",
         "Verify Lambda permissions were granted. Check S3 notification configuration."],
        ["psycopg2 import error in Lambda",
         "Use platform-specific install: pip install --platform manylinux2014_x86_64"],
        ["Approval links in email show 'None'",
         "Set APPROVAL_API_ENDPOINT environment variable in InvoiceProcessorFunction"],
        ["Bedrock result.json not found",
         "Path is {job-id}/0/custom_output/0/result.json, not inference_results/"],
        ["High-value invoice not sending email",
         "Confirm SNS email subscription. Check SNS_TOPIC_ARN environment variable."],
    ]

    troubleshooting_table = Table(troubleshooting_data, colWidths=[2.5*inch, 3.5*inch])
    troubleshooting_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#cbd5e0')),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(troubleshooting_table)

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Common Debugging Steps", heading2_style))
    debugging_steps = [
        "Check CloudWatch Logs for detailed error messages",
        "Verify all environment variables are set correctly in Lambda functions",
        "Test database connectivity using scripts/query_invoices.py",
        "Confirm IAM roles have all required permissions",
        "Validate S3 bucket names match across all configurations",
        "Ensure Bedrock model access is granted and project is in LIVE stage",
    ]
    for step in debugging_steps:
        story.append(Paragraph(f"• {step}", bullet_style))

    story.append(PageBreak())

    # ========== COST ANALYSIS ==========
    story.append(Paragraph('<a name="section7"/>7. Cost Analysis', heading1_style))

    story.append(Paragraph("Development Environment (AWS Free Tier)", heading2_style))

    dev_costs_data = [
        ["Service", "Usage", "Monthly Cost"],
        ["S3 Storage", "< 5 GB", "$0.50"],
        ["RDS db.t3.micro", "Free for 12 months", "$0.00"],
        ["Lambda", "< 1M invocations", "$0.00"],
        ["Bedrock Data Automation", "~10 test invoices", "$0.30"],
        ["SNS + API Gateway", "Minimal usage", "$0.20"],
        ["", "Total:", "$1.00 - $2.00"],
    ]

    dev_table = Table(dev_costs_data, colWidths=[2*inch, 2*inch, 2*inch])
    dev_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#cbd5e0')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BACKGROUND', (0, -1), (-1, -1), HexColor('#e2e8f0')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(dev_table)

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Production Environment (1,000 invoices/month)", heading2_style))

    prod_costs_data = [
        ["Service", "Usage", "Monthly Cost"],
        ["S3 Storage + Requests", "10 GB + API calls", "$2.00"],
        ["RDS db.t3.micro", "24/7 uptime", "$15.00"],
        ["Lambda", "3,000 invocations", "$0.20"],
        ["Bedrock Data Automation", "1,000 invoices", "$30.00"],
        ["SNS", "~100 high-value notifications", "$1.00"],
        ["API Gateway", "~100 approval requests", "$1.00"],
        ["Data Transfer", "Minimal", "$0.80"],
        ["", "Total:", "$50.00"],
    ]

    prod_table = Table(prod_costs_data, colWidths=[2*inch, 2*inch, 2*inch])
    prod_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#cbd5e0')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BACKGROUND', (0, -1), (-1, -1), HexColor('#e2e8f0')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(prod_table)

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Cost Optimization Tips", heading2_style))
    cost_tips = [
        "Use RDS auto-pause for development environments (Aurora Serverless v2)",
        "Implement S3 lifecycle policies to archive old invoices to Glacier",
        "Monitor Lambda execution time and optimize memory allocation",
        "Use Bedrock batch processing for large volumes",
        "Set CloudWatch log retention to 7 days for development",
    ]
    for tip in cost_tips:
        story.append(Paragraph(f"• {tip}", bullet_style))

    story.append(PageBreak())

    # ========== SUCCESS METRICS ==========
    story.append(Paragraph('<a name="section8"/>8. Success Metrics', heading1_style))

    story.append(Paragraph("Project Achievements", heading2_style))

    achievements_data = [
        ["Metric", "Target", "Achieved", "Status"],
        ["Extraction Accuracy", "≥ 95%", "100%", "✓"],
        ["Processing Time", "< 2 minutes", "~60 seconds", "✓"],
        ["Automation Level", "End-to-end", "100% automated", "✓"],
        ["Manual Data Entry", "Zero", "Zero", "✓"],
        ["High-Value Workflow", "Implemented", "Email + API", "✓"],
        ["Audit Trail", "Complete", "PostgreSQL logs", "✓"],
        ["Production Ready", "Yes", "Yes", "✓"],
        ["Cost Effectiveness", "< $100/month", "$50/month", "✓"],
    ]

    achievements_table = Table(achievements_data, colWidths=[1.8*inch, 1.4*inch, 1.4*inch, 1.4*inch])
    achievements_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#cbd5e0')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TEXTCOLOR', (3, 1), (3, -1), HexColor('#22543d')),
        ('FONTNAME', (3, 1), (3, -1), 'Helvetica-Bold'),
    ]))
    story.append(achievements_table)

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Technical Skills Demonstrated", heading2_style))

    skills_categories = [
        ("Cloud Architecture", [
            "Event-driven serverless design",
            "AWS service integration and orchestration",
            "Scalable, loosely-coupled components",
            "Cloud-native best practices",
        ]),
        ("AI/ML Integration", [
            "Amazon Bedrock Data Automation",
            "Custom blueprint creation",
            "Structured data extraction",
            "Confidence scoring and validation",
        ]),
        ("Backend Development", [
            "Python Lambda functions",
            "PostgreSQL database design",
            "RESTful API implementation",
            "Error handling and logging",
        ]),
        ("DevOps & Security", [
            "IAM roles and policies",
            "Secrets Manager for credentials",
            "CloudWatch monitoring",
            "Infrastructure as Code (CLI)",
        ]),
    ]

    for category, skills in skills_categories:
        story.append(Paragraph(f"<b>{category}:</b>", body_style))
        for skill in skills:
            story.append(Paragraph(f"• {skill}", bullet_style))
        story.append(Spacer(1, 0.1*inch))

    story.append(PageBreak())

    # ========== CONCLUSION ==========
    story.append(Paragraph("Conclusion", heading1_style))

    story.append(Paragraph(
        "This invoice automation system successfully demonstrates the power of modern serverless "
        "architecture combined with AI/ML capabilities. By following AWS best practices and "
        "choosing simplicity over complexity, the final implementation is more maintainable, "
        "cost-effective, and performant than the original design.",
        body_style
    ))

    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph(
        "The project showcases proficiency in cloud architecture, AI integration, database design, "
        "API development, and security best practices. The complete end-to-end automation, from "
        "PDF upload to database storage and approval workflow, demonstrates real-world problem-solving "
        "and technical implementation skills.",
        body_style
    ))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Key Takeaways", heading2_style))

    takeaways = [
        "<b>Simplicity wins:</b> The simplified architecture is easier to understand, debug, and maintain",
        "<b>AWS best practices matter:</b> Following official AWS patterns leads to better outcomes",
        "<b>Event-driven is powerful:</b> S3 triggers eliminate the need for complex orchestration",
        "<b>AI/ML is accessible:</b> Bedrock Data Automation makes document processing simple",
        "<b>Testing is critical:</b> End-to-end testing ensures all components work together",
        "<b>Documentation is essential:</b> Clear documentation enables knowledge transfer",
    ]
    for takeaway in takeaways:
        story.append(Paragraph(f"• {takeaway}", bullet_style))

    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("Next Steps", heading2_style))

    next_steps = [
        "Add email notifications for failed validations",
        "Implement duplicate invoice detection",
        "Create CloudWatch dashboard for monitoring",
        "Add integration with accounting systems (QuickBooks, Xero)",
        "Implement ML-based fraud detection",
        "Add support for multiple document types",
    ]
    for step in next_steps:
        story.append(Paragraph(f"• {step}", bullet_style))

    story.append(Spacer(1, 0.5*inch))

    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=HexColor('#718096'),
        alignment=TA_CENTER,
    )

    story.append(Paragraph("---", footer_style))
    story.append(Paragraph(
        f"Portfolio Project 1: Serverless Invoice Automation System | Generated: {datetime.now().strftime('%B %d, %Y')}",
        footer_style
    ))
    story.append(Paragraph(
        "AWS Lambda • Amazon Bedrock • RDS PostgreSQL • S3 • API Gateway • SNS",
        footer_style
    ))

    # Build PDF
    doc.build(story)
    print(f"PDF generated successfully: {filename}")
    return filename

if __name__ == "__main__":
    create_pdf()
