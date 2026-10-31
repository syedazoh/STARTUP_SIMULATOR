"""Main FastAPI Application"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import supervision as supervision_routes
from .api.routes import admin as admin_routes
from .api.routes import agent_actions as agent_actions_routes
from .api.routes import agent_modes as agent_modes_routes
from .api.routes import agents as agents_routes
from .api.routes import auth as auth_routes
from .api.routes import business_profiles as business_profiles_routes
from .api.routes import businesses as businesses_routes
from .api.routes import chat as chat_routes
from .api.routes import credentials as credentials_routes
from .api.routes import events as events_routes
from .api.routes import memory as memory_routes
from .api.routes import policies as policies_routes
from .api.routes import simulation as simulation_routes
from .api.routes import tasks as tasks_routes
from .config import settings
from .core.llm import get_groq_llm
from .database.mongodb import close_mongo_connection, connect_to_mongo, get_database, ping_mongo
from .database.utils import ensure_index, ensure_ttl_index, ensure_unique_index
from .orchestration.registry import AgentRegistry

# auth.py's lockout only ever counts attempts inside LOGIN_LOCKOUT_WINDOW_SECONDS,
# so anything older than that window is dead weight — expire it instead of letting
# the collection grow without bound under repeated failed logins.
LOGIN_ATTEMPTS_TTL_SECONDS = 60 * 60 * 24


async def _create_indexes(db) -> None:
    """Indexes for every field queried frequently enough to matter beyond
    users.email (created lazily in auth.py's register). No-ops against the
    in-memory fallback (see ensure_index)."""
    await ensure_unique_index(db["sessions"], "session_id")
    await ensure_unique_index(db["refresh_tokens"], "token_hash")
    await ensure_ttl_index(db["sessions"], "expires_at", 0)
    await ensure_ttl_index(db["refresh_tokens"], "expires_at", 0)
    await ensure_index(db["tasks"], [("business_id", 1), ("agent", 1), ("created_at", -1)])
    await ensure_index(db["ceo_plans"], [("business_id", 1), ("created_at", -1)])
    await ensure_index(db["department_reports"], [("business_id", 1), ("created_at", -1)])
    await ensure_index(db["businesses"], "owner_user_id")
    await ensure_index(db["businesses"], "business_id")
    await ensure_index(db["tasks"], [("business_id", 1), ("status", 1)])
    await ensure_index(db["agent_snapshots"], [("business_id", 1), ("agent_id", 1), ("timestamp", -1)])
    await ensure_index(db["decision_logs"], [("business_id", 1), ("simulation_run_id", 1), ("tick", 1)])
    await ensure_index(db["chat_threads"], [("business_id", 1), ("agent", 1)])
    await ensure_index(db["credentials"], [("business_id", 1), ("provider", 1)])
    await ensure_index(db["audit_logs"], [("business_id", 1), ("timestamp", -1)])
    # Every login counts attempts for this email within a time window, so the
    # compound key matches that query instead of forcing a collection scan.
    await ensure_index(db["login_attempts"], [("email", 1), ("timestamp", -1)])
    await ensure_ttl_index(db["login_attempts"], "timestamp", LOGIN_ATTEMPTS_TTL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    app.state.db = get_database()
    await _create_indexes(app.state.db)
    app.state.agent_registry = AgentRegistry(db=app.state.db)
    # Pays ChatGroq's ~1-2s construction cost (httpx/cert-store setup) once at
    # startup instead of on whichever business's request happens to trigger
    # AgentRegistry's lazy first construction — get_groq_llm() caches by
    # temperature, so every agent's later call reuses this instance.
    get_groq_llm()
    yield
    await app.state.agent_registry.close()
    await close_mongo_connection()


app = FastAPI(
    title="Startup Simulator API",
    description="Multi-Agent AI-powered Business Simulation Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(supervision_routes.router)
app.include_router(admin_routes.router)
app.include_router(businesses_routes.router)
app.include_router(business_profiles_routes.router)
app.include_router(credentials_routes.router)
app.include_router(agents_routes.router)
app.include_router(chat_routes.router)
app.include_router(memory_routes.router)
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


@app.get("/api/health")
@app.get("/health")
async def health_check():
    mongo_ok = await ping_mongo()
    return {
        "status": "healthy" if mongo_ok else "degraded",
        "service": "startup-simulator-backend",
        "mongo": "connected" if mongo_ok else "unavailable",
        "ai_configured": bool(settings.groq_api_key and settings.groq_api_key != "your-groq-api-key"),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
