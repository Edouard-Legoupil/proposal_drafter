import argparse
import asyncio
import json
import os
import sys
import uuid
import logging
import pathlib
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import register_uuid

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
register_uuid()

from backend.utils.crew_knowledge import ContentGenerationCrew
from backend.core.config import load_proposal_template



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
    parser.add_argument("--generate-if-null", action="store_true", help="Generate content for knowledge cards only when generated_sections is NULL or empty.")
    parser.add_argument("--card-type", choices=["all", "donor", "outcome", "field_context"], default="all", help="Filter processing by card type (donor, outcome, field_context). Default is all.")
    parser.add_argument("--user-id", required=True, help="The UUID of the user to associate with the created records.")
    args = parser.parse_args()

    log_file = os.path.join(os.path.dirname(__file__), 'generate_card_content.log')
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Configure specific loggers to capture API calls and other external libs
    for logger_name in ["litellm", "httpx", "httpcore", "openai"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        # Avoid adding duplicate handlers if they already propagate to root or have handlers
        if not logger.handlers and not logger.propagate:
             for handler in logging.getLogger().handlers:
                 logger.addHandler(handler)

    logging.info("Starting content generation process...")

    conn = None
    try:
        # Load environment variables from .env file
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

        # Database connection
        db_username = os.getenv("DB_USERNAME").strip('"')
        db_password = os.getenv("DB_PASSWORD")
        db_name = os.getenv("DB_NAME")
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")

        conn = psycopg2.connect(
            dbname=db_name,
            user=db_username,
            password=db_password,
            host=db_host,
            port=db_port
        )
        with conn.cursor() as cur:
            user_id = uuid.UUID(args.user_id)

            query = """
                SELECT 
                    kc.id, 
                    kc.template_name, 
                    kc.generated_sections, 
                    kc.updated_at,
                    d.name as donor_name,
                    o.name as outcome_name,
                    fc.name as field_context_name
                FROM knowledge_cards kc
                LEFT JOIN donors d ON kc.donor_id = d.id
                LEFT JOIN outcomes o ON kc.outcome_id = o.id
                LEFT JOIN field_contexts fc ON kc.field_context_id = fc.id
            """

            where_clauses = []
            if args.generate_if_null:
                where_clauses.append("(kc.generated_sections IS NULL OR kc.generated_sections::text = '{}' OR kc.generated_sections::text = 'null')")
            
            if args.card_type != "all":
                if args.card_type == "donor":
                    where_clauses.append("kc.donor_id IS NOT NULL")
                elif args.card_type == "outcome":
                    where_clauses.append("kc.outcome_id IS NOT NULL")
                elif args.card_type == "field_context":
                    where_clauses.append("kc.field_context_id IS NOT NULL")

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            cur.execute(query)
            knowledge_cards = cur.fetchall()
            logging.info(f"Found {len(knowledge_cards)} knowledge cards to process.")

            for card in knowledge_cards:
                card_id, template_name, generated_sections, card_updated_at, donor_name, outcome_name, field_context_name = card
                card_name = donor_name or outcome_name or field_context_name or f"Card {card_id}"
                
                should_generate = False
                try:
                    if args.force:
                        should_generate = True
                    elif args.generate_if_null:
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
                        logging.info(f"Generating content for knowledge card: {card_name}...")
                        template = load_proposal_template(template_name)
                        pre_prompt = f"{template.get('description', '')} {card_name}."
                        new_generated_sections = {}
                        crew = ContentGenerationCrew(knowledge_card_id=str(card_id), pre_prompt=pre_prompt)

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
                        
                        # Verification
                        cur.execute("SELECT generated_sections FROM knowledge_cards WHERE id = %s", (card_id,))
                        updated_data = cur.fetchone()
                        if updated_data and updated_data[0]:
                             logging.info(f"Verification successful: Content persisted for {card_name}")
                        else:
                             logging.error(f"Verification FAILED: Content NOT persisted for {card_name}")

                        # Create a history entry
                        create_knowledge_card_history_entry(cur, card_id, new_generated_sections, user_id)
                        logging.info(f"Successfully generated content for knowledge card: {card_name}")
                except Exception as e:
                    logging.error(f"Error processing knowledge card {card_name}: {e}", exc_info=True)
                    conn.rollback() # Rollback the transaction for the failed card


            conn.commit()
            logging.info("Content generation process finished.")
    except Exception as e:
        logging.critical("A critical error occurred in the main process.", exc_info=True)

        if conn:
            conn.rollback()
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()
        logging.info("Content generation process finished.")

if __name__ == "__main__":
    main()