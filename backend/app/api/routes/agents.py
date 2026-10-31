"""Agent status routes (business-scoped)"""

from fastapi import APIRouter, Depends, HTTPException, Request

from ..deps import get_owned_business
from ...models.business_schemas import BusinessOut

router = APIRouter(prefix="/api/businesses/{business_id}/agents", tags=["agents"])


@router.get("")
async def list_agents(
    request: Request, business: BusinessOut = Depends(get_owned_business)
):
    runtime = await request.app.state.agent_registry.get_or_create(business)
    statuses = await runtime.agent_manager.get_all_agents_status()
    await _overlay_finance(request, business, statuses)
    return statuses


@router.get("/{agent_key}")
async def get_agent(
    agent_key: str,
    request: Request,
    business: BusinessOut = Depends(get_owned_business),
):
    runtime = await request.app.state.agent_registry.get_or_create(business)
    agent = runtime.agent_manager.agents.get(agent_key)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_key}")
    result = await agent.get_status()
    statuses = {agent_key: result}
    await _overlay_finance(request, business, statuses)
    return statuses[agent_key]


@router.get("/{agent_key}/history")
async def get_agent_history(
    agent_key: str,
    request: Request,
    business: BusinessOut = Depends(get_owned_business),
    limit: int = 50,
):
    runtime = await request.app.state.agent_registry.get_or_create(business)
    agent = runtime.agent_manager.agents.get(agent_key)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_key}")

    db = request.app.state.db
    cursor = (
        db["agent_snapshots"]
        .find({"business_id": business.id, "agent_id": agent.agent_id})
        .sort("timestamp", -1)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs


async def _overlay_finance(request, business, statuses):
    from ...database.utils import find_one
    from ...services.ledger import amount, available

    account = await find_one(
        request.app.state.db["financial_accounts"], {"_id": business.id}
    )
    if account and "finance" in statuses:
        statuses["finance"].update(
            budget_pool=amount(available(account)),
            revenue=amount(account["revenue_minor"]),
            expenses=amount(account["expenses_minor"]),
        )
