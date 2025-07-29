#  Standard Library
import re
from typing import Dict

#  Third-Party Libraries
from docx import Document
from docx.shared import Pt
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.units import inch

#  Internal Modules
from backend.utils.markdown import convert_markdown_bold

# This module contains helper functions for creating and exporting documents
# in different formats, such as .docx (Word) and .pdf.

def add_markdown_paragraph(doc: Document, text: str):
    """
    Adds a paragraph to a .docx document, correctly handling Markdown bold syntax.

    It splits the text by the bold markers (**) and adds runs to the paragraph,
    applying bold formatting where necessary.

    Args:
        doc: The python-docx Document object.
        text: The paragraph text, which may contain Markdown bold.
    """
    paragraph = doc.add_paragraph()
    # Split the text by bold markdown delimiters.
    parts = re.split(r'(\*\*.*?\*\*)', text)

    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            # If the part is wrapped in **, add it as a bold run.
            paragraph.add_run(part[2:-2]).bold = True
        else:
            # Otherwise, add it as a normal run.
            paragraph.add_run(part)

    # Apply standard paragraph formatting.
    paragraph.paragraph_format.space_after = Pt(12)
    paragraph.paragraph_format.line_spacing = 1.5


def create_pdf_from_sections(output_path: str, form_data: Dict, ordered_sections: Dict):
    """
    Generates a PDF document from proposal data using ReportLab.

    Args:
        output_path: The file path to save the generated PDF.
        form_data: A dictionary containing the proposal's metadata.
        ordered_sections: A dictionary of the proposal sections and their content.
    """
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()

    # Define a custom style for justified body text.
    normal_style = ParagraphStyle(
        name='Body',
        parent=styles['Normal'],
        alignment=TA_JUSTIFY,
        leading=14
    )

    story = []

    # Add the main title.
    story.append(Paragraph("Project Proposal", styles['Title']))
    story.append(Spacer(1, 12))

    # Create a table for the form data.
    table_data = [["Field", "Value"]]
    for key, value in form_data.items():
        table_data.append([key, value])

    table = Table(table_data, colWidths=[2.5 * inch, 3.5 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))

    # Add each proposal section to the document.
    for section, content in ordered_sections.items():
        if not content:
            continue  # Skip empty sections.

        story.append(Paragraph(section, styles['Heading2']))
        story.append(Spacer(1, 6))

        # Split content into paragraphs and format them.
        for paragraph in content.split("\n\n"):
            # Convert markdown bold to reportlab's <b> tag.
            cleaned_paragraph = convert_markdown_bold(paragraph.strip())
            story.append(Paragraph(cleaned_paragraph, normal_style))
            story.append(Spacer(1, 10))

    # Build the PDF document.
    doc.build(story)
