from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

output_path = "public/Ryan-Cross-Resume.pdf"
ink = HexColor("#111411")
teal = HexColor("#126e67")
muted = HexColor("#596159")
line = HexColor("#c8cec7")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Name", fontName="Helvetica-Bold", fontSize=25, leading=28, textColor=ink, spaceAfter=4))
styles.add(ParagraphStyle(name="Subtitle", fontName="Helvetica", fontSize=10, leading=14, textColor=muted, spaceAfter=20))
styles.add(ParagraphStyle(name="Heading", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=teal, spaceBefore=15, spaceAfter=7, uppercase=True))
styles.add(ParagraphStyle(name="BodyCopy", fontName="Helvetica", fontSize=10, leading=15, textColor=ink, spaceAfter=7))
styles.add(ParagraphStyle(name="Role", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=ink))

doc = SimpleDocTemplate(output_path, pagesize=letter, leftMargin=.78*inch, rightMargin=.78*inch, topMargin=.68*inch, bottomMargin=.68*inch)
story = [
    Paragraph("RYAN CROSS", styles["Name"]),
    Paragraph("Aerospace Engineering Student | Boulder, Colorado | ryanc31415@gmail.com | linkedin.com/in/ryan-cross-", styles["Subtitle"]),
    Paragraph("Profile", styles["Heading"]),
    Paragraph("Aerospace engineering student with experience in propulsion, integrated testing, and systems engineering. Interested in building practical test plans, learning from real hardware, and turning results into useful engineering decisions.", styles["BodyCopy"]),
    Paragraph("Education", styles["Heading"]),
    Paragraph("University of Colorado Boulder", styles["Role"]),
    Paragraph("B.S. Aerospace Engineering, expected 2026", styles["BodyCopy"]),
    Paragraph("Experience", styles["Heading"]),
    Paragraph("Stampede Sky - Propulsion and Integrated Test", styles["Role"]),
    Paragraph("Contributed propulsion and integrated test work for a CU Boulder aerospace senior design team, connecting subsystem decisions with full vehicle evaluation.", styles["BodyCopy"]),
    Paragraph("Kairos Power - Test Engineering Intern", styles["Role"]),
    Paragraph("Supported test engineering work at a company developing advanced nuclear technology, with an emphasis on clear data and practical engineering decisions.", styles["BodyCopy"]),
    Paragraph("Skills", styles["Heading"]),
    Paragraph("Propulsion | Integrated Test | Systems Engineering | Test Engineering | Data Analysis", styles["BodyCopy"]),
]
doc.build(story)
