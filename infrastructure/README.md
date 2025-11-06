
# Infrastructure as Code for the Project Proposal Generator

This directory contains the Bicep templates for deploying the Project Proposal Generator application to Azure. The templates are designed to be modular and reusable, making it easy to manage the infrastructure as code.

## Structure

- **`main.bicep`**: The main entry point for the deployment. It orchestrates the deployment of all the other modules.
- **`modules/`**: This directory contains the individual Bicep modules for each Azure resource:
  - **`acr.bicep`**: Azure Container Registry
  - **`postgres.bicep`**: Azure Database for PostgreSQL
  - **`redis.bicep`**: Azure Cache for Redis
  - **`openai.bicep`**: Azure OpenAI Service
  - **`container_env.bicep`**: Azure Container Apps Environment
  - **`container_apps.bicep`**: The main Azure Container App for the backend service.

## Manual Deployment

While the recommended way to deploy the infrastructure is through the CI/CD pipeline, you can also deploy it manually using the Azure CLI.

### Prerequisites

- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- [Bicep CLI](https://docs.microsoft.com/en-us/azure/bicep/install)

### Steps

1. **Login to Azure:**
   ```bash
   az login
   ```

2. **Create a Resource Group:**
   ```bash
   az group create --name <resource-group-name> --location <location>
   ```

3. **Deploy the Bicep Template:**
   ```bash
   az deployment group create \
     --resource-group <resource-group-name> \
     --template-file main.bicep \
     --parameters backendImage=<your-backend-image> environmentSize=<environment-size> serperApiKey=<key> entraTenantId=<id> entraClientId=<id> entraClientSecret=<secret>
   ```
   - `backendImage`: The name and tag of your Docker image (e.g., `backend:latest`).
   - `environmentSize`: The desired size of the environment (e.g., `Testing`, `Expanded`).
   - You will also need to provide the secure parameters for the Serper API and Entra SSO.
