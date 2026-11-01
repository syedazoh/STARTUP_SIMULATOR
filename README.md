# Startup Simulator - Multi-Agent AI-powered Business Simulation Platform

## Project Overview

Startup Simulator is a comprehensive multi-agent AI-powered business simulation platform designed to model complex business operations through autonomous agents managing different departments of a startup.

## CEO supervision and authentication

The CEO can propose department assignments and review their execution reports. Actions from the UI, chat, event API and deployed simulation pass through task approvals. Authentication uses short-lived access tokens in memory and rotating HttpOnly refresh cookies with server-side revocation.

See [CEO supervision and session guide](docs/CEO_SUPERVISION_AND_SESSIONS.md) for usage, migration, validation and remaining work. Existing sessions require a fresh login after this update.

## Architecture

### Backend (FastAPI - Python)

The backend has four department agents and a CEO supervisor:

1. **Finance Agent** - Manages budgets, revenue tracking, expense management
2. **Marketing Agent** - Handles campaigns, market analysis, customer engagement  
3. **HR Agent** - Manages recruitment, payroll, team performance
4. **Operations Agent** - Oversees supply chain, resource allocation, process optimization
5. **CEO Agent** - Proposes department assignments, authorizes work and reviews execution evidence

### Key Components

- **Event Bus**: Central messaging system for agent communication
- **Agent Manager**: Orchestrates multiple agents and their interactions
- **FastAPI**: RESTful API for frontend communication

### Frontend (React + Vite)

- Modern React UI with Tailwind CSS styling
- Redux state management
- Real-time API integration with axios
- Responsive dashboard

### DevOps

- Docker containerization (Backend, Frontend)
- Docker Compose for local development
- MongoDB for business records, tasks, financial state and reports
- ChromaDB for retrieval of previous decision summaries
- GitHub Actions CI/CD workflows

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)

### Installation

1. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Frontend Setup**
```bash
cd frontend
npm install
```

### Running the Application

#### Option 1: Local Development

**Backend**
```bash
cd backend
uvicorn app.main:app --reload
```
API will be available at `http://localhost:8000`

**Frontend**
```bash
cd frontend
npm run dev
```
Frontend will be available at `http://localhost:5173`

#### Option 2: Docker Compose

```bash
# From the repository root, create docker/.env from docker/.env.example first.
docker compose --env-file docker/.env -f docker/docker-compose.yml up --build --renew-anon-volumes
```

See [Docker local setup and troubleshooting](docs/DOCKER_LOCAL_SETUP.md) for Windows commands, health checks, and dependency-volume recovery.

## Project Structure

Complete folder structure with 36+ files for backend, frontend, and DevOps configuration.

For AI fallback messages or chat failures, see [AI configuration and diagnostics](docs/AI_TROUBLESHOOTING.md).

## Testing

### Backend
```bash
cd backend
pytest
```

### Frontend
```bash
cd frontend
npm test
```

## Development Roadmap

Track review findings and validation in [Implementation checklist](docs/IMPLEMENTATION_CHECKLIST.md).
The current backend supports one process. Stored decision retrieval does not train
the language model. Periodic simulation income is demo income, not validated sales forecasting.

- **Weeks 1-6**: Planning & Analysis
- **Weeks 7-10**: UI/UX Design
- **Weeks 11-15**: Agent Development & Enhancement
- **Weeks 17-23**: Integration & Deployment

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Submit a pull request

## License

MIT License
