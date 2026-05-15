# Quickstart Guide: Proposal Drafter

**Version:** 1.0
**Date:** 2025-05-13
**Input:** Feature specification from `/specs/001-proposal_drafter/spec.md`
**Purpose:** Phase 1 - Quickstart Guide

---

## 🚀 Getting Started with Proposal Drafter

This guide will help you set up and run the Proposal Drafter system locally for development and testing.

---

## Prerequisites

Before you begin, ensure you have the following installed on your system:

### Required Software

| Software | Version | Purpose | Verification |
|----------|---------|---------|--------------|
| Git | 2.x+ | Version control | `git --version` |
| Python | 3.10+ | Backend runtime | `python --version` or `python3 --version` |
| Node.js | 18.x+ | Frontend runtime | `node --version` |
| npm | 9.x+ | JavaScript package manager | `npm --version` |
| PostgreSQL | 15+ | Primary database | `psql --version` |
| Redis | 7+ | Session storage & cache | `redis-cli --version` |
| Docker | 20.x+ | Containerization | `docker --version` |
| Docker Compose | 2.x+ | Multi-container orchestration | `docker-compose --version` |

### Python Dependencies

```bash
# Recommended: Use a Python virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR on Windows:
# venv\Scripts\activate
```

### Node.js Dependencies

No global Node.js packages required beyond npm.

---

## Installation

### Option 1: Docker Compose (Recommended)

The easiest way to get started is using Docker Compose, which sets up all services:

```bash
# Clone the repository
git clone https://github.com/your-org/proposal-drafter.git
cd proposal-drafter

# Start all services (backend, frontend, PostgreSQL, Redis)
docker-compose -f docker-compose-local.yml up --build

# Or for production-like setup:
docker-compose -f docker-compose-local.yml up --build -d
```

**Services Started:**
- Backend: `http://localhost:8502`
- Frontend: `http://localhost:3000`
- PostgreSQL: `localhost:5432` (user: postgres, password: postgres, db: proposalgen)
- Redis: `localhost:6379`

**Access the application:**
- Open your browser to `http://localhost:3000`
- The frontend will proxy API requests to the backend

### Option 2: Manual Installation

If you prefer to run services manually:

#### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor

# Initialize database (see Database Setup below)

# Start backend server
uvicorn main:app --host 0.0.0.0 --port 8502 --reload
```

**Backend runs at:** `http://localhost:8502`

#### 2. Frontend Setup

```bash
# Navigate to frontend directory (in a new terminal)
cd frontend

# Install Node.js dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env

# Start frontend development server
npm run dev
```

**Frontend runs at:** `http://localhost:3000`

#### 3. Database Setup

```bash
# Connect to PostgreSQL
psql postgresql://postgres:postgres@localhost:5432/postgres

# Create the database
CREATE DATABASE proposalgen;

# Exit psql
\q

# Run database setup script
psql postgresql://postgres:postgres@localhost:5432/proposalgen -f db/database-setup.sql

# Seed the database with initial data
psql postgresql://postgres:postgres@localhost:5432/proposalgen -f db/seed.sql
```

#### 4. Redis Setup

```bash
# Start Redis server
redis-server

# Or with configuration
redis-server --port 6379 --daemonize yes
```

---

## Database Configuration

### Connection Details

| Parameter | Value | Description |
|-----------|-------|-------------|
| Host | localhost | Database server |
| Port | 5432 | PostgreSQL default port |
| Database | proposalgen | Database name |
| User | postgres | Database user |
| Password | postgres | Database password |

### Initial Data

The seed script (`db/seed.sql`) creates:
- Admin user: `admin@example.com` / `admin123`
- Sample teams, roles, donors, outcomes, field contexts
- Sample templates for proposal generation
- Sample knowledge cards

---

## Environment Configuration

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/proposalgen

# Redis
REDIS_URL=redis://localhost:6379/0

# Authentication
SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256

# Azure OpenAI (optional - for LLM features)
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Google Vertex AI (optional - alternative LLM)
GOOGLE_VERTEX_AI_PROJECT=your-project-id
GOOGLE_VERTEX_AI_LOCATION=us-central1

# CORS
CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

# Debug
DEBUG=true

# Secrets Management (Production)
USE_SECRET_MANAGER=false
SECRET_MANAGER_PROJECT_ID=your-gcp-project-id
```

### Secrets Management

The Proposal Drafter supports three modes for secrets management:

#### 1. Development Mode (Environment Variables)

For local development, secrets are loaded from `.env` files:

```bash
# Copy example files
cp .env.example .env
cp backend/.env.example backend/.env

# Edit the files with your actual secrets
nano .env
nano backend/.env
```

**Important:** Never commit `.env` files with real secrets to Git. The `.gitignore` file already excludes these files.

#### 2. Production Mode (Google Cloud Secret Manager)

For production deployments on Google Cloud, use Google Cloud Secret Manager:

```bash
# Enable secret manager mode
export USE_SECRET_MANAGER=true
export SECRET_PROVIDER=gcp
export SECRET_MANAGER_PROJECT_ID=your-gcp-project-id

# Create secrets in Google Cloud Secret Manager
gcloud secrets create SECRET_KEY --replication-policy="automatic"
gcloud secrets create DB_PASSWORD --replication-policy="automatic"
# ... create other secrets as needed

# Add secret values
echo "your-strong-secret-key" | gcloud secrets versions add SECRET_KEY --data-file=-
echo "your-db-password" | gcloud secrets versions add DB_PASSWORD --data-file=-

# The application will automatically fetch secrets from Google Cloud Secret Manager
```

#### 3. Production Mode (Azure Key Vault)

For production deployments on Azure, use Azure Key Vault:

```bash
# Enable secret manager mode
export USE_SECRET_MANAGER=true
export SECRET_PROVIDER=azure
export AZURE_KEY_VAULT_NAME=your-key-vault-name

# Install Azure CLI and login
az login

# Create secrets in Azure Key Vault
az keyvault secret set --vault-name $AZURE_KEY_VAULT_NAME --name SECRET-KEY --value "your-strong-secret-key"
az keyvault secret set --vault-name $AZURE_KEY_VAULT_NAME --name DB-PASSWORD --value "your-db-password"
# ... create other secrets as needed

# The application will automatically fetch secrets from Azure Key Vault
```

### Secrets Rotation

The project includes a secrets rotation script to automate key rotation:

```bash
# Dry run (shows what would be rotated)
./scripts/secrets-rotation.sh --dry-run

# Actual rotation
./scripts/secrets-rotation.sh

# Force update .env files (use with caution)
./scripts/secrets-rotation.sh --force
```

**Rotation Policy:**
- Secrets are rotated every 90 days
- The script keeps the last 2 versions of each secret
- Old versions are disabled but not deleted

### Pre-commit Hooks

The project includes pre-commit hooks to prevent secrets from being committed:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks on all files
pre-commit run --all-files

# Update hooks to latest versions
pre-commit autoupdate
```

**Hooks include:**
- `detect-secrets`: Scans for potential secrets in code
- `detect-private-key`: Prevents private keys from being committed
- `black`: Python code formatting
- `flake8`: Python linting
- `mypy`: Type checking

### Frontend (.env)

```bash
# API Configuration
REACT_APP_API_BASE=http://localhost:8502
REACT_APP_API_WS_BASE=ws://localhost:8502

# App Configuration
REACT_APP_NAME=Proposal Drafter
REACT_APP_VERSION=2.0.0
REACT_APP_ENVIRONMENT=development

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=false
```

---

## Running the Application

### Development Mode

**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8502 --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

**Access:**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8502`
- API Docs (Swagger): `http://localhost:8502/docs`
- API Docs (ReDoc): `http://localhost:8502/redoc`

### Production Mode

**Backend:**
```bash
cd backend
source venv/bin/activate
# Use Gunicorn for production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8502
```

**Frontend:**
```bash
cd frontend
npm run build
# Serve the built files with a static server
npx serve -s build -l 3000
```

---

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_proposals.py

# Run with verbose output
pytest -v
```

### Frontend Tests

```bash
cd frontend

# Run component tests
npm run test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

### End-to-End Tests

```bash
# Ensure backend and frontend are running
cd playwright

# Run all E2E tests
pytest tests/

# Run specific test
pytest tests/test_proposal_generation.py

# Run with headed browser (for debugging)
pytest tests/test_proposal_generation.py --headed
```

---

## Common Commands

### Database Operations

```bash
# Reset database (WARNING: deletes all data)
psql postgresql://postgres:postgres@localhost:5432/proposalgen -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
psql postgresql://postgres:postgres@localhost:5432/proposalgen -f db/database-setup.sql
psql postgresql://postgres:postgres@localhost:5432/proposalgen -f db/seed.sql

# Create pgvector extension (if not already created)
psql postgresql://postgres:postgres@localhost:5432/proposalgen -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Check tables
psql postgresql://postgres:postgres@localhost:5432/proposalgen -c "\dt"
```

### Redis Operations

```bash
# Check Redis is running
redis-cli ping  # Should return "PONG"

# Flush all data
redis-cli FLUSHALL

# Monitor Redis activity
redis-cli MONITOR
```

### Logs

```bash
# View backend logs
cd backend
tail -f logs/*.log

# View frontend logs
cd frontend
npm run dev  # Logs appear in terminal

# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Symptom:** Backend fails to start with database connection error

**Solution:**
```bash
# Check if PostgreSQL is running
ps aux | grep postgres

# If not, start it
sudo service postgresql start  # Ubuntu/Debian
# OR
brew services start postgresql  # Mac

# Verify connection
psql postgresql://postgres:postgres@localhost:5432/proposalgen -c "SELECT 1"
```

#### 2. Redis Connection Failed

**Symptom:** Backend fails to start with Redis connection error

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# If not, start it
redis-server --daemonize yes
```

#### 3. Port Already in Use

**Symptom:** Error: Address already in use

**Solution:**
```bash
# Find process using port 8502
sudo lsof -i :8502

# Kill the process
kill -9 <PID>

# Or for all common ports
sudo lsof -i :8502 -i :3000 -i :5432 -i :6379
```

#### 4. Frontend Can't Connect to Backend

**Symptom:** Frontend shows connection errors

**Solution:**
```bash
# Check backend is running
curl http://localhost:8502/health

# Check CORS settings in backend .env
CORS_ORIGINS="http://localhost:3000"

# Check frontend .env
REACT_APP_API_BASE=http://localhost:8502
```

#### 5. Missing Dependencies

**Symptom:** Import errors or module not found

**Solution:**
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Docker-Specific Issues

#### Docker Compose Build Fails

```bash
# Clean up and rebuild
docker-compose -f docker-compose-local.yml down -v
docker-compose -f docker-compose-local.yml build --no-cache
```

#### Volume Permission Issues

```bash
# On Linux, ensure volumes have correct permissions
sudo chown -R $USER:$USER .
```

---

## API Quick Reference

### Authentication

```bash
# Login
curl -X POST http://localhost:8502/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'

# Get current user
curl http://localhost:8502/api/me \
  -H "Authorization: Bearer <token>"
```

### Proposals

```bash
# Create session
curl -X POST http://localhost:8502/api/create-session \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"template_name": "proposal_template_unhcr.json", "form_data": {}, "project_description": "Test proposal"}'

# Generate proposal sections
curl -X POST http://localhost:8502/api/generate-proposal-sections/<session_id> \
  -H "Authorization: Bearer <token>"

# List proposals
curl http://localhost:8502/api/proposals \
  -H "Authorization: Bearer <token>"
```

### Knowledge Cards

```bash
# List knowledge cards
curl http://localhost:8502/api/knowledge-cards \
  -H "Authorization: Bearer <token>"

# Create knowledge card
curl -X POST http://localhost:8502/api/knowledge-cards \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"summary": "Test knowledge card", "type": "reference", "donor_id": "..."}'
```

---

## Project Structure

```
proposal_drafter/
├── backend/                 # FastAPI backend
│   ├── api/                 # API routers
│   ├── core/                # Configuration, database
│   ├── models/              # Pydantic and SQLAlchemy models
│   ├── services/            # Business logic
│   ├── utils/               # Helper functions
│   └── main.py              # Application entry point
├── frontend/                # React frontend
│   ├── public/              # Static files
│   ├── src/                 # Source code
│   │   ├── components/      # Reusable components
│   │   ├── screens/         # Page components
│   │   ├── utils/           # Utilities and hooks
│   │   └── App.jsx          # Main application
│   └── package.json         # Node.js dependencies
├── db/                      # Database scripts
│   ├── database-setup.sql   # Schema definition
│   └── seed.sql             # Initial data
├── specs/                   # Spec-Kit specifications
│   └── 001-proposal_drafter/
│       ├── spec.md          # Feature specification
│       ├── plan.md          # Implementation plan
│       ├── research.md      # Research findings
│       ├── data-model.md    # Data model
│       ├── contracts/       # Interface contracts
│       └── quickstart.md    # This file
├── playwright/               # E2E tests
├── docker-compose-local.yml # Local development
└── README.md                # Project overview
```

---

## Next Steps

After getting the system running:

1. **Create your first proposal:** Use the frontend interface to create a new proposal session
2. **Explore knowledge cards:** Browse and create knowledge cards for your organization
3. **Customize templates:** Create or modify templates to match your donor requirements
4. **Set up production:** Configure for production deployment (see [Deployment Guide](#))
5. **Contribute:** Submit issues and pull requests to the repository

---

## Getting Help

### Documentation

- [README.md](README.md) - Project overview
- [AGENTS.md](AGENTS.md) - AI agent guidelines
- [docs/](docs/) - Detailed documentation

### Community

- GitHub Issues: Report bugs and request features
- GitHub Discussions: Ask questions and share ideas
- Email: contact@proposal-drafter.org

### Debugging

Enable debug mode for more verbose logging:

**Backend:**
```bash
DEBUG=true uvicorn main:app --reload
```

**Frontend:**
```bash
# Logs appear in browser console
# Or run with:
npm start
```

---

*Generated by `/speckit.architecture-guard.governed-plan` workflow - Phase 1 Quickstart*
