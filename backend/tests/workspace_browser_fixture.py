"""Disposable HTTP fixture for the Next workspace browser test.

Never imported by app.main. Explicit flag required, loopback only, no real
Supabase, MongoDB or LLM. Run from backend with PYTHONPATH=.
"""

import os

if os.environ.get("SIMULATOR_BROWSER_TEST") != "1":
    raise SystemExit("Set SIMULATOR_BROWSER_TEST=1 for this disposable fixture only")

import base64, json, time, uuid, threading, asyncio
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mongomock_motor import AsyncMongoMockClient
import app.database.mongodb as mongo
from app.config import settings
from app.main import app
import app.services.supabase_auth as auth
import app.core.llm as llm

mongo.AsyncIOMotorClient = lambda *a, **k: AsyncMongoMockClient()
settings.chroma_persist_dir = "/tmp/simulator-browser-chroma"
settings.allowed_origins = [*settings.allowed_origins, "http://127.0.0.1:5173"]
provider = FastAPI()


def encoded(v):
    return base64.urlsafe_b64encode(json.dumps(v).encode()).decode().rstrip("=")


def user(email):
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, email)),
        "email": email,
        "email_confirmed_at": "2026-11-01T00:00:00Z",
        "aud": "authenticated",
        "role": "authenticated",
        "app_metadata": {"provider": "email"},
        "user_metadata": {},
        "created_at": "2026-11-01T00:00:00Z",
    }


def token(email):
    u = user(email)
    return (
        encoded({"alg": "HS256", "typ": "JWT"})
        + "."
        + encoded(
            {
                "sub": u["id"],
                "email": email,
                "aud": "authenticated",
                "role": "authenticated",
                "iat": int(time.time()),
                "exp": int(time.time()) + 3600,
            }
        )
        + ".Zml4dHVyZQ"
    )


def claims(raw):
    return json.loads(base64.urlsafe_b64decode(raw.split(".")[1] + "==="))


@provider.post("/auth/v1/token")
async def login(request: Request):
    d = await request.json()
    email = d.get("email", "demo@example.com")
    return {
        "access_token": token(email),
        "refresh_token": "fixture-refresh",
        "expires_in": 3600,
        "expires_at": int(time.time()) + 3600,
        "token_type": "bearer",
        "user": user(email),
    }


@provider.get("/auth/v1/user")
async def me(request: Request):
    try:
        return user(
            claims(request.headers.get("authorization", "").split(" ")[1])["email"]
        )
    except Exception:
        return JSONResponse({"message": "Invalid session"}, status_code=401)


@provider.post("/auth/v1/logout")
async def logout():
    return {}


async def verify(raw):
    d = claims(raw)
    return d["sub"], d["email"]


auth.verify_identity = verify


class Model:
    def with_structured_output(self, schema):
        class Structured:
            async def ainvoke(self, prompt):
                if schema.__name__ == "TaskAuthorization":
                    return schema(
                        decision="approve", reason="Fixture CEO authorization"
                    )
                if schema.__name__ == "BudgetRequestAction":
                    return schema(amount=400, department="General")
                if schema.__name__ == "CEOPlan":
                    return schema(
                        strategy="Fixture strategy for a supervised product launch",
                        assignments=[
                            {
                                "department": "finance",
                                "objective": "Allocate launch budget",
                                "action_type": "budget_request",
                                "payload": {"amount": 25, "department": "Marketing"},
                                "success_criteria": "Allocation recorded",
                            },
                            {
                                "department": "marketing",
                                "objective": "Prepare campaign",
                                "action_type": "campaign_launch",
                                "payload": {
                                    "campaign_name": "Demo launch",
                                    "requested_budget": 25,
                                },
                                "success_criteria": "Campaign result recorded",
                            },
                            {
                                "department": "hr",
                                "objective": "Prepare staffing",
                                "action_type": "recruitment_request",
                                "payload": {
                                    "role": "Designer",
                                    "headcount": 1,
                                    "monthly_salary": 25,
                                },
                                "success_criteria": "Staffing result recorded",
                            },
                            {
                                "department": "operations",
                                "objective": "Prepare supplies",
                                "action_type": "resource_request",
                                "payload": {
                                    "resource_type": "Stock",
                                    "quantity": 1,
                                    "unit_cost": 25,
                                },
                                "success_criteria": "Resources recorded",
                            },
                        ],
                    )
                raise RuntimeError("No live provider in browser fixture")

        return Structured()

    async def ainvoke(self, prompt):
        raise RuntimeError("No live provider in browser fixture")


llm._cached_groq_llm = lambda *a: Model()

# UI fixture only: exercise durable role service calls against mocked Mongo.
# Real worker-process evidence lives in integration/test_distributed_processes.py.
from app.services import jobs, distributed
from app.models.distributed_schemas import ROLES
original_worker = jobs.worker_loop
async def fixture_worker(app):
    async def role_loop():
        while True:
            for role in ROLES:
                await distributed.run_once(app.state.db, role)
            await asyncio.sleep(.1)
    async with asyncio.TaskGroup() as group:
        group.create_task(original_worker(app))
        group.create_task(role_loop())
jobs.worker_loop = fixture_worker
threading.Thread(
    target=lambda: uvicorn.run(
        provider, host="127.0.0.1", port=8101, log_level="warning"
    ),
    daemon=True,
).start()
uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")
