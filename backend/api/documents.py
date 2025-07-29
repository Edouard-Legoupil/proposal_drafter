#  Standard Library
import os
import uuid
import json
import traceback
from datetime import datetime

#  Third-Party Libraries
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from docx import Document
from sqlalchemy import text

#  Internal Modules
from backend.core.db import engine
from backend.core.security import get_current_user
from backend.core.config import SECTIONS
from backend.utils.doc_export import add_markdown_paragraph, create_pdf_from_sections

# This router handles endpoints for generating and downloading final proposal documents.
router = APIRouter()

@router.get("/generate-document/{proposal_id}")
async def generate_and_download_document(
    proposal_id: str,
    format: str = "docx",  # Query parameter to specify 'docx' or 'pdf'
    current_user: dict = Depends(get_current_user)
):
    """
    Generates a final proposal document in either .docx or .pdf format.
    It fetches the completed proposal from the database, assembles the document,
    and returns it as a file download.
    """
    user_id = current_user["user_id"]

    try:
        # Fetch the proposal data from the database.
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT form_data, project_description, generated_sections
                    FROM proposals
                    WHERE id = :proposal_id AND user_id = :user_id
                """),
                {"proposal_id": proposal_id, "user_id": user_id}
            )
            draft = result.fetchone()

        if not draft:
            raise HTTPException(status_code=404, detail="Proposal not found for this user.")

        form_data = json.loads(draft[0]) if draft[0] else {}
        generated_sections = json.loads(draft[2]) if draft[2] else {}

        # Ensure all required sections are present before generating.
        if len(generated_sections) != len(SECTIONS):
            missing = [s for s in SECTIONS if s not in generated_sections]
            raise HTTPException(status_code=400, detail=f"Cannot generate document. Missing sections: {missing}")

        ordered_sections = {section: generated_sections.get(section, "") for section in SECTIONS}

        # --- Create Word Document (.docx) ---
        doc = Document()
        doc.add_heading("Project Proposal", level=1)

        # Add form data as a table.
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Field'
        hdr_cells[1].text = 'Value'
        for key, value in form_data.items():
            row_cells = table.add_row().cells
            row_cells[0].text = key
            row_cells[1].text = str(value) # Ensure value is a string
        doc.add_paragraph("\n")

        # Add the main content sections.
        for section, content in ordered_sections.items():
            doc.add_heading(section, level=2)
            for para in (content or "").split("\n\n"):
                add_markdown_paragraph(doc, para.strip())

        # --- Save and Return File ---
        folder_name = "proposal-documents"
        os.makedirs(folder_name, exist_ok=True)
        unique_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"

        docx_file_path = os.path.join(folder_name, f"proposal_{unique_id}.docx")
        doc.save(docx_file_path)

        if format == "pdf":
            pdf_file_path = docx_file_path.replace(".docx", ".pdf")
            try:
                # Use the PDF creation utility.
                create_pdf_from_sections(pdf_file_path, form_data, ordered_sections)
                return FileResponse(
                    path=pdf_file_path,
                    filename=f"Proposal_{proposal_id}.pdf",
                    media_type='application/pdf'
                )
            except Exception as e:
                print(f"[PDF Generation Error] {e}")
                raise HTTPException(status_code=500, detail="Failed to generate PDF document.")
        else:
            # Return the DOCX file by default.
            return FileResponse(
                path=docx_file_path,
                filename=f"Proposal_{proposal_id}.docx",
                media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Document generation failed: {str(e)}")
