"""Private stateless MCP boundary: business-scoped, revocable bearer capabilities."""

import time
from contextvars import ContextVar
from uuid import uuid4
from jose import jwt, JWTError
from fastapi import HTTPException
from starlette.responses import JSONResponse
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from ..config import settings
from ..services.jobs import persistent, enqueue
from ..models.action_schemas import validate_action

principal = ContextVar("mcp_principal", default=None)


async def mint(db, business, user, payload):
    persistent(db)
    if any(d not in business.enabled_agents for d in payload.departments):
        raise HTTPException(422, "Disabled department")
    now = int(time.time())
    key = str(uuid4())
    scopes = ["budget:read", "tasks:read", "knowledge:read"] + (
        ["tasks:propose"] if payload.allow_proposals else []
    )
    await db["mcp_grants"].insert_one(
        {
            "_id": key,
            "grant_id": key,
            "business_id": business.id,
            "user_id": user.id,
            "departments": sorted(set(payload.departments)),
            "scopes": scopes,
            "expires_ts": now + 900,
            "revoked": False,
            "window": 0,
            "requests": 0,
            "created_ts": now,
        }
    )
    token = jwt.encode(
        {
            "sub": user.id,
            "jti": key,
            "aud": settings.mcp_resource_url,
            "iss": "startup-simulator",
            "iat": now,
            "exp": now + 900,
        },
        settings.secret_key,
        algorithm="HS256",
    )
    return {
        "token": token,
        "grant_id": key,
        "expires_ts": now + 900,
        "resource": settings.mcp_resource_url,
        "scopes": scopes,
    }


async def verify(db, token):
    try:
        claims = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
            audience=settings.mcp_resource_url,
            issuer="startup-simulator",
            options={"require_exp": True, "require_sub": True, "require_jti": True},
        )
    except JWTError:
        raise HTTPException(401, "Invalid or expired MCP capability") from None
    grant = await db["mcp_grants"].find_one(
        {
            "_id": claims["jti"],
            "user_id": claims["sub"],
            "revoked": False,
            "expires_ts": {"$gt": time.time()},
        }
    )
    if not grant:
        raise HTTPException(401, "Capability revoked or expired")
    user = await db["users"].find_one({"user_id": claims["sub"]})
    business = await db["businesses"].find_one(
        {"business_id": grant["business_id"], "owner_user_id": claims["sub"]}
    )
    if not user or user.get("role", "owner") not in {"owner", "admin"} or not business:
        raise HTTPException(403, "Current ownership required")
    return grant, business


class Gateway:
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return
        headers = dict(scope.get("headers", []))
        app = scope["app"]
        try:
            origin = headers.get(b"origin", b"").decode()
            if origin and origin not in settings.allowed_origins:
                raise HTTPException(403, "MCP origin not allowed")
            auth = headers.get(b"authorization", b"").decode()
            if not auth.startswith("Bearer "):
                raise HTTPException(401, "MCP bearer capability required")
            grant, business = await verify(app.state.db, auth[7:])
            minute = int(time.time() // 60)
            await app.state.db["mcp_grants"].update_one(
                {"_id": grant["_id"], "window": {"$ne": minute}},
                {"$set": {"window": minute, "requests": 0}},
            )
            allowed = await app.state.db["mcp_grants"].find_one_and_update(
                {"_id": grant["_id"], "window": minute, "requests": {"$lt": 60}},
                {"$inc": {"requests": 1}},
            )
            if not allowed:
                raise HTTPException(429, "MCP request budget exceeded")
            context = principal.set((app, grant, business))

            async def private_send(message):
                if message["type"] == "http.response.start":
                    message = {
                        **message,
                        "headers": [
                            *message.get("headers", []),
                            (b"cache-control", b"no-store"),
                        ],
                    }
                await send(message)

            try:
                await app.state.mcp_http(scope, receive, private_send)
            finally:
                principal.reset(context)
        except HTTPException as exc:
            await JSONResponse(
                {"detail": exc.detail},
                status_code=exc.status_code,
                headers={"Cache-Control": "no-store", "WWW-Authenticate": "Bearer"},
            )(scope, receive, send)


def require(scope, department=None):
    current = principal.get()
    if not current:
        raise ValueError("No MCP authentication context")
    app, grant, business = current
    if scope not in grant["scopes"] or (
        department and department not in grant["departments"]
    ):
        raise ValueError("Capability does not permit this tool/department")
    return app, grant, business


def build_server():
    mcp = FastMCP(
        "Startup Simulator private tools",
        stateless_http=True,
        json_response=True,
        streamable_http_path="/",
        max_request_body_size=65536,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=[v.strip() for v in settings.mcp_allowed_hosts.split(",")],
            allowed_origins=settings.allowed_origins,
        ),
    )

    @mcp.tool()
    async def get_budget() -> dict:
        app, grant, doc = require("budget:read", "finance")
        from ..api.routes.businesses import _to_business_out
        from ..services import ledger

        b = _to_business_out(doc)
        runtime = await app.state.agent_registry.get_or_create(b)
        return ledger.public_account(await ledger.account_for(app.state.db, b, runtime))

    @mcp.tool()
    async def get_task_status(task_id: str) -> dict:
        app, grant, doc = require("tasks:read")
        if not 1 <= len(task_id) <= 100:
            raise ValueError("Invalid task ID")
        task = await app.state.db["tasks"].find_one(
            {"task_id": task_id, "business_id": doc["business_id"]}
        )
        if not task:
            raise ValueError("Task not found")
        require("tasks:read", task["agent"])
        from ..models.task_schemas import to_task_out

        return to_task_out(task).model_dump(mode="json")

    @mcp.tool()
    async def search_knowledge(query: str, department: str) -> dict:
        app, grant, doc = require("knowledge:read", department)
        if not 2 <= len(query) <= 1000:
            raise ValueError("Query must be 2–1000 characters")
        from ..services.knowledge import search

        return await search(app.state.db, doc["business_id"], department, query, 5)

    @mcp.tool()
    async def propose_task(
        department: str, action_type: str, payload: dict, idempotency_key: str
    ) -> dict:
        app, grant, doc = require("tasks:propose", department)
        if not settings.background_jobs_enabled:
            raise ValueError("Background worker disabled")
        if action_type not in {
            "budget_request",
            "campaign_launch",
            "recruitment_request",
            "resource_request",
        }:
            raise ValueError("Only internal simulation proposals allowed")
        import re

        if not re.fullmatch(r"[\w-]{1,100}", idempotency_key):
            raise ValueError("Invalid idempotency key")
        validated = validate_action(department, action_type, payload)
        return await enqueue(
            app.state.db,
            doc["business_id"],
            grant["user_id"],
            "propose_task",
            {
                "department": department,
                "action_type": action_type,
                "payload": validated,
                "_mcp_grant": grant["grant_id"],
            },
            idempotency_key,
        )

    return mcp, mcp.streamable_http_app()
