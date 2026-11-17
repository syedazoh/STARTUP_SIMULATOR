import asyncio
from tests.test_account_isolation import accounts  # noqa: F401
from tests.test_automation_api import configured_worker_without_loop  # noqa: F401
from app.services import jobs


def grant(c, h, a, propose=False):
    r = c.post(
        f"/api/businesses/{a}/mcp-grants",
        headers=h["alice"],
        json={"departments": ["finance"], "allow_proposals": propose},
    )
    assert r.status_code == 200, r.text
    return r.json()


def rpc(c, token, method, params=None):
    return c.post(
        "/mcp/",
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/json, text/event-stream",
        },
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}},
    )


def test_protocol_and_token_boundaries(accounts):
    c, h, a, b = accounts
    g = grant(c, h, a)
    assert (
        rpc(
            c,
            g["token"],
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            },
        ).status_code
        == 200
    )
    r = rpc(c, g["token"], "tools/list")
    assert r.status_code == 200, r.text
    assert {t["name"] for t in r.json()["result"]["tools"]} == {
        "get_budget",
        "get_task_status",
        "search_knowledge",
        "propose_task",
    }
    assert (
        rpc(c, h["alice"]["Authorization"].split(" ", 1)[1], "tools/list").status_code
        == 401
    )
    assert (
        c.get(
            "/api/auth/me", headers={"Authorization": "Bearer " + g["token"]}
        ).status_code
        == 401
    )
    assert (
        c.post(
            "/mcp/",
            headers={
                "Authorization": "Bearer " + g["token"],
                "Origin": "https://evil.example",
            },
            json={},
        ).status_code
        == 403
    )


def test_proposals_are_queued_owner_reviewed_and_revocable(accounts):
    c, h, a, b = accounts
    g = grant(c, h, a, True)
    r = rpc(
        c,
        g["token"],
        "tools/call",
        {
            "name": "propose_task",
            "arguments": {
                "department": "finance",
                "action_type": "budget_request",
                "payload": {"amount": 25},
                "idempotency_key": "mcp-test",
            },
        },
    )
    assert r.status_code == 200 and not r.json()["result"].get("isError"), r.text
    assert c.get(f"/api/businesses/{a}/tasks", headers=h["alice"]).json() == []
    assert (
        asyncio.run(jobs.run_once(c.app.state.db, c.app.state.agent_registry))["status"]
        == "succeeded"
    )
    tasks = c.get(f"/api/businesses/{a}/tasks", headers=h["alice"]).json()
    assert tasks[0]["source"] == "mcp" and tasks[0]["status"] == "pending_approval"
    assert (
        c.post(
            f"/api/businesses/{b}/mcp-grants/{g['grant_id']}/revoke", headers=h["bob"]
        ).status_code
        == 404
    )
    assert (
        c.post(
            f"/api/businesses/{a}/mcp-grants/{g['grant_id']}/revoke", headers=h["alice"]
        ).status_code
        == 200
    )
    assert rpc(c, g["token"], "tools/list").status_code == 401


def test_readonly_capability_cannot_propose_and_foreign_task_hidden(accounts):
    c, h, a, b = accounts
    g = grant(c, h, a)
    foreign = c.post(
        f"/api/businesses/{b}/agents/finance/actions/budget-request",
        headers=h["bob"],
        json={"amount": 25},
    ).json()
    r = rpc(
        c,
        g["token"],
        "tools/call",
        {"name": "get_task_status", "arguments": {"task_id": foreign["id"]}},
    )
    assert r.json()["result"]["isError"]
    r = rpc(
        c,
        g["token"],
        "tools/call",
        {
            "name": "propose_task",
            "arguments": {
                "department": "finance",
                "action_type": "budget_request",
                "payload": {"amount": 25},
                "idempotency_key": "forbidden",
            },
        },
    )
    assert r.json()["result"]["isError"]
