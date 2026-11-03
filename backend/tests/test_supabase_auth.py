"""Provider validation, explicit linking, roles and existing-data isolation."""

from datetime import datetime, timezone
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException
from mongomock_motor import AsyncMongoMockClient

from app.config import settings
from app.services import supabase_auth as auth
from app.models.auth_schemas import UserOut


@pytest.fixture
def db():
    return AsyncMongoMockClient().auth_test


@pytest.fixture
def provider(monkeypatch):
    identity = (str(uuid4()), "owner@example.com")

    async def verify(token):
        if token != "valid":
            raise HTTPException(401, "Invalid token")
        return identity

    monkeypatch.setattr(auth, "verify_identity", verify)
    return identity


@pytest.mark.asyncio
async def test_provision_repeated_identity_keeps_owner_and_key(db, provider):
    first = await auth.resolve_user(db, "valid")
    before = await db.users.find_one({"user_id": first.id})
    second = await auth.resolve_user(db, "valid")
    after = await db.users.find_one({"user_id": second.id})
    assert first.id == second.id and second.role == "owner"
    assert before["encrypted_data_key"] == after["encrypted_data_key"]
    assert await db.users.count_documents({}) == 1


@pytest.mark.asyncio
async def test_matching_email_cannot_take_existing_account(db, provider):
    await db.users.insert_one({"user_id": "original", "email": provider[1]})
    with pytest.raises(HTTPException) as exc:
        await auth.resolve_user(db, "valid")
    assert exc.value.status_code == 409
    assert await db.auth_identities.count_documents({}) == 0


@pytest.mark.asyncio
async def test_explicit_link_preserves_original_business_and_key(db, provider):
    now = datetime.now(timezone.utc)
    await db.users.insert_one(
        {
            "user_id": "original",
            "email": provider[1],
            "role": "owner",
            "created_at": now,
            "encrypted_data_key": "preserve-me",
        }
    )
    await db.businesses.insert_one(
        {"business_id": "company", "owner_user_id": "original"}
    )
    user = UserOut(id="original", email=provider[1], role="owner", created_at=now)
    await auth.link_identity(db, user, "valid")
    await auth.link_identity(db, user, "valid")
    result = await auth.resolve_user(db, "valid")
    assert result.id == "original"
    assert (await db.users.find_one({"user_id": "original"}))[
        "encrypted_data_key"
    ] == "preserve-me"
    assert (await db.businesses.find_one({}))["owner_user_id"] == result.id


@pytest.mark.asyncio
async def test_link_rejects_other_email(db, provider):
    user = UserOut(
        id="other",
        email="other@example.com",
        role="owner",
        created_at=datetime.now(timezone.utc),
    )
    with pytest.raises(HTTPException) as exc:
        await auth.link_identity(db, user, "valid")
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_bad_token_creates_nothing(db, provider):
    with pytest.raises(HTTPException):
        await auth.resolve_user(db, "invalid")
    assert await db.users.count_documents({}) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,body,expected",
    [
        (401, {}, 401),
        (500, {}, 503),
        (
            200,
            {
                "id": str(uuid4()),
                "email": "a@example.com",
                "user_metadata": {"role": "admin"},
            },
            401,
        ),
    ],
)
async def test_provider_errors_and_unverified_identity(
    monkeypatch, status, body, expected
):
    monkeypatch.setattr(settings, "supabase_url", "https://example.supabase.co")
    monkeypatch.setattr(settings, "supabase_publishable_key", "publishable-test")

    class Client:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, headers):
            assert url == "https://example.supabase.co/auth/v1/user"
            return httpx.Response(status, json=body)

    monkeypatch.setattr(auth.httpx, "AsyncClient", Client)
    with pytest.raises(HTTPException) as exc:
        await auth.verify_identity("token")
    assert exc.value.status_code == expected


@pytest.mark.asyncio
async def test_supabase_bearer_enforces_business_ownership(db, provider):
    from fastapi import FastAPI, Depends
    from fastapi.testclient import TestClient
    from app.api.deps import get_current_user, get_owned_business

    app = FastAPI()
    app.state.db = db

    @app.get("/me")
    async def me(user=Depends(get_current_user)):
        return user

    @app.get("/businesses/{business_id}")
    async def business(value=Depends(get_owned_business)):
        return value

    await db.businesses.insert_one(
        {"business_id": "other-company", "owner_user_id": "someone-else"}
    )
    with TestClient(app) as client:
        headers = {"Authorization": "Bearer valid", "X-Auth-Provider": "supabase"}
        assert client.get("/me", headers=headers).status_code == 200
        assert (
            client.get("/businesses/other-company", headers=headers).status_code == 403
        )
        assert (
            client.get("/me", headers={"Authorization": "Bearer valid"}).status_code
            == 401
        )
        assert (
            client.get("/me", headers={"X-Auth-Provider": "supabase"}).status_code
            == 401
        )


@pytest.mark.asyncio
async def test_local_role_is_authoritative(db, provider):
    await auth.resolve_user(db, "valid")
    await db.users.update_one({"email": provider[1]}, {"$set": {"role": "viewer"}})
    assert (await auth.resolve_user(db, "valid")).role == "viewer"
