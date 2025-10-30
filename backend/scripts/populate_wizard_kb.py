# backend/scripts/populate_wizard_kb.py
import os
import sys
import json
import uuid
import logging
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.db import get_engine
from backend.utils.crew_wizzard import InsightExtractionCrew

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def populate_wizard_kb():
    """
    Populates the successful_proposals_insights table by analyzing approved proposals.
    """
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        logging.info("Fetching successful proposals...")
        proposals_query = text("""
            SELECT id, form_data, generated_sections, donor_id, outcome_id, field_context_id
            FROM proposals
            WHERE status = 'approved' OR is_accepted = TRUE
        """)
        successful_proposals = session.execute(proposals_query).fetchall()

        if not successful_proposals:
            logging.info("No successful proposals found to analyze.")
            return

        logging.info(f"Found {len(successful_proposals)} successful proposals to analyze.")
        crew = InsightExtractionCrew().create_crew()

        for proposal in successful_proposals:
            proposal_id, form_data, generated_sections, donor_id, outcome_id, field_context_id = proposal

            if not generated_sections:
                logging.warning(f"Skipping proposal {proposal_id} due to empty generated_sections.")
                continue

            # Combine all sections into a single text for analysis
            full_text = " ".join(generated_sections.values())

            logging.info(f"Analyzing proposal {proposal_id}...")
            # Kick off the crew with the full proposal text
            result = crew.kickoff(inputs={'proposal_text': full_text})

            # The result from the crew should be a JSON string, but let's be safe
            try:
                insights = json.loads(result) if isinstance(result, str) else result
            except (json.JSONDecodeError, TypeError):
                 logging.error(f"Failed to parse insights for proposal {proposal_id}. Result: {result}")
                 continue

            budget_range = form_data.get('Budget Range', 'N/A')

            insight_id = uuid.uuid4()
            insert_query = text("""
                INSERT INTO successful_proposals_insights
                (id, donor_id, outcome_id, field_context_id, budget_range, success_rate, key_themes, common_keywords, dos_and_donts)
                VALUES (:id, :donor_id, :outcome_id, :field_context_id, :budget_range, :success_rate, :key_themes, :common_keywords, :dos_and_donts)
            """)

            session.execute(insert_query, {
                'id': insight_id,
                'donor_id': donor_id,
                'outcome_id': outcome_id,
                'field_context_id': field_context_id,
                'budget_range': budget_range,
                'success_rate': 0.0,
                'key_themes': json.dumps(insights.get('key_themes')),
                'common_keywords': json.dumps(insights.get('common_keywords')),
                'dos_and_donts': json.dumps(insights.get('dos_and_donts'))
            })

        session.commit()
        logging.info("Successfully populated the successful_proposals_insights table.")

    except SQLAlchemyError as e:
        logging.error(f"Database error: {e}")
        session.rollback()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    populate_wizard_kb()
