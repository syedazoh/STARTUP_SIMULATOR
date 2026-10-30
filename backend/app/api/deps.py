"""Shared FastAPI dependencies"""
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..core.security import decode_access_claims
from ..database.utils import find_one
from ..models.auth_schemas import UserOut
from ..models.business_schemas import BusinessOut

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> UserOut:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    claims = decode_access_claims(credentials.credentials)
    user_id = claims.get("sub") if claims else None
    if user_id is None or not claims.get("sid"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    session = await find_one(request.app.state.db["sessions"], {"session_id": claims["sid"]})
    if (session is None or session["revoked"] or session["user_id"] != user_id
            or session["expires_ts"] <= datetime.now(timezone.utc).timestamp()):
        raise HTTPException(status_code=401, detail="Session has ended")
    user_doc = await find_one(request.app.state.db["users"], {"user_id": user_id})
    if user_doc is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return UserOut(
        id=user_doc["user_id"],
        email=user_doc["email"],
        role=user_doc.get("role", "owner"),
        created_at=user_doc["created_at"],
    )


async def require_admin(user: UserOut = Depends(get_current_user)) -> UserOut:
    # Role is read from the DB-backed UserOut above, never from a client-supplied
    # value, so this can't be bypassed by anything the frontend sends.
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


async def get_owned_business(
    business_id: str,
    request: Request,
    user: UserOut = Depends(get_current_user),
) -> BusinessOut:
    doc = await find_one(request.app.state.db["businesses"], {"business_id": business_id})
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    if doc["owner_user_id"] != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your business")

    return BusinessOut(
        id=doc["business_id"],
        owner_user_id=doc["owner_user_id"],
        company_name=doc["company_name"],
        industry=doc["industry"],
        starting_budget=doc["starting_budget"],
        starting_customer_base=doc["starting_customer_base"],
        starting_headcount=doc["starting_headcount"],
        starting_resources=doc["starting_resources"],
        enabled_agents=doc.get("enabled_agents", ["finance", "marketing", "hr", "operations", "ceo"]),
        created_at=doc["created_at"],
    )


async def get_owned_task(
    task_id: str,
    request: Request,
    user: UserOut = Depends(get_current_user),
) -> Dict[str, Any]:
    """Task routes are top-level (/api/tasks/{id}), not business-scoped in the
    URL, so ownership has to be resolved via the task's business_id instead of
    get_owned_business's path-param lookup."""
    db = request.app.state.db
    task_doc = await find_one(db["tasks"], {"task_id": task_id})
    if task_doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    business_doc = await find_one(db["businesses"], {"business_id": task_doc["business_id"]})
    if business_doc is None or business_doc["owner_user_id"] != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your task")

    business = BusinessOut(
        id=business_doc["business_id"],
        owner_user_id=business_doc["owner_user_id"],
        company_name=business_doc["company_name"],
        industry=business_doc["industry"],
        starting_budget=business_doc["starting_budget"],
        starting_customer_base=business_doc["starting_customer_base"],
        starting_headcount=business_doc["starting_headcount"],
        starting_resources=business_doc["starting_resources"],
        enabled_agents=business_doc.get("enabled_agents", ["finance", "marketing", "hr", "operations", "ceo"]),
        created_at=business_doc["created_at"],
    )
    return {"task": task_doc, "business": business}
