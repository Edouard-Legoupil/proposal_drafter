#  Standard Library
import json
import re

#  Third-Party Libraries
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text

#  Internal Modules
from backend.utils.crew_proposal import ProposalCrew
from backend.core.redis import redis_client
from backend.core.db import engine

FALLBACK_GENERATION_MESSAGE = "Generation issue: No content was generated for this section. You can try regenerating it or edit it manually."

# This module contains the core logic for generating and regenerating proposal sections
# using the 'crew' of AI agents.


def regenerate_section_logic(
    session_id: str, section: str, concise_input: str, proposal_id: str
) -> str:
    """
    Shared logic for regenerating a proposal section using custom input.

    This function is called both when a user manually requests a regeneration and
    when the initial generation is flagged for poor quality.

    Args:
        session_id: The user's current session ID.
        section: The name of the section to regenerate.
        concise_input: The user-provided or evaluator-provided feedback for regeneration.
        proposal_id: The unique ID of the proposal being edited.

    Returns:
        The newly generated text for the section.

    Raises:
        HTTPException: If session data is missing or the section is invalid.
    """
    session_data_str = redis_client.get(session_id)
    if not session_data_str:
        raise HTTPException(
            status_code=400,
            detail="Base data not found in session. Please store it first.",
        )

    session_data = json.loads(session_data_str)
    form_data = session_data.get("form_data", {})
    project_description = session_data.get("project_description", "")

    # Get proposal template from session data
    proposal_template = session_data.get("proposal_template")
    if not proposal_template:
        raise HTTPException(
            status_code=400, detail="Proposal template not found in session."
        )

    # Find the specific instructions and word limit for the section.
    section_config = next(
        (
            s
            for s in proposal_template.get("sections", [])
            if s.get("section_name") == section
        ),
        None,
    )
    if not section_config:
        raise HTTPException(status_code=400, detail=f"Invalid section name: {section}")

    char_limit = section_config.get("char_limit")
    word_limit = section_config.get("word_limit")
    if char_limit is not None:
        limit_type = "char"
        limit_value = char_limit
    elif word_limit is not None:
        limit_type = "word"
        limit_value = word_limit
    else:
        limit_type = "word"
        limit_value = 350
    limit_instruction = f"Do not exceed {limit_value} {'character' if limit_type == 'char' else 'word'}s."
    instructions += " " + limit_instruction

    proposal_crew = ProposalCrew()
    crew_instance = proposal_crew.regenerate_proposal_crew()

    section_input = {
        "section": section,
        "form_data": form_data,
        "project_description": project_description,
        "instructions": instructions,
        "limit_type": limit_type,
        "limit_value": limit_value,
        "concise_input": concise_input,
    }

    result = crew_instance.kickoff(inputs=section_input)

    # Clean and parse the raw output from the crew.
    # raw_output = result.raw.replace("`", "")
    # raw_output = re.sub(r'[\x00-\x1F\x7F]', '', raw_output)

    raw_output = result.raw if hasattr(result, "raw") and result.raw else ""

    # Use a regex to find and extract the JSON code block
    json_match = re.search(r"```json\s*(\{.*\})\s*```", raw_output, re.DOTALL)

    if json_match:
        raw_output = json_match.group(1)
    else:
        # If a markdown code block isn't found, try to find a standalone JSON object
        # This regex is less specific and might catch more non-JSON content
        json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if json_match:
            raw_output = json_match.group(0)
        else:
            raise HTTPException(
                status_code=500, detail="No JSON object found in crew output."
            )

    try:
        parsed = json.loads(raw_output)
        generated_text = parsed.get("generated_content", "").strip()
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500, detail="Invalid JSON response from regeneration crew."
        )

    if not generated_text:
        generated_text = FALLBACK_GENERATION_MESSAGE

    # Update the section in the session data.
    session_data.setdefault("generated_sections", {})[section] = generated_text
    redis_client.set(session_id, json.dumps(session_data))

    return generated_text
