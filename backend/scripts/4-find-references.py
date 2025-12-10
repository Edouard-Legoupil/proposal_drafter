import argparse
import os
import sys
import uuid
import json
import logging
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import register_uuid
import re

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.utils.crew_reference import ReferenceIdentificationCrew

register_uuid()

def main():
    parser = argparse.ArgumentParser(description="Find references for knowledge cards.")
    # Changed to optional argument with --card-type to match other scripts and user expectation
    parser.add_argument("--card-type", choices=['outcome', 'field_context', 'donor', 'all'], required=True, help="The type of knowledge card to find references for, or 'all' to process every type.")
    parser.add_argument("--user-id", required=True, help="The UUID of the user to associate with the created records.")

    args = parser.parse_args()

    # Logging Configuration
    log_file = os.path.join(os.path.dirname(__file__), 'find_references.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Suppress verbose logs from external libraries as per user request
    for logger_name in ["litellm", "httpx", "httpcore", "openai", "urllib3"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    logging.info("Starting reference finding process...")

    # Load environment variables from .env file
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

    # Database connection
    db_username = os.getenv("DB_USERNAME").strip('"')
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    db_host = os.getenv("DB_HOST", "localhost") # Added default
    db_port = os.getenv("DB_PORT", "5432") # Added default

    conn = None
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_username,
            password=db_password,
            host=db_host,
            port=db_port
        )
        with conn.cursor() as cur:
            user_id = uuid.UUID(args.user_id)

            card_types_to_process = []
            if args.card_type == 'all':
                card_types_to_process = ['outcome', 'field_context', 'donor']
            else:
                card_types_to_process.append(args.card_type)

            table_map = {
                'outcome': ('outcomes', 'outcome_id'),
                'field_context': ('field_contexts', 'field_context_id'),
                'donor': ('donors', 'donor_id')
            }

            for card_type in card_types_to_process:
                table_name, column_name = table_map[card_type]
                cur.execute(f"SELECT id, name FROM {table_name}")
                items = cur.fetchall()
                
                logging.info(f"Processing {len(items)} items for type: {card_type}")

                for item_id, item_name in items:
                    logging.info(f"Processing record: {item_name} ({card_type})")

                    try:
                        reference_crew = ReferenceIdentificationCrew()
                        # Crew execution (API calls happen here, detailed logs suppressed)
                        crew_result = reference_crew.kickoff(link_type=card_type, topic=item_name)

                        # Handle CrewOutput object if applicable
                        if hasattr(crew_result, 'raw'):
                            crew_output = crew_result.raw
                        else:
                            crew_output = crew_result

                        urls = []
                        # Case 1: Output is already a structured list of dicts
                        if isinstance(crew_output, list):
                            for item in crew_output:
                                if isinstance(item, dict) and 'url' in item:
                                    urls.append(item['url'])
                        
                        # Case 2: Output is a string (could be JSON string or Markdown)
                        elif isinstance(crew_output, str):
                            # Try parsing as JSON first
                            try:
                                json_data = json.loads(crew_output)
                                if isinstance(json_data, list):
                                    for item in json_data:
                                        if isinstance(item, dict) and 'url' in item:
                                            urls.append(item['url'])
                                elif isinstance(json_data, dict) and 'url' in json_data:
                                     urls.append(json_data['url'])
                                else:
                                     # If valid JSON but not the structure we want, fall back to regex
                                     raise ValueError("Not a list of refs")
                            except (json.JSONDecodeError, ValueError):
                                # Fallback to regex for Markdown links
                                found_urls = re.findall(r'\[.*?\]\((https?://[^\s]+)\)', crew_output)
                                urls.extend(found_urls)
                        
                        else:
                            logging.warning(f"Unexpected output type from crew: {type(crew_output)}")

                        if not urls:
                             logging.info(f"No references found for {item_name}.")
                             continue

                        count_new = 0
                        for url in urls:
                            # Check if reference exists, otherwise create it
                            cur.execute("SELECT id FROM knowledge_card_references WHERE url = %s", (url,))
                            result = cur.fetchone()
                            if result:
                                reference_id = result[0]
                            else:
                                reference_id = uuid.uuid4()
                                cur.execute("""
                                    INSERT INTO knowledge_card_references (id, url, reference_type, summary, created_by, updated_by)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, (reference_id, url, 'web', f'Reference for {item_name}', user_id, user_id))
                                count_new += 1

                            # Get knowledge_card_id
                            cur.execute(f"SELECT id FROM knowledge_cards WHERE {column_name} = %s", (item_id,))
                            card_id_result = cur.fetchone()
                            if not card_id_result:
                                logging.warning(f"Knowledge card not found for {item_name} (ID: {item_id})")
                                continue
                            card_id = card_id_result[0]

                            # Link reference to knowledge card
                            cur.execute("""
                                INSERT INTO knowledge_card_to_references (knowledge_card_id, reference_id)
                                VALUES (%s, %s) ON CONFLICT DO NOTHING
                            """, (card_id, reference_id))
                        
                        logging.info(f"Successfully processed {item_name}. found {len(urls)} refs ({count_new} new).")

                    except Exception as inner_e:
                         logging.error(f"Error processing item {item_name}: {inner_e}", exc_info=True)

            conn.commit()
            logging.info("All references updated successfully.")

    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Critical error: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()
        logging.info("Process finished.")

if __name__ == "__main__":
    main()
