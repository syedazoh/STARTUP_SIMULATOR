"""Compatibility helpers for interacting with either a real Motor database or
the in-memory fallback (see mongodb.py's InMemoryDatabase) — both only
guarantee the query-builder `.find(query).to_list(length)` path, not
`find_one`, and the fallback has no `create_index` at all.
"""
from typing import Any, Dict, Optional


async def find_one(collection, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    results = await collection.find(query).to_list(length=1)
    return results[0] if results else None


async def ensure_unique_index(collection, field: str) -> None:
    create_index = getattr(collection, "create_index", None)
    if create_index is None:
        return
    try:
        await create_index(field, unique=True)
    except Exception:
        pass
