#  Standard Library
import io
import json
import logging
from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError

#  Third-Party Libraries
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from docx import Document
from sqlalchemy import text

#  Internal Modules
from backend.core.db import get_engine
from backend.core.security import get_current_user
from backend.core.config import load_proposal_template
from backend.utils.doc_export import create_word_from_sections, create_pdf_from_sections

# This router handles endpoints for generating and downloading final proposal documents.
router = APIRouter()
logger = logging.getLogger(__name__)

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

    # Validate UUID
    try:
        UUID(proposal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid proposal_id: {proposal_id}")


    user_id = current_user["user_id"]

    try:
        # Fetch the proposal data from the database.
        with get_engine().connect() as connection:
            result = connection.execute(
                text("""
                    SELECT form_data, project_description, generated_sections, template_name
                    FROM proposals
                    WHERE id = :proposal_id AND user_id = :user_id
                """),
                {"proposal_id": proposal_id, "user_id": user_id}
            )
            draft = result.fetchone()

        if not draft:
            raise HTTPException(status_code=404, detail="Proposal not found for this user.")

        form_data, _, generated_sections, template_name = draft
        form_data = form_data if isinstance(form_data, dict) else {}
        generated_sections = generated_sections if isinstance(generated_sections, dict) else {}

        # Load the template to get the correct section order and list.
        if not template_name:
            # Fallback to a default if no template is stored with the proposal.
            template_name = "unhcr_proposal_template.json"
            logger.warning(f"Proposal {proposal_id} has no template_name, falling back to default.")

        proposal_template = load_proposal_template(template_name)
        template_sections = [s.get("section_name") for s in proposal_template.get("sections", [])]


        # # Ensure all required sections are present before generating.
        # if len(generated_sections) < len(template_sections):
        #     missing = [s for s in template_sections if s not in generated_sections]
        #     raise HTTPException(status_code=400, detail=f"Cannot generate document. Missing sections: {', '.join(missing)}")

        ordered_sections = {section: generated_sections.get(section, "") for section in template_sections}

        if format == "pdf":
            try:
                pdf_buffer = create_pdf_from_sections(form_data, ordered_sections)
                return StreamingResponse(
                    io.BytesIO(pdf_buffer),
                    media_type='application/pdf',
                    headers={"Content-Disposition": f"attachment; filename=Proposal_{proposal_id}.pdf"}
                )
            except Exception as e:
                logger.error(f"[PDF Generation Error] {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Failed to generate PDF document.")
        else:
            # Return the DOCX file by default.
            try:
                doc = create_word_from_sections(form_data, ordered_sections)
                docx_buffer = io.BytesIO()
                doc.save(docx_buffer)
                docx_buffer.seek(0)
                return StreamingResponse(
                    docx_buffer,
                    media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    headers={"Content-Disposition": f"attachment; filename=Proposal_{proposal_id}.docx"}
                )
            except Exception as e:
                logger.error(f"[DOCX Generation Error] {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Failed to generate DOCX document.")



    except SQLAlchemyError as e:
        logger.error(f"Database error during document generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="A database error occurred.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during document generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
