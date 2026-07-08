from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

def generate_pdf_letter(content: str) -> bytes:
    """Generate a formal PDF from the negotiation letter text content."""
    buffer = BytesIO()
    
    # Page setup
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        name='DocTitle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=20,
        textColor='#1e293b'
    )
    
    body_style = ParagraphStyle(
        name='DocBody',
        parent=styles['Normal'],
        alignment=TA_LEFT,
        fontSize=11,
        leading=16,
        spaceAfter=10,
        textColor='#334155'
    )
    
    story = []
    
    # Title
    story.append(Paragraph("<b>FinRelief AI - One-Time Settlement Proposal</b>", title_style))
    story.append(Spacer(1, 15))
    
    # Parse lines and render
    lines = content.split('\n')
    for line in lines:
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 8))
        else:
            # Simple bold formatting (if line contains **)
            formatted = stripped
            if formatted.startswith("**") and formatted.endswith("**"):
                formatted = f"<b>{formatted[2:-2]}</b>"
            elif formatted.startswith("- **"):
                # Bullet list parsing
                parts = formatted[4:].split("**")
                if len(parts) >= 2:
                    formatted = f"&bull; <b>{parts[0]}</b>{parts[1]}"
                else:
                    formatted = f"&bull; {formatted[4:]}"
            elif formatted.startswith("- "):
                formatted = f"&bull; {formatted[2:]}"
                
            story.append(Paragraph(formatted, body_style))
            
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
