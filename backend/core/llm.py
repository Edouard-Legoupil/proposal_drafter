#  Standard Library
import os

# Load environment variables from a .env file.
from dotenv import load_dotenv
load_dotenv()


# --- Azure OpenAI Configuration ---
#  Third-Party Libraries
from langchain_openai import AzureChatOpenAI

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

def get_embedder_config():
    """
    Returns the configuration for the Azure OpenAI embedder.
    """
    return {
        "provider": "azure",
        "config": {
            "model": os.getenv("AZURE_EMBEDDING_MODEL", "text-embedding-ada-002"),
            "deployment_id": os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-ada-002"),
            "api_key": os.getenv("AZURE_OPENAI_API_KEY_EMBED"),
            "api_base": os.getenv("AZURE_OPENAI_ENDPOINT_EMBED"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION_EMBED", "2023-05-15")
        }
    }


# # --- Google Gemini Configuration ---

# #  Third-Party Libraries
# from crewai import LLM

# # Set environment variables required by Gemini client.
# os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")

# # Validate that all required environment variables are set.
# required_vars = [
#     "GEMINI_API_KEY"
# ]
# missing_vars = [var for var in required_vars if not os.getenv(var)]
# if missing_vars:
#     raise ValueError(f"Missing required environment variables for LLM: {', '.join(missing_vars)}")

# # --- Language Model Initialization ---

# # Initialize Geminia language model.
# # This object will be used by the CrewAI agents to interact with the Azure OpenAI service.
# llm = LLM(
#      model="gemini/gemini-1.5-flash", # Or "gemini/#gemini-1.5-pro"
#      temperature=0.4,
#      api_key=os.getenv("GEMINI_API_KEY") # 
# )

# def get_embedder_config():
#     """
#     Returns the configuration for the Azure OpenAI embedder.
#     """
#     return {
#         "provider": "google",  
#         "config": {
#             # Use the Gemini #embedding model
#             "model": "models/embedding-001", 
#             # Optional: #Specify task type for optimized embeddings
#             "task_type": "retrieval_document", 
#             "api_key": os.getenv("GEMINI_API_KEY") 
#             # Ensure API #key is passed for embedding as well
#         }
#     }
