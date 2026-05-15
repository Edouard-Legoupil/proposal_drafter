# Standard Library
import os
import logging
from typing import Optional, Dict, Any

# Third-Party Libraries
from google.cloud import secretmanager
from google.api_core.exceptions import GoogleAPICallError, NotFound

try:
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient
except ImportError:
    # Azure Key Vault is optional
    DefaultAzureCredential = None
    SecretClient = None

# Local Imports

# Configure logging
logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Secrets management service that provides a unified interface for accessing secrets
    from either environment variables (development), Google Cloud Secret Manager, or Azure Key Vault (production).

    Supports multiple cloud providers through a unified API:
    - Google Cloud Secret Manager (default)
    - Azure Key Vault
    - Environment variables (fallback)

    Configuration:
    - USE_SECRET_MANAGER: Enable/disable secret manager (true/false)
    - SECRET_PROVIDER: Choose provider (gcp/azure), default: gcp
    - SECRET_MANAGER_PROJECT_ID: GCP project ID
    - AZURE_KEY_VAULT_NAME: Azure Key Vault name
    """

    def __init__(self):
        self.use_secret_manager = os.getenv("USE_SECRET_MANAGER", "false").lower() == "true"
        self.secret_provider = os.getenv("SECRET_PROVIDER", "gcp").lower()  # gcp or azure
        self.project_id = os.getenv("SECRET_MANAGER_PROJECT_ID")
        self.key_vault_name = os.getenv("AZURE_KEY_VAULT_NAME")
        self.gcp_client = None
        self.azure_client = None

        if self.use_secret_manager:
            if self.secret_provider == "gcp" and self.project_id:
                try:
                    self.gcp_client = secretmanager.SecretManagerServiceClient()
                    logger.info("Google Cloud Secret Manager initialized")
                except Exception as e:
                    logger.error(f"Failed to initialize Google Cloud Secret Manager: {e}")
                    self.use_secret_manager = False
            elif self.secret_provider == "azure" and self.key_vault_name:
                try:
                    if SecretClient is not None:
                        credential = DefaultAzureCredential()
                        vault_url = f"https://{self.key_vault_name}.vault.azure.net/"
                        self.azure_client = SecretClient(vault_url=vault_url, credential=credential)
                        logger.info("Azure Key Vault initialized")
                    else:
                        logger.error("Azure Key Vault libraries not installed")
                        self.use_secret_manager = False
                except Exception as e:
                    logger.error(f"Failed to initialize Azure Key Vault: {e}")
                    self.use_secret_manager = False
            else:
                logger.error("No valid secret provider configured")
                self.use_secret_manager = False
        else:
            logger.info("Using environment variables for secrets (development mode)")

    def get_secret(self, secret_name: str, version: str = "latest") -> Optional[str]:
        """
        Retrieve a secret from either Google Cloud Secret Manager or environment variables.

        Args:
            secret_name: Name of the secret to retrieve
            version: Version of the secret (default: "latest")

        Returns:
            Secret value as string, or None if not found
        """
        if not secret_name:
            logger.error("Secret name cannot be empty")
            return None

        # Try secret manager first if enabled
        if self.use_secret_manager:
            if self.secret_provider == "gcp" and self.gcp_client:
                try:
                    # Construct the full secret path
                    secret_path = f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"

                    # Access the secret version
                    response = self.gcp_client.access_secret_version(name=secret_path)
                    secret_value = response.payload.data.decode("UTF-8")

                    logger.debug(f"Successfully retrieved secret from GCP: {secret_name}")
                    return secret_value

                except NotFound:
                    logger.warning(f"Secret not found in Google Cloud Secret Manager: {secret_name}")
                except GoogleAPICallError as e:
                    logger.error(f"Google Cloud Secret Manager error: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error accessing secret {secret_name}: {e}")

            elif self.secret_provider == "azure" and self.azure_client:
                try:
                    # Get secret from Azure Key Vault
                    retrieved_secret = self.azure_client.get_secret(secret_name)
                    secret_value = retrieved_secret.value

                    logger.debug(f"Successfully retrieved secret from Azure Key Vault: {secret_name}")
                    return secret_value

                except Exception as e:
                    logger.error(f"Azure Key Vault error: {e}")

        # Fall back to environment variables
        env_var_name = self._secret_name_to_env_var(secret_name)
        env_value = os.getenv(env_var_name)

        if env_value:
            logger.debug(f"Retrieved secret from environment variable: {env_var_name}")
            return env_value
        else:
            logger.warning(f"Secret not found in environment variables: {env_var_name}")
            return None

    def _secret_name_to_env_var(self, secret_name: str) -> str:
        """
        Convert secret name to environment variable name format.

        Args:
            secret_name: Secret name (e.g., "db_password")

        Returns:
            Environment variable name (e.g., "DB_PASSWORD")
        """
        return secret_name.upper().replace("-", "_").replace(".", "_")

    def get_all_secrets(self, secret_names: Dict[str, str]) -> Dict[str, Any]:
        """
        Retrieve multiple secrets at once.

        Args:
            secret_names: Dictionary mapping secret names to their expected environment variable names

        Returns:
            Dictionary with retrieved secret values
        """
        secrets = {}

        for secret_name, env_var in secret_names.items():
            # Try to get from secret manager or environment
            secret_value = self.get_secret(secret_name)

            if secret_value is None:
                # Fall back to direct environment variable lookup
                secret_value = os.getenv(env_var)

            if secret_value:
                secrets[env_var] = secret_value
            else:
                logger.warning(f"Could not retrieve secret: {secret_name} (env var: {env_var})")

        return secrets

    def create_or_update_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Create or update a secret in Google Cloud Secret Manager or Azure Key Vault.

        Args:
            secret_name: Name of the secret
            secret_value: Value of the secret

        Returns:
            True if successful, False otherwise
        """
        if not self.use_secret_manager:
            logger.error("Secret Manager not initialized")
            return False

        try:
            if self.secret_provider == "gcp" and self.gcp_client:
                # Create the secret if it doesn't exist
                secret_path = f"projects/{self.project_id}/secrets/{secret_name}"

                try:
                    self.gcp_client.get_secret(name=secret_path)
                    logger.info(f"Secret already exists: {secret_name}")
                except NotFound:
                    # Create the secret
                    self.gcp_client.create_secret(
                        request={
                            "parent": f"projects/{self.project_id}",
                            "secret_id": secret_name,
                            "secret": {"replication": {"automatic": {}}},
                        }
                    )
                    logger.info(f"Created new secret: {secret_name}")

                # Add the secret version
                self.gcp_client.add_secret_version(
                    request={
                        "parent": secret_path,
                        "payload": {"data": secret_value.encode("UTF-8")},
                    }
                )

                logger.info(f"Successfully updated secret in GCP: {secret_name}")
                return True

            elif self.secret_provider == "azure" and self.azure_client:
                # Azure Key Vault automatically creates the secret if it doesn't exist
                self.azure_client.set_secret(secret_name, secret_value)
                logger.info(f"Successfully updated secret in Azure Key Vault: {secret_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to create/update secret {secret_name}: {e}")
            return False

    def rotate_secret(self, secret_name: str, new_value: str) -> bool:
        """
        Rotate a secret by creating a new version.

        Args:
            secret_name: Name of the secret to rotate
            new_value: New value for the secret

        Returns:
            True if successful, False otherwise
        """
        return self.create_or_update_secret(secret_name, new_value)


# Global secrets manager instance
secrets_manager = SecretsManager()


def get_secret(secret_name: str, version: str = "latest") -> Optional[str]:
    """
    Convenience function to get a secret.

    Args:
        secret_name: Name of the secret
        version: Version of the secret

        Returns:
            Secret value or None
    """
    return secrets_manager.get_secret(secret_name, version)


def get_database_secrets() -> Dict[str, str]:
    """
    Get database-related secrets.

    Returns:
        Dictionary with database secrets
    """
    secret_names = {
        "db_username": "DB_USERNAME",
        "db_password": "DB_PASSWORD",
        "db_host": "DB_HOST",
        "db_port": "DB_PORT",
        "db_name": "DB_NAME",
    }

    return secrets_manager.get_all_secrets(secret_names)


def get_auth_secrets() -> Dict[str, str]:
    """
    Get authentication-related secrets.

    Returns:
        Dictionary with auth secrets
    """
    secret_names = {
        "secret_key": "SECRET_KEY",
        "entra_tenant_id": "ENTRA_TENANT_ID",
        "entra_client_id": "ENTRA_CLIENT_ID",
        "entra_client_secret": "ENTRA_CLIENT_SECRET",
    }

    return secrets_manager.get_all_secrets(secret_names)


def get_llm_secrets() -> Dict[str, str]:
    """
    Get LLM-related secrets.

    Returns:
        Dictionary with LLM secrets
    """
    secret_names = {
        "azure_openai_endpoint": "AZURE_OPENAI_ENDPOINT",
        "azure_openai_api_key": "AZURE_OPENAI_API_KEY",
        "gemini_api_key": "GEMINI_API_KEY",
    }

    return secrets_manager.get_all_secrets(secret_names)
