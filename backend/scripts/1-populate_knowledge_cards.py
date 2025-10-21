import argparse
import os
import sys
import uuid
import pandas as pd
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import register_uuid

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
register_uuid()

def main():
    parser = argparse.ArgumentParser(description="Populate the database with knowledge cards and references from an Excel file.")
    parser.add_argument("--excel-file", default='db/seed_data.xlsx', help="Path to the Excel file.")
    parser.add_argument("--user-id", required=True, help="The UUID of the user to associate with the created records.")
    parser.add_argument("--mode", choices=['update', 'reset'], default='update', help="Choose 'update' to add new data or 'reset' to delete all existing data before populating.")
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

            if args.mode == 'reset':
                print("Deleting all existing data from tables...")
                cur.execute("""
                    TRUNCATE TABLE
                        knowledge_card_to_references,
                        knowledge_card_references,
                        knowledge_cards,
                        outcomes,
                        donors,
                        field_contexts
                    RESTART IDENTITY CASCADE;
                """)
                print("All tables have been cleared.")

            # Read data from Excel file
            xls = pd.ExcelFile(args.excel_file)
            field_contexts_df = pd.read_excel(xls, 'field_contexts')
            donor_df = pd.read_excel(xls, 'donor')
            outcome_df = pd.read_excel(xls, 'outcome')
            reference_df = pd.read_excel(xls, 'reference')

            # Store generated UUIDs to link tables
            field_context_ids = {}
            donor_ids = {}
            outcome_ids = {}
            knowledge_card_ids = {}
            reference_ids = {}

            # Populate field_contexts
            for index, row in field_contexts_df.iterrows():
                fc_id = uuid.uuid4()
                field_context_ids[row['name']] = fc_id
                cur.execute("""
                    INSERT INTO field_contexts (id, name, geographic_coverage, category, created_by)
                    VALUES (%s, %s, %s, %s, %s) ON CONFLICT (name) DO NOTHING
                """, (fc_id, row['name'], row['geographic_coverage'], row['category'], user_id))
            print("Populated field_contexts table.")

            # Populate donors
            for index, row in donor_df.iterrows():
                donor_id = uuid.uuid4()
                donor_ids[row['name']] = donor_id
                cur.execute("""
                    INSERT INTO donors (id, name, account_id, country, donor_group, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (name) DO NOTHING
                """, (donor_id, row['name'], row['account_id'], row['country'], row['donor_group'], user_id))
            print("Populated donors table.")

            # Populate outcomes
            for index, row in outcome_df.iterrows():
                outcome_id = uuid.uuid4()
                outcome_ids[row['name']] = outcome_id
                cur.execute("""
                    INSERT INTO outcomes (id, name, created_by)
                    VALUES (%s, %s, %s) ON CONFLICT (name) DO NOTHING
                """, (outcome_id, row['name'], user_id))
            print("Populated outcomes table.")

            # Create knowledge cards
            for name, fc_id in field_context_ids.items():
                card_id = uuid.uuid4()
                knowledge_card_ids[('field_contexts', name)] = card_id
                cur.execute("""
                    INSERT INTO knowledge_cards (id, summary, field_context_id, template_name, created_by, updated_by)
                    VALUES (%s, 'v1', %s, %s, %s, %s)
                """, (card_id, fc_id, "knowledge_card_field_context_template.json", user_id, user_id))

            for name, donor_id in donor_ids.items():
                card_id = uuid.uuid4()
                knowledge_card_ids[('donor', name)] = card_id
                cur.execute("""
                    INSERT INTO knowledge_cards (id, summary, donor_id, template_name, created_by, updated_by)
                    VALUES (%s, 'v1', %s, %s, %s, %s)
                """, (card_id, donor_id, "knowledge_card_donor_template.json", user_id, user_id))

            for name, outcome_id in outcome_ids.items():
                card_id = uuid.uuid4()
                knowledge_card_ids[('outcome', name)] = card_id
                cur.execute("""
                    INSERT INTO knowledge_cards (id, summary, outcome_id, template_name, created_by, updated_by)
                    VALUES (%s, 'v1', %s, %s, %s, %s)
                """, (card_id, outcome_id, "knowledge_card_outcome_template.json", user_id, user_id))
            print("Populated knowledge_cards table.")

            # Deduplicate references by URL and populate knowledge_card_references
            unique_references_df = reference_df.drop_duplicates(subset=['url'])
            for index, row in unique_references_df.iterrows():
                ref_id = uuid.uuid4()
                reference_ids[row['url']] = ref_id
                cur.execute("""
                    INSERT INTO knowledge_card_references (id, url, reference_type, summary, created_by, updated_by)
                    VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (url) DO NOTHING
                """, (ref_id, row['url'], row['reference_type'], row['summary'], user_id, user_id))

            # Retrieve existing references from the DB to create a complete mapping
            cur.execute("SELECT id, url FROM knowledge_card_references")
            existing_references = cur.fetchall()
            for ref_id, url in existing_references:
                reference_ids[url] = ref_id
            print("Populated knowledge_card_references table.")

            # Link knowledge_cards and knowledge_card_references using the original reference_df
            for index, row in reference_df.iterrows():
                card_id = knowledge_card_ids.get((row['type'], row['name']))
                ref_id = reference_ids.get(row['url'])
                if card_id and ref_id:
                    cur.execute("""
                        INSERT INTO knowledge_card_to_references (knowledge_card_id, reference_id)
                        VALUES (%s, %s) ON CONFLICT DO NOTHING
                    """, (card_id, ref_id))
            print("Populated knowledge_card_to_references table.")

            conn.commit()
            print("Database populated successfully.")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
