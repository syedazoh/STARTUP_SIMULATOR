"""Credential vault routes (business-scoped): connect / list / revoke.

Phase 3 ships a mock connect flow — the owner pastes the access token a real
OAuth redirect would eventually hand back, rather than this driving an
actual Meta OAuth dance (no registered app to redirect to yet). Swapping in
real OAuth later only touches the connect() handler below; the vault
(services/credentials.py) and execute_task's use of it don't change.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..deps import get_current_user, get_owned_business
from ...config import _DEFAULT_CREDENTIAL_MASTER_KEY, settings
from ...core.rate_limit import RateLimiter, rate_limit_dependency
from ...models.auth_schemas import UserOut
from ...models.business_schemas import BusinessOut
from ...models.credential_schemas import CredentialConnectIn, CredentialOut
from ...services.credentials import connect_credential, list_credentials, revoke_credential

router = APIRouter(prefix="/api/businesses/{business_id}/credentials", tags=["credentials"])

SUPPORTED_PROVIDERS = {"instagram"}

_credentials_rate_limiter = RateLimiter(max_requests=30, window_seconds=60)
_rate_limited = Depends(rate_limit_dependency(_credentials_rate_limiter))


def _to_credential_out(doc: dict) -> CredentialOut:
    return CredentialOut(
        provider=doc["provider"],
        connected_by_user_id=doc["connected_by_user_id"],
        connected_at=doc["connected_at"],
        last_used_at=doc.get("last_used_at"),
        scopes=doc.get("scopes", []),
    )


@router.get("", response_model=List[CredentialOut])
async def get_credentials(request: Request, business: BusinessOut = Depends(get_owned_business)):
    docs = await list_credentials(request.app.state.db, business.id)
    return [_to_credential_out(d) for d in docs]


@router.post("/{provider}/connect", response_model=CredentialOut, dependencies=[_rate_limited])
async def connect(
    provider: str,
    payload: CredentialConnectIn,
    request: Request,
    business: BusinessOut = Depends(get_owned_business),
    user: UserOut = Depends(get_current_user),
):
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Unsupported provider: {provider}")

    if settings.credential_master_key == _DEFAULT_CREDENTIAL_MASTER_KEY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot store credentials: a deployment-specific CREDENTIAL_MASTER_KEY must be configured.",
        )

    doc = await connect_credential(
        request.app.state.db, business.id, provider, payload.access_token, payload.scopes, user.id
    )
    return _to_credential_out(doc)


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_rate_limited])
async def disconnect(
    provider: str,
    request: Request,
    business: BusinessOut = Depends(get_owned_business),
    user: UserOut = Depends(get_current_user),
):
    revoked = await revoke_credential(request.app.state.db, business.id, provider, user.id)
    if not revoked:
        raise HTTPException(status_code=404, detail="No credential connected for this provider")
