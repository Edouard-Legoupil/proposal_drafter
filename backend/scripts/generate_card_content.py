import argparse
import asyncio
import json
import os
import sys
import uuid
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import register_uuid

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
register_uuid()

from backend.utils.crew_knowledge import ContentGenerationCrew
from backend.core.config import load_proposal_template

# Ensure the log directory exists
os.makedirs("log", exist_ok=True)

def create_knowledge_card_history_entry(cur, card_id, generated_sections, user_id):
    """
    Creates a history entry for a knowledge card.
    """
    cur.execute("""
        INSERT INTO knowledge_card_history (knowledge_card_id, generated_sections_snapshot, created_by, created_at)
        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
    """, (card_id, json.dumps(generated_sections), user_id))

def main():
    parser = argparse.ArgumentParser(description="Generate content for knowledge cards.")
    parser.add_argument("--force", action="store_true", help="Force regeneration of content for all knowledge cards.")
    parser.add_argument("--user-id", required=True, help="The UUID of the user to associate with the created records.")
    args = parser.parse_args()

    # Load environment variables from .env file
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

    # Database connection
    db_username = os.getenv("DB_USERNAME").strip('"')
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    db_host = "localhost"
    db_port = "5432"

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

            # Get all knowledge cards
            cur.execute("""
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
            """)
            knowledge_cards = cur.fetchall()

            for card in knowledge_cards:
                card_id, template_name, generated_sections, card_updated_at, donor_name, outcome_name, field_context_name = card
                should_generate = False

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
                    print(f"Generating content for knowledge card {card_id}...")
                    template = load_proposal_template(template_name)
                    name = donor_name or outcome_name or field_context_name
                    pre_prompt = f"{template.get('description', '')} for {name}."
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

                    # Create a history entry
                    create_knowledge_card_history_entry(cur, card_id, new_generated_sections, user_id)
                    print(f"Successfully generated content for knowledge card {card_id}")

            conn.commit()
            print("Content generation process finished.")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()