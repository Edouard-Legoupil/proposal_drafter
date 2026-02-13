#  Standard Library
import json
import re
import logging

#  Internal Modules
from backend.utils.proposal_logic import regenerate_section_logic

# Configure logging
logger = logging.getLogger(__name__)


def repair_json_string(json_str):
    """
    Attempts to repair common AI JSON syntax errors.
    """
    # Clean only truly problematic control characters
    clean_json_str = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", json_str)
    
    try:
        return json.loads(clean_json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"Initial JSON parse failed, attempting repair: {e}")
        
        # Step 1: Escape literal newlines inside JSON strings
        # Use a NON-GREEDY match for strings to avoid matching across properties
        def escape_newlines_callback(match):
            return match.group(0).replace("\n", "\\n").replace("\r", "\\r")
        
        repaired = re.sub(r'"(?:[^"\\]|\\.)*?"', escape_newlines_callback, clean_json_str, flags=re.DOTALL)
        
        # Step 2: Fix numbers with commas (thousands separators like 1,800.00)
        for _ in range(3):
            repaired = re.sub(r'(\d),(\d{3})(?!\d)', r'\1\2', repaired)

        # Step 3: Remove trailing commas within objects and arrays
        repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
        
        # Step 4: Quote unquoted keys
        # We look for words followed by a colon. We exclude things already in quotes.
        # This is safer: find {key: or ,key:
        repaired = re.sub(r"([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)", r'\1"\2"\3', repaired)
        
        # Step 5: Handle single quote usage for keys/values
        # Keys: {'key': ...} -> {"key": ...}
        repaired = re.sub(r"([{,]\s*)'([a-zA-Z_][a-zA-Z0-9_]*)'(\s*:)", r'\1"\2"\3', repaired)
        # Values: {..., "key": 'value'} -> {..., "key": "value"}
        repaired = re.sub(r"(:\s*)'([^']*)'(\s*[,}])", r'\1"\2"\3', repaired)
        
        try:
            return json.loads(repaired)
        except Exception as repair_err:
            logger.error(f"JSON repair failed final attempt: {repair_err}")
            return None


def extract_json_from_crew_output(result):
    """
    Extracts and parses JSON from CrewAI result, handling potential markdown blocks.
    """
    try:
        raw_output = result.raw if hasattr(result, "raw") and result.raw else ""
        if not raw_output:
            return None

        # Try to find JSON content often wrapped in markdown blocks
        json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if not json_match:
            return None
        
        return repair_json_string(json_match.group(0))
    except Exception as e:
        logger.error(f"Critical error in extract_json_from_crew_output: {e}")
        return None


def handle_text_format(
    section_config,
    crew_instance,
    form_data,
    project_description,
    session_id,
    proposal_id,
    special_requirements="None",
):
    """Handles 'text' format_type."""
    section_name = section_config["section_name"]
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
        limit_value = 350  # fallback

    limit_instruction = f"IMPORTANT: Do not exceed {limit_value} {'characters' if limit_type == 'char' else 'words'} for this section. If your response is longer, you MUST summarize or truncate to fit the limit."
    instructions = section_config.get("instructions", "")
    if instructions:
        instructions += " " + limit_instruction
    else:
        instructions = limit_instruction

    inputs = {
        "section": section_name,
        "form_data": form_data,
        "project_description": project_description,
        "instructions": instructions,
        "special_requirements": special_requirements,
        "limit_value": limit_value,
        "limit_term": "character" if limit_type == "char" else "word",
    }
    if limit_type == "char":
        inputs["char_limit"] = limit_value
    else:
        inputs["word_limit"] = limit_value
    result = crew_instance.kickoff(inputs=inputs)
    parsed = extract_json_from_crew_output(result)
    if not parsed:
        logger.error(f"[CREWAI PARSE ERROR] for section {section_name}")
        return ""

    generated_text = parsed.get("generated_content", "").strip()
    evaluation_status = parsed.get("evaluation_status", "")
    feedback = parsed.get("feedback", "")

    # REMOVED AGGRESSIVE SANITISATION (LIMIT TRUNCATION) TO PRESERVE MARKDOWN
    # We now trust the LLM to follow the length instructions in the prompt.
    # if limit_type == "char" and isinstance(generated_text, str):
    #     generated_text = generated_text[:limit_value]
    # elif limit_type == "word" and isinstance(generated_text, str):
    #     generated_text = " ".join(generated_text.split()[:limit_value])

    if evaluation_status.lower() == "flagged" and feedback:
        generated_text = regenerate_section_logic(
            session_id, section_name, feedback, proposal_id
        )

    return generated_text


def handle_fixed_text_format(section_config):
    """Handles 'fixed_text' format_type."""
    return section_config.get("fixed_text", "")


def handle_number_format(
    section_config,
    crew_instance,
    form_data,
    project_description,
    special_requirements="None",
):
    """Handles 'number' format_type."""
    section_name = section_config["section_name"]
    # Always provide all three vars for robust prompts
    inputs = {
        "section": section_name,
        "form_data": form_data,
        "project_description": project_description,
        "instructions": section_config.get("instructions", ""),
        "word_limit": 10,  # Numbers use a small word limit
        "special_requirements": special_requirements,
        "limit_value": 10,
        "limit_term": "word",
    }
    result = crew_instance.kickoff(inputs=inputs)

    parsed = extract_json_from_crew_output(result)
    if not parsed:
        logger.error(f"[CREWAI PARSE ERROR] for section {section_name}")
        return "0"

    generated_text = parsed.get("generated_content", "").strip()
    # Extract the first number from the output
    match = re.search(r"\d+", generated_text)
    return match.group(0) if match else "0"


def handle_table_format(
    section_config,
    crew_instance,
    form_data,
    project_description,
    special_requirements="None",
):
    """Handles 'table' format_type by converting generated JSON to a Markdown table."""
    section_name = section_config["section_name"]
    instructions = section_config.get("instructions", "")
    columns = section_config.get("columns", [])
    rows = section_config.get("rows", [])

    # Construct a detailed prompt for the table
    prompt = (
        f"{instructions}\n\n"
        f"Generate a JSON object for the section '{section_name}'. "
        "The JSON object must have a single top-level key which is the section name. "
        "The value for this key should be an object containing two keys: 'table' and 'notes'.\n"
        "- The 'table' key should contain a list of JSON objects, where each object represents a row.\n"
        "- The 'notes' key should contain a string for any footnotes or additional information.\n\n"
        "The columns for the table are:\n"
    )
    column_names = [col["name"] for col in columns]
    prompt += f"`{', '.join(column_names)}`\n\n"

    prompt += "Use the following column definitions for guidance:\n"
    for col in columns:
        prompt += f"- Column '{col['name']}': {col.get('instructions', '')}\n"

    prompt += "\nUse the following row definitions for guidance:\n"
    for row in rows:
        prompt += f"- Row '{row['row_title']}': {row.get('instructions', '')}\n"

    # Dynamic limit values for tables
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
        limit_value = 2000  # fallback for tables

    inputs = {
        "section": section_name,
        "form_data": form_data,
        "project_description": project_description,
        "instructions": prompt,
        "special_requirements": special_requirements,
        "limit_value": limit_value,
        "limit_term": "character" if limit_type == "char" else "word",
    }
    if limit_type == "char":
        inputs["char_limit"] = limit_value
    else:
        inputs["word_limit"] = limit_value

    result = crew_instance.kickoff(inputs=inputs)

    parsed_crew_output = extract_json_from_crew_output(result)
    if not parsed_crew_output:
        logger.error(f"[CREWAI PARSE ERROR] for section {section_name}")
        return ""

    generated_content = parsed_crew_output.get("generated_content", "")
    logger.info(
        f"Generated content for section '{section_name}':\n{json.dumps(generated_content, indent=2)}"
    )

    table_data = {}
    pre_text = ""
    post_text = ""

    try:
        # Handle dict format for generated_content
        if isinstance(generated_content, dict):
            table_data = generated_content

        # Handle str format for generated_content
        elif isinstance(generated_content, str):
            json_match = re.search(r"\{.*\}", generated_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                pre_text = generated_content[: json_match.start()].strip()
                post_text = generated_content[json_match.end() :].strip()
                try:
                    table_data = repair_json_string(json_str) or {}
                except Exception:
                    logger.warning(
                        f"Could not parse JSON from string for section '{section_name}'. Returning as is."
                    )
                    return generated_content
            else:
                logger.warning(
                    f"No JSON object found in the string content for section '{section_name}'. Returning as is."
                )
                return generated_content

        section_data = table_data.get(section_name, {})
        table_rows = section_data.get("table", [])
        notes = section_data.get("notes", "")
        
        # REMOVED AGGRESSIVE SANITISATION ON NOTES
        # Use LLM compliance for length control
        # if (
        #     "limit_type" in locals()
        #     and "limit_value" in locals()
        #     and isinstance(notes, str)
        # ):
        #     if limit_type == "char":
        #         notes = notes[:limit_value]
        #     elif limit_type == "word":
        #         notes = " ".join(notes.split()[:limit_value])

        if not table_rows:
            # If table is empty, return original text content containing the error/message
            logger.warning(
                f"No rows found in the table for section '{section_name}'. Returning original content."
            )
            return json.dumps(table_data) if table_data else ""

        # --- VALIDATION STEP ---
        if not isinstance(table_rows, list):
             logger.error(f"Table data for section '{section_name}' is not a list. Skipping table formatting.")
             return json.dumps(table_data)
        
        # Check for missing columns in the first row (and warn)
        if table_rows and isinstance(table_rows[0], dict):
             expected_columns = [col["name"] for col in columns]
             actual_columns = table_rows[0].keys()
             missing_cols = set(expected_columns) - set(actual_columns)
             if missing_cols:
                  logger.warning(f"Table for section '{section_name}' is missing columns: {missing_cols}. Proceeding with available data.")
        # -----------------------

        # Use headers from the first row to maintain order
        headers = list(table_rows[0].keys())

        header_line = f"| {' | '.join(headers)} |"
        separator_line = f"| {' | '.join(['---'] * len(headers))} |"
        row_lines = []
        for row in table_rows:
            formatted_cells = []
            for h in headers:
                cell_value = str(row.get(h, ""))
                # Replace both literal and escaped newlines with <br> for markdown tables
                cell_value = cell_value.replace("\\n", "<br>").replace("\n", "<br>")
                formatted_cells.append(cell_value)
            row_lines.append(f"| {' | '.join(formatted_cells)} |")

        markdown_table = "\n".join([header_line, separator_line] + row_lines)

        final_content = []
        if pre_text:
            final_content.append(pre_text)

        final_content.append(markdown_table)

        if notes:
            final_content.append(f"\n{notes}")

        if post_text:
            final_content.append(f"\n{post_text}")

        final_output = "\n".join(final_content)
        logger.info(
            f"Successfully formatted section '{section_name}' with a Markdown table."
        )
        return final_output

    except Exception as e:
        logger.error(
            f"[CREWAI TABLE FORMAT ERROR] for section {section_name}: {e}", exc_info=True
        )
        return ""
