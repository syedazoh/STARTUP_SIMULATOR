"""Revocable sessions with one-use, hashed refresh tokens."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from fastapi import HTTPException, Request, Response
from pymongo import ReturnDocument
from ..config import settings
from ..database.utils import find_one

COOKIE_NAME = "simulator_refresh"


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def check_cookie_request(request: Request):
    # A custom header makes browser cross-site requests require a successful
    # CORS preflight. Origin is also checked when supplied by the browser.
    origin = request.headers.get("origin")
    if request.headers.get("x-requested-with") != "XMLHttpRequest" or (
        origin is not None and origin not in settings.allowed_origins
    ):
        raise HTTPException(status_code=403, detail="Invalid session request origin")


def set_refresh_cookie(response: Response, token: str):
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=not settings.debug,
        samesite="strict",
        path="/api/auth",
        max_age=settings.refresh_token_expire_days * 86400,
    )
    response.headers["Cache-Control"] = "no-store"


def clear_refresh_cookie(response: Response):
    response.delete_cookie(
        COOKIE_NAME,
        path="/api/auth",
        secure=not settings.debug,
        httponly=True,
        samesite="strict",
    )
    response.headers["Cache-Control"] = "no-store"


async def _new_refresh(db, session_id, expires_at):
    token = secrets.token_urlsafe(48)
    await db["refresh_tokens"].insert_one(
        {
            "token_hash": token_hash(token),
            "session_id": session_id,
            "used": False,
            "expires_at": expires_at,
            "expires_ts": expires_at.timestamp(),
        }
    )
    return token


async def create_session(db, user_id):
    session_id = str(uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    await db["sessions"].insert_one(
        {
            "session_id": session_id,
            "user_id": user_id,
            "revoked": False,
            "expires_at": expires_at,
            "expires_ts": expires_at.timestamp(),
        }
    )
    return session_id, await _new_refresh(db, session_id, expires_at)


async def rotate_refresh(db, token):
    now = datetime.now(timezone.utc)
    doc = await find_one(db["refresh_tokens"], {"token_hash": token_hash(token)})
    if doc is None or doc["expires_ts"] <= now.timestamp():
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    session = await find_one(db["sessions"], {"session_id": doc["session_id"]})
    if (
        session is None
        or session["revoked"]
        or session["expires_ts"] <= now.timestamp()
    ):
        raise HTTPException(status_code=401, detail="Session has ended")
    claimed = await db["refresh_tokens"].find_one_and_update(
        {"token_hash": doc["token_hash"], "used": False},
        {"$set": {"used": True}},
        return_document=ReturnDocument.AFTER,
    )
    if claimed is None:
        await revoke_session(db, session["session_id"])
        raise HTTPException(
            status_code=401, detail="Refresh token reuse detected; sign in again"
        )
    if await find_one(db["users"], {"user_id": session["user_id"]}) is None:
        await revoke_session(db, session["session_id"])
        raise HTTPException(status_code=401, detail="User not found")
    # Fixed absolute session lifetime; rotation does not extend it indefinitely.
    expires_at = datetime.fromtimestamp(session["expires_ts"], timezone.utc)
    return session, await _new_refresh(db, session["session_id"], expires_at)


async def revoke_session(db, session_id):
    await db["sessions"].update_one(
        {"session_id": session_id}, {"$set": {"revoked": True}}
    )
