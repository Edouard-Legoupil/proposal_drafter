import argparse
import asyncio
import json
import os
import sys
import uuid
import logging
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import register_uuid
from slugify import slugify

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
register_uuid()

from backend.utils.crew_knowledge import ContentGenerationCrew
from backend.core.config import load_proposal_template

# Ensure the log directory exists
os.makedirs("log", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log/generate_card_content.log"),
        logging.StreamHandler()
    ]
)

def _save_knowledge_card_content_to_file(cur, card_id: uuid.UUID, generated_sections: dict):
    """
    Saves the generated content of a knowledge card to a file in the 'backend/knowledge' directory.
    """
    try:
        # Fetch the knowledge card's details and the name of the linked entity
        cur.execute("""
            SELECT
                kc.summary,
                kc.donor_id,
                kc.outcome_id,
                kc.field_context_id,
                d.name as donor_name,
                o.name as outcome_name,
                fc.name as field_context_name
            FROM
                knowledge_cards kc
            LEFT JOIN
                donors d ON kc.donor_id = d.id
            LEFT JOIN
                outcomes o ON kc.outcome_id = o.id
            LEFT JOIN
                field_contexts fc ON kc.field_context_id = fc.id
            WHERE
                kc.id = %s
        """, (str(card_id),))
        card_details = cur.fetchone()

        if not card_details:
            logging.error(f"Cannot save content to file: Knowledge card with id {card_id} not found.")
            return

        # Manually assign column names
        summary_idx = 0
        donor_id_idx = 1
        outcome_id_idx = 2
        field_context_id_idx = 3
        donor_name_idx = 4
        outcome_name_idx = 5
        field_context_name_idx = 6

        card_summary = card_details[summary_idx]
        link_type = None
        link_label = None

        if card_details[donor_id_idx]:
            link_type = "donor"
            link_label = card_details[donor_name_idx]
        elif card_details[outcome_id_idx]:
            link_type = "outcome"
            link_label = card_details[outcome_name_idx]
        elif card_details[field_context_id_idx]:
            link_type = "field_context"
            link_label = card_details[field_context_name_idx]

        # Create a clean, URL-safe filename using the human-readable label
        if link_type and link_label:
            filename = f"{link_type}-{slugify(link_label)}-{slugify(card_summary)}.json"
        else:
            # Fallback for cards without a direct link
            filename = f"{slugify(card_summary)}.json"

        # Construct a robust path to the 'backend/knowledge' directory.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        knowledge_dir = os.path.join(current_dir, "..", "knowledge")
        filepath = os.path.join(knowledge_dir, filename)

        # Ensure the knowledge directory exists
        os.makedirs(knowledge_dir, exist_ok=True)

        # Write the generated sections to the JSON file
        with open(filepath, 'w') as f:
            json.dump(generated_sections, f, indent=4)

        logging.info(f"Knowledge card content saved to {filepath}")

    except Exception as e:
        logging.error(f"Failed to save knowledge card content to file for card {card_id}: {e}", exc_info=True)


def create_knowledge_card_history_entry(cur, card_id, generated_sections, user_id):
    """
    Creates a history entry for a knowledge card.
    """
    try:
        cur.execute("""
            INSERT INTO knowledge_card_history (knowledge_card_id, generated_sections_snapshot, created_by, created_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        """, (card_id, json.dumps(generated_sections), user_id))
    except Exception as e:
        logging.error(f"Failed to create history entry for card {card_id}: {e}", exc_info=True)

def main():
    parser = argparse.ArgumentParser(description="Generate content for knowledge cards.")
    parser.add_argument("--force", action="store_true", help="Force regeneration of content for all knowledge cards.")
    parser.add_argument("--user-id", required=True, help="The UUID of the user to associate with the created records.")
    args = parser.parse_args()

    logging.info("Starting content generation process...")

    conn = None
    try:
        # Load environment variables from .env file
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

        # Database connection
        db_username = os.getenv("DB_USERNAME").strip('"')
        db_password = os.getenv("DB_PASSWORD")
        db_name = os.getenv("DB_NAME")
        db_host = "localhost"
        db_port = "5432"

        conn = psycopg2.connect(
            dbname=db_name,
            user=db_username,
            password=db_password,
            host=db_host,
            port=db_port
        )
        with conn.cursor() as cur:
            user_id = uuid.UUID(args.user_id)

            # Get all knowledge cards
            cur.execute("SELECT id, template_name, generated_sections, updated_at FROM knowledge_cards")
            knowledge_cards = cur.fetchall()
            logging.info(f"Found {len(knowledge_cards)} knowledge cards to process.")

            for card in knowledge_cards:
                card_id, template_name, generated_sections, card_updated_at = card
                should_generate = False

                try:
                    if args.force:
                        should_generate = True
                    elif not generated_sections or generated_sections == '{}':
                        should_generate = True
                    else:
                        # Check if any reference is newer than the card
                        cur.execute("""
                            SELECT COUNT(*)
                            FROM knowledge_card_to_references kctr
                            JOIN knowledge_card_references kcr ON kctr.reference_id = kcr.id
                            WHERE kctr.knowledge_card_id = %s AND kcr.updated_at > %s
                        """, (card_id, card_updated_at))
                        if cur.fetchone()[0] > 0:
                            should_generate = True

                    if should_generate:
                        logging.info(f"Generating content for knowledge card {card_id}...")
                        template = load_proposal_template(template_name)
                        new_generated_sections = {}
                        crew = ContentGenerationCrew(knowledge_card_id=str(card_id))

                        for section in template.get("sections", []):
                            section_name = section.get("section_name")
                            instructions = section.get("instructions")
                            inputs = {
                                "section_name": section_name,
                                "instructions": instructions,
                            }
                            result = crew.create_crew().kickoff(inputs=inputs)
                            new_generated_sections[section_name] = str(result)

                        # Update the knowledge card
                        cur.execute("""
                            UPDATE knowledge_cards
                            SET generated_sections = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (json.dumps(new_generated_sections), card_id))

                        # Save content to file
                        _save_knowledge_card_content_to_file(cur, card_id, new_generated_sections)

                        # Create a history entry
                        create_knowledge_card_history_entry(cur, card_id, new_generated_sections, user_id)
                        logging.info(f"Successfully generated content for knowledge card {card_id}")
                except Exception as e:
                    logging.error(f"Error processing knowledge card {card_id}: {e}", exc_info=True)
                    conn.rollback() # Rollback the transaction for the failed card

            conn.commit()
    except Exception as e:
        logging.critical("A critical error occurred in the main process.", exc_info=True)
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
        logging.info("Content generation process finished.")

if __name__ == "__main__":
    main()
