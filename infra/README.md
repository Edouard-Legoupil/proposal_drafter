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
   az group create --name <RESOURCE_GROUP> --location <LOCATION>  --tags Environment=Dev
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
  --resource-group <RESOURCE_GROUP> \
  --name <WEBAPP_NAME> \
  --settings WEBSITES_PORT=8080 WEBSITES_CONTAINER_START_TIME_LIMIT=1800
```

Once done the bicep template for the full ressource group can be exported from the Azure Portal.


### Set Database

The app use a vector store for the embeddings. The vector store is a PostgreSQL database with a vector extension. The vector extension is a PostgreSQL extension that allows you to store and query vector data. It is only available in the GeneralPurpose tier (about 100$/month).

```bash
az postgres flexible-server update \
  --server-name <DB_SERVER_NAME> \
  --resource-group <RESOURCE_GROUP> \
  --tier GeneralPurpose \
  --sku-name standard_d2ds_v5

# now enable the correct extensions
az postgres flexible-server parameter set \
  --server-name <DB_SERVER_NAME> \
  --resource-group <RESOURCE_GROUP> \
  --name azure.extensions \
  --value pgcrypto,vector
```

```bash
az postgres flexible-server db create \
  --server-name <DB_SERVER_NAME> \
  --resource-group <RESOURCE_GROUP> \
  --database-name <DB_NAME> \
  --charset utf8 \
  --collation en_US.utf8
```

**Configure a Virtual Network (VNet)**
A Virtual Network (VNet) in Azure is like a private network in the cloud. It allows resources (VMs, databases, Bastion) to communicate securely without exposing them to the public internet.
Your PostgreSQL Flexible Server can be configured with private access, meaning it only accepts connections from resources inside the same VNet (or peered VNets).

 * VNet = private network
 * Private Endpoint = private door to the DB
 * DNS = phonebook
 * Jump VM = controlled entry point
 * Bastion = secure remote access


```bash
############################################
# NETWORK FOUNDATION
############################################

# Create a Virtual Network (VNet), which is a private network in Azure
# Think of this as your own isolated LAN in the cloud.
# It uses the 10.0.0.0/16 address space and already includes:
# - one subnet dedicated to the database private endpoint
az network vnet create \
  --resource-group <RESOURCE_GROUP> \
  --name <VNET_NAME> \
  --address-prefixes 10.0.0.0/16 \
  --subnet-name dbSubnet \
  --subnet-prefixes 10.0.1.0/24


# Add a subnet that is *exclusively* reserved for Azure Bastion.
# Azure Bastion requires:
# - a dedicated subnet
# - the subnet name MUST be exactly "AzureBastionSubnet"
# Bastion will later be used to securely SSH into the VM without public IPs.
az network vnet subnet create \
  --resource-group <RESOURCE_GROUP> \
  --vnet-name <VNET_NAME> \
  --name AzureBastionSubnet \
  --address-prefixes 10.0.2.0/24


# Add a subnet for the jump VM (also called a bastion host or jump box).
# This VM will be the only machine allowed to talk to the database directly.
az network vnet subnet create \
  --resource-group <RESOURCE_GROUP> \
  --vnet-name <VNET_NAME> \
  --name vmSubnet \
  --address-prefixes 10.0.3.0/24


############################################
# PRIVATE ACCESS TO POSTGRESQL
############################################

# Create a Private Endpoint for the PostgreSQL Flexible Server.
# This does 3 important things:
# 1. Gives the database a private IP inside the VNet
# 2. Removes the need for any public database access
# 3. Makes the database reachable ONLY from inside this VNet
az network private-endpoint create \
  --name <PE_NAME> \
  --resource-group <RESOURCE_GROUP> \
  --vnet-name <VNET_NAME> \
  --subnet dbSubnet \
  --private-connection-resource-id $(az postgres flexible-server show \
      --resource-group <RESOURCE_GROUP> \
      --name <DB_NAME> \
      --query id -o tsv) \
  --group-id postgres \
  --connection-name postgres-pe-connection


############################################
# PRIVATE DNS (NAME RESOLUTION)
############################################

# Without this DNS setup, the database hostname would still resolve
# to a public IP (which we do NOT want).
# These steps ensure:
# *.postgres.database.azure.com → private IP inside the VNet

# Create a Private DNS Zone for PostgreSQL private endpoints
az network private-dns zone create \
  --resource-group <RESOURCE_GROUP> \
  --name privatelink.postgres.database.azure.com


# Link the Private DNS Zone to the VNet.
# This allows any resource inside the VNet to resolve
# PostgreSQL hostnames to their private IPs automatically.
az network private-dns link vnet create \
  --resource-group <RESOURCE_GROUP> \
  --zone-name privatelink.postgres.database.azure.com \
  --name MyDNSLink \
  --virtual-network <VNET_NAME> \
  --registration-enabled false


# Associate the Private Endpoint with the DNS zone.
# This step creates the actual DNS A-record pointing
# the database hostname to the private IP.
az network private-endpoint dns-zone-group create \
  --resource-group <RESOURCE_GROUP> \
  --endpoint-name <PE_NAME> \
  --name MyDNSZoneGroup \
  --private-dns-zone privatelink.postgres.database.azure.com \
  --zone-name privatelink.postgres.database.azure.com


############################################
# JUMP VM (CONTROLLED ACCESS POINT)
############################################

# Create a small Linux VM that lives inside the VNet.
# This VM:
# - has NO public IP
# - can access the private database
# - is only reachable through Azure Bastion
az vm create \
  --resource-group <RESOURCE_GROUP> \
  --name jumpVM \
  --image UbuntuLTS \
  --size Standard_B1s \
  --admin-username <vm_user> \
  --generate-ssh-keys \
  --vnet-name <VNET_NAME> \
  --subnet vmSubnet


############################################
# AZURE BASTION (SECURE REMOTE ACCESS)
############################################

# Create a public IP for Azure Bastion.
# This is the ONLY public-facing component in the setup.
# Bastion uses this IP to provide secure browser/CLI access to the VM.
az network public-ip create \
  --resource-group <RESOURCE_GROUP> \
  --name BastionPublicIP \
  --sku Standard \
  --location <LOCATION>


# Deploy Azure Bastion into the VNet.
# Bastion allows you to SSH into the jump VM:
# - without exposing the VM to the internet
# - without managing inbound firewall rules
az network bastion create \
  --resource-group <RESOURCE_GROUP> \
  --name <BASTION_NAME> \
  --vnet-name <VNET_NAME> \
  --public-ip-address BastionPublicIP \
  --location <LOCATION>


############################################
# LOCAL ACCESS VIA SSH TUNNELS
############################################

# Open a Bastion tunnel from your local machine to the jump VM.
# This forwards:
#   localhost:2022 → jumpVM:22
# allowing you to SSH as if the VM were local.
az network bastion tunnel \
  --name <BASTION_NAME> \
  --resource-group <RESOURCE_GROUP> \
  --target-resource-id /subscriptions/<SUB_ID>/resourceGroups/<RESOURCE_GROUP>/providers/Microsoft.Compute/virtualMachines/jumpVM \
  --resource-port 22 \
  --port 2022


# Create a local SSH tunnel to PostgreSQL *through* the jump VM.
# This forwards:
#   localhost:5432 → PostgreSQL private endpoint
# Result: local tools can connect to the database as if it were local.
ssh -L 5432:<DB_NAME>.postgres.database.azure.com:5432 \
    <vm_user>@127.0.0.1 -p 2022

```

Once this is done, you can connect to the database and create the tables. Then go to the `backend` directory and run the back office initialisation scripts `backend/scripts/README.md`.


### Build and Push Docker Image

From the root of the project, build the Docker image for the backend:

```bash
cd ../
docker build --no-cache -t <ACR_NAME>.azurecr.io/backend:latest .

#Confirm it starts and responds.
docker run --env-file ./backend/.env -p 8080:8080 <ACR_NAME>.azurecr.io/backend:latest
```
*Note: Replace `<ACR_NAME>` with the name of the Azure Container Registry created by the Bicep template.*

Login to ACR:
```bash
az acr login --name <ACR_NAME>
```

Push the image to ACR:
```bash
docker push <ACR_NAME>.azurecr.io/backend:latest

## Ensure that the web app can log in to the ACR
ACR_USER=$(az acr credential show --name propalgen --query "username" -o tsv)
ACR_PASS=$(az acr credential show --name propalgen --query "passwords[0].value" -o tsv)
az webapp config container set \
  --name <WEBAPP_NAME> \
  --resource-group <RESOURCE_GROUP> \
  ---container-image-name <ACR_NAME>.azurecr.io/backend:latest \
  --container-registry-server-url https://<ACR_NAME>.azurecr.io \
  --container-registry-server-user $ACR_USER \
  --container-registry-server-password $ACR_PASS
```

  Secure the app throug the virtual network

```bash
############################################
# ALLOW AZURE WEB APP TO REACH THE PRIVATE DB
############################################

# Integrate the Azure Web App with the VNet.
# This allows the Web App to:
# - send traffic INTO the VNet
# - reach private resources (like the PostgreSQL private endpoint)
# Without this, the Web App cannot see private IPs at all.
#
# NOTE:
# - This does NOT expose the Web App publicly
# - This does NOT require inbound rules
# - It only enables outbound access to the VNet
az webapp vnet-integration add \
  --resource-group <RESOURCE_GROUP> \
  --name <WEBAPP_NAME> \
  --vnet <VNET_NAME> \
  --subnet vmSubnet
``` 

To check app deployment run

```bash
az webapp log config \
  --name <WEBAPP_NAME> \
  --resource-group <RESOURCE_GROUP> \
  --application-logging filesystem \
  --level information

az webapp log tail \
  --name <WEBAPP_NAME> \
  --resource-group <RESOURCE_GROUP> \
  | tee  logs/azure_deployment_logfile.txt

# or get a zip of the logs
az webapp log download \
  --name <WEBAPP_NAME> \
  --resource-group <RESOURCE_GROUP> \
  --log-file logs/propalgen_logs_$(date +%Y%m%d_%H%M%S).zip
```   



 
or visit the debug console: https://<WEBAPP_NAME>.scm.azurewebsites.net/DebugConsole 

 **Application is Ready**:

Once the deployment is complete and the image is pushed, you may manually restart the app from the Azure Portal, the application will be then available at the URL provided in the portal.

To SSH in the app:

```bash
# Make sure remote debugging is OFF; it can block the tunnel
az webapp config set \
  --resource-group <resource-group-name> \
  --name <WEBAPP_NAME> \
  --remote-debugging-enabled false

az webapp ssh \
  --name <WEBAPP_NAME> \
  --resource-group <resource-group-name>

# Start the tunnel
az webapp create-remote-connection \
  --subscription <subscription-id> \
  --resource-group <resource-group-name> \
  --name propalgen

# In another terminal, use the printed local port:
ssh root@127.0.0.1 -p
```


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


 