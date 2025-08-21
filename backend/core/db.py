#  Standard Library
import logging
import urllib.parse
import os

#  Third-Party Libraries
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from google.cloud.sql.connector import Connector
import pg8000.dbapi
import psycopg2

#  Internal Modules
from backend.core.config import on_gcp, db_host, db_name, db_username, db_password

# Configure logging
logger = logging.getLogger(__name__)

# --- Cloud SQL Connector Initialization ---
# The Connector instance is not fork-safe, so we must initialize it
# lazily in each worker process after Gunicorn forks.
connector = None


def get_connector() -> Connector:
    """Initializes and returns a Cloud SQL Connector instance."""
    global connector
    if connector is None:
        logger.info("Initializing Cloud SQL Connector for this process...")
        connector = Connector()
    return connector


# <-- Start with None, lazy-load later
engine = None 

def get_engine():
    """
    Lazily initializes and returns a SQLAlchemy engine.
    """
    global engine
    if engine is not None:
        return engine


    logger.info("Initializing new SQLAlchemy engine...")

    if os.getenv("TESTING"):
        from unittest.mock import MagicMock
        logger.info("TESTING mode: using MagicMock engine")
        engine = MagicMock()
        return engine

    if on_gcp:
        logger.info(f"Creating GCP SQLAlchemy engine for {db_host}")
        try:
            engine = create_engine(
                "postgresql+pg8000://",
                creator=lambda: get_connector().connect(
                    db_host,
                    "pg8000",
                    user=db_username,
                    password=db_password,
                    db=db_name,
                ),
                pool_pre_ping=True,
                pool_recycle=300,
            )
            logger.info("GCP engine created successfully")
        except Exception as e:
            logger.error(f"Failed to create GCP engine: {e}")
            raise
    else:
        encoded_password = urllib.parse.quote_plus(db_password) if db_password else ""
        connection_string = (
            f"postgresql+psycopg2://{db_username}:{encoded_password}@{db_host}:5432/{db_name}"
        )
        logger.info(f"Creating local SQLAlchemy engine for {db_host}")
        try:
            engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                pool_recycle=300,
            )
            logger.info("Local engine created successfully")
        except Exception as e:
            logger.error(f"Failed to create local engine: {e}")
            raise

    return engine

def test_connection():
    """
    Explicitly test database connectivity.
    """
    try:
        eng = get_engine()
        with eng.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(ext("SELECT NOW() as current_time, version() as db_version"))
            logger.info(f"✅ Database connection successful. Current time: {result.scalar()}")
            return True
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        return False

# def getconn():
#     """
#     Creates and returns a database connection.

#     This function dynamically chooses the connection method based on the
#     environment (GCP or local).
#     """
#     logger.info("Creating database connection...")

#     if on_gcp:
#         # Use the Cloud SQL Connector to connect to the database on GCP.
#         logger.debug(f"Connecting to Cloud SQL: {db_host}")
#         conn: pg8000.dbapi.Connection = get_connector().connect(
#             db_host,  # Instance connection name
#             "pg8000",
#             user=db_username,
#             password=db_password,
#             db=db_name,
#         )
#         return conn
#     else:
#         # Connect directly to a local PostgreSQL instance.
#         logger.debug(f"Connecting to local DB: {db_host}:5432")
#         return psycopg2.connect(
#             host=db_host,
#             port=5432,
#             user=db_username,
#             password=db_password,
#             database=db_name
#         )

# # --- SQLAlchemy Engine Creation ---
# # The engine is the central point for an application to communicate with the database.
# import os
# from unittest.mock import MagicMock

# if os.getenv("TESTING"):
#     engine = MagicMock()
# else:
#     if on_gcp:
#         # For GCP, the engine is created with a `creator` function (`getconn`).
#         engine = create_engine(
#             "postgresql+pg8000://",
#             creator=getconn,
#             pool_pre_ping=True,  # Check connection validity before use.
#             pool_recycle=300,   # Recycle connections after 300 seconds.
#         )
#     else:
#         # For local development, the engine is created using a standard connection string.
#         encoded_password = urllib.parse.quote_plus(db_password) if db_password else ""
#         connection_string = f"postgresql+psycopg2://{db_username}:{encoded_password}@{db_host}:5432/{db_name}"
#         logger.debug(f"Local connection string: {connection_string.split(':')[0]}...")
#         engine = create_engine(
#             connection_string,
#             pool_pre_ping=True,
#             pool_recycle=300
#         )

#     # --- Database Connection Test ---
#     # Verify that the database connection is successful upon application startup.
#     try:
#         with engine.connect() as connection:
#             result = connection.execute(text("SELECT NOW()"))
#             logger.info(f"✅ Database connection successful. Current time: {result.scalar()}")
#     except Exception as e:
#         logger.error(f"❌ Failed to connect to database: {e}")
#         # Re-raising the exception to prevent the application from starting
#         # with a faulty database connection.
#         raise


