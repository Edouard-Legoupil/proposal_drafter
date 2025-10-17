# Deploying 'proposal_drafter' on different Cloud





# Azure Platform

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

## GitHub CI/CD Workflow Automation

This section sets up a CI/CD pipeline using GitHub Actions to automate deployments to Azure whenever you push changes to the repository.

### Step 1: Set up GitHub Secrets

In your GitHub repo, go to **Settings > Secrets and Variables > Actions**, and add the elemnts defining the target Azure Infrastructure::

- `AZURE_CREDENTIALS` (from `az ad sp create-for-rbac`)
- `REGISTRY_LOGIN_SERVER` -- # Must end with .azurecr.io
- `REGISTRY_USERNAME` -- az acr credential show --name <your-acr-name> --query "{username: username, password: passwords[0].value}"
- `REGISTRY_PASSWORD` -- same as above
- `AZURE_WEBAPP_PUBLISH_PROFILE`  -- you can get this from the Azure Portal > App Service > Get Publish Profile
- `AZURE_WEBAPP_NAME` -- the name of your Azure Web App



### Step 2: Application Settings (Environment Variables)

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

### Step 3: GitHub Actions workflow file

The script `.github/workflows/deploy.yml` orchestrates the CI/CD pipeline.

Note that you main need to verify that the `docker-compose.yml` file is correctly set up to use the environment variables defined in the Azure App Service and check that you container registry can be accessed by Github Actions.
az acr update --name <your-acr-name> --public-network-enabled true  

### Step 4: Push to GitHub

```bash
git remote add origin https://github.com/edouard-legoupil/proposal_drafter.git
git push -u origin main
```


If the workflow is set up correctly, it will automatically build and deploy the application to Azure whenever you push changes to the `main` branch.

If the target application in azure does not start correctly, you can check the logs in the Azure Portal > App Service > Log Stream.


```bash
## check the log of the app service using the Azure CLI:
az webapp log tail --name <your-app-name> --resource-group <your-resource-group>
## Check if it is actually deployed
az webapp config container show \
  --name <your-app-name> \
  --resource-group <your-resource-group> \
  --query "[name, image]"
```

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




# Google Cloud Run Platform

This tutorial provides a step-by-step guide to deploying the proposal_drafter application, consisting of a PostgreSQL database, FastAPI backend, React frontend, and Nginx, to Google Cloud Platform (GCP):

 * Database: Hosted on Cloud SQL for PostgreSQL.

 * Backend: Running as a serverless container on Cloud Run.

 * Frontend: Served as static files from github pages or Cloud Storage, optionally accelerated by Cloud CDN.

## 1. Prerequisites

Before you begin, ensure you have the following:

 * Google Cloud Account: A GCP account with billing enabled.

 * Google Cloud SDK (gcloud CLI): Installed and configured on your local machine. Install instructions: https://cloud.google.com/sdk/docs/install 

 * Docker: Installed on your local machine: Install instructions: https://docs.docker.com/get-docker/

 * Git: Installed on your local machine.

 * Node.js and npm/yarn: For building the React frontend.

## 2. Clone the Repository

First, clone your application's source code from GitHub:

```bash
git clone https://github.com/Edouard-Legoupil/proposal_drafter.git
cd proposal_drafter
```

## 3. Set Up Google Cloud Project

If you don't have a project, create one:


```bash
## Initialize connection 
gcloud init
gcloud projects create YOUR_PROJECT_ID --name="Your Proposal Drafter Project"

## ou can also check your existing project with
gcloud projects list
gcloud config set project YOUR_PROJECT_ID
```

Replace YOUR_PROJECT_ID with a unique ID for your project.

Enable necessary APIs:


```bash
gcloud services enable sqladmin.googleapis.com \
                       run.googleapis.com \
                       artifactregistry.googleapis.com \
                       cloudbuild.googleapis.com \
                       storage.googleapis.com \
                       compute.googleapis.com \
                       dns.googleapis.com

```

https://console.cloud.google.com/flows/enableapi?apiid=sqladmin&redirect=https://console.cloud.google.com

## 4. Deploy PostgreSQL Database (Cloud SQL)

We'll use Cloud SQL to host your PostgreSQL database.

### 4.1 Create a Cloud SQL Instance

```bash
gcloud sql instances create proposal-drafter-db \
    --database-version=POSTGRES_14 \
    --region=europe-west1 \
    --tier=db-f1-micro \
    --root-password=YOUR_DB_ROOT_PASSWORD \
    --database-flags=cloudsql.iam_authentication=On
```

Replace `YOUR_DB_ROOT_PASSWORD` with a strong password.

Choose a region close to your users (e.g., europe-west1).

`db-f1-micro` is a cost-effective tier for development/testing. Adjust for production.
`cloudsql.iam_authentication=On` is recommended for more secure connections.

Once created you can check  the Connection Name for your Cloud SQL instance
```bash
gcloud sql instances describe proposal-drafter-db --format="value(connectionName)"
```

It will look something like `YOUR_PROJECT_ID:europe-west1:proposal-drafter-db`.

if you want to connect to your DB with a local client like pgadmin4, Download and Install [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy), then run the below (
you may use a different port- for instance 5431- if you have already postgres running on your machine)

```bash
gcloud auth application-default login

./cloud-sql-proxy --port 5431 YOUR_PROJECT_ID:europe-west1:proposal-drafter-db 
```

### 4.2 Create a Database and User

Connect to your Cloud SQL instance using the gcloud sql connect command or the Cloud SQL Proxy (recommended for local development/testing).


```bash
# Connect using gcloud (requires gcloud sql connect component)
gcloud sql connect proposal-drafter-db --user=postgres

# Once connected, run SQL commands from database-setup.sql
```

Replace YOUR_DB_USER_PASSWORD with a strong password for your application user.

Alternatively, you can create a user and database directly via gcloud commands:

```bash
gcloud sql databases create proposal_drafter --instance=proposal-drafter-db
gcloud sql users create proposal_user --instance=proposal-drafter-db \
    --password=YOUR_DB_USER_PASSWORD --host=%
```
 
Note that the connection string is slightly different if using cloudd SQl than local settings - this is managed within main.py by checking if we have 

`if os.getenv("GAE_ENV") == "standard" or os.getenv("K_SERVICE"): # Running on Cloud Run/App Engine`


### 4.3 Set up  IAM Authentication

* Go to the [Cloud SQL Instances page](https://console.cloud.google.com/sql/) in the GCP Console.

* Click on your instance ID.

* In the left navigation, click on Authentication.

* Under "IAM authentication", ensure Allow IAM authentication for all connections is checked. If not, check it and save.

you should see --  
Database flags and parameters 
cloudsql.iam_authentication on -

 

Next create a service account that your containerized application will use to authenticate with Cloud SQL and grant it access.

```bash
gcloud iam service-accounts create cloud-sql-connector-sa     --display-name "Service Account for Cloud SQL Connector"

## give permission
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member "serviceAccount:cloud-sql-connector-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role "roles/cloudsql.client"

## Check
gcloud iam service-accounts list --project YOUR_PROJECT_ID
```
From the last step, take note of the email of your newly created user

Now, you need to add this service account as an IAM user to your Cloud SQL database.

* On the the Cloud SQL Instances page , in the left navigation, click on Users.

* Click Add user account.

* Select Cloud IAM.

*   For "Principal type", select Service account.

* For "Principal", enter the full service account email: `cloud-sql-connector-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com` and  Click Add.

Before deploying, ensure the Cloud Run service account has Secret Manager permissions. The error "Permission denied on secret" means the service account needs the 'Secret Manager Secret Accessor' role.

```bash
gcloud secrets add-iam-policy-binding DB_USER_PASSWORD \
    --member="serviceAccount:cloud-sql-connector-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com"  \
    --role="roles/secretmanager.secretAccessor" \
    --project=YOUR_PROJECT_ID  
```


Now you need to give access to this user to the specific database created in the previous step 

```sql
GRANT CONNECT ON DATABASE proposal TO "cloud-sql-connector-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com";
GRANT USAGE ON SCHEMA public TO "cloud-sql-connector-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "cloud-sql-connector-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "cloud-sql-connector-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com";

```


## 5. Deploy FastAPI Backend (Cloud Run)

We'll containerize your FastAPI application and deploy it to Cloud Run.



### 5.1 Prepare the FastAPI Application

Navigate to your backend directory:

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

You can test that it is working with
```bash
uvicorn main:app --host 0.0.0.0 --port 8502 --reload
```

### 5.2 Deploy to Cloud Run with Docker Registry

Loging to your docker desktop and configure Docker to authenticate with Container Registry 

```bash
gcloud auth configure-docker
```

Now build and push your container

```bash
docker build -t gcr.io/YOUR_PROJECT_ID/proposal_drafter-app:v1 .
docker push gcr.io/YOUR_PROJECT_ID/proposal_drafter-app:v1
```

Finally deploy  your container to Cloud Run, ensuring it uses the service account created earlie and with your environment variables

```bash
gcloud run deploy proposal_drafter-service \
    --image gcr.io/YOUR_PROJECT_ID/proposal_drafter-app:v1 \
    --platform managed \
    --region YOUR_GCP_REGION \
    --no-allow-unauthenticated \
    --service-account cloud-sql-connector-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars INSTANCE_CONNECTION_NAME="YOUR_PROJECT_ID:YOUR_GCP_REGION:YOUR_CLOUD_SQL_INSTANCE_NAME" \
    --set-env-vars DB_USER="cloud-sql-connector-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --set-env-vars DB_NAME="YOUR_DATABASE_NAME" # etc.
## you can check what env variables were deployed with
gcloud run services describe proposaldrafter-service \
  --region=YOUR_GCP_REGION \
  --format="value(spec.template.spec.containers[0].env)"

```



### 5.3 Deploy to Cloud Run with Artifact Registry
 
Alternatively, you can have Docker to authenticate with **Google Cloud's Artifact Registry**. Artifact Registry is the newer, recommended service.

```bash
# Set your preferred region for Artifact Registry (e.g., europe-west1)
export AR_REGION=europe-west1

# Create a Docker repository in Artifact Registry
gcloud artifacts repositories create proposal-drafter-backend \
    --repository-format=docker \
    --location=$AR_REGION \
    --description="Docker repository for proposal-drafter backend"

# Configure Docker to use gcloud as a credential helper
gcloud auth configure-docker $AR_REGION-docker.pkg.dev
```

Now, build your Docker image and push it:

```bash
# Navigate back to the root of your project if you're in the backend directory
# cd .. # if you were in backend/

# Build the Docker image (make sure you are in the root of your project or specify context)
docker build -t $AR_REGION-docker.pkg.dev/YOUR_PROJECT_ID/proposal-drafter-backend/api:latest ./backend

# Push the image to Artifact Registry
docker push $AR_REGION-docker.pkg.dev/YOUR_PROJECT_ID/proposal-drafter-backend/api:latest
```

You can see you artefact registry here: https://console.cloud.google.com/artifacts


Deploy the container image to Cloud Run, connecting it to your Cloud SQL instance.



Now, proceed with the Cloud Run deployment command.

```bash
gcloud run deploy proposal-drafter-backend \
    --image $AR_REGION-docker.pkg.dev/YOUR_PROJECT_ID/proposal-drafter-backend/api:latest \
    --platform managed \
    --region europe-west1 \
    --allow-unauthenticated \
    --add-cloudsql-instances YOUR_PROJECT_ID:europe-west1:proposal-drafter-db \
    --set-env-vars DB_USER=proposal_user,DB_NAME=proposal_drafter,CLOUD_SQL_CONNECTION_NAME=YOUR_PROJECT_ID:europe-west1:proposal-drafter-db \
    # Use Secret Manager for production!
    --update-secrets DB_PASSWORD=DB_USER_PASSWORD:latest 
```

--allow-unauthenticated: Makes the service publicly accessible. For production, consider using Identity-Aware Proxy (IAP) or internal access.

--add-cloudsql-instances: Connects your Cloud Run service to the Cloud SQL instance.

--set-env-vars: Sets environment variables for your application.

--update-secrets DB_PASSWORD=DB_USER_PASSWORD:latest: Crucially, use Google Secret Manager for sensitive data like database passwords in production.


To use Secret Manager:

* Create the secret:

* echo "YOUR_DB_USER_PASSWORD" | gcloud secrets create DB_USER_PASSWORD --data-file=-

Grant Cloud Run service account access to the secret:

```bash
# Get the Cloud Run service account email
SERVICE_ACCOUNT=$(gcloud run services describe proposal-drafter-backend --platform managed --region europe-west1 --format="value(spec.template.spec.serviceAccountName)")
gcloud secrets add-iam-policy-binding DB_USER_PASSWORD \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"
```

Then, in your gcloud run deploy command, use --update-secrets DB_PASSWORD=DB_USER_PASSWORD:latest.

After deployment, Cloud Run will provide a URL for your backend service (e.g., https://proposal-drafter-backend-xxxxxx-ew.a.run.app). Note this URL.



## 6. Deploy React Frontend 

We'll build your React application and serve the static files from a Cloud Storage bucket, optionally using Cloud CDN for performance.

### 6.1 Build the React Application

Navigate to your frontend directory:

```bash
cd ../frontend
# Install dependencies and build the project:
npm install  
npm run build 
```

This will create a build/ directory containing your static HTML, CSS, and JavaScript files.


### 6.2 Use github page for front end (simpple)


* Install `gh-pages`: Run `npm install gh-pages --save-dev`.

*in your `package.json`, add the following script - `"predeploy": "npm run build",  "deploy": "gh-pages -d dist -b pages"` and `"homepage": "https://edouard-legoupil.github.io/proposal_drafter/"` .

* Update `vite.config.js`: Add `base: '/proposal_drafter/'` to your defineConfig object.

* Deploy: Run `npm run deploy`.

Configure GitHub Pages: Go to your repository settings on GitHub, navigate to "Pages," and ensure the source is set to "Deploy from a branch" and `pages` branch.

### 6.3 Alternative - Create a Cloud Storage Bucket & CDN (more complex)

Create a bucket to host your static files. The bucket name must be globally unique.

```bash
gsutil mb -l europe-west1 gs://your-proposal-drafter-frontend-bucket
```

Replace your-proposal-drafter-frontend-bucket with a unique name.

Upload the contents of your dist/ directory to the bucket:

```bash
gsutil -m cp -r dist/* gs://your-proposal-drafter-frontend-bucket/
```

Set the bucket as a static website host and make its contents publicly readable:

```bash
gsutil web set -m index.html -e index.html gs://your-proposal-drafter-frontend-bucket
gsutil iam ch allUsers:objectViewer gs://your-proposal-drafter-frontend-bucket
```

Your frontend will now be accessible via a URL like https://storage.googleapis.com/your-proposal-drafter-frontend-bucket/index.html.



To improve performance and reduce latency for your users, enable Cloud CDN for your bucket. This requires setting up a Load Balancer.

Create a Backend Bucket:
```bash
gcloud compute backend-buckets create proposal-drafter-frontend-backend \
    --gcs-bucket-name=your-proposal-drafter-frontend-bucket \
    --enable-cdn
```
Create a URL Map:
```bash
gcloud compute url-maps create proposal-drafter-url-map \
    --default-backend-bucket=proposal-drafter-frontend-backend
```
Create a Global External IP Address:
```bash
gcloud compute addresses create proposal-drafter-frontend-ip --global
```
Note the IP address: gcloud compute addresses describe proposal-drafter-frontend-ip --global --format="value(address)"

Create an HTTP(S) Load Balancer:

```bash
gcloud compute target-http-proxies create proposal-drafter-http-proxy \
    --url-map=proposal-drafter-url-map

gcloud compute forwarding-rules create proposal-drafter-http-rule \
    --address=proposal-drafter-frontend-ip \
    --global \
    --target-http-proxy=proposal-drafter-http-proxy \
    --ports=80
```

For HTTPS, you'd also need a gcloud compute ssl-certificates create and gcloud compute target-https-proxies. Your frontend will now be accessible via the IP address of the load balancer.

To use your own domain (e.g., app.yourdomain.com), you'll need to configure DNS. If you don't already manage your domain in Cloud DNS:

```bash
gcloud dns managed-zones create your-domain-zone \
    --dns-name="yourdomain.com." \
    --description="Managed zone for yourdomain.com"
```
Note the Name Servers provided by Cloud DNS and update your domain registrar's settings to use them. For the Cloud Run backend, you can map a custom domain directly:

```bash
gcloud run domain-mappings create --service proposal-drafter-backend \
    --domain app.yourdomain.com \
    --platform managed \
    --region europe-west1
```
Follow the instructions provided by the command to create the necessary DNS records (CNAME or A/AAAA) in Cloud DNS. If you set up Cloud CDN for your frontend, create an A record pointing to your Load Balancer's IP address:

```bash
gcloud dns record-sets create frontend.yourdomain.com. \
    --rrdatas="LOAD_BALANCER_IP_ADDRESS" \
    --type="A" \
    --ttl="300" \
    --zone="your-domain-zone"
```
Replace LOAD_BALANCER_IP_ADDRESS with the IP address you obtained earlier for the frontend load balancer.

## 7. Connect Frontend to Backend


### 7.1 Update Frontend Environment Variables

Your React frontend needs to know the URL of your FastAPI backend.
In your React project, you likely use environment variables (e.g., .env files or REACT_APP_ variables) to configure the backend API URL.

Edit your frontend's configuration (e.g., frontend/.env.production or similar) to point to your Cloud Run backend URL:

```bash
# frontend/.env.production (example)
VITE_BACKEND_URL=https://proposal-drafter-backend-xxxxxx-ew.a.run.app
```

Or, if you configured a custom domain:

```bash
VITE_BACKEND_URL=https://api.yourdomain.com
```

Then, rebuild your frontend and re-upload the files to Cloud Storage as described in section 6.1 and 6.3.

```bash
cd ../frontend # if you're not already there
npm run build  
gsutil -m cp -r dist/* gs://your-proposal-drafter-frontend-bucket/
```
### 7.2 CORS Configuration

Ensure your FastAPI backend has appropriate CORS (Cross-Origin Resource Sharing) headers configured to allow requests from your frontend domain.

In `main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
     "http://localhost:8503", # For local development
     "https://edouard-legoupil.github.io/proposal_drafter/", ## if using frontend hosted on github page
    "https://storage.googleapis.com", # Default Cloud Storage domain (if not using CDN/custom domain)
    "https://your-proposal-drafter-frontend-bucket.appspot.com", # If using App Engine standard for static files
    "https://frontend.yourdomain.com", # Your custom frontend domain
    # Add the Cloud CDN IP if you're accessing via IP directly for testing
]

```

Important: Be specific with your allow_origins in production to only include your actual frontend domains.


## 8. CI/CD deployment script from github

Google Cloud Setup: Workload Identity Federation (WIF): You need to have Workload Identity Federation set up in your GCP project.

Create a Workload Identity Pool: 

```bash
gcloud iam workload-identity-pools create github-pool --location=global --display-name="GitHub Actions Pool"
```

Create a Provider within the pool: 

```bash
gcloud iam workload-identity-pools providers create-oidc github-provider --location=global --workload-identity-pool=github-pool --display-name="GitHub Actions Provider" --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" --issuer-uri="https://token.actions.githubusercontent.com"


gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --display-name="GitHub Actions Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-condition="attribute.repository_owner == 'YOUR_GITHUB_ORG' && attribute.repository == 'YOUR_REPO_NAME'"
```

Grant the necessary permissions to your SERVICE_ACCOUNT on the Workload Identity Pool (e.g., roles/run.admin, roles/artifactregistry.writer, roles/iam.serviceAccountUser).

gcloud projects describe YOUR_PROJECT_ID_ALPHANUMERIC --format="value(projectNumber)"

```bash
## First get your project numeric id
gcloud projects describe YOUR_PROJECT_ID_ALPHANUMERIC --format="value(projectNumber)"

gcloud iam service-accounts add-iam-policy-binding YOUR_SERVICE_ACCOUNT_EMAIL  --member="principalSet://iam.googleapis.com/projects/NUMERIC_PROJECT_ID/locations/global/workloadIdentityPools/github-pool/attribute.repository/YOUR_GITHUB_ORG/YOUR_REPO_NAME"  
```

Ensure the service_account used in the workflow (github-actions-sa@${{ env.PROJECT_ID }}.iam.gserviceaccount.com) exists and has the necessary roles for Cloud Run deployment and Artifact Registry access.

Artifact Registry: Create a Docker repository in Artifact Registry in the specified GAR_LOCATION (e.g., 

gcloud artifacts repositories create proposalgen-backend --repository-format=docker --location=europe-west1 --description="Docker repository for proposalgen backend").

 The BACKEND_SERVICE_NAME is used here.


## Next Steps

* Monitoring & Logging: Explore Cloud Monitoring and Cloud Logging for insights into your application's performance and issues.

* CI/CD: Set up continuous integration and continuous deployment using Cloud Build to automate your deployment process.

* Security: Review IAM roles and permissions, consider using VPC Service Controls for enhanced network security, and regularly rotate database credentials using Secret Manager.

* Scaling: Adjust Cloud Run concurrency, CPU, and memory settings based on your traffic patterns. For Cloud SQL, consider increasing instance tiers or adding read replicas.

* Error Handling: Implement robust error handling and logging within your FastAPI application.

* Data Migration: If you have existing data, plan for data migration to Cloud SQL.