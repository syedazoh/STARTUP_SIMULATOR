# Startup Simulator - Multi-Agent AI-powered Business Simulation Platform

## Project Overview

Startup Simulator is a comprehensive multi-agent AI-powered business simulation platform designed to model complex business operations through autonomous agents managing different departments of a startup.

## Architecture

### Backend (FastAPI - Python)

The backend consists of four autonomous agents:

1. **Finance Agent** - Manages budgets, revenue tracking, expense management
2. **Marketing Agent** - Handles campaigns, market analysis, customer engagement  
3. **HR Agent** - Manages recruitment, payroll, team performance
4. **Operations Agent** - Oversees supply chain, resource allocation, process optimization

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
- PostgreSQL for data persistence
- Redis for caching
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

Login requires MongoDB, including permission to create the `login_attempts`
TTL index. Each email address (case insensitive) gets five login attempts per
fixed five-minute window, shared across backend workers. All attempts count,
including successful logins. Excess attempts return HTTP 429 with `Retry-After`;
throttled attempts emit a warning without logging passwords or email addresses.
Login returns HTTP 503 if the throttle store is unavailable, including when the
simulator uses its in-memory database fallback.

**Frontend**
```bash
cd frontend
npm run dev
```
Frontend will be available at `http://localhost:5173`

#### Option 2: Docker Compose

```bash
cd docker
docker-compose up
```

## Project Structure

Complete folder structure with 36+ files for backend, frontend, and DevOps configuration.

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
