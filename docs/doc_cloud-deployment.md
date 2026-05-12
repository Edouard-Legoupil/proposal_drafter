# Deploying 'proposal_drafter' on different Cloud

# Azure Deployment Guide

This document outlines the recommended architecture and deployment strategy for the Project Proposal Generator application on Microsoft Azure. The proposed solution prioritizes scalability, security, and cost-effectiveness by leveraging Azure's modern cloud-native services.

## 1. Recommended Architecture

The recommended architecture uses a single-container model where the FastAPI backend serves the static React frontend files. This simplifies the deployment and management of the application.

| Component | Technology | Azure Service | Rationale |
| :--- | :--- | :--- | :--- |
| **Application** | FastAPI & React | **Azure Container Apps** | A serverless container service ideal for hosting web and API applications with automatic scaling and integrated CI/CD. |
| **Database** | PostgreSQL + `vector` | **Azure Database for PostgreSQL** | A fully managed PostgreSQL service that supports the `pgvector` extension, crucial for similarity search. |
| **Cache** | Redis | **Azure Cache for Redis** | A secure, in-memory data store for session management, improving application performance. |
| **AI Models**| GPT-4 & Embeddings | **Azure OpenAI Service** | Provides enterprise-grade access to powerful language models for inference and embedding tasks. |
| **AI/Search** | Serper | **External API (Serper)** | Leverages a powerful external service for web search capabilities. |

## 2. Deployment & CI/CD Strategy

The deployment is managed through Infrastructure as Code (IaC) using Bicep and a CI/CD pipeline using GitHub Actions. This approach ensures that deployments are automated, repeatable, and version-controlled.

- **Infrastructure as Code (IaC):** The Bicep templates in the `infra/` directory define all the necessary Azure resources. The templates are parameterized to allow for the deployment of different environment sizes (e.g., "Testing," "Expanded").
- **CI/CD Pipeline:** The GitHub Actions workflow in `.github/workflows/deploy.yml` automates the process of building the Docker image, pushing it to Azure Container Registry, and deploying the Bicep infrastructure.

For detailed instructions on manual deployment and the structure of the Bicep files, please refer to the `infra/README.md` file.

## 3. Cost Estimation

All cost estimates are based on the **Northern Europe** region and are subject to change.

### a. One-Time Setup Cost

This cost is incurred at the beginning of the project to populate the initial knowledge base.

- **Initial Document Embedding (1000 documents):**
  - **Total Tokens:** ~250,000,000
  - **Cost (text-embedding-3-large @ $0.13/1M tokens):** **~$32.50**
- **Initial Knowledge Card Creation (300 CrewAI runs):**
  - **Serper API (300 runs * 10 queries/run):** 3,000 queries @ $0.001/query = **$3.00**
  - **OpenAI API (300 runs * 75k tokens/run):** 22,500,000 tokens @ $10/1M tokens (GPT-4 Turbo) = **$225.00**
- **Total Estimated Setup Cost:** **~$260.50**

### b. Integrated Monthly Cost Scenarios (Based on Annual Proposal Volume)

The following scenarios provide an all-inclusive monthly cost estimate, combining Azure infrastructure and external API usage. The scenarios are defined by the number of proposals generated per year, with the costs presented as the monthly equivalent.

#### Scenario 1: Testing (100 proposals/year -> ~8/month)

- **Azure Infrastructure:**
  - **Container Apps (2 vCPU, 4 GiB):** ~$60
  - **PostgreSQL (Burstable, 2 vCores, 128 GiB):** ~$50
  - **Redis (Basic C0, 256 MB):** ~$25
- **API Usage:**
  - **Serper API (8 * 10 queries):** 80 queries = **~$0.08**
  - **OpenAI API (8 * 75k tokens):** 600,000 tokens = **$6.00**
- **Total Estimated Monthly Cost:** **~$141.08**
- **Estimated Cost Per Proposal:** **~$17.64**

#### Scenario 2: Exploratory (500 proposals/year -> ~42/month)

- **Azure Infrastructure:** (Same as Testing)
  - **Container Apps (2 vCPU, 4 GiB):** ~$60
  - **PostgreSQL (Burstable, 2 vCores, 128 GiB):** ~$50
  - **Redis (Basic C0, 256 MB):** ~$25
- **API Usage:**
  - **Serper API (42 * 15 queries):** 630 queries = **~$0.63**
  - **OpenAI API (42 * 100k tokens):** 4,200,000 tokens = **$42.00**
- **Total Estimated Monthly Cost:** **~$177.63**
- **Estimated Cost Per Proposal:** **~$4.23**

#### Scenario 3: Expanded (1500 proposals/year -> 125/month)

- **Azure Infrastructure:**
  - **Container Apps (4 vCPU, 8 GiB):** ~$120
  - **PostgreSQL (General Purpose, 2 vCores, 256 GiB):** ~$110
  - **Redis (Standard C1, 1 GB):** ~$60
- **API Usage:**
  - **Serper API (125 * 20 queries):** 2,500 queries = **$2.50**
  - **OpenAI API (125 * 125k tokens):** 15,625,000 tokens = **~$156.25**
- **Total Estimated Monthly Cost:** **~$448.75**
- **Estimated Cost Per Proposal:** **~$3.59**

#### Scenario 4: Organization-Wide (Targeting 1600 successful proposals/year)

*This scenario assumes a 30% success rate, requiring a total of ~5333 proposals to be generated annually, or ~444 per month.*

- **Azure Infrastructure:**
  - **Container Apps (8 vCPU, 16 GiB):** ~$240
  - **PostgreSQL (General Purpose, 4 vCores, 256 GiB):** ~$180
  - **Redis (Standard C1, 1 GB):** ~$60
- **API Usage:**
  - **Serper API (444 * 25 queries):** ~11,100 queries @ ~$0.00075/query = **~$8.33**
  - **OpenAI API (444 * 150k tokens):** ~66,600,000 tokens = **$666.00**
- **Total Estimated Monthly Cost:** **~$1,154.33**
- **Estimated Cost Per Generated Proposal:** **~$2.60**

## 4. Security & Compliance Recommendations

- **Authentication:** Integrate Azure Active Directory (AAD) for single sign-on (SSO).
- **Data Encryption:** Enable Transparent Data Encryption (TDE) for PostgreSQL and enforce SSL connections.
- **Networking:** Deploy services within a Virtual Network (VNet) for isolation.
- **Monitoring:** Use Azure Monitor and Application Insights for performance tracking and alerting.

# Google Cloud Run Platform

This section provides a guide to deploying the application to Google Cloud Platform (GCP) and includes a detailed cost analysis for different usage scenarios.

## 1. Recommended Architecture

| Component | Technology | Google Cloud Service |
| :--- | :--- | :--- |
| **Application** | FastAPI & React | **Cloud Run** |
| **Database** | PostgreSQL + `vector` | **Cloud SQL for PostgreSQL** |
| **Cache** | Redis | **Memorystore for Redis** |
| **AI Models**| GPT-4 & Embeddings | **Vertex AI** |
| **AI/Search** | Serper | **External API (Serper)** |

## 2. Cost Estimation (Google Cloud)

The following estimates are based on the **europe-west1** region and are subject to change.

### a. One-Time Setup Cost

- **Initial Document Embedding & Knowledge Card Creation:**
  - **Vertex AI & Serper API:** **~$260** (Similar to Azure, as API costs are dominant)

### b. Integrated Monthly Cost Scenarios (Based on Annual Proposal Volume)

#### Scenario 1: Testing (100 proposals/year -> ~8/month)

- **GCP Infrastructure:**
  - **Cloud Run (2 vCPU, 4 GiB):** ~$70
  - **Cloud SQL (db-g1-small):** ~$60
  - **Memorystore for Redis (Basic, 1 GB):** ~$30
- **API Usage:**
  - **Vertex AI & Serper API:** ~$6.08
- **Total Estimated Monthly Cost:** **~$166.08**
- **Estimated Cost Per Proposal:** **~$20.76**

#### Scenario 2: Exploratory (500 proposals/year -> ~42/month)

- **GCP Infrastructure:** (Same as Testing)
  - **Cloud Run, Cloud SQL, Memorystore:** ~$160
- **API Usage:**
  - **Vertex AI & Serper API:** ~$42.63
- **Total Estimated Monthly Cost:** **~$202.63**
- **Estimated Cost Per Proposal:** **~$4.82**

#### Scenario 3: Expanded (1500 proposals/year -> 125/month)

- **GCP Infrastructure:**
  - **Cloud Run (4 vCPU, 8 GiB):** ~$140
  - **Cloud SQL (db-n1-standard-2):** ~$130
  - **Memorystore for Redis (Standard, 1 GB):** ~$70
- **API Usage:**
  - **Vertex AI & Serper API:** ~$158.50
- **Total Estimated Monthly Cost:** **~$500.00**
- **Estimated Cost Per Proposal:** **~$4.00**

#### Scenario 4: Organization-Wide (Targeting 1600 successful proposals/year)

*This scenario assumes a 30% success rate, requiring a total of ~5333 proposals to be generated annually, or ~444 per month.*

- **GCP Infrastructure:**
  - **Cloud Run (8 vCPU, 16 GiB):** ~$280
  - **Cloud SQL (db-n1-standard-4):** ~$200
  - **Memorystore for Redis (Standard, 5 GB):** ~$150
- **API Usage:**
  - **Vertex AI & Serper API:** ~$674.33
- **Total Estimated Monthly Cost:** **~$1,304.33**
- **Estimated Cost Per Generated Proposal:** **~$2.94**

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