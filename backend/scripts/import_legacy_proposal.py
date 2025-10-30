# backend/scripts/import_legacy_proposal.py
import argparse
import logging
import fitz  # PyMuPDF
import os
import json
import re
import sys
import uuid
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import Json, register_uuid

# Add the project root to the Python path and register UUID for psycopg2
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
register_uuid()

from utils.crew_legacy_import import ParameterExtractionCrew

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text_as_markdown(pdf_path: str) -> str:
    markdown_content = ""
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_INHIBIT_SPACES)["blocks"]
            font_sizes = [span['size'] for block in blocks if 'lines' in block for line in block['lines'] for span in line['spans']]
            if not font_sizes: continue
            base_font_size_threshold = sorted(list(set(font_sizes)), reverse=True)[0] * 0.95

            for block in blocks:
                if "lines" not in block: continue
                for line in block["lines"]:
                    line_text = "".join(span["text"] for span in line["spans"]).strip()
                    if not line_text: continue
                    span_sizes = [span['size'] for span in line['spans']]
                    is_heading = any(size > base_font_size_threshold for size in span_sizes)
                    if is_heading:
                        markdown_content += f"## {line_text}\n\n"
                    else:
                        markdown_content += f"{line_text}\n"
                markdown_content += "\n"
    except Exception as e:
        logging.error(f"Failed to extract text from {pdf_path}: {e}")
        return ""
    return markdown_content

def find_best_template_match(markdown_content: str) -> str:
    pdf_headings = set(re.findall(r"^##\s(.+)", markdown_content, re.MULTILINE))
    if not pdf_headings:
        logging.warning("No headings found in the PDF content.")
        return None

    templates_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
    best_match = None
    highest_score = 0

    for filename in os.listdir(templates_dir):
        if filename.startswith("proposal_template_") and filename.endswith(".json"):
            filepath = os.path.join(templates_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    template_data = json.load(f)
                    template_headings = set(section['section_name'] for section in template_data.get('sections', []))
                    score = len(pdf_headings.intersection(template_headings))
                    if score > highest_score:
                        highest_score = score
                        best_match = filename
            except Exception as e:
                logging.error(f"Failed to read or parse template {filename}: {e}")
    return best_match

def get_or_create_record(cur, table_name, name, user_id):
    if not name: return None
    cur.execute(f"SELECT id FROM {table_name} WHERE name = %s", (name,))
    result = cur.fetchone()
    if result:
        return result[0]
    else:
        new_id = uuid.uuid4()
        cur.execute(f"INSERT INTO {table_name} (id, name, created_by) VALUES (%s, %s, %s)", (new_id, name, user_id))
        logging.info(f"Created new entry in {table_name} for '{name}'.")
        return new_id

def main():
    parser = argparse.ArgumentParser(description="Import a legacy proposal from a PDF document.")
    parser.add_argument("pdf_path", type=str, help="The path to the PDF file to import.")
    parser.add_argument("--user-id", required=True, help="The UUID of the user to associate with the imported proposal.")
    args = parser.parse_args()

    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    db_username = os.getenv("DB_USERNAME").strip('"')
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    conn = None

    try:
        conn = psycopg2.connect(dbname=db_name, user=db_username, password=db_password, host="localhost", port="5432")
        with conn.cursor() as cur:
            user_id = uuid.UUID(args.user_id)

            markdown_text = extract_text_as_markdown(args.pdf_path)
            if not markdown_text:
                raise Exception("Failed to extract text from PDF.")

            template_name = find_best_template_match(markdown_text)
            if not template_name:
                raise Exception("No matching template found.")
            logging.info(f"Matched template: {template_name}")

            crew = ParameterExtractionCrew(proposal_markdown=markdown_text)
            params = crew.run()
            if not params or not isinstance(params, dict):
                 # Attempt to parse from string if needed
                try:
                    params = json.loads(params)
                except (json.JSONDecodeError, TypeError):
                    raise Exception(f"AI crew returned invalid or empty parameters: {params}")

            logging.info(f"Extracted parameters: {json.dumps(params, indent=2)}")

            # Get or create foreign key records
            donor_id = get_or_create_record(cur, 'donors', params.get('Targeted Donor'), user_id)
            outcome_id = get_or_create_record(cur, 'outcomes', params.get('Main Outcome'), user_id)
            field_context_id = get_or_create_record(cur, 'field_contexts', params.get('Country / Location(s)'), user_id)

            # Create the proposal record
            proposal_id = uuid.uuid4()
            form_data = {key: val for key, val in params.items() if val is not None}

            # Ensure main relations are set correctly in form_data for consistency
            form_data['Targeted Donor'] = donor_id
            form_data['Main Outcome'] = [outcome_id] if outcome_id else []
            form_data['Country / Location(s)'] = field_context_id

            cur.execute(
                """
                INSERT INTO proposals (id, project_name, status, form_data, created_by)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (proposal_id, params.get('Project Draft Short name', 'Untitled Legacy Proposal'), 'draft', Json(form_data), user_id)
            )
            logging.info(f"Created new proposal record with ID: {proposal_id}")

            # Update the record with the full markdown content and set status to submitted
            generated_sections = { "Imported Content": markdown_text }
            cur.execute(
                """
                UPDATE proposals
                SET status = 'submitted', generated_sections = %s, proposal_template_name = %s
                WHERE id = %s
                """,
                (Json(generated_sections), template_name, proposal_id)
            )
            logging.info(f"Updated proposal {proposal_id} with full content and set status to 'submitted'.")

            conn.commit()
            logging.info("Legacy proposal import successful.")

    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
