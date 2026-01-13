#  Standard Library
import json
import re
import logging

#  Internal Modules
from backend.utils.proposal_logic import regenerate_section_logic

# Configure logging
logger = logging.getLogger(__name__)


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
    try:
        raw_output = result.raw if hasattr(result, "raw") and result.raw else ""
        clean_output = re.sub(r"[`\x00-\x1F\x7F]", "", raw_output)
        parsed = json.loads(clean_output)
    except (AttributeError, json.JSONDecodeError) as e:
        print(f"[CREWAI PARSE ERROR] for section {section_name}: {e}")
        return ""

    generated_text = parsed.get("generated_content", "").strip()
    evaluation_status = parsed.get("evaluation_status", "")
    feedback = parsed.get("feedback", "")

    # ENFORCE CHAR OR WORD LIMITS on text output
    if limit_type == "char" and isinstance(generated_text, str):
        generated_text = generated_text[:limit_value]
    elif limit_type == "word" and isinstance(generated_text, str):
        generated_text = " ".join(generated_text.split()[:limit_value])

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

    try:
        raw_output = result.raw if hasattr(result, "raw") and result.raw else ""
        clean_output = re.sub(r"[`\x00-\x1F\x7F]", "", raw_output)
        parsed = json.loads(clean_output)
        generated_text = parsed.get("generated_content", "").strip()
        # Extract the first number from the output
        match = re.search(r"\d+", generated_text)
        return match.group(0) if match else "0"
    except (AttributeError, json.JSONDecodeError) as e:
        print(f"[CREWAI PARSE ERROR] for section {section_name}: {e}")
        return "0"


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

    try:
        raw_output = result.raw if hasattr(result, "raw") and result.raw else ""
        clean_output = re.sub(r"[`\x00-\x1F\x7F]", "", raw_output)
        parsed_crew_output = json.loads(clean_output)
        generated_content = parsed_crew_output.get("generated_content", "")
        logger.info(
            f"Generated content for section '{section_name}':\n{json.dumps(generated_content, indent=2)}"
        )

        table_data = {}
        pre_text = ""
        post_text = ""

        # Handle  dict  format for generated_content
        if isinstance(generated_content, dict):
            table_data = generated_content

        # Handle str  format for generated_content
        elif isinstance(generated_content, str):
            json_match = re.search(r"\{.*\}", generated_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                pre_text = generated_content[: json_match.start()].strip()
                post_text = generated_content[json_match.end() :].strip()
                try:
                    table_data = json.loads(json_str)
                except json.JSONDecodeError:
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
        # ENFORCE CHAR OR WORD LIMIT ON NOTES
        if (
            "limit_type" in locals()
            and "limit_value" in locals()
            and isinstance(notes, str)
        ):
            if limit_type == "char":
                notes = notes[:limit_value]
            elif limit_type == "word":
                notes = " ".join(notes.split()[:limit_value])
        if not table_rows:
            # If table is empty, return original text content
            logger.warning(
                f"No rows found in the table for section '{section_name}'. Returning original content."
            )
            return json.dumps(table_data) if table_data else ""

        # Use headers from the first row to maintain order
        headers = list(table_rows[0].keys())

        header_line = f"| {' | '.join(headers)} |"
        separator_line = f"| {' | '.join(['---'] * len(headers))} |"
        row_lines = [
            f"| {' | '.join([str(row.get(h, '')) for h in headers])} |"
            for row in table_rows
        ]

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

    except (AttributeError, json.JSONDecodeError) as e:
        logger.error(
            f"[CREWAI PARSE ERROR] for section {section_name}: {e}", exc_info=True
        )
        return ""
