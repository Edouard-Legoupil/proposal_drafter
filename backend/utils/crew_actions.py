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
    column_names = [col['name'] for col in columns]
    prompt += f"`{', '.join(column_names)}`\n\n"

    prompt += "Use the following column definitions for guidance:\n"
    for col in columns:
        prompt += f"- Column '{col['name']}': {col.get('instructions', '')}\n"

    prompt += "\nUse the following row definitions for guidance:\n"
    for row in rows:
        prompt += f"- Row '{row['row_title']}': {row.get('instructions', '')}\n"


    result = crew_instance.kickoff(inputs={
        "section": section_name,
        "form_data": form_data,
        "project_description": project_description,
        "instructions": prompt,
        "word_limit": 2000  # Increased limit for JSON verbosity
    })
    try:
        raw_output = result.raw if hasattr(result, 'raw') and result.raw else ""
        clean_output = re.sub(r'[`\x00-\x1F\x7F]', '', raw_output)
        # The AI's output is a JSON object with 'generated_content'
        parsed_crew_output = json.loads(clean_output)
        generated_content_str = parsed_crew_output.get("generated_content", "").strip()
        
        # The generated content itself is a JSON string.
        try:
            # Clean up potential markdown code fences around the JSON
            if generated_content_str.startswith("```json"):
                generated_content_str = generated_content_str[7:]
            if generated_content_str.endswith("```"):
                generated_content_str = generated_content_str[:-3]
            
            table_data = json.loads(generated_content_str)
            
            # Extract data from the expected structure
            section_data = table_data.get(section_name, {})
            table_rows = section_data.get("table", [])
            notes = section_data.get("notes", "")

            if not table_rows:
                return "" # Return empty if no table data

            headers = list(table_rows[0].keys())
            
            # Build markdown table
            header_line = f"| {' | '.join(headers)} |"
            separator_line = f"| {' | '.join(['---'] * len(headers))} |"
            
            row_lines = []
            for row in table_rows:
                values = [str(row.get(h, '')) for h in headers]
                row_lines.append(f"| {' | '.join(values)} |")
            
            markdown_table = "\n".join([header_line, separator_line] + row_lines)

            if notes:
                markdown_table += f"\n\n{notes}"
            
            return markdown_table

        except (json.JSONDecodeError, AttributeError, IndexError) as e:
            print(f"[MARKDOWN CONVERSION ERROR] for section {section_name}: {e}. Raw content: {generated_content_str}")
            return f"Error: Could not parse table from AI output.\n\n{generated_content_str}"

    except (AttributeError, json.JSONDecodeError) as e:
        print(f"[CREWAI PARSE ERROR] for section {section_name}: {e}")
        return ""
