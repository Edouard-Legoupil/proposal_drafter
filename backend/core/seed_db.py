import logging
import uuid
from sqlalchemy import create_engine, insert, select, func
from backend.core.db import engine
from backend.core.init_db import outcomes, initialize_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTCOMES_DATA = [
    "OA1: Access to Territory, Reg. and Documentation",
    "OA2: Status Determination",
    "OA3: Protection Policy and Law",
    "OA4: Gender-based Violence",
    "OA5: Child Protection",
    "OA6: Safety and Access to Justice",
    "OA7: Community Engagement and Women's Empowerment",
    "OA8: Well-Being and Basic Needs",
    "OA9: Sustainable Housing and Settlements",
    "OA10: Healthy Lives",
    "OA11: Education",
    "OA12: Clean Water, Sanitation and Hygiene",
    "OA13: Self Reliance, Economic Inclusion and Livelihoods",
    "OA14: Voluntary Return and Sustainable Reintegration",
    "OA15: Resettlement and Complementary Pathways",
    "OA16: Integration and other Local Solutions",
    "EA17: Systems and Processes",
    "EA18: Operational Support and Supply Chain",
    "EA19: People and Culture",
    "EA20: External Engagement and Resource Mobilization",
    "EA21: Leadership and Governance",
]

def seed_database():
    # First, ensure the tables are created
    initialize_database()

    with engine.begin() as connection:
        logger.info("Seeding outcomes...")
        for outcome_name in OUTCOMES_DATA:
            # Check if the outcome already exists
            exists = connection.execute(
                select(outcomes).where(outcomes.c.name == outcome_name)
            ).first()

            if not exists:
                stmt = insert(outcomes).values(id=str(uuid.uuid4()), name=outcome_name)
                connection.execute(stmt)
                logger.info(f"  - Added outcome: {outcome_name}")
            else:
                logger.info(f"  - Outcome already exists: {outcome_name}")

        logger.info("Seeding complete.")

        # Verification step
        logger.info("Verifying seeded data...")
        count = connection.execute(select(func.count()).select_from(outcomes)).scalar()
        logger.info(f"Found {count} outcomes in the database.")
        if count >= len(OUTCOMES_DATA):
            logger.info("✅ Verification successful.")
        else:
            logger.error(f"❌ Verification failed. Expected at least {len(OUTCOMES_DATA)} outcomes, but found {count}.")


if __name__ == "__main__":
    seed_database()
