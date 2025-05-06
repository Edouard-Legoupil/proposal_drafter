# IOM - Proposal Generator  

## Brief Introduction  
An agentic AI application to help generate project proposals for IOM.  

## Table of Contents

1. [Prerequisites](#prerequisites)

2. [Local Development Setup](#local-development-setup)
   - [Backend Setup](#backend-setup)
   - [Frontend Setup](#frontend-setup)

3. [Docker Configuration](#docker-configuration)

4. [Azure Deployment](#azure-deployment)
   - [Resource Creation](#resource-creation)
   - [Container Registry Setup](#container-registry-setup)

5. [CI/CD Pipeline](#cicd-pipeline)
   - [GitHub Secrets](#github-secrets)
   - [Workflow Configuration](#workflow-configuration)

6. [Post-Deployment](#post-deployment)
   - [Accessing the App](#accessing-your-app)
   - [Troubleshooting](#troubleshooting)

## Prerequisites

- **GitHub Account** with your project repository
- **Python 3.9+** with Uvicorn installed
- **Node.js 16+** for React development
- **Azure Account** with active subscription
- **Azure CLI** installed (`az` command)
- **Docker** for containerization

Once you have this clone this repository.

## Local Development Setup

### Backend Setup

Go to the backend folder:

```bash
cd backend
```

We need to use a virtual environment in Python development. This is essential for managing dependencies, avoiding conflicts, and ensuring reproducibility. It allows you to isolate project-specific libraries and versions, preventing interference with other projects or the global Python installation. This isolation helps maintain a clean development environment, simplifies project setup for collaborators, and enhances security by reducing the risk of introducing vulnerabilities. Overall, virtual environments provide a consistent and organized way to manage your Python projects effectively.

Make sure to install the last [stable version of python language](https://www.python.org/downloads/) and create a dedicated python environment to have a fresh install where to manage correctly all the dependencies between packages. To specify a particular version of Python when creating a virtual environment, you can use the full path to the desired Python executable. Here is how you can do it:

Open your terminal (Command Prompt, PowerShell, or any terminal emulator).

Navigate to your project directory where you want to create the virtual environment.

Run the following command to create a virtual environment,here called **`.venv`**:

```bash
python -m venv .venv`
```
Then, activate the virtual environment:

```bash
# On Windows:
.\.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

Install the required python packages using:

```bash
pip install -r requirements.txt   
```

Now configure the environment variables. This assumes you have already created an Azure OpenAI resource and have the necessary keys and endpoints.

Create a file called **`.env`** in the backend directory and add the following lines to [configure crewai with Azure OpenAI](https://blog.crewai.com/configuring-azure-openai-with-crewai-a-comprehensive-guide/):

```bash
# Azure OpenAI Configuration
AZURE_API_KEY=your-api-key # Replace with KEY1 or KEY2
AZURE_API_BASE=https://example.openai.azure.com/  # Replace with your endpoint
AZURE_API_VERSION=2024-08-01-preview # API version
AZURE_DEPLOYMENT_NAME=your-deployment-name # Replace with your deployment name

```


Test run the server with

```bash 
uvicorn main:app --host 0.0.0.0 --port 8502 --reload
```

### Frontend Setup

Open a new terminal and go to the frontend folder:

```bash
cd frontend
```

Create environment file (.env) that contains the API URL for the backend server. This file is used to store environment variables that can be accessed in the React application. The `.env` file should be located in the root of your React project. Create a file called **`.env`** in the frontend directory and add the following line:
```bash
echo "VITE_API_URL=http://localhost:8502  # For local development" > .env
```

Install dependencies using npm:
```bash
npm install
```

Build the frontend server:
```bash
npm run build
```

Start development server:
```bash
npm run dev 
```

## Docker Configuration

We have two Dockerfiles, one for the backend and one for the frontend. The backend is a FastAPI application, and the frontend is a React application. Then `docker-compose.yml` brings the two components together.

How to Verify that the dockerisation Works?
Use Docker Desktop with admin privileges, login without your account and then generate the image to check that the image is built correctly. From your project root, run:

```bash
docker-compose up --build
```

Check that:

* Backend becomes available at http://localhost:8501
* Frontend appears at http://localhost


## CI/CD Pipeline

Create Azure service principal:

```bash
az ad sp create-for-rbac --name MyAppSP \
                         --role contributor \
                         --scopes /subscriptions/<sub-id>/resourceGroups/ProposalDrafter \
                         --sdk-auth
```

Add these secrets to GitHub so that the workflow can access them and the docker images can be pushed to the Azure Container Registry.
Go to your GitHub repository, click on **Settings** > **Secrets and variables** > **Actions** > **New repository secret**.

 * AZURE_CREDENTIALS: Output from above command

 * REGISTRY_LOGIN_SERVER: myappregistry.azurecr.io

 * REGISTRY_USERNAME: ACR username

 * REGISTRY_PASSWORD: ACR password

 Workflow Configuration is done through `.github/workflows/deploy.yml`. When ever there is a push to the main branch, the workflow will be triggered. It builds the Docker images for both frontend and backend, pushes them to Azure Container Registry, and deploys them to Azure App Service.

## Post-Deployment

### Accessing the App

 * Frontend: https://myapp-frontend.azurewebsites.net

 * Backend API: https://myapp-backend.azurewebsites.net

### Troubleshooting

Check logs:
```bash
az webapp log tail --name myapp-backend --resource-group ProposalDrafter
```

Verify deployment:
```bash
az webapp config container list --name myapp-backend --resource-group ProposalDrafter
```

Common issues:

* Port mismatch: Verify WEBSITES_PORT matches your Uvicorn port

* CORS errors: Configure FastAPI CORS middleware

*  Database connections: Verify connection strings