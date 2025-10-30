# backend/scripts/populate_dummy_wizard_kb.py
import os
import sys
import uuid
import logging
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.db import get_engine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def populate_dummy_wizard_kb():
    """
    Populates the successful_proposals_insights table with a dummy dataset.
    """
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        logging.info("Populating successful_proposals_insights table with dummy data...")

        # Clear existing data
        session.execute(text("DELETE FROM successful_proposals_insights"))

        # Fetch some existing IDs from the database to use in the dummy data
        donor_ids = [row[0] for row in session.execute(text("SELECT id FROM donors LIMIT 3")).fetchall()]
        outcome_ids = [row[0] for row in session.execute(text("SELECT id FROM outcomes LIMIT 3")).fetchall()]
        field_context_ids = [row[0] for row in session.execute(text("SELECT id FROM field_contexts LIMIT 3")).fetchall()]

        dummy_insights = [
            {
                'id': uuid.uuid4(),
                'donor_id': donor_ids[0] if donor_ids else None,
                'outcome_id': outcome_ids[0] if outcome_ids else None,
                'field_context_id': field_context_ids[0] if field_context_ids else None,
                'budget_range': '100k$-250k$',
                'beneficiaries_profile': 'Refugees, Internally Displaced Persons',
                'success_likelihood': 0.8,
                'analysis_summary': 'Proposals with a focus on education for displaced children have a high success rate with this donor.',
                'suggested_donor_id': donor_ids[0] if donor_ids else None,
                'suggested_outcome_id': outcome_ids[0] if outcome_ids else None,
                'suggested_field_context_id': field_context_ids[0] if field_context_ids else None,
                'suggested_budget_range': '150k$-300k$',
                'suggested_prompt': 'A project to provide primary education to 1000 refugee children in the Dadaab refugee camp.',
                'key_themes': '["education", "children", "refugees"]',
                'common_keywords': '["school", "learning", "protection"]',
                'dos_and_donts': '["Do focus on measurable outcomes", "Do not exceed the budget"]'
            },
            {
                'id': uuid.uuid4(),
                'donor_id': donor_ids[1] if len(donor_ids) > 1 else None,
                'outcome_id': outcome_ids[1] if len(outcome_ids) > 1 else None,
                'field_context_id': field_context_ids[1] if len(field_context_ids) > 1 else None,
                'budget_range': '500k$-1M$',
                'beneficiaries_profile': 'Women and girls',
                'success_likelihood': 0.7,
                'analysis_summary': 'This donor favors projects that empower women through economic opportunities.',
                'suggested_donor_id': donor_ids[1] if len(donor_ids) > 1 else None,
                'suggested_outcome_id': outcome_ids[1] if len(outcome_ids) > 1 else None,
                'suggested_field_context_id': field_context_ids[1] if len(field_context_ids) > 1 else None,
                'suggested_budget_range': '750k$-1.2M$',
                'suggested_prompt': 'A vocational training program for 500 women in rural areas, focusing on entrepreneurship and financial literacy.',
                'key_themes': '["women empowerment", "economic development", "vocational training"]',
                'common_keywords': '["gender equality", "income generation", "skills development"]',
                'dos_and_donts': '["Do include a strong gender analysis", "Do not neglect monitoring and evaluation"]'
            }
        ]

        for insight in dummy_insights:
            if all(insight.get(k) is not None for k in ['donor_id', 'outcome_id', 'field_context_id']):
                insert_query = text("""
                    INSERT INTO successful_proposals_insights
                    (id, donor_id, outcome_id, field_context_id, budget_range, beneficiaries_profile, success_likelihood, analysis_summary, suggested_donor_id, suggested_outcome_id, suggested_field_context_id, suggested_budget_range, suggested_prompt, key_themes, common_keywords, dos_and_donts)
                    VALUES (:id, :donor_id, :outcome_id, :field_context_id, :budget_range, :beneficiaries_profile, :success_likelihood, :analysis_summary, :suggested_donor_id, :suggested_outcome_id, :suggested_field_context_id, :suggested_budget_range, :suggested_prompt, :key_themes, :common_keywords, :dos_and_donts)
                """)
                session.execute(insert_query, insight)

        session.commit()
        logging.info("Successfully populated the successful_proposals_insights table with dummy data.")

    except SQLAlchemyError as e:
        logging.error(f"Database error: {e}")
        session.rollback()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    populate_dummy_wizard_kb()
