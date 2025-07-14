### Deploying 'proposal_drafter' on Google Cloud Platform

This tutorial provides a step-by-step guide to deploying the proposal_drafter application, consisting of a PostgreSQL database, FastAPI backend, React frontend, and Nginx, to Google Cloud Platform (GCP):

 * Database: Hosted on Cloud SQL for PostgreSQL.

 * Backend: Running as a serverless container on Cloud Run.

 * Frontend: Served as static files from Cloud Storage, optionally accelerated by Cloud CDN.

### 1. Prerequisites

Before you begin, ensure you have the following:

 * Google Cloud Account: A GCP account with billing enabled.

 * Google Cloud SDK (gcloud CLI): Installed and configured on your local machine. Install instructions: https://cloud.google.com/sdk/docs/install 

 * Docker: Installed on your local machine: Install instructions: https://docs.docker.com/get-docker/

 * Git: Installed on your local machine.

 * Node.js and npm/yarn: For building the React frontend.

### 2. Clone the Repository

First, clone your application's source code from GitHub:

```bash
git clone https://github.com/Edouard-Legoupil/proposal_drafter.git
cd proposal_drafter
```

### 3. Set Up Google Cloud Project

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


### 4. Deploy PostgreSQL Database (Cloud SQL)

We'll use Cloud SQL to host your PostgreSQL database.

#### 4.1 Create a Cloud SQL Instance

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




#### 4.2 Create a Database and User

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

### 5. Deploy FastAPI Backend (Cloud Run)

We'll containerize your FastAPI application and deploy it to Cloud Run.

#### 5.1 Prepare the FastAPI Application

Navigate to your backend directory:

```bash
cd backend
```


First, configure Docker to authenticate with Google Cloud's Artifact Registry (or Container Registry if you prefer). Artifact Registry is the newer, recommended service.

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

#### 5.3 Deploy to Cloud Run

Deploy the container image to Cloud Run, connecting it to your Cloud SQL instance.

```bash


# IMPORTANT: Before deploying, ensure the Cloud Run service account has Secret Manager permissions.
# The error "Permission denied on secret" means the service account needs the 'Secret Manager Secret Accessor' role.
# Follow these steps to grant the necessary permissions:

# 1. Get the Cloud Run service account email. This service account is automatically created.
#    Note: The service account name is usually in the format YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com
#    or sometimes default service account for Cloud Run, which is YOUR_PROJECT_NUMBER@cloudbuild.gserviceaccount.com.
#    To be sure, you can run:
SERVICE_ACCOUNT_EMAIL=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")-compute@developer.gserviceaccount.com
# Alternatively, if you've already attempted a deployment, you can get it from the failed revision's details:
# SERVICE_ACCOUNT_EMAIL=$(gcloud run services describe proposal-drafter-backend --platform managed --region europe-west1 --format="value(spec.template.spec.serviceAccountName)")

# 2. Grant the 'Secret Manager Secret Accessor' role to this service account on your secret.
#    Replace 'YOUR_PROJECT_ID' with your actual project ID.
gcloud secrets add-iam-policy-binding DB_USER_PASSWORD \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    --project=YOUR_PROJECT_ID # Explicitly specify the project where the secret is.

# 3. Now, proceed with the Cloud Run deployment command.
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

### 6. Deploy React Frontend 

We'll build your React application and serve the static files from a Cloud Storage bucket, optionally using Cloud CDN for performance.

#### 6.1 Build the React Application

Navigate to your frontend directory:

```bash
cd ../frontend
# Install dependencies and build the project:
npm install  
npm run build 
```

This will create a build/ directory containing your static HTML, CSS, and JavaScript files.


#### 6.2 Use github page for front end


#### 6.3 Alternative - Create a Cloud Storage Bucket (Option - Cloud Storage & Cloud CDN)

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

For HTTPS, you'd also need a gcloud compute ssl-certificates create and gcloud compute target-https-proxies.

Your frontend will now be accessible via the IP address of the load balancer.


To use your own domain (e.g., app.yourdomain.com), you'll need to configure DNS.


If you don't already manage your domain in Cloud DNS:

```bash
gcloud dns managed-zones create your-domain-zone \
    --dns-name="yourdomain.com." \
    --description="Managed zone for yourdomain.com"
```
Note the Name Servers provided by Cloud DNS and update your domain registrar's settings to use them.


For the Cloud Run backend, you can map a custom domain directly:
```bash
gcloud run domain-mappings create --service proposal-drafter-backend \
    --domain app.yourdomain.com \
    --platform managed \
    --region europe-west1
```
Follow the instructions provided by the command to create the necessary DNS records (CNAME or A/AAAA) in Cloud DNS.


If you set up Cloud CDN for your frontend, create an A record pointing to your Load Balancer's IP address:

```bash
gcloud dns record-sets create frontend.yourdomain.com. \
    --rrdatas="LOAD_BALANCER_IP_ADDRESS" \
    --type="A" \
    --ttl="300" \
    --zone="your-domain-zone"
```
Replace LOAD_BALANCER_IP_ADDRESS with the IP address you obtained earlier for the frontend load balancer.

### 7. Connect Frontend to Backend

Your React frontend needs to know the URL of your FastAPI backend.

#### 7.1 Update Frontend Environment Variables

In your React project, you likely use environment variables (e.g., .env files or REACT_APP_ variables) to configure the backend API URL.

Edit your frontend's configuration (e.g., frontend/.env.production or similar) to point to your Cloud Run backend URL:

```bash
# frontend/.env.production (example)
REACT_APP_API_URL=https://proposal-drafter-backend-xxxxxx-ew.a.run.app
```

Or, if you configured a custom domain:

```bash
REACT_APP_API_URL=https://api.yourdomain.com
```

Then, rebuild your frontend and re-upload the files to Cloud Storage as described in section 6.1 and 6.3.

```bash
cd ../frontend # if you're not already there
npm run build # or yarn build
gsutil -m cp -r dist/* gs://your-proposal-drafter-frontend-bucket/
```
#### 7.2 CORS Configuration

Ensure your FastAPI backend has appropriate CORS (Cross-Origin Resource Sharing) headers configured to allow requests from your frontend domain.

In your FastAPI main.py (or where you configure CORS):

```bash
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000", # For local development
    "https://storage.googleapis.com", # Default Cloud Storage domain (if not using CDN/custom domain)
    "https://your-proposal-drafter-frontend-bucket.appspot.com", # If using App Engine standard for static files
    "https://frontend.yourdomain.com", # Your custom frontend domain
    # Add the Cloud CDN IP if you're accessing via IP directly for testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ... your other FastAPI routes
```

Important: Be specific with your allow_origins in production to only include your actual frontend domains.

### Next Steps

* Monitoring & Logging: Explore Cloud Monitoring and Cloud Logging for insights into your application's performance and issues.

* CI/CD: Set up continuous integration and continuous deployment using Cloud Build to automate your deployment process.

* Security: Review IAM roles and permissions, consider using VPC Service Controls for enhanced network security, and regularly rotate database credentials using Secret Manager.

* Scaling: Adjust Cloud Run concurrency, CPU, and memory settings based on your traffic patterns. For Cloud SQL, consider increasing instance tiers or adding read replicas.

* Error Handling: Implement robust error handling and logging within your FastAPI application.

* Data Migration: If you have existing data, plan for data migration to Cloud SQL.