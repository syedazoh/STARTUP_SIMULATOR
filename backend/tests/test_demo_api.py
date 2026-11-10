"""Actual owner guards and approval routes, with Mongo/provider boundaries faked."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tests.test_account_isolation import accounts  # noqa: F401 - pytest fixture
from app.main import app

SAMPLE = Path(__file__).resolve().parents[2] / "datasets/product-launch-v1/dataset.json"


def import_sample(client, headers, business):
    url = f"/api/businesses/{business}/demo/imports"
    content = SAMPLE.read_bytes()
    result = client.post(
        url,
        headers=headers,
        files={"file": ("dataset.json", content)},
        data={"format": "json"},
    )
    assert result.status_code == 200, result.text
    digest = result.json()["digest"]
    result = client.post(
        url,
        headers=headers,
        files={"file": ("dataset.json", content)},
        data={"format": "json", "action": "commit", "expected_digest": digest},
    )
    assert result.status_code == 200, result.text
    return result.json()["import_id"], digest


def propose(client, h, business, import_id, budget=100000):
    return client.post(
        f"/api/businesses/{business}/demo/{import_id}/launch",
        headers=h,
        json={"campaign_id": "campaign-launch", "budget_minor": budget},
    )


def test_launch_approval_results_and_baseline(accounts, monkeypatch):
    client, headers, a, b = accounts

    # The scenario must never reach external providers or live agent execution.
    async def forbidden(*args, **kwargs):
        raise AssertionError("Live execution called")

    monkeypatch.setattr("app.services.social.post_to_instagram", forbidden)
    monkeypatch.setattr(
        "app.orchestration.registry.AgentRegistry.get_or_create", forbidden
    )
    imp, checksum = import_sample(client, headers["alice"], a)
    task = propose(client, headers["alice"], a, imp)
    assert task.status_code == 200, task.text
    task = task.json()
    assert task["status"] == "pending_approval" and task["result"] is None
    assert set(task["ceo_review"]["departments"]) == {
        "finance",
        "marketing",
        "hr",
        "operations",
        "ceo",
    }
    assert {
        v["data"]["dataset_digest"] for v in task["ceo_review"]["departments"].values()
    } == {checksum}
    again = propose(client, headers["alice"], a, imp).json()
    assert again["id"] == task["id"]
    assert (
        client.post(
            f"/api/tasks/{task['id']}/approve", headers=headers["bob"]
        ).status_code
        == 403
    )
    response = client.post(f"/api/tasks/{task['id']}/approve", headers=headers["alice"])
    assert response.status_code == 200, response.text
    result = response.json()["result"]
    assert (
        result["fulfilled_units"] == 100 and result["baseline"]["fulfilled_units"] == 25
    )
    assert result["ceo_report"]["task_id"] == task["id"]
    assert (
        client.post(
            f"/api/tasks/{task['id']}/approve", headers=headers["alice"]
        ).status_code
        == 200
    )
    # Separate branches do not mutate business financial state or original stock.
    assert (
        client.get(
            f"/api/businesses/{a}/demo/{imp}/records/operations",
            headers=headers["alice"],
        ).json()["records"]["inventory"][0]["quantity"]
        == 150
    )


def test_isolation_all_demo_paths_and_unauthenticated(accounts):
    client, headers, a, b = accounts
    imp, _ = import_sample(client, headers["alice"], a)
    for suffix in [
        "",
        f"/{imp}/records/hr",
        f"/{imp}/references/ceo?q=launch",
        f"/{imp}/reset",
    ]:
        assert (
            client.get(
                f"/api/businesses/{a}/demo{suffix}", headers=headers["bob"]
            ).status_code
            == 403
        )
        assert client.get(f"/api/businesses/{a}/demo{suffix}").status_code == 401
    assert (
        client.get(
            f"/api/businesses/{b}/demo/{imp}/records/hr", headers=headers["bob"]
        ).status_code
        == 404
    )
    assert propose(client, headers["bob"], a, imp).status_code == 403
    assert (
        client.post(
            f"/api/businesses/{a}/demo/{imp}/reset",
            headers=headers["bob"],
            json={"digest": "a" * 64, "confirmation": "RESET SYNTHETIC DEMO"},
        ).status_code
        == 403
    )
    content = json.loads(SAMPLE.read_text())
    content["business_id"] = b
    response = client.post(
        f"/api/businesses/{a}/demo/imports",
        headers=headers["alice"],
        files={"file": ("forged.json", json.dumps(content))},
        data={"format": "json"},
    )
    assert response.status_code == 422


def test_reset_preserves_other_records_and_prevents_old_approval(accounts):
    client, headers, a, b = accounts
    imp, checksum = import_sample(client, headers["alice"], a)
    other, _ = import_sample(client, headers["bob"], b)
    task = propose(client, headers["alice"], a, imp).json()
    info = client.get(
        f"/api/businesses/{a}/demo/{imp}/reset", headers=headers["alice"]
    ).json()
    assert info["tasks"] == 1
    url = f"/api/businesses/{a}/demo/{imp}/reset"
    assert (
        client.post(
            url,
            headers=headers["alice"],
            json={"digest": checksum, "confirmation": "wrong"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            url,
            headers=headers["alice"],
            json={"digest": checksum, "confirmation": "RESET SYNTHETIC DEMO"},
        ).status_code
        == 200
    )
    assert (
        client.get(f"/api/businesses/{a}/demo", headers=headers["alice"]).json()[
            "imports"
        ]
        == []
    )
    assert (
        client.post(
            f"/api/tasks/{task['id']}/approve", headers=headers["alice"]
        ).status_code
        == 409
    )
    assert (
        client.get(
            f"/api/businesses/{b}/demo/{other}/records/hr", headers=headers["bob"]
        ).status_code
        == 200
    )
    assert (
        client.get(f"/api/businesses/{a}", headers=headers["alice"]).status_code == 200
    )
    new_imp, _ = import_sample(client, headers["alice"], a)
    assert new_imp != imp
    assert propose(client, headers["alice"], a, new_imp).json()["id"] != task["id"]


@pytest.mark.parametrize("mutation", ["payload", "expiry", "reject"])
def test_changed_expired_and_rejected_proposals_cannot_execute(accounts, mutation):
    client, headers, a, _ = accounts
    imp, _ = import_sample(client, headers["alice"], a)
    task = propose(client, headers["alice"], a, imp).json()
    # Test-only DB mutation models a stale/altered persisted snapshot.
    if mutation == "reject":
        assert (
            client.post(
                f"/api/tasks/{task['id']}/reject", headers=headers["alice"], json={}
            ).status_code
            == 200
        )
    else:
        changed = (
            {
                "approval_expires_at": (
                    datetime.now(timezone.utc) - timedelta(hours=1)
                ).isoformat()
            }
            if mutation == "expiry"
            else {"payload": {**task["payload"], "budget_minor": 1}}
        )
        import asyncio

        asyncio.run(
            app.state.db["tasks"].update_one({"task_id": task["id"]}, {"$set": changed})
        )
    assert (
        client.post(
            f"/api/tasks/{task['id']}/approve", headers=headers["alice"]
        ).status_code
        == 409
    )


def test_insufficient_budget_is_blocked(accounts):
    client, headers, a, _ = accounts
    imp, _ = import_sample(client, headers["alice"], a)
    task = propose(client, headers["alice"], a, imp, budget=10**12).json()
    assert task["status"] == "blocked" and not task["ceo_authorized"]
    assert (
        client.post(
            f"/api/tasks/{task['id']}/approve", headers=headers["alice"]
        ).status_code
        == 409
    )


def test_approved_demo_can_resume_after_interrupted_response(accounts):
    import asyncio

    client, headers, a, _ = accounts
    imp, _ = import_sample(client, headers["alice"], a)
    task = propose(client, headers["alice"], a, imp).json()
    # Simulate a process stopping after the existing approval write, before computation.
    asyncio.run(
        app.state.db["tasks"].update_one(
            {"task_id": task["id"]},
            {
                "$set": {
                    "status": "approved",
                    "approval_digest": task["proposal_digest"],
                    "approved_by": client.get(
                        "/api/auth/me", headers=headers["alice"]
                    ).json()["id"],
                }
            },
        )
    )
    response = client.post(f"/api/tasks/{task['id']}/approve", headers=headers["alice"])
    assert response.status_code == 200
    assert response.json()["status"] == "executed"


def test_rule_change_requires_new_proposal(accounts, monkeypatch):
    client, headers, a, _ = accounts
    imp, _ = import_sample(client, headers["alice"], a)
    task = propose(client, headers["alice"], a, imp).json()
    monkeypatch.setattr("app.services.demo_launch.RULE_VERSION", "launch-v2")
    assert (
        client.post(
            f"/api/tasks/{task['id']}/approve", headers=headers["alice"]
        ).status_code
        == 409
    )


def test_demo_revision_cannot_change_approved_content(accounts):
    client, headers, a, _ = accounts
    imp, _ = import_sample(client, headers["alice"], a)
    task = propose(client, headers["alice"], a, imp).json()
    response = client.post(
        f"/api/tasks/{task['id']}/revise",
        headers=headers["alice"],
        json={"payload": {**task["payload"], "budget_minor": 1}},
    )
    assert response.status_code == 409
    assert (
        client.post(
            f"/api/tasks/{task['id']}/release-budget", headers=headers["alice"]
        ).status_code
        == 409
    )
