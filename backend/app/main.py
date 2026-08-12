"""Main FastAPI Application"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import agent_actions as agent_actions_routes
from .api.routes import agent_modes as agent_modes_routes
from .api.routes import agents as agents_routes
from .api.routes import auth as auth_routes
from .api.routes import business_profiles as business_profiles_routes
from .api.routes import businesses as businesses_routes
from .api.routes import chat as chat_routes
from .api.routes import credentials as credentials_routes
from .api.routes import events as events_routes
from .api.routes import policies as policies_routes
from .api.routes import simulation as simulation_routes
from .api.routes import tasks as tasks_routes
from .core.llm import get_groq_llm
from .database.mongodb import close_mongo_connection, connect_to_mongo, get_database, ping_mongo
from .orchestration.registry import AgentRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    app.state.db = get_database()
    app.state.agent_registry = AgentRegistry()
    # Pays ChatGroq's ~1-2s construction cost (httpx/cert-store setup) once at
    # startup instead of on whichever business's request happens to trigger
    # AgentRegistry's lazy first construction — get_groq_llm() caches by
    # temperature, so every agent's later call reuses this instance.
    get_groq_llm()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Startup Simulator API",
    description="Multi-Agent AI-powered Business Simulation Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(businesses_routes.router)
app.include_router(business_profiles_routes.router)
app.include_router(credentials_routes.router)
app.include_router(agents_routes.router)
app.include_router(chat_routes.router)
app.include_router(agent_actions_routes.router)
app.include_router(events_routes.router)
app.include_router(policies_routes.router)
app.include_router(agent_modes_routes.router)
app.include_router(tasks_routes.router)
app.include_router(tasks_routes.task_actions_router)
app.include_router(simulation_routes.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Startup Simulator API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    mongo_ok = await ping_mongo()
    return {
        "status": "healthy",
        "service": "startup-simulator-backend",
        "mongo": "connected" if mongo_ok else "unavailable",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
