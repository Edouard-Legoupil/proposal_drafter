#  Standard Library
import os

#  Third-Party Libraries
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv

# Load environment variables from a .env file.
load_dotenv()

# --- Azure OpenAI Configuration ---

# Set environment variables required by the Azure OpenAI client.
os.environ["AZURE_API_TYPE"] = "azure"
os.environ["AZURE_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT")
os.environ["AZURE_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["AZURE_API_VERSION"] = os.getenv("OPENAI_API_VERSION")
os.environ["AZURE_DEPLOYMENT_NAME"] = os.getenv("AZURE_DEPLOYMENT_NAME")

# Validate that all required environment variables are set.
required_vars = [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "OPENAI_API_VERSION",
    "AZURE_DEPLOYMENT_NAME"
]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables for LLM: {', '.join(missing_vars)}")

# --- Language Model Initialization ---

# Initialize the AzureChatOpenAI language model.
# This object will be used by the CrewAI agents to interact with the Azure OpenAI service.
llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_DEPLOYMENT_NAME"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("OPENAI_API_VERSION"),
    model=f"azure/{os.getenv('AZURE_DEPLOYMENT_NAME')}",
    max_retries=3,
    timeout=30
)
