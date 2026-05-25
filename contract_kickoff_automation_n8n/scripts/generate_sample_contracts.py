"""
Generate 5 sample test contracts as PDF files for Phase 1 and Phase 2 testing.

Usage:
    pip install fpdf2
    python generate_sample_contracts.py

Output: sample_contracts/ folder (5 PDF files)
"""

from fpdf import FPDF, XPos, YPos
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "sample_contracts"
OUTPUT_DIR.mkdir(exist_ok=True)

_REPLACEMENTS = {
    "—": " - ",   # em dash
    "–": "-",     # en dash
    "‘": "'",     # left single quote
    "’": "'",     # right single quote
    "“": '"',     # left double quote
    "”": '"',     # right double quote
}

def _clean(text: str) -> str:
    for char, replacement in _REPLACEMENTS.items():
        text = text.replace(char, replacement)
    return text


def make_pdf(filename: str, title: str, body_sections: list[tuple[str, str]]) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(20, 20, 20)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _clean(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(6)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "TEST DOCUMENT - FOR AUTOMATION TESTING ONLY", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    pdf.set_draw_color(200, 200, 200)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(6)

    for heading, content in body_sections:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, _clean(heading), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, _clean(content))
        pdf.ln(4)

    pdf.output(str(OUTPUT_DIR / filename))
    print(f"  Created: {filename}")


def test_001_web_design():
    """Fixed-scope web design — explicit dates, clear deliverables."""
    make_pdf(
        "TEST-001_web_design_project.pdf",
        "Web Design Services Agreement",
        [
            ("Parties", (
                "This agreement is entered into on June 1, 2025 between Acme Creative Agency "
                "(Agency) and Brightfield Solutions Inc. (Client).\n"
                "Client contact: Sarah Chen, sarah.chen@brightfield.com"
            )),
            ("Engagement Overview", (
                "Service Type: Website Redesign Project\n"
                "Engagement Start Date: June 15, 2025\n"
                "Engagement End Date: August 15, 2025\n"
                "Contract Value: $18,500 USD"
            )),
            ("Payment Terms", (
                "50% deposit due upon signing ($9,250). Remaining 50% due upon final delivery."
            )),
            ("Deliverables", (
                "1. Discovery & Wireframes\n"
                "   Due: June 30, 2025\n"
                "   Owner: Agency\n"
                "   Client approval required before proceeding to design phase.\n\n"
                "2. Visual Design Mockups (3 page templates)\n"
                "   Due: July 15, 2025\n"
                "   Owner: Agency\n"
                "   Includes: Home, Services, Contact pages.\n\n"
                "3. Development & CMS Integration\n"
                "   Due: August 1, 2025\n"
                "   Owner: Agency\n"
                "   WordPress CMS. Client to provide all copy and images by July 20, 2025.\n\n"
                "4. QA, Testing & Launch\n"
                "   Due: August 15, 2025\n"
                "   Owner: Agency\n"
                "   Includes cross-browser testing, mobile responsiveness, go-live."
            )),
            ("Special Conditions", (
                "Client is responsible for providing all written content and brand assets "
                "by July 20, 2025. Delays in client deliverables may extend the project timeline. "
                "Agency reserves the right to adjust deadlines proportionally."
            )),
        ]
    )


def test_002_marketing_retainer():
    """Monthly marketing retainer — 3-month fixed term with concrete first-month deliverable dates."""
    make_pdf(
        "TEST-002_marketing_retainer.pdf",
        "Monthly Marketing Retainer Agreement",
        [
            ("Parties", (
                "This retainer agreement is effective May 1, 2025 between Growth Engine LLC "
                "(Agency) and Pinnacle Fitness Co. (Client).\n"
                "Client contact: Marcus Webb, marcus@pinnaclefitness.com"
            )),
            ("Engagement Overview", (
                "Service Type: Monthly Marketing Retainer\n"
                "Engagement Start Date: May 1, 2025\n"
                "Engagement End Date: July 31, 2025 (3-month initial term)\n"
                "Total Contract Value: $13,500 USD ($4,500/month, invoiced on the 1st of each month).\n"
                "Either party may extend or terminate with 30 days written notice after July 31, 2025."
            )),
            ("Deliverables", (
                "1. Social Media Content Pack (Month 1)\n"
                "   Due: May 10, 2025\n"
                "   Owner: Agency\n"
                "   20 posts across Instagram and Facebook for the month of May.\n\n"
                "2. Email Newsletter (Month 1)\n"
                "   Due: May 15, 2025\n"
                "   Owner: Agency\n"
                "   Client to provide promotional offers and featured products by May 10.\n\n"
                "3. Paid Ads Campaign Setup — Google + Meta\n"
                "   Due: May 7, 2025\n"
                "   Owner: Agency\n"
                "   Initial campaign setup, audience targeting, and creative brief approval.\n\n"
                "4. Monthly Performance Report (Month 1)\n"
                "   Due: May 31, 2025\n"
                "   Owner: Agency\n"
                "   Covers: reach, engagement, leads generated, ad spend vs. ROAS."
            )),
            ("Special Conditions", (
                "Client ad spend budget ($3,000/month minimum) is separate from retainer fee "
                "and billed directly by ad platforms. Agency manages but does not pay ad spend. "
                "Deliverable schedule for months 2 and 3 mirrors month 1 cadence."
            )),
        ]
    )


def test_003_consulting_sow():
    """Multi-phase SOW — consulting engagement with conditional milestones."""
    make_pdf(
        "TEST-003_consulting_sow.pdf",
        "Statement of Work — Operational Consulting Engagement",
        [
            ("Parties", (
                "This Statement of Work is executed between Meridian Strategy Group (Consultant) "
                "and Harborview Manufacturing Ltd. (Client) as of March 10, 2025.\n"
                "Client contact: Diana Okafor, COO, d.okafor@harborview.com"
            )),
            ("Engagement Overview", (
                "Service Type: Operational Efficiency Consulting\n"
                "Engagement Start Date: April 1, 2025\n"
                "Estimated Engagement End Date: September 30, 2025\n"
                "Total Contract Value: $67,000 USD (paid in milestone installments)"
            )),
            ("Phase 1 — Discovery & Assessment (April 1 – May 15, 2025)", (
                "Deliverable 1A: Current-State Process Audit\n"
                "  Due: April 30, 2025 | Owner: Consultant\n"
                "  Requires: Client to provide access to production floor and ERP system data.\n\n"
                "Deliverable 1B: Gap Analysis Report\n"
                "  Due: May 15, 2025 | Owner: Consultant\n"
                "  Milestone payment: $15,000 due upon delivery and client sign-off.\n"
                "  Note: Phase 2 does not begin until client approves Gap Analysis Report."
            )),
            ("Phase 2 — Strategy & Roadmap (May 16 – July 15, 2025)", (
                "Deliverable 2A: Operational Improvement Roadmap\n"
                "  Due: June 30, 2025 | Owner: Consultant\n"
                "  Requires: Client sign-off on Phase 1 Gap Analysis.\n\n"
                "Deliverable 2B: Change Management Plan\n"
                "  Due: July 15, 2025 | Owner: Consultant\n"
                "  Milestone payment: $22,000 due upon delivery.\n"
                "  Team members involved: Diana Okafor (COO), Robert Tran (Plant Manager)"
            )),
            ("Phase 3 — Implementation Support (July 16 – September 30, 2025)", (
                "Deliverable 3A: Bi-weekly Implementation Check-ins (6 sessions)\n"
                "  Scheduled: Every other Wednesday starting July 16, 2025\n"
                "  Owner: Consultant + Client Joint\n\n"
                "Deliverable 3B: Final Impact Assessment Report\n"
                "  Due: September 30, 2025 | Owner: Consultant\n"
                "  Milestone payment: $30,000 due upon final delivery."
            )),
            ("Special Conditions", (
                "Phase 2 is contingent on client written approval of Phase 1 deliverables. "
                "If approval is delayed beyond 5 business days, all Phase 2 deadlines shift proportionally. "
                "Travel expenses (estimated $3,000 total) billed at cost, not included in contract value."
            )),
        ]
    )


def test_004_brand_identity():
    """Brand identity project — relative due dates (due_days_from_start). Tests date resolution in A6."""
    make_pdf(
        "TEST-004_brand_identity_project.pdf",
        "Brand Identity Design Agreement",
        [
            ("Parties", (
                "This agreement is entered into on July 1, 2025 between Volta Creative Studio "
                "(Agency) and Clearwater Health Co. (Client).\n"
                "Client contact: Priya Nair, Head of Marketing, priya.nair@clearwaterhealth.com"
            )),
            ("Engagement Overview", (
                "Service Type: Brand Identity Design\n"
                "Engagement Start Date: July 14, 2025\n"
                "Engagement Duration: 10 weeks from start date\n"
                "Contract Value: $22,000 USD\n"
                "Payment Terms: 40% deposit upon signing ($8,800). 30% at logo approval. "
                "Final 30% upon full delivery."
            )),
            ("Deliverables", (
                "1. Brand Discovery & Positioning Brief\n"
                "   Due: 10 days from start date\n"
                "   Owner: Agency\n"
                "   Requires client to complete brand questionnaire within 3 business days of start.\n\n"
                "2. Logo Concepts (3 directions)\n"
                "   Due: 25 days from start date\n"
                "   Owner: Agency\n"
                "   Client selects one direction for refinement. Two rounds of revisions included.\n\n"
                "3. Final Logo Package\n"
                "   Due: 42 days from start date\n"
                "   Owner: Agency\n"
                "   Delivered in SVG, PNG, and PDF. Light and dark variants included.\n\n"
                "4. Brand Style Guide\n"
                "   Due: 56 days from start date\n"
                "   Owner: Agency\n"
                "   Covers: color palette, typography, logo usage rules, tone of voice guidelines.\n\n"
                "5. Brand Asset Library\n"
                "   Due: 70 days from start date\n"
                "   Owner: Agency\n"
                "   Business card, letterhead, email signature, social profile templates."
            )),
            ("Team Members", (
                "Agency lead: Jordan Reyes (Creative Director)\n"
                "Client lead: Priya Nair (Head of Marketing)"
            )),
            ("Special Conditions", (
                "Client feedback must be provided within 5 business days of each deliverable or "
                "the timeline shifts proportionally. Stock photography and font licensing fees "
                "are not included in the contract value and will be billed at cost if required."
            )),
        ]
    )


def test_005_scanned_pdf():
    """Scanned/image-only PDF — no extractable text. Tests pdf_text_empty path."""
    pdf = FPDF()
    pdf.add_page()

    # Draw a large white rectangle to simulate a blank scanned page
    # No text objects are added — pdfminer extracts 0 characters
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(0, 0, 210, 297, style="F")

    # Add very faint border lines to simulate a scanned page edge (no text)
    pdf.set_draw_color(220, 220, 220)
    pdf.rect(10, 10, 190, 277)

    filename = "TEST-005_scanned_image_only.pdf"
    pdf.output(str(OUTPUT_DIR / filename))
    print(f"  Created: {filename} (blank page — simulates image-only scanned PDF)")


if __name__ == "__main__":
    print(f"Generating sample contracts in: {OUTPUT_DIR}\n")
    test_001_web_design()
    test_002_marketing_retainer()
    test_003_consulting_sow()
    test_004_brand_identity()
    test_005_scanned_pdf()
    print(f"\nDone. {len(list(OUTPUT_DIR.glob('*.pdf')))} PDFs in {OUTPUT_DIR}")
