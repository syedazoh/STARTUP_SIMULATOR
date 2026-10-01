"""Business profile routes (business-scoped).

The profile is the canonical record agents draw context from, so writes here
replace the whole nested document (PUT, not PATCH) to avoid ambiguity about
which fields a partial update was meant to touch.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request

from ..deps import get_owned_business
from ...core.rate_limit import RateLimiter, rate_limit_dependency
from ...database.utils import find_one
from ...models.business_profile_schemas import (
    BusinessProfileIn,
    BusinessProfileOut,
    CustomContextIn,
    CustomContextNote,
)
from ...models.business_schemas import BusinessOut

router = APIRouter(prefix="/api/businesses/{business_id}/profile", tags=["business_profiles"])

_profile_rate_limiter = RateLimiter(max_requests=30, window_seconds=60)
_rate_limited = Depends(rate_limit_dependency(_profile_rate_limiter))

# custom_context round-trips in full on every profile read/write and gets
# copied into every chat prompt (services/chat.py) — capped so an
# unbounded note history can't blow out the LLM's context window.
MAX_CUSTOM_CONTEXT_NOTES = 50


def _to_profile_out(doc: dict) -> BusinessProfileOut:
    return BusinessProfileOut(
        business_id=doc["business_id"],
        brand=doc.get("brand", {}),
        product=doc.get("product", {}),
        marketing=doc.get("marketing", {}),
        finance=doc.get("finance", {}),
        operations=doc.get("operations", {}),
        custom_context=doc.get("custom_context", []),
        updated_at=doc["updated_at"],
    )


def _empty_profile(business_id: str) -> BusinessProfileOut:
    return BusinessProfileOut(business_id=business_id, updated_at=datetime.now(timezone.utc))


@router.get("", response_model=BusinessProfileOut)
async def get_profile(request: Request, business: BusinessOut = Depends(get_owned_business)):
    doc = await find_one(request.app.state.db["business_profiles"], {"business_id": business.id})
    if doc is None:
        return _empty_profile(business.id)
    return _to_profile_out(doc)


@router.post("", response_model=BusinessProfileOut, dependencies=[_rate_limited])
async def upsert_profile(
    payload: BusinessProfileIn, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    db = request.app.state.db
    existing = await find_one(db["business_profiles"], {"business_id": business.id})
    updated_at = datetime.now(timezone.utc)

    doc = {
        "business_id": business.id,
        "brand": payload.brand.model_dump(),
        "product": payload.product.model_dump(),
        "marketing": payload.marketing.model_dump(),
        "finance": payload.finance.model_dump(),
        "operations": payload.operations.model_dump(),
        # custom_context is appended via its own endpoint, not replaced here.
        "custom_context": existing.get("custom_context", []) if existing else [],
        "updated_at": updated_at,
    }

    if existing is None:
        await db["business_profiles"].insert_one(doc)
    else:
        await db["business_profiles"].update_one({"business_id": business.id}, {"$set": doc})

    return _to_profile_out(doc)


@router.post("/context", response_model=BusinessProfileOut, dependencies=[_rate_limited])
async def add_context_note(
    payload: CustomContextIn, request: Request, business: BusinessOut = Depends(get_owned_business)
):
    db = request.app.state.db
    note = CustomContextNote(label=payload.label, text=payload.text)
    existing = await find_one(db["business_profiles"], {"business_id": business.id})
    updated_at = datetime.now(timezone.utc)

    if existing is None:
        doc = _empty_profile(business.id).model_dump()
        doc["custom_context"] = [note.model_dump()]
        doc["updated_at"] = updated_at
        await db["business_profiles"].insert_one(doc)
    else:
        custom_context = (existing.get("custom_context", []) + [note.model_dump()])[-MAX_CUSTOM_CONTEXT_NOTES:]
        await db["business_profiles"].update_one(
            {"business_id": business.id},
            {"$set": {"custom_context": custom_context, "updated_at": updated_at}},
        )
        doc = {**existing, "custom_context": custom_context, "updated_at": updated_at}

    # TODO(Phase 7): re-embed custom_context into this business's RAG collection.
    return _to_profile_out(doc)
