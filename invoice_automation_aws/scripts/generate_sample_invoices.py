#!/usr/bin/env python3
"""
Generate sample invoice PDFs for testing the automation system
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from faker import Faker
from datetime import datetime, timedelta
import random
import os

fake = Faker()

def generate_invoice_pdf(invoice_number, output_dir='sample_invoices'):
    """Generate a single invoice PDF"""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{output_dir}/invoice_{invoice_number:04d}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    
    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Company header
    elements.append(Paragraph("ACME CORPORATION", title_style))
    elements.append(Paragraph("123 Business Street, New York, NY 10001", styles['Normal']))
    elements.append(Paragraph("Tel: (555) 123-4567 | Email: billing@acme.com", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Invoice details
    invoice_date = datetime.now() - timedelta(days=random.randint(1, 90))
    due_date = invoice_date + timedelta(days=30)
    
    invoice_info = [
        ['INVOICE', ''],
        ['Invoice Number:', f'INV-{invoice_number:04d}'],
        ['Invoice Date:', invoice_date.strftime('%Y-%m-%d')],
        ['Due Date:', due_date.strftime('%Y-%m-%d')],
        ['PO Number:', f'PO-{random.randint(1000, 9999)}']
    ]
    
    invoice_table = Table(invoice_info, colWidths=[2*inch, 3*inch])
    invoice_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 18),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('SPAN', (0, 0), (-1, 0)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
    ]))
    
    elements.append(invoice_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Bill to section
    customer_name = fake.name()
    customer_company = fake.company()
    customer_email = fake.email()
    
    bill_to = [
        ['BILL TO:', ''],
        [customer_name, ''],
        [customer_company, ''],
        [fake.street_address(), ''],
        [f"{fake.city()}, {fake.state_abbr()} {fake.zipcode()}", ''],
        [f"Email: {customer_email}", '']
    ]
    
    bill_table = Table(bill_to, colWidths=[3*inch, 3*inch])
    bill_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 12),
    ]))
    
    elements.append(bill_table)
    elements.append(Spacer(1, 0.4*inch))
    
    # Line items
    items = []
    num_items = random.randint(3, 8)
    
    services = [
        "Consulting Services", "Software Development", "Cloud Infrastructure",
        "Data Analytics", "API Integration", "Technical Support",
        "Project Management", "Security Audit", "Performance Optimization",
        "System Maintenance"
    ]
    
    # Header
    items.append(['Description', 'Quantity', 'Unit Price', 'Amount'])
    
    subtotal = 0
    for _ in range(num_items):
        description = random.choice(services)
        quantity = random.randint(1, 100)
        unit_price = random.choice([50, 75, 100, 125, 150, 175, 200]) + random.uniform(0, 0.99)
        amount = quantity * unit_price
        subtotal += amount
        
        items.append([
            description,
            str(quantity),
            f"${unit_price:,.2f}",
            f"${amount:,.2f}"
        ])
    
    # Totals
    tax_rate = 0.08  # 8% sales tax
    tax_amount = subtotal * tax_rate
    
    # Randomly add discount for some invoices
    discount = 0
    if random.random() > 0.7:  # 30% chance of discount
        discount = subtotal * random.choice([0.05, 0.10, 0.15])
    
    total = subtotal - discount + tax_amount
    
    items.append(['', '', '', ''])  # Spacer
    items.append(['', '', 'Subtotal:', f"${subtotal:,.2f}"])
    if discount > 0:
        items.append(['', '', 'Discount:', f"-${discount:,.2f}"])
    items.append(['', '', 'Tax (8%):', f"${tax_amount:,.2f}"])
    items.append(['', '', 'TOTAL:', f"${total:,.2f}"])
    
    items_table = Table(items, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Data rows
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -5), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -5), 0.5, colors.grey),
        
        # Totals section
        ('FONTNAME', (2, -4), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (2, -4), (-1, -4), 1, colors.black),
        ('LINEABOVE', (2, -1), (-1, -1), 2, colors.black),
        ('FONTSIZE', (2, -1), (-1, -1), 12),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Payment terms
    elements.append(Paragraph("<b>Payment Terms:</b>", styles['Normal']))
    elements.append(Paragraph("Payment is due within 30 days of invoice date.", styles['Normal']))
    elements.append(Paragraph("Please include invoice number on payment.", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Bank details
    elements.append(Paragraph("<b>Payment Details:</b>", styles['Normal']))
    elements.append(Paragraph("Bank: First National Bank", styles['Normal']))
    elements.append(Paragraph("Account: 1234567890", styles['Normal']))
    elements.append(Paragraph("Routing: 987654321", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    
    return {
        'invoice_number': f'INV-{invoice_number:04d}',
        'vendor': 'ACME CORPORATION',
        'customer': customer_name,
        'email': customer_email,
        'date': invoice_date.strftime('%Y-%m-%d'),
        'due_date': due_date.strftime('%Y-%m-%d'),
        'subtotal': subtotal,
        'tax': tax_amount,
        'discount': discount,
        'total': total,
        'filename': filename
    }

def generate_sample_invoices(count=10):
    """Generate multiple sample invoices"""
    
    print(f"Generating {count} sample invoices...")
    
    invoices = []
    for i in range(1, count + 1):
        invoice_data = generate_invoice_pdf(i)
        invoices.append(invoice_data)
        print(f"✓ Generated: {invoice_data['filename']} (Total: ${invoice_data['total']:,.2f})")
    
    print(f"\n✓ Successfully generated {count} invoices in 'sample_invoices/' directory")
    print(f"  Total value: ${sum(inv['total'] for inv in invoices):,.2f}")
    
    # Create a summary CSV for reference
    summary_file = 'sample_invoices/invoices_summary.csv'
    with open(summary_file, 'w') as f:
        f.write('Invoice Number,Vendor,Customer,Email,Date,Due Date,Subtotal,Tax,Discount,Total,Filename\n')
        for inv in invoices:
            f.write(f"{inv['invoice_number']},{inv['vendor']},{inv['customer']},{inv['email']},"
                   f"{inv['date']},{inv['due_date']},{inv['subtotal']:.2f},{inv['tax']:.2f},"
                   f"{inv['discount']:.2f},{inv['total']:.2f},{inv['filename']}\n")
    
    print(f"✓ Summary saved to: {summary_file}")
    
    return invoices

if __name__ == "__main__":
    # Generate 10 sample invoices
    invoices = generate_sample_invoices(count=10)
    
    print("\nReady to upload to S3!")
    print("Run these commands:")
    print('  $SUFFIX="your-suffix"')
    print('  aws s3 cp sample_invoices\\ s3://invoice-automation-incoming-$SUFFIX/ --recursive --exclude "*" --include "*.pdf"')