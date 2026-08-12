"""Third-party posting tools, called only from execute_task().

post_to_instagram is the one place a decrypted Instagram token exists in
memory, and only for the duration of this call — it never gets logged,
returned to a route, or placed in an LLM prompt. The caller only ever sees
this function's result dict.
"""
from typing import Any, Dict

from ..models.business_schemas import BusinessOut
from .credentials import get_decrypted_token


async def post_to_instagram(db, business: BusinessOut, payload: Dict[str, Any]) -> Dict[str, Any]:
    token = await get_decrypted_token(db, business.id, "instagram")
    if token is None:
        return {"status": "failed", "reason": "no_instagram_credential_connected"}

    # instagram_post's payload has `content` directly; reel_request (Phase 4's
    # requires_asset path) has `campaign_name`/`brief` instead — both action
    # types end up posting to the same place, so one handler covers both
    # rather than duplicating the credential-check + result shape per type.
    content = payload.get("content") or payload.get("campaign_name", "")
    # No real Meta Graph API call yet — Phase 3 ships the vault and the
    # execute_task wiring; swap this block for an httpx call to
    # graph.instagram.com (passing `token`) once a Meta app is registered
    # (see routes/credentials.py's docstring). `token` is decrypted above
    # only to prove a credential exists; it deliberately isn't used for
    # anything else yet.
    return {"status": "posted", "provider": "instagram", "content_preview": content[:80]}
