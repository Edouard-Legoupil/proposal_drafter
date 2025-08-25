#  Standard Library
import os
import sys
import importlib
import json
import logging

from fastapi import HTTPException

# Configure logging
logger = logging.getLogger(__name__)

# --- Install Configuration ---

# Print Python version
logger.info("Python Version:")
logger.info(sys.version)
logger.info("-----")

# Print Python Install Directory
logger.info("Python Install Directory:")
logger.info(sys.prefix)
logger.info("-----")

# Print the PATH environment variable
logger.info("PATH Environment Variable:")
logger.info(os.getenv("PATH"))
logger.info("-----")

# Print PYTHONPATH if it's set
logger.info("PYTHONPATH Environment Variable:")
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    logger.info(pythonpath)
else:
    logger.info("Not Set")
logger.info("-----")

# Print PYTHONHOME if it's set
logger.info("PYTHONHOME Environment Variable:")
pythonhome = os.getenv("PYTHONHOME")
if pythonhome:
    logger.info(pythonhome)
else:
    logger.info("Not Set")
logger.info("-----")

# Attempt to import the 'openai' module and print its version and file location
try:
    # Importing the openai module
    import openai
    
    # Print openai module version if available
    logger.info("OpenAI Module Version:")
    if hasattr(openai, '__version__'):
        logger.info(openai.__version__)
    else:
        logger.info("Version not specified")
    logger.info("-----")

    # Print location of the openai module
    logger.info("OpenAI Module Location:")
    logger.info(importlib.util.find_spec("openai").origin)
    logger.info("-----")

except ImportError:
    logger.info("OpenAI module is not installed")
    logger.info("-----")



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
# This is used to decide whether to use the Cloud SQL Connector that leverage the Cloud SQL socket .
on_gcp = os.getenv('DB_HOST') != 'localhost'
#logger.info(f"Running on GCP: {on_gcp}")


# --- CORS Configuration ---

# List of allowed origins for Cross-Origin Resource Sharing (CORS).
# This controls which frontend URLs can make requests to the API.
origins = [
    #"https://edouard-legoupil.github.io", # Client in github page
    "http://localhost:8503",      
    "http://localhost:8503",          # Client for local dev 
    "https://localhost:8080",               
    "https://proposalgen-290826171799.europe-west9.run.app/" ## GCP deployment
]


# --- Proposal Configuration ---

# Construct a robust path to the templates directory.
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BACKEND_DIR, "templates")

def get_available_templates():
    """
    Scans the templates directory and returns a list of available .json template files.
    """
    if not os.path.isdir(TEMPLATES_DIR):
        logger.error(f"Templates directory not found at: {TEMPLATES_DIR}")
        return []

    return [f for f in os.listdir(TEMPLATES_DIR) if f.endswith('.json') and os.path.isfile(os.path.join(TEMPLATES_DIR, f))]

def load_proposal_template(template_name: str):
    """
    Loads a specific proposal template by its filename.
    """
    # Validate that the template name is in the list of available templates to prevent
    # directory traversal attacks.
    if template_name not in get_available_templates():
        logger.error(f"Invalid or non-existent template requested: {template_name}")
        raise HTTPException(status_code=400, detail=f"Template '{template_name}' not found.")

    template_path = os.path.join(TEMPLATES_DIR, template_name)

    try:
        with open(template_path, "r", encoding="utf-8") as file:
            proposal_data = json.load(file)
            logger.info(f"Proposal template loaded successfully from {template_path}")
            return proposal_data
    except FileNotFoundError:
        logger.error(f"Proposal template file not found at: {template_path}")
        raise HTTPException(status_code=404, detail="Proposal template file not found.")
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from proposal template file: {template_path}")
        raise HTTPException(status_code=500, detail="Error parsing proposal template file.")

# Load the default template to extract section names for backward compatibility
# in some parts of the app that might still rely on a global SECTIONS list.
try:
    DEFAULT_TEMPLATE_NAME = "unhcr_cerf_proposal_template.json"
    if DEFAULT_TEMPLATE_NAME in get_available_templates():
        default_proposal_data = load_proposal_template(DEFAULT_TEMPLATE_NAME)
        SECTIONS = [section.get("section_name") for section in default_proposal_data.get("sections", [])]
    else:
        SECTIONS = []
        logger.warning("Default proposal template not found. SECTIONS list will be empty.")
except Exception as e:
    SECTIONS = []
    logger.error(f"Failed to load default template for SECTIONS: {e}")


if not SECTIONS:
    logger.error("No sections were loaded from the default proposal template JSON.")

 