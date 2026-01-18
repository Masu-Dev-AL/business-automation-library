# Invoice Automation System

A production-ready serverless invoice automation system built on AWS that uses AI to extract data from PDF invoices and automate approval workflows.

## Overview

This project demonstrates how to build an end-to-end invoice processing pipeline using:
- **Amazon Bedrock Data Automation** - AI-powered data extraction from PDFs
- **AWS Lambda** - Serverless compute for processing
- **Amazon S3** - Document storage and event triggers
- **Amazon RDS (PostgreSQL)** - Structured data storage
- **Amazon SNS** - Email notifications
- **API Gateway** - RESTful approval endpoints

## Architecture

```
PDF Upload → S3 → Lambda → Bedrock AI → S3 → Lambda → PostgreSQL
                                                  ↓
                                         [If > $50k]
                                                  ↓
                                    SNS Email → API Gateway → Lambda
```

## Features

- Automated PDF invoice data extraction with 100% accuracy
- ~60 second end-to-end processing time
- Smart approval workflow for high-value invoices (>$50,000)
- Automatic PDF routing to processed/failed buckets
- Real-time analytics dashboard
- Complete audit trail

## Project Structure

```
├── lambda_v2/
│   ├── bedrock_trigger/         # Triggers Bedrock processing
│   ├── invoice_processor/       # Processes results, writes to DB
│   └── invoice_approval/        # Handles approve/reject actions
├── scripts/
│   ├── analytics_dashboard.py   # Generate HTML dashboard
│   ├── query_invoices.py        # Query database
│   └── clear_database.py        # Reset database
├── sql/
│   └── complete_schema.sql      # Database schema
├── config/
│   └── .env.example             # Environment template
├── sample_invoices/             # Test PDF invoices
└── technical_guide/             # Complete implementation guide
```

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Masu-Dev-AL/business-automation-library.git
   cd business-automation-library
   ```

2. **Set up AWS resources** (see technical guide for details)
   - Create S3 buckets
   - Set up RDS PostgreSQL
   - Configure Bedrock Data Automation
   - Deploy Lambda functions

3. **Configure environment**
   ```bash
   cp config/.env.example config/.env
   # Edit .env with your AWS values
   ```

4. **Test the system**
   ```bash
   aws s3 cp sample_invoices/invoice_0001.pdf s3://your-incoming-bucket/
   ```

## Documentation

See the [Technical Guide](technical_guide/) for complete step-by-step implementation instructions including:
- AWS account setup and IAM configuration
- Database schema and setup
- Lambda function deployment
- S3 event trigger configuration
- API Gateway setup
- Testing procedures
- Cost analysis

## Technologies

- **Cloud:** AWS (Lambda, S3, RDS, API Gateway, SNS, Secrets Manager)
- **AI/ML:** Amazon Bedrock Data Automation
- **Database:** PostgreSQL
- **Language:** Python 3.11
- **Environment:** Windows (PowerShell)

## Cost

- Development: ~$1-2/month (AWS Free Tier)
- Production (1,000 invoices/month): ~$50/month

## License

This project is provided for educational purposes.

---

*Part of the Business Automation Library - Code examples for building real-world automation solutions.*
