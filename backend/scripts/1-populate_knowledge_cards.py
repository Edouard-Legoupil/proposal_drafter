"""
Script: 1-populate_knowledge_cards.py
Description: Populates the database with knowledge cards, field contexts, donors, outcomes, and references from an Excel file.

Modes:
    - update (default): Adds new records and updates existing ones based on unique names/URLs.
      It fetches existing IDs to ensure foreign key integrity and updates fields like 'updated_at' and 'updated_by'.
    - reset: DELETES ALL EXISTING DATA in the target tables before populating from scratch.
      It creates a backup of the existing data to 'db/seed_data_backup.xlsx' before truncation.

Usage:
    python backend/scripts/1-populate_knowledge_cards.py --user-id <UUID> [--mode update|reset] [--excel-file path/to/file.xlsx]
"""

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

def reset_database(cur):
    """
    Backs up existing data and truncates tables.
    """
    print("Backing up existing data...")

    # Fetch data from tables
    cur.execute("SELECT name, geographic_coverage, category FROM field_contexts")
    field_contexts_backup_df = pd.DataFrame(cur.fetchall(), columns=['name', 'geographic_coverage', 'category'])

    cur.execute("SELECT name, account_id, country, donor_group FROM donors")
    donors_backup_df = pd.DataFrame(cur.fetchall(), columns=['name', 'account_id', 'country', 'donor_group'])

    cur.execute("SELECT name FROM outcomes")
    outcomes_backup_df = pd.DataFrame(cur.fetchall(), columns=['name'])

    cur.execute("""
        SELECT
            CASE
                WHEN kc.donor_id IS NOT NULL THEN 'donor'
                WHEN kc.outcome_id IS NOT NULL THEN 'outcome'
                WHEN kc.field_context_id IS NOT NULL THEN 'field_context'
            END as type,
            COALESCE(d.name, o.name, fc.name) as name,
            kcr.url,
            kcr.reference_type,
            kcr.summary
        FROM knowledge_card_to_references kctr
        JOIN knowledge_cards kc ON kctr.knowledge_card_id = kc.id
        JOIN knowledge_card_references kcr ON kctr.reference_id = kcr.id
        LEFT JOIN donors d ON kc.donor_id = d.id
        LEFT JOIN outcomes o ON kc.outcome_id = o.id
        LEFT JOIN field_contexts fc ON kc.field_context_id = fc.id
    """)
    references_backup_df = pd.DataFrame(cur.fetchall(), columns=['type', 'name', 'url', 'reference_type', 'summary'])

    # Save to Excel
    backup_path = 'db/seed_data_backup.xlsx'
    # Ensure db directory exists
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    
    with pd.ExcelWriter(backup_path) as writer:
        field_contexts_backup_df.to_excel(writer, sheet_name='field_contexts', index=False)
        donors_backup_df.to_excel(writer, sheet_name='donor', index=False)
        outcomes_backup_df.to_excel(writer, sheet_name='outcome', index=False)
        references_backup_df.to_excel(writer, sheet_name='reference', index=False)

    print(f"Backup created at {backup_path}")

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

def populate_database(cur, user_id, excel_file):
    """
    Populates the database from the Excel file using upsert logic.
    """
    print(f"Populating database from {excel_file}...")
    
    # Read data from Excel file
    xls = pd.ExcelFile(excel_file)
    
    def clean_df(df, subset_col=None):
        # Replace NaN with None
        df = df.where(pd.notnull, None)
        # Drop rows where the subset column is None (if specified)
        if subset_col:
            df = df.dropna(subset=[subset_col])
        # Strip whitespace from string columns
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        # Drop duplicates if subset_col is provided
        if subset_col:
            df = df.drop_duplicates(subset=[subset_col])
        return df

    field_contexts_df = clean_df(pd.read_excel(xls, 'field_contexts'), 'name')
    donor_df = clean_df(pd.read_excel(xls, 'donor'), 'name')
    outcome_df = clean_df(pd.read_excel(xls, 'outcome'), 'name')
    reference_df = clean_df(pd.read_excel(xls, 'reference'), 'url')

    # Store generated UUIDs to link tables
    field_context_ids = {}
    donor_ids = {}
    outcome_ids = {}
    knowledge_card_ids = {}
    reference_ids = {}

    # --- Populate field_contexts ---
    print("Processing field_contexts...")
    for index, row in field_contexts_df.iterrows():
        # Generate a new ID to use if inserting, but we might ignore it if updating
        new_id = uuid.uuid4()
        cur.execute("""
            INSERT INTO field_contexts (id, name, geographic_coverage, category, created_by)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE 
            SET geographic_coverage = EXCLUDED.geographic_coverage,
                category = EXCLUDED.category,
                last_updated = NOW()
            RETURNING id
        """, (new_id, row['name'], row['geographic_coverage'], row['category'], user_id))
        fc_id = cur.fetchone()[0]
        field_context_ids[row['name']] = fc_id
    print("Populated field_contexts table.")

    # --- Populate donors ---
    print("Processing donors...")
    for index, row in donor_df.iterrows():
        new_id = uuid.uuid4()
        cur.execute("""
            INSERT INTO donors (id, name, account_id, country, donor_group, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_id) DO UPDATE
            SET name = EXCLUDED.name,
                country = EXCLUDED.country,
                donor_group = EXCLUDED.donor_group,
                last_updated = NOW()
            RETURNING id
        """, (new_id, row['name'], row['account_id'], row['country'], row['donor_group'], user_id))
        donor_id = cur.fetchone()[0]
        donor_ids[row['name']] = donor_id
    print("Populated donors table.")

    # --- Populate outcomes ---
    print("Processing outcomes...")
    for index, row in outcome_df.iterrows():
        new_id = uuid.uuid4()
        cur.execute("""
            INSERT INTO outcomes (id, name, created_by)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO UPDATE
            SET last_updated = NOW()
            RETURNING id
        """, (new_id, row['name'], user_id))
        outcome_id = cur.fetchone()[0]
        outcome_ids[row['name']] = outcome_id
    print("Populated outcomes table.")

    # --- Create knowledge cards ---
    print("Processing knowledge_cards...")
    
    def upsert_knowledge_card(entity_type, entity_name, entity_id, template_name):
        # Check if card exists for this entity
        col_name = f"{entity_type}_id" # e.g. field_context_id
        
        # For knowledge cards, we don't have a unique constraint on the entity_id alone in the schema usually?
        # Let's check the schema. Assuming one card per entity for now based on previous logic.
        # But we can't use ON CONFLICT if there isn't a unique constraint.
        # So we stick to SELECT -> UPDATE/INSERT for this one, but we use the ID we just got.
        
        cur.execute(f"SELECT id FROM knowledge_cards WHERE {col_name} = %s", (entity_id,))
        res = cur.fetchone()
        
        if res:
            card_id = res[0]
            cur.execute("""
                UPDATE knowledge_cards 
                SET template_name = %s, updated_by = %s, updated_at = NOW()
                WHERE id = %s
            """, (template_name, user_id, card_id))
        else:
            card_id = uuid.uuid4()
            cur.execute(f"""
                INSERT INTO knowledge_cards (id, summary, {col_name}, template_name, created_by, updated_by)
                VALUES (%s, 'v1', %s, %s, %s, %s)
            """, (card_id, entity_id, template_name, user_id, user_id))
        
        knowledge_card_ids[(entity_type if entity_type != 'field_context' else 'field_contexts', entity_name)] = card_id

    for name, fc_id in field_context_ids.items():
        upsert_knowledge_card('field_context', name, fc_id, "knowledge_card_field_context_template.json")

    for name, donor_id in donor_ids.items():
        upsert_knowledge_card('donor', name, donor_id, "knowledge_card_donor_template.json")

    for name, outcome_id in outcome_ids.items():
        upsert_knowledge_card('outcome', name, outcome_id, "knowledge_card_outcome_template.json")
    
    print("Populated knowledge_cards table.")

    # --- Deduplicate references by URL and populate knowledge_card_references ---
    print("Processing references...")
    # reference_df is already deduplicated by clean_df
    for index, row in reference_df.iterrows():
        new_id = uuid.uuid4()
        cur.execute("""
            INSERT INTO knowledge_card_references (id, url, reference_type, summary, created_by, updated_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE
            SET reference_type = EXCLUDED.reference_type,
                summary = EXCLUDED.summary,
                updated_by = %s,
                updated_at = NOW()
            RETURNING id
        """, (new_id, row['url'], row['reference_type'], row['summary'], user_id, user_id, user_id))
        ref_id = cur.fetchone()[0]
        reference_ids[row['url']] = ref_id

    print("Populated knowledge_card_references table.")

    # --- Link knowledge_cards and knowledge_card_references ---
    print("Linking cards and references...")
    for index, row in reference_df.iterrows():
        # Map excel type to our key format
        key_type = row['type']
        if key_type == 'field_context':
            key_type = 'field_contexts'
        
        card_id = knowledge_card_ids.get((key_type, row['name']))
        ref_id = reference_ids.get(row['url'])
        
        if card_id and ref_id:
            cur.execute("""
                INSERT INTO knowledge_card_to_references (knowledge_card_id, reference_id)
                VALUES (%s, %s) ON CONFLICT DO NOTHING
            """, (card_id, ref_id))
    print("Populated knowledge_card_to_references table.")

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
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")

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
                reset_database(cur)
                # After reset, we populate fresh
                populate_database(cur, user_id, args.excel_file)
            elif args.mode == 'update':
                populate_database(cur, user_id, args.excel_file)

            conn.commit()
            print("Database operation completed successfully.")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
