"""Chroma-backed store for past agent decisions (RAG memory).

Each agent gets its own namespaced collection (e.g., "agent_decisions_finance_<business_id>")
for better isolation and query performance.
"""
from typing import Any, Dict, List, Optional
from uuid import uuid4

import chromadb

from ..config import settings
from .embeddings import get_embedding_function


class DecisionMemoryStore:
    """Persists and retrieves past agent decisions as embedded documents in Chroma.

    Each agent has its own collection named "agent_decisions_{agent_id}".
    """

    def __init__(self):
        self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self._collections: Dict[str, Any] = {}

    def _get_collection(self, agent_id: str):
        """Get or create a collection for the given agent_id."""
        if agent_id not in self._collections:
            collection_name = f"agent_decisions_{agent_id}"
            self._collections[agent_id] = self._client.get_or_create_collection(
                name=collection_name,
                embedding_function=get_embedding_function(),
            )
        return self._collections[agent_id]

    def add_decision(
        self,
        agent_id: str,
        event_type: str,
        summary_text: str,
        metadata: Dict[str, Any],
    ) -> str:
        doc_id = str(uuid4())
        collection = self._get_collection(agent_id)
        collection.add(
            ids=[doc_id],
            documents=[summary_text],
            metadatas=[{"agent_id": agent_id, "event_type": event_type, **metadata}],
        )
        return doc_id

    def query_similar(self, agent_id: str, query_text: str, k: int = 3) -> List[Dict[str, Any]]:
        collection = self._get_collection(agent_id)
        count = collection.count()
        if count == 0:
            return []
        results = collection.query(
            query_texts=[query_text],
            n_results=min(k, count),
        )
        documents = results.get("documents") or [[]]
        metadatas = results.get("metadatas") or [[]]
        distances = results.get("distances") or [[]]
        return [
            {"document": doc, "metadata": meta, "distance": dist}
            for doc, meta, dist in zip(documents[0], metadatas[0], distances[0])
        ]

    def get_recent(self, agent_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Browse an agent's memories without a search query — for the memory
        inspector's default view. Chroma's .get() has no relevance ranking or
        recency ordering of its own, so this returns whatever order the
        collection yields and lets the caller decide whether to reverse it."""
        collection = self._get_collection(agent_id)
        results = collection.get(limit=limit)
        documents = results.get("documents") or []
        metadatas = results.get("metadatas") or []
        return [{"document": doc, "metadata": meta, "distance": None} for doc, meta in zip(documents, metadatas)]


_store_instance: Optional[DecisionMemoryStore] = None


def get_decision_memory_store() -> DecisionMemoryStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = DecisionMemoryStore()
    return _store_instance
