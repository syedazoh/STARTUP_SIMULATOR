"""Test the media asset (requires_asset) task path: reel_request lands
awaiting_asset, upload triggers an automated review, and the verdict decides
whether the task clears into the approval queue or bounces back for a
reshoot (Phase 4 addendum)."""
import shutil

import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

import app.database.mongodb as mongodb_module
from app.main import app
from app.services.media_assets import UPLOAD_DIR


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(mongodb_module, "AsyncIOMotorClient", lambda *a, **kw: AsyncMongoMockClient())
    with TestClient(app) as test_client:
        yield test_client
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)


def _auth_headers(client, email):
    client.post("/api/auth/register", json={"email": email, "password": "supersecret123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "supersecret123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _create_business(client, headers, **overrides):
    payload = {"company_name": "Acme Inc", "industry": "Widgets", **overrides}
    response = client.post("/api/businesses", json=payload, headers=headers)
    return response.json()["id"]


def _request_reel(client, headers, business_id):
    response = client.post(
        f"/api/businesses/{business_id}/agents/marketing/actions/reel-request",
        json={"campaign_name": "Summer Launch", "brief": "upbeat, 15s, product in hand"},
        headers=headers,
    )
    return response.json()["id"]


class TestReelRequestCreatesAwaitingAsset:
    def test_reel_request_lands_awaiting_asset(self, client):
        headers = _auth_headers(client, "asset1@example.com")
        business_id = _create_business(client, headers)

        response = client.post(
            f"/api/businesses/{business_id}/agents/marketing/actions/reel-request",
            json={"campaign_name": "Summer Launch", "brief": "upbeat, 15s"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "awaiting_asset"
        assert response.json()["requires_asset"] is True


class TestUploadApproved:
    def test_upload_image_gets_approved_and_moves_to_pending_approval(self, client):
        headers = _auth_headers(client, "asset2@example.com")
        business_id = _create_business(client, headers)
        task_id = _request_reel(client, headers, business_id)

        response = client.post(
            f"/api/tasks/{task_id}/assets",
            data={"media_type": "image"},
            files={"file": ("reel.jpg", b"fake-image-bytes", "image/jpeg")},
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["agent_review"]["verdict"] == "approved"
        assert body["media_type"] == "image"

        task_response = client.get(f"/api/businesses/{business_id}/tasks", headers=headers).json()
        task = next(t for t in task_response if t["id"] == task_id)
        assert task["status"] == "pending_approval"
        assert task["asset_id"] == body["id"]

    def test_approved_task_can_then_be_approved_and_executes(self, client):
        headers = _auth_headers(client, "asset3@example.com")
        business_id = _create_business(client, headers)
        client.post(
            f"/api/businesses/{business_id}/credentials/instagram/connect",
            json={"access_token": "ig-token", "scopes": []},
            headers=headers,
        )
        task_id = _request_reel(client, headers, business_id)
        client.post(
            f"/api/tasks/{task_id}/assets",
            data={"media_type": "video"},
            files={"file": ("reel.mp4", b"fake-video-bytes", "video/mp4")},
            headers=headers,
        )

        response = client.post(f"/api/tasks/{task_id}/approve", headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "executed"
        assert response.json()["result"]["status"] == "posted"


class TestUploadRejectedOrReshoot:
    def test_unsupported_media_type_bounces_back_to_awaiting_asset(self, client):
        headers = _auth_headers(client, "asset4@example.com")
        business_id = _create_business(client, headers)
        task_id = _request_reel(client, headers, business_id)

        response = client.post(
            f"/api/tasks/{task_id}/assets",
            data={"media_type": "audio"},
            files={"file": ("clip.mp3", b"fake-audio-bytes", "audio/mpeg")},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["agent_review"]["verdict"] == "reshoot_requested"

        task_response = client.get(f"/api/businesses/{business_id}/tasks", headers=headers).json()
        task = next(t for t in task_response if t["id"] == task_id)
        assert task["status"] == "awaiting_asset"

    def test_can_reupload_after_reshoot_requested(self, client):
        headers = _auth_headers(client, "asset5@example.com")
        business_id = _create_business(client, headers)
        task_id = _request_reel(client, headers, business_id)

        client.post(
            f"/api/tasks/{task_id}/assets",
            data={"media_type": "audio"},
            files={"file": ("clip.mp3", b"fake-audio-bytes", "audio/mpeg")},
            headers=headers,
        )
        response = client.post(
            f"/api/tasks/{task_id}/assets",
            data={"media_type": "image"},
            files={"file": ("reel2.jpg", b"fake-image-bytes", "image/jpeg")},
            headers=headers,
        )
        assert response.json()["agent_review"]["verdict"] == "approved"

        task_response = client.get(f"/api/businesses/{business_id}/tasks", headers=headers).json()
        task = next(t for t in task_response if t["id"] == task_id)
        assert task["status"] == "pending_approval"


class TestUploadGuards:
    def test_cannot_upload_when_task_not_awaiting_asset(self, client):
        headers = _auth_headers(client, "asset6@example.com")
        business_id = _create_business(client, headers)
        create_response = client.post(
            f"/api/businesses/{business_id}/agents/finance/actions/budget-request",
            json={"amount": 1000, "department": "Operations"},
            headers=headers,
        )
        task_id = create_response.json()["id"]
        assert create_response.json()["status"] == "pending_approval"

        response = client.post(
            f"/api/tasks/{task_id}/assets",
            data={"media_type": "image"},
            files={"file": ("x.jpg", b"data", "image/jpeg")},
            headers=headers,
        )
        assert response.status_code == 409

    def test_cannot_upload_asset_for_another_users_task(self, client):
        owner_headers = _auth_headers(client, "assetowner@example.com")
        business_id = _create_business(client, owner_headers)
        task_id = _request_reel(client, owner_headers, business_id)

        intruder_headers = _auth_headers(client, "assetintruder@example.com")
        response = client.post(
            f"/api/tasks/{task_id}/assets",
            data={"media_type": "image"},
            files={"file": ("x.jpg", b"data", "image/jpeg")},
            headers=intruder_headers,
        )
        assert response.status_code == 403
