# IOM Proposal Drafter - Setup Guide

This document provides comprehensive setup instructions for the IOM Proposal Drafter application, covering both CI/CD deployment and local development paths.

## Architecture Overview

The application consists of four main components:
- Frontend (React/Vite)
- Backend (FastAPI with Python)
- Nginx Proxy (for routing between frontend and backend)
- Database (PostgreSQL)

## Prerequisites

1. Docker and Docker Compose
2. Azure subscription (for cloud deployment)
3. Azure CLI (for managing Azure resources)
4. Git
5. Node.js and npm (for local frontend development)
6. Python 3.11+ (for local backend development)

## Deployment Options

There are two main paths for deploying this application:

1. **Git-based CI/CD Pipeline** - For production environments
2. **Local Docker Development** - For development and testing

## Option 1: Git-based CI/CD Pipeline (Azure)

### 1. Set up Azure Resources

First, set up the necessary Azure resources:

```bash
# Login to Azure
az login

# Create resource group
az group create --name proposalgen-rg --location eastus

# Create Azure Container Registry (ACR)
az acr create --resource-group proposalgen-rg --name proposalgenacr --sku Basic --admin-enabled true

# Get ACR credentials
az acr credential show --name proposalgenacr
```

### 2. Deploy Azure Resources with Bicep

Use the Azure Bicep template to deploy all required resources:

```bash
# Deploy resources using bicep
az deployment group create \
  --resource-group proposalgen-rg \
  --template-file azure-resources.bicep \
  --parameters \
    baseName=proposalgen \
    dockerRegistryServerUrl=proposalgenacr.azurecr.io \
    dockerRegistryServerUsername=proposalgenacr \
    dockerRegistryServerPassword=<ACR-PASSWORD> \
    azureOpenAiEndpoint=<YOUR-OPENAI-ENDPOINT> \
    azureOpenAiApiKey=<YOUR-OPENAI-KEY> \
    openAiApiVersion=<YOUR-OPENAI-API-VERSION> \
    azureDeploymentName=<YOUR-DEPLOYMENT-NAME> \
    secretKey=<YOUR-SECRET-KEY> \
    postgresAdminPassword=<POSTGRES-ADMIN-PASSWORD>
```

### 3. Set up Azure DevOps Pipeline

1. Push your code to Azure DevOps repository:
   ```bash
   git remote add origin https://dev.azure.com/<org>/<project>/_git/<repo>
   git push -u origin main
   ```

2. Configure service connections in Azure DevOps:
   - Create an Azure Resource Manager service connection
   - Create a Docker Registry service connection to your ACR

3. Create a pipeline using the azure-pipelines.yml file in the repository:
   - Go to Pipelines > New Pipeline
   - Select Azure Repos Git
   - Select your repository
   - Select "Existing Azure Pipelines YAML file"
   - Select azure-pipelines.yml
   - Save and run

### 4. Set up the Database

```bash
# Run the database setup script
bash azure-db-setup.sh
```

## Option 2: Local Docker Development

### 1. Clone the Repository

```bash
git clone <repository-url>
cd proposal_drafter-dev
```

### 2. Set up Environment Variables

Create a .env file in the root directory:

```
# OpenAI settings
AZURE_OPENAI_ENDPOINT=<your-openai-endpoint>
AZURE_OPENAI_API_KEY=<your-openai-key>
OPENAI_API_VERSION=2023-07-01-preview
AZURE_DEPLOYMENT_NAME=gpt-4o

# Database settings
DB_USERNAME=iom_uc1_user
DB_PASSWORD=
DB_NAME=proposalgen
DB_HOST=db
DB_PORT=5432

# Security
SECRET_KEY=<your-secret-key>
```

### 3. Start the Application with Docker Compose

```bash
# Build and start all containers
docker-compose -f docker-compose-local.yml up --build
```

This will start:
- Frontend on http://localhost:8503
- Backend on http://localhost:8502
- PostgreSQL database on port 5432
- Redis cache on port 6379

### 4. Verify the Setup

1. Frontend should be accessible at http://localhost:8503
2. Backend health check should be accessible at http://localhost:8502/api/health_check
3. Database should be properly initialized with tables

## Database Setup Details

The application requires a PostgreSQL database with specific tables and users. Here's how to set it up:

### Database Schema

The database includes:
- `users` table for user authentication
- `proposals` table for storing proposal drafts

### Setting up the Database

#### Using the Setup Script (Recommended)

```bash
# For local development
docker-compose -f docker-compose-local.yml up -d db
sleep 10  # Wait for database to initialize
psql postgresql://postgres:postgres@localhost:5432/proposalgen -f database-setup.sql

# For Azure deployment
bash azure-db-setup.sh
```

#### Manual Setup

1. Connect to your PostgreSQL database:
   ```bash
   psql -U <username> -h <hostname> -d proposalgen
   ```

2. Run the SQL commands from database-setup.sql

## Development Workflow

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8502 --reload
```

## Troubleshooting

### Nginx Issues

If you encounter problems with the API not working:

1. Check nginx configuration:
   ```bash
   docker exec -it <nginx-container-id> cat /etc/nginx/conf.d/default.conf
   ```

2. Verify proxy_pass settings in nginx.conf:
   - Ensure the backend service name and port are correct
   - Remove trailing slashes in proxy_pass that can strip path prefixes

3. Check logs:
   ```bash
   docker logs <nginx-container-id>
   ```

### Database Connectivity Issues

If the application can't connect to the database:

1. Verify environment variables are correct
2. Test direct database connection:
   ```bash
   psql postgresql://<username>:<password>@<hostname>:<port>/<dbname>
   ```
3. Check firewall rules (for Azure)

### Container Networking

If containers can't communicate:

```bash
# Check container network
docker network ls
docker network inspect <network-name>

# Test connectivity from within a container
docker exec -it <container-id> ping <service-name>
```

## Maintenance

### Monitoring Logs

```bash
# View logs for a specific container
docker logs -f <container-id>

# View logs for all containers
docker-compose -f docker-compose-local.yml logs -f
```

### Updating the Application

```bash
# Pull latest code
git pull

# Rebuild and restart containers
docker-compose -f docker-compose-local.yml up -d --build
```