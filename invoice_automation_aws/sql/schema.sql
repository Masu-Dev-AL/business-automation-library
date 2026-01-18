CREATE TABLE vendors (
 vendor_id SERIAL PRIMARY KEY,
 vendor_name VARCHAR(255) UNIQUE NOT NULL,
 vendor_email VARCHAR(255),
 payment_terms VARCHAR(50),
 is_approved BOOLEAN DEFAULT false
);
CREATE TABLE invoices (
 invoice_id SERIAL PRIMARY KEY,
 invoice_number VARCHAR(100) UNIQUE NOT NULL,
 vendor_id INTEGER REFERENCES vendors(vendor_id),
 invoice_date DATE NOT NULL,
 due_date DATE,
 subtotal DECIMAL(12, 2),
 tax_amount DECIMAL(12, 2),
 total_amount DECIMAL(12, 2) NOT NULL,
 status VARCHAR(50) DEFAULT 'pending',
 s3_key VARCHAR(500),
 processed_at TIMESTAMP,
 approved_at TIMESTAMP,
 paid_at TIMESTAMP
);
CREATE TABLE invoice_line_items (
 line_item_id SERIAL PRIMARY KEY,
 invoice_id INTEGER REFERENCES invoices(invoice_id),
 description TEXT NOT NULL,
 quantity DECIMAL(10, 2),
 unit_price DECIMAL(12, 2),
 amount DECIMAL(12, 2)
);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_date ON invoices(invoice_date);