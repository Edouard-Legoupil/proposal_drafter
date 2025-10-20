import argparse
import csv
import json
import os
import sys
import uuid
from collections import defaultdict
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import register_uuid

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
register_uuid()

def add_reference(cur, card_id, url, reference_type, summary, user_id):
    """Add a reference if it doesn't exist and link it to the knowledge card."""
    # Check if reference exists
    cur.execute("SELECT id FROM knowledge_card_references WHERE url = %s", (url,))
    result = cur.fetchone()
    if result:
        ref_id = result[0]
    else:
        cur.execute("""
            INSERT INTO knowledge_card_references (url, reference_type, summary, created_by, updated_by)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (url, reference_type, summary, user_id, user_id))
        ref_id = cur.fetchone()[0]

    # Link to knowledge card
    cur.execute("""
        INSERT INTO knowledge_card_to_references (knowledge_card_id, reference_id)
        VALUES (%s, %s) ON CONFLICT DO NOTHING
    """, (card_id, ref_id))

def process_donors(cur, user_id, donors_file):
    """Process the donors CSV and create knowledge cards with references."""
    donors_refs = defaultdict(list)
    with open(donors_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['name']
            donors_refs[name].append({
                'account_id': row['account_id'],
                'country': row['country'],
                'donor_group': row['donor_group'],
                'url': row['url'],
                'reference_type': row['reference_type'],
                'summary': row['summary']
            })

    for name, refs in donors_refs.items():
        # Assume donor info is consistent across rows; take first
        donor_info = refs[0]
        # Check if donor exists
        cur.execute("SELECT id FROM donors WHERE name = %s", (name,))
        result = cur.fetchone()
        if result:
            donor_id = result[0]
        else:
            cur.execute("""
                INSERT INTO donors (account_id, name, country, donor_group, created_by)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, (donor_info['account_id'], name, donor_info['country'], donor_info['donor_group'], user_id))
            donor_id = cur.fetchone()[0]

        # Create knowledge card
        summary = f"Default knowledge card for donor {name}"
        generated_sections = json.dumps({})
        cur.execute("""
            INSERT INTO knowledge_cards (template_name, summary, generated_sections, donor_id, created_by, updated_by)
            VALUES (NULL, %s, %s, %s, %s, %s) RETURNING id
        """, (summary, generated_sections, donor_id, user_id, user_id))
        card_id = cur.fetchone()[0]

        # Add references
        for ref in refs:
            add_reference(cur, card_id, ref['url'], ref['reference_type'], ref['summary'], user_id)

def process_outcomes(cur, user_id, outcomes_file):
    """Process the outcomes CSV and create knowledge cards with references."""
    outcomes_refs = defaultdict(list)
    with open(outcomes_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['name']
            outcomes_refs[name].append({
                'url': row['url'],
                'reference_type': row['reference_type'],
                'summary': row['summary']
            })

    for name, refs in outcomes_refs.items():
        # Check if outcome exists
        cur.execute("SELECT id FROM outcomes WHERE name = %s", (name,))
        result = cur.fetchone()
        if result:
            outcome_id = result[0]
        else:
            cur.execute("""
                INSERT INTO outcomes (name, created_by)
                VALUES (%s, %s) RETURNING id
            """, (name, user_id))
            outcome_id = cur.fetchone()[0]

        # Create knowledge card
        summary = f"Default knowledge card for outcome {name}"
        generated_sections = json.dumps({})
        cur.execute("""
            INSERT INTO knowledge_cards (template_name, summary, generated_sections, outcome_id, created_by, updated_by)
            VALUES (NULL, %s, %s, %s, %s, %s) RETURNING id
        """, (summary, generated_sections, outcome_id, user_id, user_id))
        card_id = cur.fetchone()[0]

        # Add references
        for ref in refs:
            add_reference(cur, card_id, ref['url'], ref['reference_type'], ref['summary'], user_id)

def process_field_contexts(cur, user_id, field_contexts_file):
    """Process the field contexts CSV and create knowledge cards with references."""
    field_contexts_refs = defaultdict(list)
    with open(field_contexts_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['name']
            field_contexts_refs[name].append({
                'title': row['title'],
                'category': row['category'],
                'geographic_coverage': row['geographic_coverage'] if row['geographic_coverage'] else None,
                'url': row['url'],
                'reference_type': row['reference_type'],
                'summary': row['summary']
            })

    for name, refs in field_contexts_refs.items():
        # Assume field context info is consistent across rows; take first
        fc_info = refs[0]
        # Check if field context exists
        cur.execute("SELECT id FROM field_contexts WHERE name = %s", (name,))
        result = cur.fetchone()
        if result:
            fc_id = result[0]
        else:
            cur.execute("""
                INSERT INTO field_contexts (title, name, category, geographic_coverage, created_by)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, (fc_info['title'], name, fc_info['category'], fc_info['geographic_coverage'], user_id))
            fc_id = cur.fetchone()[0]

        # Create knowledge card
        summary = f"Default knowledge card for field context {name}"
        generated_sections = json.dumps({})
        cur.execute("""
            INSERT INTO knowledge_cards (template_name, summary, generated_sections, field_context_id, created_by, updated_by)
            VALUES (NULL, %s, %s, %s, %s, %s) RETURNING id
        """, (summary, generated_sections, fc_id, user_id, user_id))
        card_id = cur.fetchone()[0]

        # Add references
        for ref in refs:
            add_reference(cur, card_id, ref['url'], ref['reference_type'], ref['summary'], user_id)

def main():
    parser = argparse.ArgumentParser(description="Populate the database with knowledge cards and references from CSV files.")
    parser.add_argument("--donors-file", required=True, help="Path to the donors CSV file.")
    parser.add_argument("--outcomes-file", required=True, help="Path to the outcomes CSV file.")
    parser.add_argument("--field-contexts-file", required=True, help="Path to the field contexts CSV file.")
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
            process_donors(cur, user_id, args.donors_file)
            process_outcomes(cur, user_id, args.outcomes_file)
            process_field_contexts(cur, user_id, args.field_contexts_file)
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