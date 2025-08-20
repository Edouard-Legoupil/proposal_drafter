import logging
import os
from sqlalchemy import create_engine, text

# Configure logging
logger = logging.getLogger(__name__)

# --- SQLite Database Configuration ---
DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DB_PATH = os.path.join(DB_DIR, 'proposal_drafter.db')

# Ensure the data directory exists
os.makedirs(DB_DIR, exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# --- Database Connection Test ---
try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        logger.info(f"✅ Database connection successful. Result: {result.scalar()}")
except Exception as e:
    logger.error(f"❌ Failed to connect to database: {e}")
    raise
