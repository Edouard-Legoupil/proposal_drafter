# Infrastructure as Code for ☁️ Azure Deployment 

This project contains the Bicep templates for deploying the Project Proposal Generator application to Azure. The templates are designed to be modular and reusable, making it easy to manage the infrastructure as code.


## Azure Prerequisites

Before you can deploy the infrastructure, you need to set up the following in Azure:

1.  **Azure Subscription**: You will need an active Azure subscription.
2.  **Resource Group**: Create a resource group to hold the deployed resources.

First you need to obtain Azure Command line tool

- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)

**Note:** All resources deployed using these templates will be tagged with `Environment=Dev`.

### Steps

1. **Login to Azure:**
   ```bash
   az login
   ```

2. **Create a Resource Group:**
   ```bash
   az group create --name <resource-group-name> --location <location>  --tags Environment=Dev
   az provider register --namespace Microsoft.CognitiveServices
   az provider register --namespace Microsoft.OpenAI
   ```

note that Only newer regions support Microsoft.OpenAI (eastus, swedencentral, australiaeast, canadacentral).

---


## Manual Deployment

While the recommended way to deploy the infrastructure is through the CI/CD pipeline (see below), you can also deploy it manually using the Azure CLI. 

This option is for deploying the infrastructure without SSO capabilities (which requires the capacity to create a service principal account and an application ID).

### Deploy manually the correct ressources
Building a bicep infrastructure deployment script from scratch is not recommended, as it requires a lot of parameters and is not very user-friendly. Rather, it is exported from the Azure Portal following the manual set up of :

 - Azure OpenAI - setting gpt-4.1 mini and adda
 - Azure Database for PostgreSQL Flexible Server
 - Azure Container Registry to push the docker image
 - Azure Web App to run the docker image with the required environment variables and expose it to the internet

In Azure Web App, set all environment variables as per backend/.env plus 
 * Portal → Configuration → WEBSITES_PORT=8080 (and restart). 
 Portal → Configuration → WEBSITES_CONTAINER_START_TIME_LIMIT=1800. -- this to allow more time for the container to start. 

```bash
az webapp config appsettings set \
  --resource-group <resource-group-name> \
  --name <app-name> \
  --settings WEBSITES_PORT=8080 WEBSITES_CONTAINER_START_TIME_LIMIT=1800
```

Once done the bicep template for the full ressource group can be exported from the Azure Portal.


### Set Database

The app use a vector store for the embeddings. The vector store is a PostgreSQL database with a vector extension. The vector extension is a PostgreSQL extension that allows you to store and query vector data. It is only available in the GeneralPurpose tier (about 100$/month).

```bash
az postgres flexible-server update \
    --server-name <db-server-name> \
    --resource-group <resource-group-name> \
    --tier GeneralPurpose \
    --sku-name standard_d2ds_v5

# now enable the correct extensions
az postgres flexible-server parameter set \
  --server-name <db-server-name> \
  --resource-group <resource-group-name> \
  --name azure.extensions \
  --value pgcrypto,vector
```

```bash
az postgres flexible-server db create \
    --server-name <db-server-name> \
    --resource-group <resource-group-name> \
    --database-name <db-name> \
    --charset utf8 \
    --collation en_US.utf8
```

**Configure PostgreSQL firewall.**

You can do this in the Azure portal, or by using the Azure CLI:

```bash
az extension add --name ssh


az ssh vm \
  --name <db-server-name> \
  --resource-group <RESOURCE_GROUP> \
  --local-port 5432:<POSTGRES_PRIVATE_IP>:5432


az postgres flexible-server firewall-rule create --resource-group <your-resource-group> --name <your-postgres-server-name> --rule-name AllowMyIP --start-ip-address <your-ip-address> --end-ip-address <your-ip-address>
```

Once this is done, you can connect to the database and create the tables. Then go to the `backend` directory and run the back office initialisation scripts `backend/scripts/README.md`.


### Build and Push Docker Image

From the root of the project, build the Docker image for the backend:

```bash
cd ../
docker build --no-cache -t <acr-name>.azurecr.io/backend:latest .

#Confirm it starts and responds.
docker run --env-file ./backend/.env -p 8080:8080 <acr-name>.azurecr.io/backend:latest
```
*Note: Replace `<acr-name>` with the name of the Azure Container Registry created by the Bicep template.*

Login to ACR:
```bash
az acr login --name <acr-name>
```

Push the image to ACR:
```bash
docker push <acr-name>.azurecr.io/backend:latest

## Ensure that the web app can log in to the ACR
ACR_USER=$(az acr credential show --name propalgen --query "username" -o tsv)
ACR_PASS=$(az acr credential show --name propalgen --query "passwords[0].value" -o tsv)
az webapp config container set \
  --name <app-name> \
  --resource-group <resource-group-name> \
  --docker-custom-image-name propalgen.azurecr.io/backend:latest \
  --docker-registry-server-url https://propalgen.azurecr.io \
  --docker-registry-server-user $ACR_USER \
  --docker-registry-server-password $ACR_PASS
```

To check app deployment run

```bash
az webapp log config \
  --name <app-name> \
  --resource-group <resource-group-name> \
  --application-logging filesystem \
  --level information

az webapp log tail \
  --name <app-name> \
  --resource-group <resource-group-name> \
  | tee  logs/azure_deployment_logfile.txt

# or get a zip of the logs
az webapp log download \
  --name <app-name> \
  --resource-group <resource-group-name> \
  --log-file logs/propalgen_logs_$(date +%Y%m%d_%H%M%S).zip
```   
 
or visit the debug console: https://<app-name>.scm.azurewebsites.net/DebugConsole 

 **Application is Ready**:

Once the deployment is complete and the image is pushed, you may manually restart the app from the Azure Portal, the application will be then available at the URL provided in the portal.


---

## CI/CD Deployment (with SSO)

**Service Principal**: The CI/CD workflow needs a service principal to authenticate with Azure.

### Create Service Principal for SSO Workflow

This is the recommended deployment option and includes Single Sign-On (SSO) with Entra ID.

Create a service principal with the `Contributor` role scoped to the resource group you just created.

```bash
# Get your subscription and resource group details
export SUBSCRIPTION_ID=$(az account show --query id --output tsv)
export RESOURCE_GROUP="<your-resource-group-name>"

# Create the service principal
az ad sp create-for-rbac --name "<your-sp-name>" --role contributor --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP"
```

> **Permission Error?**
> If you get an `Insufficient privileges to complete the operation` error, your Azure user account does not have permission to register applications in Microsoft Entra ID.
> **Solution:**
> 1. Ask your Azure administrator to grant you the `Application Administrator` role.
> 2. Or, use the **CI/CD Deployment (No SSO)** option below, which does not require these permissions.
> For more details, see the [Microsoft documentation on app registration permissions](https://docs.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal-portal#permissions-for-registering-an-app).

This command will output a JSON object. You will need the `appId` (which is the `AZURE_CLIENT_ID`) and the `tenant` (which is the `AZURE_TENANT_ID`) for the GitHub secrets.



###  Configure GitHub Secrets

In your GitHub repository, go to `Settings > Secrets and variables > Actions` and create the following secrets:

-   `AZURE_CLIENT_ID`: The `appId` from the service principal you created.
-   `AZURE_TENANT_ID`: The `tenant` from the service principal you created.
-   `AZURE_SUBSCRIPTION_ID`: Your Azure subscription ID.
-   `AZURE_RG`: The name of your resource group.
-   `RESOURCE_PREFIX`: A short, unique prefix for your resources (e.g., `ppg-prod`).
-   `BACKEND_IMAGE`: The name and tag of your Docker image (e.g., `backend:latest`).
-   `ENVIRONMENT_SIZE`: The size of the environment (e.g., `Testing`, `Expanded`).
-   `SERPER_API_KEY`: Your Serper API key.
-   `ENTRA_TENANT_ID`: Your Entra Tenant ID for SSO.
-   `ENTRA_CLIENT_ID`: Your Entra Client ID for SSO.
-   `ENTRA_CLIENT_SECRET`: Your Entra Client Secret for SSO.
-   `SECRET_KEY`: A strong, randomly generated secret key for your application.
-   `CF_ACCESS_CLIENT_ID`: Your Cloudflare Access Client ID.
-   `CF_ACCESS_CLIENT_SECRET`: Your Cloudflare Access Client Secret.

### Automated Secret Setup

To simplify the process of setting up GitHub secrets, you can use the `setup_github_secrets.sh` script. This script will prompt you for the necessary values and set the secrets in your GitHub repository automatically.


Run the script from the `infra` directory:
```bash
./setup_github_secrets.sh
```

 * Enter the name of your GitHub repository (e.g., `owner/repo`).
 * Choose the deployment option (with or without SSO).
 * Provide the requested secret values.

The script will then set the secrets in your repository, and you can proceed to activate the workflow.

---

### Activate the Workflow

The workflow is defined in `.github/workflows/deploy.yml` and will be **automatically triggered** on every push to the `main` branch.

- **`infra/main.bicep`**: The main entry point for the deployment with SSO.
- **`infra/modules/`**: This directory contains the individual Bicep modules for each Azure resource.

After either workflow has successfully run, you can find the outputs in the workflow run logs. The outputs will include the `acrName`, `postgresServerName`, and `containerAppUrl`.


 