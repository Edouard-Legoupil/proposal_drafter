
# 🚀 Proposal Drafter - Setup Guide

This guide walks you through progressive steps for setting up the **Proposal Drafter** application:

1. **Local development (no Docker)**
2. **Docker-based development**






## 🧱 Application Overview

The app has four core components:
- 🖼 **Frontend** – React + Vite
- 🧠 **Backend** – FastAPI (Python)
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
git clone https://github.com/edouard-legoupil/proposal_drafter.git
cd proposal_drafter
```

### Step 2: Start a PostgreSQL database

You can use a local [PostgreSQL](https://www.postgresql.org/download/).

`psql` client will be then required (you can install it with `sudo apt-get update && sudo apt-get install -y postgresql-client`)

Once installed, Run setup script:

```bash
psql postgresql://postgres:postgres@localhost:5432/proposalgen -f db/database-setup.sql

# Load the test data
psql postgresql://postgres:postgres@localhost:5432/proposalgen -f db/seed.sql
```


### Step 3: Set Environment Variables



The application uses environment variables for configuration. You can find a list of the required variables in `backend/.env.example`. Create a `.env` file in this directory with your own values when running locally.


Create `backend/.env` from `backend/.env.example` and replace every placeholder:


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

### Step 4: Start the backend

Run the backend from the repository root so the `backend` package resolves correctly:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
set -a
source backend/.env
set +a
uvicorn backend.main:app --host 0.0.0.0 --port 8502 --reload
```

Open http://localhost:8502/health to verify the service is running. A minimal liveness endpoint is available at
http://localhost:8502/healthz.

### Step 5: Start the frontend

Open a new terminal to launch the second part of the application.

```bash
cd frontend
npm install
npm run dev
```

The application should now be running at http://localhost:8503

### Running everything together

for further deployment, it is easier if both frontend and backend run on the same fastapi process. To do so the frontend is loaded as static page within fastapi. This part is managed through a provided `start.sh` script that you can laumch with:

```bash
./start.sh
```

The application should now be running at http://localhost:8502

---

# 2️⃣ Local Docker Development

Before getting here, stop the backend and frontend servers you started in the previous step. (ctrl + c).

On windows, You can use [Docker Destop](https://docs.docker.com/desktop/setup/install/windows-install/) for this step, or use the [Docker CLI](https://docs.docker.com/engine/install/) if you prefer.

### Step 1: Start Docker containers

A specific `docker-compose-local.yml` file is provided to run the application locally with Docker. This file includes services for the frontend, backend, PostgreSQL database, and Redis.
Make sure you have Docker and Docker Compose installed.

Create a `.env` file in the `root` directory - see `.env.example` for reference:

Run the checked-in Compose stack, which includes PostgreSQL:

```bash
docker-compose  --env-file .env -f docker-compose-local.yml up --build
```

Services:
- Frontend: http://localhost:8503
- Backend: http://localhost:8502/health
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Step 2: Run database setup

```bash
sleep 10
psql postgresql://postgres:postgres@localhost:5432/proposalgen -f db/database-setup.sql
```

Congrat if you have everything working locally, you can go to the next step - getting this on the cloud:

For cloud deployment, see [the cloud deployment guide](doc_cloud-deployment.md).

For browser tests, see [the Playwright guide](../playwright/README.md).


## Test

```bash
cd frontend && npm run lint && npm run test -- --run && npm run build
set -a && source backend/.env && set +a && pytest backend/tests
```
