
#  Standard Library
import logging
import urllib.parse
import os

#  Third-Party Libraries
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import pg8000.dbapi
import psycopg2

#  Internal Modules
from backend.core.config import db_host, db_name, db_username, db_password

# Configure logging
logger = logging.getLogger(__name__)

# --- Additional Config ---
cloud_provider = os.getenv("CLOUD_PROVIDER", "local").lower()  # gcp | azure | local

# <--- Start with None, lazy-load later
engine = None


def get_engine():
    """
    Lazily initializes and returns a SQLAlchemy engine.
    """
    global engine
    if engine is not None:
        return engine

    logger.info(f"Initializing SQLAlchemy engine... cloud_provider={cloud_provider}")

    if os.getenv("TESTING"):
        from unittest.mock import MagicMock
        logger.info("TESTING mode: using MagicMock engine")
        engine = MagicMock()
        return engine

    try:
        if cloud_provider == "gcp":
            # --- Cloud SQL Connector Initialization ---
            connector = None

            def get_connector() -> "Connector":
                """Initializes and returns a Cloud SQL Connector instance."""
                global connector
                if connector is None:
                    from google.cloud.sql.connector import Connector
                    connector = Connector()
                return connector

            logger.info(f"Creating GCP SQLAlchemy engine for {db_host}, db: {db_name}, user: {db_username}")
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

            # Test the connection immediately
            with engine.connect() as test_conn:
                result = test_conn.execute(text("SELECT CURRENT_TIMESTAMP"))
                logger.info(f"✅ GCP Database connection test passed: {result.scalar()}")

        elif cloud_provider == "azure":
            encoded_password = urllib.parse.quote_plus(db_password) if db_password else ""
            connection_string = (
                f"postgresql+psycopg2://{db_username}:{encoded_password}@{db_host}:5432/{db_name}?sslmode=require"
            )
            logger.info(f"Creating Azure engine for {db_host}")
            engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                pool_recycle=300,
            )
            logger.info("Azure engine created successfully")

            # Test the connection immediately
            with engine.connect() as test_conn:
                result = test_conn.execute(text("SELECT CURRENT_TIMESTAMP"))
                logger.info(f"✅ Azure Database connection test passed: {result.scalar()}")

        else:  # local or default
            logger.info(f"Creating local engine for {db_host}")
            encoded_password = urllib.parse.quote_plus(db_password) if db_password else ""
            connection_string = (
                f"postgresql+psycopg2://{db_username}:{encoded_password}@{db_host}:5432/{db_name}"
            )
            engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                pool_recycle=300,
            )

            # Test the connection immediately
            with engine.connect() as test_conn:
                result = test_conn.execute(text("SELECT CURRENT_TIMESTAMP"))
                logger.info(f"✅ Local Database connection test passed: {result.scalar()}")

    except Exception as e:
        logger.error(f"Failed to create engine for {cloud_provider}: {e}", exc_info=True)
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
            result = conn.execute(text("SELECT CURRENT_TIMESTAMP as current_time, version() as db_version"))
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

