# Standard Library
import os
from unittest.mock import patch, MagicMock

# Third-Party Libraries

# Local Imports
from backend.core.secrets import SecretsManager, get_secret, get_database_secrets


class TestSecretsManager:
    """Test suite for the SecretsManager class."""

    def test_initialization_without_secret_manager(self):
        """Test initialization when USE_SECRET_MANAGER is false."""
        # Set environment to disable secret manager
        os.environ["USE_SECRET_MANAGER"] = "false"

        manager = SecretsManager()

        assert manager.use_secret_manager is False
        assert manager.gcp_client is None
        assert manager.azure_client is None

    def test_initialization_with_secret_manager(self):
        """Test initialization when USE_SECRET_MANAGER is true."""
        # Set environment to enable secret manager
        os.environ["USE_SECRET_MANAGER"] = "true"
        os.environ["SECRET_MANAGER_PROJECT_ID"] = "test-project"

        with patch("backend.core.secrets.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            manager = SecretsManager()

            assert manager.use_secret_manager is True
            assert manager.gcp_client is not None
            assert manager.azure_client is None
            mock_client.assert_called_once()

    def test_get_secret_fallback_to_env(self):
        """Test getting a secret falls back to environment variables."""
        os.environ["USE_SECRET_MANAGER"] = "false"
        os.environ["TEST_SECRET"] = "test-value"

        manager = SecretsManager()

        # Should fall back to environment variable
        result = manager.get_secret("test_secret")

        assert result == "test-value"

    def test_get_secret_from_secret_manager(self):
        """Test getting a secret from Google Cloud Secret Manager."""
        os.environ["USE_SECRET_MANAGER"] = "true"
        os.environ["SECRET_MANAGER_PROJECT_ID"] = "test-project"

        with patch("backend.core.secrets.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            # Mock the secret response
            mock_response = MagicMock()
            mock_response.payload.data.decode.return_value = "secret-value"
            mock_instance.access_secret_version.return_value = mock_response

            manager = SecretsManager()
            result = manager.get_secret("test_secret")

            assert result == "secret-value"
            mock_instance.access_secret_version.assert_called_once()

    def test_get_secret_empty_name(self):
        """Test getting a secret with empty name returns None."""
        manager = SecretsManager()
        result = manager.get_secret("")

        assert result is None

    def test_get_secret_not_found(self):
        """Test getting a non-existent secret returns None."""
        os.environ["USE_SECRET_MANAGER"] = "false"
        os.environ.pop("NON_EXISTENT_SECRET", None)

        manager = SecretsManager()
        result = manager.get_secret("non_existent_secret")

        assert result is None

    def test_secret_name_to_env_var_conversion(self):
        """Test secret name to environment variable conversion."""
        manager = SecretsManager()

        # Test various naming conventions
        assert manager._secret_name_to_env_var("test_secret") == "TEST_SECRET"
        assert manager._secret_name_to_env_var("test-secret") == "TEST_SECRET"
        assert manager._secret_name_to_env_var("test.secret") == "TEST_SECRET"
        assert manager._secret_name_to_env_var("test") == "TEST"


class TestSecretsFunctions:
    """Test suite for the convenience functions."""

    def test_get_secret_function(self):
        """Test the convenience get_secret function."""
        os.environ["USE_SECRET_MANAGER"] = "false"
        os.environ["TEST_SECRET"] = "test-value"

        result = get_secret("test_secret")

        assert result == "test-value"

    def test_get_database_secrets(self):
        """Test getting database secrets."""
        os.environ["USE_SECRET_MANAGER"] = "false"
        os.environ["DB_USERNAME"] = "test-user"
        os.environ["DB_PASSWORD"] = "test-pass"
        os.environ["DB_HOST"] = "localhost"
        os.environ["DB_PORT"] = "5432"
        os.environ["DB_NAME"] = "test-db"

        secrets = get_database_secrets()

        assert secrets["DB_USERNAME"] == "test-user"
        assert secrets["DB_PASSWORD"] == "test-pass"
        assert secrets["DB_HOST"] == "localhost"
        assert secrets["DB_PORT"] == "5432"
        assert secrets["DB_NAME"] == "test-db"


class TestSecretsManagerIntegration:
    """Integration tests for secrets manager."""

    def test_secret_manager_fallback_chain(self):
        """Test the fallback chain: Secret Manager -> Environment Variables."""
        os.environ["USE_SECRET_MANAGER"] = "true"
        os.environ["SECRET_MANAGER_PROJECT_ID"] = "test-project"
        os.environ["FALLBACK_SECRET"] = "env-value"

        with patch("backend.core.secrets.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            # Simulate secret not found in Secret Manager
            from google.api_core.exceptions import NotFound

            mock_instance.access_secret_version.side_effect = NotFound("Secret not found")

            manager = SecretsManager()
            result = manager.get_secret("fallback_secret")

            # Should fall back to environment variable
            assert result == "env-value"

    def test_secret_manager_error_handling(self):
        """Test error handling in Secret Manager."""
        os.environ["USE_SECRET_MANAGER"] = "true"
        os.environ["SECRET_MANAGER_PROJECT_ID"] = "test-project"
        os.environ["FALLBACK_SECRET"] = "env-value"

        with patch("backend.core.secrets.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            # Simulate various errors
            from google.api_core.exceptions import GoogleAPICallError

            mock_instance.access_secret_version.side_effect = GoogleAPICallError("API error")

            manager = SecretsManager()
            result = manager.get_secret("fallback_secret")

            # Should fall back to environment variable on API error
            assert result == "env-value"


class TestAzureKeyVaultIntegration:
    """Test suite for Azure Key Vault integration."""

    def test_azure_initialization(self):
        """Test Azure Key Vault initialization."""
        os.environ["USE_SECRET_MANAGER"] = "true"
        os.environ["SECRET_PROVIDER"] = "azure"
        os.environ["AZURE_KEY_VAULT_NAME"] = "test-vault"

        with patch("backend.core.secrets.SecretClient") as mock_secret_client:
            with patch("backend.core.secrets.DefaultAzureCredential") as mock_credential:
                mock_client_instance = MagicMock()
                mock_secret_client.return_value = mock_client_instance

                manager = SecretsManager()

                assert manager.use_secret_manager is True
                assert manager.secret_provider == "azure"
                assert manager.azure_client is not None
                mock_secret_client.assert_called_once()
                mock_credential.assert_called_once()

    def test_azure_get_secret_success(self):
        """Test getting a secret from Azure Key Vault."""
        os.environ["USE_SECRET_MANAGER"] = "true"
        os.environ["SECRET_PROVIDER"] = "azure"
        os.environ["AZURE_KEY_VAULT_NAME"] = "test-vault"

        with patch("backend.core.secrets.SecretClient") as mock_secret_client:
            with patch("backend.core.secrets.DefaultAzureCredential"):
                mock_client_instance = MagicMock()
                mock_secret_client.return_value = mock_client_instance

                # Mock the secret response
                mock_secret = MagicMock()
                mock_secret.value = "azure-secret-value"
                mock_client_instance.get_secret.return_value = mock_secret

                manager = SecretsManager()
                result = manager.get_secret("test_secret")

                assert result == "azure-secret-value"
                mock_client_instance.get_secret.assert_called_once_with("test_secret")

    def test_azure_get_secret_failure(self):
        """Test getting a secret from Azure Key Vault with error."""
        os.environ["USE_SECRET_MANAGER"] = "true"
        os.environ["SECRET_PROVIDER"] = "azure"
        os.environ["AZURE_KEY_VAULT_NAME"] = "test-vault"
        os.environ["FALLBACK_SECRET"] = "env-value"

        with patch("backend.core.secrets.SecretClient") as mock_secret_client:
            with patch("backend.core.secrets.DefaultAzureCredential"):
                mock_client_instance = MagicMock()
                mock_secret_client.return_value = mock_client_instance

                # Simulate Azure error
                mock_client_instance.get_secret.side_effect = Exception("Azure error")

                manager = SecretsManager()
                result = manager.get_secret("fallback_secret")

                # Should fall back to environment variable
                assert result == "env-value"

    def test_azure_create_secret(self):
        """Test creating a secret in Azure Key Vault."""
        os.environ["USE_SECRET_MANAGER"] = "true"
        os.environ["SECRET_PROVIDER"] = "azure"
        os.environ["AZURE_KEY_VAULT_NAME"] = "test-vault"

        with patch("backend.core.secrets.SecretClient") as mock_secret_client:
            with patch("backend.core.secrets.DefaultAzureCredential"):
                mock_client_instance = MagicMock()
                mock_secret_client.return_value = mock_client_instance

                manager = SecretsManager()
                result = manager.create_or_update_secret("test_secret", "test_value")

                assert result is True
                mock_client_instance.set_secret.assert_called_once_with("test_secret", "test_value")


# Clean up environment variables after tests
def teardown_function():
    """Clean up environment variables after each test."""
    env_vars = [
        "USE_SECRET_MANAGER",
        "SECRET_MANAGER_PROJECT_ID",
        "SECRET_PROVIDER",
        "AZURE_KEY_VAULT_NAME",
        "TEST_SECRET",
        "DB_USERNAME",
        "DB_PASSWORD",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "FALLBACK_SECRET",
        "NON_EXISTENT_SECRET",
    ]

    for var in env_vars:
        os.environ.pop(var, None)
