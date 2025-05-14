# IOM Proposal Drafter

An agentic AI application to help generate project proposals for IOM.

## Project Structure

- `frontend/` - React application
- `backend/` - FastAPI application with CrewAI integration
- `.github/workflows/` - CI/CD configuration

## Deployment Options

### Option 1: Deploy with Docker (Recommended)

Prerequisites:
- Docker
- Docker Compose

Steps:

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd proposal_drafter-dev
   ```

2. Start all services:
   ```bash
   docker-compose up -d
   ```

3. Access the application:
   - Frontend: http://localhost:8503
   - Backend API: http://localhost:8502

To rebuild the containers after changes:
```bash
docker-compose up -d --build
```

### Option 2: Deploy without Docker

Prerequisites:
- Node.js 20.x
- Python 3.11
- Redis server
- Nginx (for production)

Steps:

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd proposal_drafter-dev
   ```

2. Setup and start the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8502 --reload
   ```

3. Setup and start the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. Access the application:
   - Frontend: http://localhost:8503 (development server)
   - Backend API: http://localhost:8502

For production deployment, use the provided `deploy.sh` script:
```bash
./deploy.sh
```

## CI/CD Pipeline

The project includes two CI/CD pipeline configurations:

1. `docker-ci.yml` - For Docker-based deployment
2. `standard-ci.yml` - For traditional deployment

These pipelines handle:
- Code linting and testing
- Building the frontend
- Creating Docker images (Docker pipeline)
- Deploying to a production server (Standard pipeline)

## Development

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8502 --reload
```