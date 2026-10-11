from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph
from datetime import datetime
import os


def generate_report(data, image_name):

    os.makedirs("outputs", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    pdf_name = f"report_{timestamp}.pdf"

    pdf_path = os.path.join("outputs", pdf_name)

    styles = getSampleStyleSheet()

    pdf = SimpleDocTemplate(pdf_path)

    story = []

    story.append(Paragraph("<b><font size=18>SMARTMEASURE AI REPORT</font></b>", styles["Title"]))

    story.append(Paragraph("<br/>", styles["Normal"]))

    story.append(Paragraph(f"<b>Date :</b> {datetime.now()}", styles["Normal"]))

    story.append(Paragraph("<br/>", styles["Normal"]))

    story.append(Paragraph(f"<b>Object :</b> {data['object']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Shape :</b> {data['shape']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Width :</b> {data['width']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Height :</b> {data['height']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Area :</b> {data['area']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Volume :</b> {data['volume']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Confidence :</b> {data['confidence']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Quality :</b> {data['quality']}", styles["Normal"]))

    story.append(Paragraph("<br/>", styles["Normal"]))

    story.append(Paragraph(f"<b>Captured Image :</b> {image_name}", styles["Normal"]))

    pdf.build(story)

    return pdf_name