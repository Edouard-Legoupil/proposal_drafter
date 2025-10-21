import argparse
import os
import sys
import uuid
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
    parser.add_argument("card_type", choices=['outcome', 'field_context', 'donor'], help="The type of knowledge card to find references for.")
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

            table_map = {
                'outcome': ('outcomes', 'outcome_id'),
                'field_context': ('field_contexts', 'field_context_id'),
                'donor': ('donors', 'donor_id')
            }
            table_name, column_name = table_map[args.card_type]

            cur.execute(f"SELECT id, name FROM {table_name}")
            items = cur.fetchall()

            for item_id, item_name in items:
                print(f"Finding references for {args.card_type}: {item_name}")

                reference_crew = ReferenceIdentificationCrew()
                crew_output = reference_crew.kickoff(link_type=args.card_type, topic=item_name)

                urls = re.findall(r'\[.*?\]\((https?://[^\s]+)\)', crew_output)

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

                    # Get knowledge_card_id
                    cur.execute(f"SELECT id FROM knowledge_cards WHERE {column_name} = %s", (item_id,))
                    card_id_result = cur.fetchone()
                    if not card_id_result:
                        continue
                    card_id = card_id_result[0]

                    # Link reference to knowledge card
                    cur.execute("""
                        INSERT INTO knowledge_card_to_references (knowledge_card_id, reference_id)
                        VALUES (%s, %s) ON CONFLICT DO NOTHING
                    """, (card_id, reference_id))

            conn.commit()
            print("References updated successfully.")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
