"""MongoDB connection management with an in-memory fallback.

The app is designed around MongoDB persistence (snapshots, decision logs, run
summaries).  When MongoDB is not reachable (e.g. local dev without a running
``mongod``), the routes that touch the database would otherwise crash with a
``ServerSelectionTimeoutError``.

To keep the simulator usable without MongoDB, ``connect_to_mongo()`` probes the
server and, if it is unavailable, installs a lightweight in-memory store that
implements the small subset of the Motor/pymongo API the routes use:

- ``db[collection].insert_one(doc)`` / ``insert_many(docs)``
- ``db[collection].update_one(filter, update)`` (``$set``)
- ``db[collection].delete_one(filter)``
- ``db[collection].find(query).sort(field, -1).limit(n).to_list(n)``

This keeps all existing route code unchanged while allowing the platform to run
with or without a database.
"""
import logging
from copy import deepcopy
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from ..config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory fallback implementation of the Motor API subset used by the app
# ---------------------------------------------------------------------------


class InMemoryCursor:
    """Async cursor supporting the chained API used by the routes."""

    def __init__(self, docs: List[Dict[str, Any]], sort_field: Optional[str], sort_dir: int):
        self._docs = docs
        if sort_field is not None:
            self._docs = sorted(
                self._docs,
                key=lambda d: d.get(sort_field),
                reverse=(sort_dir == -1),
            )

    async def to_list(self, length: Optional[int] = None) -> List[Dict[str, Any]]:
        docs = deepcopy(self._docs)
        if length is not None:
            docs = docs[:length]
        return docs


class InMemoryCollection:
    """In-memory stand-in for a MongoDB collection."""

    def __init__(self, name: str):
        self.name = name
        self._docs: List[Dict[str, Any]] = []
        self._seq = 0

    async def insert_one(self, document: Dict[str, Any]) -> None:
        doc = deepcopy(document)
        if "_id" not in doc:
            self._seq += 1
            doc["_id"] = self._seq
        self._docs.append(doc)

    async def insert_many(self, documents: List[Dict[str, Any]]) -> None:
        for document in documents:
            await self.insert_one(document)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any]) -> None:
        matched = self._find(query)
        if not matched:
            return
        doc = matched[0]
        if "$set" in update:
            doc.update(deepcopy(update["$set"]))
        else:
            doc.update(deepcopy(update))

    async def delete_one(self, query: Dict[str, Any]) -> None:
        matched = self._find(query)
        if matched:
            self._docs.remove(matched[0])

    def _find(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Every call site in this codebase queries by plain equality — no
        # Mongo operator (`$in`, `$gt`, etc.) is used against the in-memory
        # fallback today. Rather than silently matching nothing (or the
        # wrong documents) if one shows up, fail loudly so a future feature
        # that needs one gets caught in dev instead of shipping broken.
        for key, value in query.items():
            if isinstance(value, dict) and any(k.startswith("$") for k in value):
                raise NotImplementedError(
                    f"In-memory Mongo fallback does not support query operators "
                    f"(got {value!r} for field {key!r}). Run against real MongoDB, "
                    f"or extend InMemoryCollection._find to support this operator."
                )
        results = []
        for doc in self._docs:
            if all(doc.get(k) == v for k, v in query.items()):
                results.append(doc)
        return results

    def find(self, query: Optional[Dict[str, Any]] = None) -> "InMemoryQueryBuilder":
        return InMemoryQueryBuilder(self, query or {})


class InMemoryQueryBuilder:
    """Chainable query builder: ``find(...).sort(...).limit(...)``."""

    def __init__(self, collection: InMemoryCollection, query: Dict[str, Any]):
        self._collection = collection
        self._query = query
        self._sort_field: Optional[str] = None
        self._sort_dir = 1

    def sort(self, field: str, direction: int = 1) -> "InMemoryQueryBuilder":
        self._sort_field = field
        self._sort_dir = direction
        return self

    def limit(self, n: int) -> "InMemoryQueryBuilder":
        self._limit = n
        return self

    def _build_cursor(self) -> InMemoryCursor:
        docs = self._collection._find(self._query)
        cursor = InMemoryCursor(docs, self._sort_field, self._sort_dir)
        return cursor

    async def to_list(self, length: Optional[int] = None) -> List[Dict[str, Any]]:
        cursor = self._build_cursor()
        limit = length if length is not None else getattr(self, "_limit", None)
        return await cursor.to_list(length=limit)

    def __getattr__(self, item: str) -> Any:
        # Other cursor methods (e.g. sort/limit combos) fall back to the cursor.
        cursor = self._build_cursor()
        return getattr(cursor, item)


class InMemoryDatabase:
    """In-memory stand-in for an AsyncIOMotorDatabase."""

    def __init__(self) -> None:
        self._collections: Dict[str, InMemoryCollection] = {}

    def __getitem__(self, name: str) -> InMemoryCollection:
        if name not in self._collections:
            self._collections[name] = InMemoryCollection(name)
        return self._collections[name]

    async def close(self) -> None:
        self._collections.clear()


# ---------------------------------------------------------------------------
# Connection lifecycle
# ---------------------------------------------------------------------------


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Any = None


mongodb = MongoDB()


async def connect_to_mongo() -> None:
    """Connect to MongoDB, falling back to an in-memory store when unavailable."""
    try:
        client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=2000)
        # Force a round-trip so an unreachable server fails fast and we fall back.
        await client.admin.command("ping")
    except Exception as exc:
        logger.warning(
            "MongoDB unavailable at %s (%s); using in-memory fallback. "
            "Data will NOT persist across restarts.",
            settings.mongodb_url,
            exc,
        )
        mongodb.client = None
        mongodb.db = InMemoryDatabase()
        return

    mongodb.client = client
    mongodb.db = client[settings.mongodb_db_name]


async def close_mongo_connection() -> None:
    if mongodb.client is not None:
        mongodb.client.close()
    if isinstance(mongodb.db, InMemoryDatabase):
        await mongodb.db.close()
    mongodb.db = None


def get_database() -> Any:
    if mongodb.db is None:
        raise RuntimeError("MongoDB is not connected. Call connect_to_mongo() first.")
    return mongodb.db


async def ping_mongo() -> bool:
    if mongodb.client is None:
        return False
    try:
        await mongodb.client.admin.command("ping")
        return True
    except Exception:
        return False

