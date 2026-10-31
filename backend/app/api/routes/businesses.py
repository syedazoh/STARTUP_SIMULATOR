"""Business (onboarding) routes"""

from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, status

from ..deps import get_current_user, get_owned_business
from ...models.auth_schemas import UserOut
from ...models.business_schemas import BusinessCreate, BusinessOut

router = APIRouter(prefix="/api/businesses", tags=["businesses"])

DEFAULT_ENABLED_AGENTS = ["finance", "marketing", "hr", "operations", "ceo"]


def _to_business_out(doc: dict) -> BusinessOut:
    return BusinessOut(
        id=doc["business_id"],
        owner_user_id=doc["owner_user_id"],
        company_name=doc["company_name"],
        industry=doc["industry"],
        starting_budget=doc["starting_budget"],
        starting_customer_base=doc["starting_customer_base"],
        starting_headcount=doc["starting_headcount"],
        starting_resources=doc["starting_resources"],
        enabled_agents=doc.get("enabled_agents", DEFAULT_ENABLED_AGENTS),
        created_at=doc["created_at"],
    )


@router.post("", response_model=BusinessOut, status_code=status.HTTP_201_CREATED)
async def create_business(
    payload: BusinessCreate, request: Request, user: UserOut = Depends(get_current_user)
):
    business_id = str(uuid4())
    created_at = datetime.now(timezone.utc)
    enabled_agents = payload.enabled_agents or DEFAULT_ENABLED_AGENTS
    doc = {
        "business_id": business_id,
        "owner_user_id": user.id,
        "company_name": payload.company_name,
        "industry": payload.industry,
        "starting_budget": payload.starting_budget,
        "starting_customer_base": payload.starting_customer_base,
        "starting_headcount": payload.starting_headcount,
        "starting_resources": payload.starting_resources,
        "enabled_agents": enabled_agents,
        "created_at": created_at,
    }
    await request.app.state.db["businesses"].insert_one(doc)
    return _to_business_out(doc)


@router.get("", response_model=List[BusinessOut])
async def list_businesses(request: Request, user: UserOut = Depends(get_current_user)):
    cursor = request.app.state.db["businesses"].find({"owner_user_id": user.id})
    docs = await cursor.to_list(length=200)
    return [_to_business_out(doc) for doc in docs]


@router.get("/{business_id}", response_model=BusinessOut)
async def get_business(business: BusinessOut = Depends(get_owned_business)):
    return business


@router.get("/{business_id}/finances")
async def finances(
    request: Request, business: BusinessOut = Depends(get_owned_business)
):
    from ...services import ledger

    runtime = await request.app.state.agent_registry.get_or_create(business)
    return ledger.public_account(
        await ledger.account_for(request.app.state.db, business, runtime)
    )
