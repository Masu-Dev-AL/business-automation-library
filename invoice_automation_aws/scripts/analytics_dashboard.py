import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict

load_dotenv('config/.env')

def generate_dashboard():
    """Generate a simple HTML analytics dashboard"""
    
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=5432,
        database='invoice_automation',
        user='postgres',
        password=os.getenv('DB_PASSWORD')
    )
    
    cursor = conn.cursor()
    
    # Get summary statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_invoices,
            SUM(total_amount) as total_amount,
            AVG(total_amount) as avg_amount
        FROM invoices
    """)
    total_invoices, total_amount, avg_amount = cursor.fetchone()
    
    # Get monthly trend data
    cursor.execute("""
        SELECT 
            DATE_TRUNC('month', invoice_date) as month,
            COUNT(*) as invoice_count,
            SUM(total_amount) as total_amount
        FROM invoices
        WHERE invoice_date IS NOT NULL
        GROUP BY DATE_TRUNC('month', invoice_date)
        ORDER BY month DESC
        LIMIT 12
    """)
    monthly_data = cursor.fetchall()
    
    # Get status breakdown
    cursor.execute("""
        SELECT status, COUNT(*) as count, SUM(total_amount) as amount
        FROM invoices
        GROUP BY status
        ORDER BY count DESC
    """)
    status_data = cursor.fetchall()
    
    # Get top vendors
    cursor.execute("""
        SELECT v.vendor_name, COUNT(i.invoice_id) as invoice_count, SUM(i.total_amount) as total_amount
        FROM vendors v
        JOIN invoices i ON v.vendor_id = i.vendor_id
        GROUP BY v.vendor_name
        ORDER BY total_amount DESC
        LIMIT 5
    """)
    vendor_data = cursor.fetchall()
    
    # Get recent invoices
    cursor.execute("""
        SELECT i.invoice_number, v.vendor_name, i.total_amount, i.status, i.processed_at
        FROM invoices i
        JOIN vendors v ON i.vendor_id = v.vendor_id
        ORDER BY i.processed_at DESC
        LIMIT 10
    """)
    recent_invoices = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Invoice Automation Analytics Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .chart-container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        h2 {{
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .status-approved {{
            background: #4caf50;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .status-pending {{
            background: #ff9800;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .status-failed {{
            background: #f44336;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .bar {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 30px;
            border-radius: 5px;
            margin: 10px 0;
            display: flex;
            align-items: center;
            padding-left: 10px;
            color: white;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            color: white;
            margin-top: 30px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Invoice Automation Dashboard</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Invoices</div>
                <div class="stat-value">{total_invoices or 0}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Amount</div>
                <div class="stat-value">${total_amount or 0:,.2f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Average Invoice</div>
                <div class="stat-value">${avg_amount or 0:,.2f}</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>Invoice Volume Over Time</h2>
            <div style="margin-top: 20px;">
    """
    
    # Generate monthly trend bars
    if monthly_data:
        max_amount = max([row[2] for row in monthly_data])
        for month, count, amount in reversed(monthly_data):
            month_str = month.strftime('%B %Y') if month else 'Unknown'
            width = (amount / max_amount * 100) if max_amount > 0 else 0
            html += f"""
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="font-weight: 600;">{month_str}</span>
                        <span style="color: #666;">{count} invoices • ${amount:,.2f}</span>
                    </div>
                    <div class="bar" style="width: {width}%;">${amount:,.0f}</div>
                </div>
            """
    else:
        html += "<p style='color: #999; text-align: center;'>No invoice data available</p>"
    
    html += """
            </div>
        </div>
        
        <div class="chart-container">
            <h2>Invoice Status Breakdown</h2>
            <table>
                <tr>
                    <th>Status</th>
                    <th>Count</th>
                    <th>Total Amount</th>
                    <th>Distribution</th>
                </tr>
    """
    
    max_count = max([row[1] for row in status_data]) if status_data else 1
    
    for status, count, amount in status_data:
        status_class = f"status-{status.replace('_', '-')}" if status in ['approved', 'failed'] else "status-pending"
        width = (count / max_count * 100) if max_count > 0 else 0
        html += f"""
                <tr>
                    <td><span class="{status_class}">{status.upper()}</span></td>
                    <td>{count}</td>
                    <td>${amount or 0:,.2f}</td>
                    <td><div class="bar" style="width: {width}%">{count}</div></td>
                </tr>
        """
    
    html += """
            </table>
        </div>
        
        <div class="chart-container">
            <h2>Top Vendors by Amount</h2>
            <table>
                <tr>
                    <th>Vendor</th>
                    <th>Invoice Count</th>
                    <th>Total Amount</th>
                </tr>
    """
    
    for vendor_name, invoice_count, total in vendor_data:
        html += f"""
                <tr>
                    <td>{vendor_name}</td>
                    <td>{invoice_count}</td>
                    <td>${total:,.2f}</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
        
        <div class="chart-container">
            <h2>Recent Invoices</h2>
            <table>
                <tr>
                    <th>Invoice #</th>
                    <th>Vendor</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Processed</th>
                </tr>
    """
    
    for invoice_number, vendor_name, total_amt, status, processed_at in recent_invoices:
        status_class = f"status-{status.replace('_', '-')}" if status in ['approved', 'failed'] else "status-pending"
        html += f"""
                <tr>
                    <td>{invoice_number}</td>
                    <td>{vendor_name}</td>
                    <td>${total_amt:,.2f}</td>
                    <td><span class="{status_class}">{status.upper()}</span></td>
                    <td>{processed_at.strftime('%Y-%m-%d %H:%M') if processed_at else 'N/A'}</td>
                </tr>
        """
    
    html += f"""
            </table>
        </div>
        
        <div class="footer">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Invoice Automation System
        </div>
    </div>
</body>
</html>
    """
    
    # Save to file
    output_file = 'dashboard.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Dashboard generated: {output_file}")
    print(f"  Open in browser to view analytics")
    
    return output_file

if __name__ == '__main__':
    generate_dashboard()