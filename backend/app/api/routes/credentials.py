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
from ...models.auth_schemas import UserOut
from ...models.business_schemas import BusinessOut
from ...models.credential_schemas import CredentialConnectIn, CredentialOut
from ...services.credentials import connect_credential, list_credentials, revoke_credential

router = APIRouter(prefix="/api/businesses/{business_id}/credentials", tags=["credentials"])

SUPPORTED_PROVIDERS = {"instagram"}


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


@router.post("/{provider}/connect", response_model=CredentialOut)
async def connect(
    provider: str,
    payload: CredentialConnectIn,
    request: Request,
    business: BusinessOut = Depends(get_owned_business),
    user: UserOut = Depends(get_current_user),
):
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Unsupported provider: {provider}")

    doc = await connect_credential(
        request.app.state.db, business.id, provider, payload.access_token, payload.scopes, user.id
    )
    return _to_credential_out(doc)


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(provider: str, request: Request, business: BusinessOut = Depends(get_owned_business)):
    revoked = await revoke_credential(request.app.state.db, business.id, provider)
    if not revoked:
        raise HTTPException(status_code=404, detail="No credential connected for this provider")
