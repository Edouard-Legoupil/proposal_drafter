#  Standard Library
import json
import re

#  Internal Modules
from backend.utils.proposal_logic import regenerate_section_logic

def handle_text_format(section_config, crew_instance, form_data, project_description, session_id, proposal_id):
    """Handles 'text' format_type."""
    section_name = section_config["section_name"]
    result = crew_instance.kickoff(inputs={
        "section": section_name,
        "form_data": form_data,
        "project_description": project_description,
        "instructions": section_config.get("instructions", ""),
        "word_limit": section_config.get("word_limit", 350)
    })
    try:
        raw_output = result.raw if hasattr(result, 'raw') and result.raw else ""
        clean_output = re.sub(r'[`\x00-\x1F\x7F]', '', raw_output)
        parsed = json.loads(clean_output)
    except (AttributeError, json.JSONDecodeError) as e:
        print(f"[CREWAI PARSE ERROR] for section {section_name}: {e}")
        return ""

    generated_text = parsed.get("generated_content", "").strip()
    evaluation_status = parsed.get("evaluation_status", "")
    feedback = parsed.get("feedback", "")

    if evaluation_status.lower() == "flagged" and feedback:
        generated_text = regenerate_section_logic(
            session_id, section_name, feedback, proposal_id
        )

    return generated_text

def handle_fixed_text_format(section_config):
    """Handles 'fixed_text' format_type."""
    return section_config.get("fixed_text", "")

def handle_number_format(section_config, crew_instance, form_data, project_description):
    """Handles 'number' format_type."""
    section_name = section_config["section_name"]
    result = crew_instance.kickoff(inputs={
        "section": section_name,
        "form_data": form_data,
        "project_description": project_description,
        "instructions": section_config.get("instructions", ""),
        "word_limit": 10  # A small word limit for numbers
    })
    try:
        raw_output = result.raw if hasattr(result, 'raw') and result.raw else ""
        clean_output = re.sub(r'[`\x00-\x1F\x7F]', '', raw_output)
        parsed = json.loads(clean_output)
        generated_text = parsed.get("generated_content", "").strip()
        # Extract the first number from the output
        match = re.search(r'\d+', generated_text)
        return match.group(0) if match else "0"
    except (AttributeError, json.JSONDecodeError) as e:
        print(f"[CREWAI PARSE ERROR] for section {section_name}: {e}")
        return "0"


def handle_table_format(section_config, crew_instance, form_data, project_description):
    """Handles 'table' format_type."""
    section_name = section_config["section_name"]
    instructions = section_config.get("instructions", "")
    columns = section_config.get("columns", [])
    rows = section_config.get("rows", [])

    # Construct a detailed prompt for the table
    prompt = f"{instructions}\n\nGenerate a Markdown table.\n\n"
    prompt += "Use the following column definitions:\n"
    for col in columns:
        prompt += f"- Column '{col['name']}': {col.get('instructions', '')}\n"

    prompt += "\nUse the following row definitions:\n"
    for row in rows:
        prompt += f"- Row '{row['row_title']}': {row.get('instructions', '')}\n"


    result = crew_instance.kickoff(inputs={
        "section": section_name,
        "form_data": form_data,
        "project_description": project_description,
        "instructions": prompt,
        "word_limit": 1000  # A larger word limit for tables
    })
    try:
        raw_output = result.raw if hasattr(result, 'raw') and result.raw else ""
        clean_output = re.sub(r'[`\x00-\x1F\x7F]', '', raw_output)
        parsed = json.loads(clean_output)
        return parsed.get("generated_content", "").strip()
    except (AttributeError, json.JSONDecodeError) as e:
        print(f"[CREWAI PARSE ERROR] for section {section_name}: {e}")
        return ""
