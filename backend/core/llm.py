#  Standard Library
import atexit
import os
from threading import Lock
from typing import Any

# Load environment variables from a .env file.
from dotenv import load_dotenv

# Third-Party Libraries
from crewai.llms.providers.azure.completion import AzureCompletion
from openai import AzureOpenAI

load_dotenv()


# --- Azure OpenAI Configuration ---
# Third-Party Libraries

# Note: We now use CrewAI's native Azure LLM support instead of LangChain

DEFAULT_EMBEDDING_MODEL = "text-embedding-ada-002"
DEFAULT_EMBEDDING_API_VERSION = "2023-05-15"
_embedding_client: AzureOpenAI | None = None
_embedding_client_lock = Lock()


class AzureOpenAICompletion(AzureCompletion):
    """Native Azure OpenAI completion that supports aliased deployments."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # AzureCompletion otherwise infers this from the deployment alias prefix.
        self.is_openai_model = True


# Validate that all required environment variables are set.
required_vars = [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "OPENAI_API_VERSION",
    "AZURE_DEPLOYMENT_NAME",
]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables for LLM: {', '.join(missing_vars)}")

# --- Language Model Initialization ---

# Initialize the CrewAI LLM for Azure OpenAI
# This object will be used by the CrewAI agents to interact with the Azure OpenAI service.

llm = AzureOpenAICompletion(
    model=os.getenv("AZURE_DEPLOYMENT_NAME"),
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("OPENAI_API_VERSION"),
    timeout=30,
)


def _get_embedding_settings() -> dict[str, str]:
    required_vars = (
        "AZURE_OPENAI_ENDPOINT_EMBED",
        "AZURE_OPENAI_API_KEY_EMBED",
    )
    missing_vars = [name for name in required_vars if not os.getenv(name)]
    if missing_vars:
        raise ValueError("Missing required environment variables for embeddings: " + ", ".join(missing_vars))

    return {
        "endpoint": os.environ["AZURE_OPENAI_ENDPOINT_EMBED"],
        "api_key": os.environ["AZURE_OPENAI_API_KEY_EMBED"],
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION_EMBED", DEFAULT_EMBEDDING_API_VERSION),
        "model": os.getenv("AZURE_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        "deployment": os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME", DEFAULT_EMBEDDING_MODEL),
    }


def _get_embedding_client() -> AzureOpenAI:
    """Return the process-wide synchronous client used by embedding workers."""
    global _embedding_client

    with _embedding_client_lock:
        if _embedding_client is None:
            settings = _get_embedding_settings()
            _embedding_client = AzureOpenAI(
                azure_endpoint=settings["endpoint"],
                api_key=settings["api_key"],
                api_version=settings["api_version"],
                timeout=30,
                max_retries=3,
            )
        return _embedding_client


def reset_embedding_client() -> None:
    """Close and clear the retained embedding client, if one exists."""
    global _embedding_client

    with _embedding_client_lock:
        client = _embedding_client
        _embedding_client = None

    if client is not None:
        client.close()


atexit.register(reset_embedding_client)


def create_embedding(content: str) -> list[float]:
    """Create an embedding through the official Azure OpenAI client."""
    settings = _get_embedding_settings()
    response = _get_embedding_client().embeddings.create(
        model=settings["deployment"],
        input=[content],
    )
    return response.data[0].embedding


def get_embedder_config():
    """
    Returns the configuration for the Azure OpenAI embedder.
    """
    settings = _get_embedding_settings()
    return {
        "provider": "azure",
        "config": {
            "model": settings["model"],
            "deployment_id": settings["deployment"],
            "api_key": settings["api_key"],
            "api_base": settings["endpoint"],
            "api_version": settings["api_version"],
        },
    }


# --- Google Gemini Configuration ---

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
#      model='gemini/gemini-2.5-pro', # Or "gemini/#gemini-2.5-flash"
#      temperature=0.0,
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
