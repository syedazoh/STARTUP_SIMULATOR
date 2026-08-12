"""API-facing RAG memory-inspector schemas (Phase 7)."""
from typing import Any, Dict, Optional

from pydantic import BaseModel


class MemoryEntryOut(BaseModel):
    document: str
    metadata: Dict[str, Any]
    # Vector distance to the search query — omitted (None) when browsing
    # recent entries without a query, since there's nothing to be distant from.
    distance: Optional[float] = None
