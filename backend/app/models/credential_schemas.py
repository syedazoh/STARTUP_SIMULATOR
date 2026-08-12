"""API-facing credential (vault) schemas.

Deliberately excludes the token/payload from every response shape — no
route in routes/credentials.py ever returns decrypted (or even encrypted)
material, only connection metadata.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CredentialConnectIn(BaseModel):
    # Mock connect flow (see routes/credentials.py): the owner supplies the
    # access token a real OAuth redirect would eventually hand back.
    access_token: str = Field(min_length=1)
    scopes: List[str] = Field(default_factory=list)


class CredentialOut(BaseModel):
    provider: str
    connected_by_user_id: str
    connected_at: datetime
    last_used_at: Optional[datetime] = None
    scopes: List[str] = Field(default_factory=list)
