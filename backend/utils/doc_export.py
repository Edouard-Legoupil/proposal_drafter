# Standard Library
import re
from typing import Dict

# Third-Party Libraries
from docx import Document
from docx.shared import Pt
from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.table import table_plugin
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Internal Modules
from backend.utils.markdown import convert_markdown_bold


def add_markdown_to_doc(doc: Document, text: str):
    """
    Adds content to a .docx document, correctly handling Markdown syntax.

    This function parses the Markdown text and adds elements to the document,
    including paragraphs with bold text and tables.

    Args:
        doc: The python-docx Document object.
        text: The text, which may contain Markdown syntax.
    """
    # Configure the Markdown parser to handle tables.
    md = MarkdownIt().use(front_matter_plugin).use(table_plugin)
    tokens = md.parse(text)

    for token in tokens:
        if token.type == "table_open":
            # Create a table in the document.
            table_data = []
            headers = []
            # Extract table headers.
            for th in tokens[tokens.index(token) + 2].children:
                if th.type == "text":
                    headers.append(th.content)
            # Create the table with the correct number of columns.
            table = doc.add_table(rows=1, cols=len(headers))
            table.style = "Table Grid"
            hdr_cells = table.rows[0].cells
            # Populate table headers.
            for i, header in enumerate(headers):
                hdr_cells[i].text = header
            # Extract and populate table rows.
            for tr in tokens[tokens.index(token) + 4:]:
                if tr.type == "tr_open":
                    row_cells = table.add_row().cells
                    cell_index = 0
                    for td in tr.children:
                        if td.type == "text":
                            row_cells[cell_index].text = td.content
                            cell_index += 1
        elif token.type == "paragraph_open":
            # Handle paragraphs, including bold text.
            paragraph = doc.add_paragraph()
            for child in token.children:
                if child.type == "strong_open":
                    # Add bold text.
                    run = paragraph.add_run(child.next_sibling.content)
                    run.bold = True
                elif child.type == "text" and not child.find_predecessor("strong_open"):
                    # Add regular text.
                    paragraph.add_run(child.content)
            # Apply paragraph formatting.
            paragraph.paragraph_format.space_after = Pt(12)
            paragraph.paragraph_format.line_spacing = 1.5


def create_word_from_sections(form_data: Dict, ordered_sections: Dict) -> Document:
    """
    Generates a .docx document from proposal data.

    Args:
        form_data: A dictionary containing the proposal's metadata.
        ordered_sections: A dictionary of the proposal sections and their content.

    Returns:
        A python-docx Document object.
    """
    doc = Document()
    # Add the main title.
    doc.add_heading("Project Proposal", level=1)

    # Add the form data as a table.
    doc.add_heading("Project Details", level=2)
    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Field"
    hdr_cells[1].text = "Value"
    for key, value in form_data.items():
        row_cells = table.add_row().cells
        row_cells[0].text = key
        row_cells[1].text = str(value)

    # Add each proposal section to the document.
    for section, content in ordered_sections.items():
        if not content:
            continue  # Skip empty sections.
        doc.add_heading(section, level=2)
        add_markdown_to_doc(doc, content)

    return doc


#  Standard Library
import io


def create_pdf_from_sections(form_data: Dict, ordered_sections: Dict) -> bytes:
    """
    Generates a PDF document from proposal data using ReportLab and returns it as a byte buffer.

    Args:
        form_data: A dictionary containing the proposal's metadata.
        ordered_sections: A dictionary of the proposal sections and their content.

    Returns:
        A byte buffer containing the generated PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72
    )
    styles = getSampleStyleSheet()

    # Define a custom style for justified body text.
    normal_style = ParagraphStyle(name="Body", parent=styles["Normal"], alignment=TA_JUSTIFY, leading=14)

    story = []

    # Add the main title.
    story.append(Paragraph("Project Proposal", styles["Title"]))
    story.append(Spacer(1, 12))

    # Create a table for the form data.
    table_data = [["Field", "Value"]]
    for key, value in form_data.items():
        table_data.append([key, str(value)])

    table = Table(table_data, colWidths=[2.5 * inch, 3.5 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 20))

    # Add each proposal section to the document.
    for section, content in ordered_sections.items():
        if not content:
            continue  # Skip empty sections.

        story.append(Paragraph(section, styles["Heading2"]))
        story.append(Spacer(1, 6))

        # Split content into paragraphs and format them.
        for paragraph in content.split("\n\n"):
            # Convert markdown bold to reportlab's <b> tag.
            cleaned_paragraph = convert_markdown_bold(paragraph.strip())
            story.append(Paragraph(cleaned_paragraph, normal_style))
            story.append(Spacer(1, 10))

    # Build the PDF document.
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_final_markdown(generated_sections: Dict) -> str:
    """
    Compiles all generated sections into a single Markdown string.

    Args:
        generated_sections: A dictionary of the proposal sections and their content.

    Returns:
        A string containing the full proposal in Markdown format.
    """
    markdown_content = ""
    for section, content in generated_sections.items():
        markdown_content += f"## {section}\n\n{content.strip()}\n\n"
    return markdown_content
