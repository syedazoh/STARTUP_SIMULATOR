"""Chroma-backed store for past agent decisions (RAG memory)"""
from typing import Any, Dict, List, Optional
from uuid import uuid4

import chromadb

from ..config import settings
from .embeddings import get_embedding_function


class DecisionMemoryStore:
    """Persists and retrieves past agent decisions as embedded documents in Chroma"""

    def __init__(self):
        self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self._collection = self._client.get_or_create_collection(
            name="agent_decisions",
            embedding_function=get_embedding_function(),
        )

    def add_decision(
        self,
        agent_id: str,
        event_type: str,
        summary_text: str,
        metadata: Dict[str, Any],
    ) -> str:
        doc_id = str(uuid4())
        self._collection.add(
            ids=[doc_id],
            documents=[summary_text],
            metadatas=[{"agent_id": agent_id, "event_type": event_type, **metadata}],
        )
        return doc_id

    def query_similar(self, agent_id: str, query_text: str, k: int = 3) -> List[Dict[str, Any]]:
        count = self._collection.count()
        if count == 0:
            return []
        results = self._collection.query(
            query_texts=[query_text],
            n_results=min(k, count),
            where={"agent_id": agent_id},
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
        results = self._collection.get(where={"agent_id": agent_id}, limit=limit)
        documents = results.get("documents") or []
        metadatas = results.get("metadatas") or []
        return [{"document": doc, "metadata": meta, "distance": None} for doc, meta in zip(documents, metadatas)]


_store_instance: Optional[DecisionMemoryStore] = None


def get_decision_memory_store() -> DecisionMemoryStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = DecisionMemoryStore()
    return _store_instance
