"""Shared FastAPI dependencies"""
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..core.security import decode_access_token
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

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

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
        created_at=doc["created_at"],
    )
