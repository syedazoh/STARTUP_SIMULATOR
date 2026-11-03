"""Opt-in provider validation; local ownership/roles remain authoritative."""

from datetime import datetime, timezone
from uuid import UUID

import httpx
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from pydantic import EmailStr, TypeAdapter

from ..config import settings
from ..core.crypto import encrypt_data_key, generate_data_key
from ..database.utils import find_one, ensure_unique_index
from ..models.auth_schemas import UserOut


async def verify_identity(token):
    url = settings.supabase_url
    key = settings.supabase_publishable_key
    if not url or not key:
        raise HTTPException(503, "Supabase authentication is not configured")
    # Only the operator-configured provider receives bearer credentials.
    from urllib.parse import urlsplit

    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.path not in ("", "/")
        or parts.query
        or parts.fragment
        or parts.username
    ):
        raise HTTPException(503, "Invalid authentication provider configuration")
    if len(token) > 16384:
        raise HTTPException(401, "Invalid authentication token")
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
            response = await client.get(
                url.rstrip("/") + "/auth/v1/user",
                headers={"apikey": key, "Authorization": "Bearer " + token},
            )
        if response.status_code in (401, 403):
            raise HTTPException(401, "Invalid or expired Supabase session")
        if response.status_code != 200:
            raise HTTPException(503, "Authentication provider unavailable")
        body = response.json()
        subject = str(UUID(body["id"]))
        email = str(TypeAdapter(EmailStr).validate_python(body["email"])).lower()
        if not body.get("email_confirmed_at") or body.get("is_anonymous"):
            raise HTTPException(401, "Verify your email before continuing")
        return subject, email
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        raise HTTPException(503, "Authentication provider unavailable") from None


async def identity_index(db):
    # Mapping is separate: no unique-null migration on existing user records.
    await ensure_unique_index(db["auth_identities"], "subject")
    await ensure_unique_index(db["users"], "email")


def public_user(doc):
    return UserOut(
        id=doc["user_id"],
        email=doc["email"],
        role=doc.get("role", "owner"),
        created_at=doc["created_at"],
    )


async def resolve_user(db, token):
    subject, email = await verify_identity(token)
    await identity_index(db)
    mapping = await find_one(db["auth_identities"], {"subject": subject})
    if mapping:
        doc = await find_one(db["users"], {"user_id": mapping["user_id"]})
        if not doc:
            raise HTTPException(401, "Account unavailable")
        return public_user(doc)
    user_id = "supabase:" + subject
    doc = await find_one(db["users"], {"user_id": user_id})
    if doc is None:
        if await find_one(db["users"], {"email": email}):
            raise HTTPException(
                409,
                "Existing account: sign in with your original password and link Supabase",
            )
        doc = {
            "user_id": user_id,
            "email": email,
            "role": "owner",
            "created_at": datetime.now(timezone.utc),
            "encrypted_data_key": encrypt_data_key(generate_data_key()),
        }
        try:
            await db["users"].insert_one(doc)
        except DuplicateKeyError:
            doc = await find_one(db["users"], {"user_id": user_id})
            if not doc:
                raise HTTPException(
                    409, "Account conflict; link your existing account"
                ) from None
    try:
        await db["auth_identities"].insert_one({"subject": subject, "user_id": user_id})
    except DuplicateKeyError:
        mapping = await find_one(db["auth_identities"], {"subject": subject})
        if not mapping or mapping["user_id"] != user_id:
            raise HTTPException(409, "Identity already linked") from None
    return public_user(doc)


async def link_identity(db, user, token):
    subject, email = await verify_identity(token)
    if email != user.email.lower():
        raise HTTPException(409, "Use the same verified email as your existing account")
    await identity_index(db)
    existing = await find_one(db["auth_identities"], {"subject": subject})
    if existing:
        if existing["user_id"] == user.id:
            return
        raise HTTPException(409, "Identity already linked")
    # A provisioned Supabase account must not be merged implicitly.
    if await find_one(db["users"], {"user_id": "supabase:" + subject}):
        raise HTTPException(
            409, "Identity already provisioned; contact an administrator"
        )
    try:
        await db["auth_identities"].insert_one({"subject": subject, "user_id": user.id})
    except DuplicateKeyError:
        raise HTTPException(409, "Identity already linked; retry sign-in") from None
