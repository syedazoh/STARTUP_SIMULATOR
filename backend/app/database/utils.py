"""Compatibility helpers for interacting with either a real Motor database or
the in-memory fallback (see mongodb.py's InMemoryDatabase) — both only
guarantee the query-builder `.find(query).to_list(length)` path, not
`find_one`, and the fallback has no `create_index` at all.
"""
from typing import Any, Dict, Optional, Union


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


async def ensure_index(collection, keys: Union[str, list]) -> None:
    """Like ensure_unique_index but non-unique, and accepting either a single
    field name or a pymongo-style compound key list (e.g.
    [("business_id", 1), ("status", 1)]) for fields that are always queried
    together."""
    create_index = getattr(collection, "create_index", None)
    if create_index is None:
        return
    try:
        await create_index(keys)
    except Exception:
        pass


async def ensure_ttl_index(collection, field: str, expire_after_seconds: int) -> None:
    """Non-unique index on `field` with Mongo's TTL monitor deleting documents
    once `field` is older than `expire_after_seconds`. TTL deletion is
    asynchronous — Mongo sweeps roughly once a minute — so a query must still
    filter on the field itself rather than trusting the row to be gone."""
    create_index = getattr(collection, "create_index", None)
    if create_index is None:
        return
    try:
        await create_index(field, expireAfterSeconds=expire_after_seconds)
    except Exception:
        pass
