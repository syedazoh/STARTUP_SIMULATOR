"""RAG decision-memory inspector routes (business-scoped).

Every agent now writes to the same Chroma-backed DecisionMemoryStore
Finance originated (see rag/store.py) — this just exposes it for reading.
Memories are namespaced by the live agent's own agent_id (e.g.
"finance_<business_id>"), so results are automatically scoped to both the
business and the agent without a separate collection per agent.
"""
from typing import List, Optional
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Query

from ..deps import get_owned_business
from ...models.business_schemas import BusinessOut
from ...models.memory_schemas import MemoryEntryOut
from ...rag import get_decision_memory_store

router = APIRouter(prefix="/api/businesses/{business_id}/agents/{agent_key}/memory", tags=["memory"])


@router.get("", response_model=List[MemoryEntryOut])
async def get_agent_memory(
    agent_key: str,
    request: Request,
    business: BusinessOut = Depends(get_owned_business),
    query: Optional[str] = Query(default=None, max_length=1000),
    k: int = Query(default=10, ge=1, le=100),
):
    runtime = await request.app.state.agent_registry.get_or_create(business)
    agent = runtime.agent_manager.agents.get(agent_key)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_key}")

    try:
        store = get_decision_memory_store()
        if query:
            results = await asyncio.to_thread(store.query_similar, agent.agent_id, query, k=k)
        else:
            results = await asyncio.to_thread(store.get_recent, agent.agent_id, limit=k)
        return [MemoryEntryOut(**r) for r in results]
    except Exception as exc:
        logging.getLogger(__name__).warning("Decision memory unavailable (%s)", type(exc).__name__)
        raise HTTPException(503, "Decision memory is unavailable. Try browsing without a search, or check storage and the embedding model cache.") from None
