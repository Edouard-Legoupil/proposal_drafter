#  Standard Library
import os
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

# --- Application Configuration ---

# Secret key for JWT encoding and decoding.
# It's crucial to set this in the environment for production.
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_dev_secret")

# --- Database Configuration ---

# Load database credentials and settings from environment variables.
db_username = os.getenv('DB_USERNAME')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME')

# Flag to enable/disable Google Cloud IAM database authentication.
enable_iam_auth = os.getenv('ENABLE_IAM_AUTH', 'true').lower() == 'true'

# Log the loaded database configuration for debugging purposes.
# Note: Be cautious about logging sensitive information in production.
logger.info(f"DEBUG: enable_iam_auth: {enable_iam_auth}")
logger.info(f"GAE_ENV: {os.getenv('GAE_ENV')}")
logger.info(f"K_SERVICE: {os.getenv('K_SERVICE')}")
logger.info(f"DEBUG: db_username from env: {db_username}")
logger.info(f"DEBUG: db_password (first 3 chars): {db_password[:3] if db_password else 'None'}")
logger.info(f"DEBUG: db_host from env: {db_host}")

# --- Critical Environment Variable Checks ---
# Ensure that essential database configuration is present.
if not db_username:
    logger.error("db_username environment variable is missing or empty.")
    raise ValueError("db_username environment variable is missing or empty.")
if not db_password:
    logger.error("db_password environment variable is missing or empty. Cannot authenticate with database.")
    raise ValueError("db_password environment variable is missing or empty.")
if not db_host:
    logger.error("db_host environment variable is missing. Cannot connect to database.")
    raise ValueError("db_host environment variable is missing.")
if not db_name:
    logger.error("db_name environment variable is missing. Cannot select database.")
    raise ValueError("db_name environment variable is missing.")
if not db_password and not enable_iam_auth:
    logger.warning("DB_PASSWORD is missing but ENABLE_IAM_AUTH is false. Connection may fail without credentials.")

# --- Environment Detection ---

# Determine if the application is running in a Google Cloud Platform environment.
# This is used to decide whether to use the Cloud SQL Connector.
on_gcp = os.getenv('DB_HOST') != 'localhost'
logger.info(f"Running on GCP: {on_gcp}")


# --- CORS Configuration ---

# List of allowed origins for Cross-Origin Resource Sharing (CORS).
# This controls which frontend URLs can make requests to the API.
origins = [
    #"https://edouard-legoupil.github.io", # Client in github page
    "http://localhost:8503",               # Client for local dev
    "https://proposalgenerator-290826171799.europe-west1.run.app/" ## GCP deployment
]


# --- Proposal Configuration ---

# Construct an absolute path to the configuration file.
# This makes the path robust, regardless of the current working directory.
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BACKEND_DIR, "templates/unhcr_cerf_proposal_template.json")


# List of section names, defining the structure of a proposal.
SECTIONS = [
    "Summary", "Rationale", "Project Description", "Partnerships and Coordination",
    "Monitoring", "Evaluation", "Results Matrix", "Work Plan", "Budget",
    "Annex 1. Risk Assessment Plan"
]

# Load the proposal template data from the JSON file.
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        proposal_data = json.load(file)
except FileNotFoundError:
    logger.error(f"Proposal template file not found at: {CONFIG_PATH}")
    proposal_data = {"sections": []}
except json.JSONDecodeError:
    logger.error(f"Error decoding JSON from proposal template file: {CONFIG_PATH}")
    proposal_data = {"sections": []}
