
# 🚀 Proposal Drafter - Setup Guide

This guide walks you through progressive steps for setting up the **Proposal Drafter** application:

1. **Local development (no Docker)**
2. **Docker-based development**
3. **Azure cloud deployment**
4. **CI/CD with GitHub Actions**

---

## 🧱 Application Overview

The app has four core components:
- 🖼 **Frontend** – React + Vite
- 🧠 **Backend** – FastAPI (Python)
- 🌐 **Nginx** – Reverse proxy
- 🗃 **Database** – PostgreSQL

---

## 🔧 Prerequisites

Install these tools before you begin:

- [x] Docker & Docker Compose  
- [x] Node.js + npm  
- [x] Python 3.11+  
- [x] Git  
- [x] Azure CLI (for deployment)  
- [x] Azure Subscription (for deployment)

---

# 1️⃣ Local Development (No Docker)

### Step 1: Clone the repository

```bash
git clone <repository-url>
cd proposal_drafter
```

### Step 2: Set environment variables

Create a `.env` file in the root directory:

```env
# OpenAI settings
AZURE_OPENAI_ENDPOINT=<your-openai-endpoint>
AZURE_OPENAI_API_KEY=<your-openai-key>
OPENAI_API_VERSION=2023-07-01-preview
AZURE_DEPLOYMENT_NAME=gpt-4o

# Database
DB_USERNAME=postgres
DB_PASSWORD=postgres
DB_NAME=proposalgen
DB_HOST=localhost
DB_PORT=5432

# Security
SECRET_KEY=<your-secret-key>
```

### Step 3: Start the backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8502 --reload
```

You can go to http://localhost:8502/api/health_check to verify the service is running.

### Step 4: Start the frontend

```bash
cd frontend
npm install
npm run dev
```

### Step 5: Start a PostgreSQL database

You can use a local PostgreSQL or a Docker image with the follwing command:

```bash
docker run --name pg-local -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres
```

Run setup script:

```bash
psql postgresql://postgres:postgres@localhost:5432/proposalgen -f database-setup.sql
```

---

# 2️⃣ Local Docker Development

### Step 1: Start Docker containers

```bash
docker-compose -f docker-compose-local.yml up --build
```

Services:
- Frontend: http://localhost:8503
- Backend: http://localhost:8502/api/health_check
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Step 2: Run database setup

```bash
sleep 10
psql postgresql://postgres:postgres@localhost:5432/proposalgen -f database-setup.sql
```

---

# 3️⃣ Azure Deployment (first Manual Steps)

## Step 1: Log into Azure and create resources

We create an Azure Container Registry (ACR) where the Docker images will be stored. We also need an Azure App Service (Linux, Multi-Container) where the app will be hosted. It will be configured it to pull images from ACR. Last, the App Service Plan defines the compute resources (CPU, memory), region, and pricing tier that host your apps. 

Below is a script that automates the creation of these resources:

```bash
az login

# ──────────────────────────────
# ✅ CONFIGURE THESE VARIABLES
# ──────────────────────────────
RESOURCE_GROUP="proposalgen-rg"
LOCATION="eastus"
ACR_NAME="proposalgenacr"                    # Must be globally unique
APP_SERVICE_PLAN="proposalgen-plan"
WEBAPP_NAME="proposalgen-app"
SERVICE_PRINCIPAL_NAME="gh-deploy-sp"
DOCKER_COMPOSE_FILE="docker-compose.yml"
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# ──────────────────────────────
# 1. Create Resource Group
# ──────────────────────────────
echo "Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# ──────────────────────────────
# 2. Create Azure Container Registry (ACR)
# ──────────────────────────────
echo "Creating Azure Container Registry..."
az acr create --name $ACR_NAME --resource-group $RESOURCE_GROUP --sku Basic --admin-enabled true

# ──────────────────────────────
# 3. Create App Service Plan (Linux)
# ──────────────────────────────
echo "Creating App Service Plan..."
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --sku B1 \
  --is-linux

# ──────────────────────────────
# 4. Create Web App (Linux, Multi-Container)
# ──────────────────────────────
echo "Creating Azure Web App..."
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $WEBAPP_NAME \
  --multicontainer-config-type compose \
  --multicontainer-config-file $DOCKER_COMPOSE_FILE

# ──────────────────────────────
# 5. Enable Managed Identity for App Service
# ──────────────────────────────
echo "Enabling Managed Identity..."
az webapp identity assign \
  --name $WEBAPP_NAME \
  --resource-group $RESOURCE_GROUP

PRINCIPAL_ID=$(az webapp show \
  --name $WEBAPP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query identity.principalId \
  --output tsv)

# ──────────────────────────────
# 6. Grant ACR Pull Permissions to App Service
# ──────────────────────────────
echo "Granting 'AcrPull' role to App Service identity..."
ACR_ID=$(az acr show --name $ACR_NAME --query id --output tsv)

az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "AcrPull" \
  --scope $ACR_ID

# ──────────────────────────────
# 7. Create Service Principal for GitHub Actions
# ──────────────────────────────
echo "Creating Service Principal for GitHub Actions..."
az ad sp create-for-rbac \
  --name $SERVICE_PRINCIPAL_NAME \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth > azure-credentials.json

echo ""
echo "🔑 Service Principal credentials written to azure-credentials.json"
echo "👉 Add this file content to GitHub Secrets as AZURE_CREDENTIALS"
echo ""
```

## Step 2: Build & Push Docker Images

```bash
# Backend
docker build -t proposalgen2acr.azurecr.io/proposalgen-backend:latest ./backend
docker push proposalgen2acr.azurecr.io/proposalgen-backend:latest

# Frontend
docker build -t proposalgen2acr.azurecr.io/proposalgen-frontend:latest --build-arg VITE_BACKEND_URL=/api ./frontend
docker push proposalgen2acr.azurecr.io/proposalgen-frontend:latest

# Nginx
docker build -t proposalgen2acr.azurecr.io/proposalgen-nginx:latest ./nginx-proxy
docker push proposalgen2acr.azurecr.io/proposalgen-nginx:latest
```

## Step 3: Deploy infrastructure using Bicep

```bash
az deployment group create \
  --resource-group proposalgen-rg \
  --template-file azure-resources.bicep \
  --parameters \
    baseName=proposalgen \
    dockerRegistryServerUrl=proposalgen2acr.azurecr.io \
    dockerRegistryServerUsername=proposalgen2acr \
    dockerRegistryServerPassword=<ACR-PASSWORD> \
    azureOpenAiEndpoint=<YOUR-OPENAI-ENDPOINT> \
    azureOpenAiApiKey=<YOUR-OPENAI-KEY> \
    openAiApiVersion=<YOUR-OPENAI-API-VERSION> \
    azureDeploymentName=<YOUR-DEPLOYMENT-NAME> \
    secretKey=<YOUR-SECRET-KEY> 
```

## Step 4: Set up Azure database

```bash
bash azure-db-setup.sh
```

---

# 4️⃣ GitHub CI/CD Workflow Automation

This section sets up a CI/CD pipeline using GitHub Actions to automate deployments to Azure whenever you push changes to the repository.


### Step 1: Push to GitHub

```bash
git remote add origin https://github.com/<your-org>/<your-repo>.git
git push -u origin main
```

### Step 2: Set up GitHub Secrets

In your GitHub repo, go to **Settings > Secrets and Variables > Actions**, and add the elemnts defining the target Azure Infrastructure::

- `AZURE_CREDENTIALS` (from `az ad sp create-for-rbac`)
- `REGISTRY_USERNAME`
- `REGISTRY_PASSWORD`
- `AZURE_WEBAPP_PUBLISH_PROFILE` -- 
- `REGISTRY_LOGIN_SERVER`

### Step 3: Application Settings (Environment Variables)

In the Azure Portal > App Service > Configuration, add the same environment variables you have in your Docker Compose file:
and the internal environment variables used in the app:

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `OPENAI_API_VERSION`
- `AZURE_DEPLOYMENT_NAME`
- `SECRET_KEY`
- `DB_USERNAME`
- `DB_PASSWORD`
- `DB_NAME`
- `DB_HOST`
- `DB_PORT`

### Step 4: GitHub Actions workflow file

The script `.github/workflows/deploy.yml` orchestrates the CI/CD pipeline.


---

## 🧪 Verification Checklist

| Task | Expected Output |
|------|------------------|
| Frontend | http://localhost:8503 |
| Backend health | http://localhost:8502/api/health_check |
| PostgreSQL | Tables created |
| Azure App | Live app URL after deployment |
| CI/CD | Auto-deploys on `git push` |

---

## 🛠 Troubleshooting

### 🧱 SSL Error in Docker Build

**Error**: `CERTIFICATE_VERIFY_FAILED`  
**Fix**: Inside your Dockerfile, add:

```Dockerfile
RUN apt-get update && apt-get install -y ca-certificates && update-ca-certificates
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
```

### 🔥 Nginx Not Routing

1. Run `docker logs <nginx-container-id>`
2. Ensure backend URL is correct in `proxy_pass`
3. Remove trailing slash from `proxy_pass` (important!)

### 🧩 Database Connection

Test connection manually:

```bash
psql postgresql://<username>:<password>@<host>:<port>/<dbname>
```

---

## 🔁 Updating the App

```bash
git pull
docker-compose -f docker-compose-local.yml up -d --build
```
