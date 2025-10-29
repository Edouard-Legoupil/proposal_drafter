#  Standard Library
import json
import re
import logging

#  Internal Modules
from backend.utils.proposal_logic import regenerate_section_logic

# Configure logging
logger = logging.getLogger(__name__)

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
        generated_content = parsed_crew_output.get("generated_content")

        generated_content = parsed_crew_output.get("generated_content", "")
        logger.info(f"Generated content for section '{section_name}':\n{generated_content}")

        # Handle both dict and str for generated_content
        if isinstance(generated_content, dict):
            content_str = json.dumps(generated_content)
        else:
            content_str = str(generated_content).strip()
        
        # Regex to find JSON block within the string
        json_match = re.search(r'\{.*\}', content_str, re.DOTALL)
        
        if not json_match:
            # If no JSON is found, return the content as is, assuming it's just text.
            logger.warning(f"No JSON object found in the content for section '{section_name}'. Returning as is.")
            return content_str

        json_str = json_match.group(0)
        pre_text = content_str[:json_match.start()].strip()
        post_text = content_str[json_match.end():].strip()
        logger.info(f"Extracted pre-text: '{pre_text}'")
        logger.info(f"Extracted post-text: '{post_text}'")

        try:
            table_data = json.loads(json_str)
            
            section_data = table_data.get(section_name, {})
            table_rows = section_data.get("table", [])
            notes = section_data.get("notes", "")

            if not table_rows:
                # If table is empty, return original text content
                logger.warning(f"No rows found in the table for section '{section_name}'. Returning original content.")
                return content_str

            headers = list(table_rows[0].keys())
            
            header_line = f"| {' | '.join(headers)} |"
            separator_line = f"| {' | '.join(['---'] * len(headers))} |"
            
            row_lines = [f"| {' | '.join([str(row.get(h, '')) for h in headers])} |" for row in table_rows]
            
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
            logger.info(f"Successfully formatted section '{section_name}' with a Markdown table.")
            return final_output

        except (json.JSONDecodeError, AttributeError, IndexError) as e:
            logger.error(f"[MARKDOWN CONVERSION ERROR] for section {section_name}: {e}. Raw content: {content_str}", exc_info=True)
            # Fallback to returning the original content if table parsing fails
            return content_str

    except (AttributeError, json.JSONDecodeError) as e:
        logger.error(f"[CREWAI PARSE ERROR] for section {section_name}: {e}", exc_info=True)
        return ""
