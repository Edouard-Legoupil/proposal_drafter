
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

### Step 4: Start the frontend

```bash
cd frontend
npm install
npm run dev
```

### Step 5: Start a PostgreSQL database

You can use Docker or local PostgreSQL:

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

# 3️⃣ Azure Deployment (Manual Steps)

## Step 1: Log into Azure and create resources

```bash
az login
az group create --name proposalgen-rg --location eastus
az acr create --resource-group proposalgen-rg --name proposalgen2acr --sku Basic --admin-enabled true
az acr credential show --name proposalgen2acr
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
    secretKey=<YOUR-SECRET-KEY> \
    postgresAdminPassword=<POSTGRES-ADMIN-PASSWORD>
```

## Step 4: Set up Azure database

```bash
bash azure-db-setup.sh
```

---

# 4️⃣ GitHub CI/CD Workflow (Recommended)

### Step 1: Push to GitHub

```bash
git remote add origin https://github.com/<your-org>/<your-repo>.git
git push -u origin main
```

### Step 2: Set up GitHub Secrets

In your GitHub repo, go to **Settings > Secrets and Variables > Actions**, and add:

- `AZURE_CREDENTIALS` (from `az ad sp create-for-rbac`)
- `ACR_USERNAME`
- `ACR_PASSWORD`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `SECRET_KEY`
- `POSTGRES_ADMIN_PASSWORD`

### Step 3: Add GitHub Actions workflow file

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Build and Push Backend
        run: |
          docker build -t proposalgen-backend ./backend
          echo "${{ secrets.ACR_PASSWORD }}" | docker login proposalgen2acr.azurecr.io -u ${{ secrets.ACR_USERNAME }} --password-stdin
          docker tag proposalgen-backend proposalgen2acr.azurecr.io/proposalgen-backend:latest
          docker push proposalgen2acr.azurecr.io/proposalgen-backend:latest

      # Repeat for frontend and nginx as needed
```

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
