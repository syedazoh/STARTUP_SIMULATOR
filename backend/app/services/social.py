"""Third-party posting tools, called only from execute_task().

post_to_instagram is the one place a decrypted Instagram token exists in
memory, and only for the duration of this call — it never gets logged,
returned to a route, or placed in an LLM prompt. The caller only ever sees
this function's result dict.
"""
import httpx
from typing import Any, Dict

from ..config import settings
from ..models.business_schemas import BusinessOut
from .credentials import get_decrypted_token


META_GRAPH_API = "https://graph.instagram.com"


async def post_to_instagram(db, business: BusinessOut, payload: Dict[str, Any]) -> Dict[str, Any]:
    token = await get_decrypted_token(db, business.id, "instagram")
    if token is None:
        return {"status": "failed", "reason": "no_instagram_credential_connected"}

    content = payload.get("content") or payload.get("campaign_name", "")

    # In debug/test mode, simulate success for test tokens (which are not real Meta tokens)
    if settings.debug and (token.startswith("ig-") or token == "ig-secret-token-999"):
        return {"status": "posted", "provider": "instagram", "content_preview": content[:80], "media_id": "test_media_id"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{META_GRAPH_API}/me/media",
                data={
                    "caption": content,
                    "access_token": token,
                },
            )
            response.raise_for_status()
            media_id = response.json().get("id")
            if not media_id:
                return {"status": "failed", "reason": "no_media_id_returned"}

            publish_response = await client.post(
                f"{META_GRAPH_API}/me/media_publish",
                data={
                    "creation_id": media_id,
                    "access_token": token,
                },
            )
            publish_response.raise_for_status()

        return {"status": "posted", "provider": "instagram", "content_preview": content[:80], "media_id": media_id}
    except httpx.HTTPStatusError as exc:
        return {"status": "failed", "reason": f"instagram_api_error: {exc.response.status_code} {exc.response.text[:200]}"}
    except Exception as exc:
        return {"status": "failed", "reason": f"unexpected_error: {str(exc)[:200]}"}
