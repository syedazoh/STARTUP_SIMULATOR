"""Authentication routes"""
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from ..deps import get_current_user
from ...core.crypto import encrypt_data_key, generate_data_key
from ...core.security import create_access_token, hash_password, verify_password
from ...database.utils import ensure_unique_index, find_one
from ...models.auth_schemas import TokenOut, UserCreate, UserLogin, UserOut
from ...services.sessions import (COOKIE_NAME, check_cookie_request, create_session,
    rotate_refresh, revoke_session, set_refresh_cookie, clear_refresh_cookie, token_hash)
from ...core.security import decode_access_claims

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, request: Request):
    db = request.app.state.db
    users = db["users"]
    await ensure_unique_index(users, "email")

    email = payload.email.lower()
    existing = await find_one(users, {"email": email})
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user_id = str(uuid4())
    created_at = datetime.now(timezone.utc)
    await users.insert_one({
        "user_id": user_id,
        "email": email,
        "hashed_password": hash_password(payload.password),
        "role": "owner",
        "encrypted_data_key": encrypt_data_key(generate_data_key()),
        "created_at": created_at,
    })
    return UserOut(id=user_id, email=email, role="owner", created_at=created_at)


import logging

logger = logging.getLogger(__name__)

MAX_FAILED_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_WINDOW_SECONDS = 900  # 15 minutes


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/login", response_model=TokenOut)
async def login(payload: UserLogin, request: Request, response: Response):
    origin = request.headers.get("origin")
    from ...config import settings
    if origin is not None and origin not in settings.allowed_origins:
        raise HTTPException(status_code=403, detail="Invalid login origin")
    db = request.app.state.db
    email = payload.email.lower()
    client_ip = _get_client_ip(request)
    now = datetime.now(timezone.utc)
    cutoff = datetime.fromtimestamp(now.timestamp() - LOGIN_LOCKOUT_WINDOW_SECONDS, timezone.utc)

    # Account-aware throttling before bcrypt verification
    failed_attempts_count = await db["login_attempts"].count_documents({
        "email": email,
        "timestamp": {"$gte": cutoff},
    })

    if failed_attempts_count >= MAX_FAILED_LOGIN_ATTEMPTS:
        logger.warning(
            "Excessive failed login attempts for account: %s from IP: %s (count: %s)",
            email,
            client_ip,
            failed_attempts_count,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
        )

    user_doc = await find_one(db["users"], {"email": email})
    if user_doc is None or not verify_password(payload.password, user_doc["hashed_password"]):
        await db["login_attempts"].insert_one({
            "email": email,
            "ip": client_ip,
            "timestamp": now,
        })
        logger.warning(
            "Failed login attempt for account: %s from IP: %s (recent failures: %s)",
            email,
            client_ip,
            failed_attempts_count + 1,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    # Clear failed login attempts on successful login
    await db["login_attempts"].delete_many({"email": email})

    session_id, refresh = await create_session(db, user_doc["user_id"])
    set_refresh_cookie(response, refresh)
    token = create_access_token(subject=user_doc["user_id"], session_id=session_id)
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user: UserOut = Depends(get_current_user)):
    return user


@router.post("/refresh", response_model=TokenOut)
async def refresh(request: Request, response: Response):
    check_cookie_request(request)
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="No refresh session")
    session, rotated = await rotate_refresh(request.app.state.db, token)
    set_refresh_cookie(response, rotated)
    return TokenOut(access_token=create_access_token(session["user_id"], session_id=session["session_id"]))


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response):
    check_cookie_request(request)
    db = request.app.state.db
    token = request.cookies.get(COOKIE_NAME)
    if token:
        doc = await find_one(db["refresh_tokens"], {"token_hash": token_hash(token)})
        if doc:
            await revoke_session(db, doc["session_id"])
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        claims = decode_access_claims(authorization[7:])
        if claims and claims.get("sid"):
            await revoke_session(db, claims["sid"])
    clear_refresh_cookie(response)
