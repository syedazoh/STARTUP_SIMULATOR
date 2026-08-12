"""Credential vault: connect, list, revoke, and (internal-only) decrypt.

get_decrypted_token is the one function in this whole codebase allowed to
produce a plaintext third-party token, and it's not imported by any route —
only by tool functions like services/social.py's post_to_instagram, which
use the value for a single outbound call and then let it fall out of scope.
No admin-facing code path exists here at all; that boundary is a property of
what this module chooses to expose, not a permissions check a future route
could accidentally bypass.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..core.crypto import decrypt_data_key, decrypt_with_data_key, encrypt_with_data_key
from ..database.utils import find_one
from .audit import record_audit


async def connect_credential(
    db,
    business_id: str,
    provider: str,
    access_token: str,
    scopes: List[str],
    connected_by_user_id: str,
) -> Dict[str, Any]:
    user_doc = await find_one(db["users"], {"user_id": connected_by_user_id})
    data_key = decrypt_data_key(user_doc["encrypted_data_key"])
    encrypted_payload = encrypt_with_data_key(data_key, access_token)

    doc = {
        "business_id": business_id,
        "provider": provider,
        "encrypted_payload": encrypted_payload,
        "encryption_key_id": connected_by_user_id,
        "connected_by_user_id": connected_by_user_id,
        "connected_at": datetime.now(timezone.utc),
        "last_used_at": None,
        "scopes": scopes,
    }

    existing = await find_one(db["credentials"], {"business_id": business_id, "provider": provider})
    if existing is None:
        await db["credentials"].insert_one(doc)
    else:
        await db["credentials"].update_one({"business_id": business_id, "provider": provider}, {"$set": doc})

    await record_audit(
        db, connected_by_user_id, business_id, "credential_connected", target_id=provider
    )
    return doc


async def list_credentials(db, business_id: str) -> List[Dict[str, Any]]:
    cursor = db["credentials"].find({"business_id": business_id})
    return await cursor.to_list(length=50)


async def revoke_credential(db, business_id: str, provider: str, user_id: str) -> bool:
    existing = await find_one(db["credentials"], {"business_id": business_id, "provider": provider})
    if existing is None:
        return False
    await db["credentials"].delete_one({"business_id": business_id, "provider": provider})
    await record_audit(db, user_id, business_id, "credential_revoked", target_id=provider)
    return True


async def get_decrypted_token(db, business_id: str, provider: str) -> Optional[str]:
    cred = await find_one(db["credentials"], {"business_id": business_id, "provider": provider})
    if cred is None:
        return None

    user_doc = await find_one(db["users"], {"user_id": cred["encryption_key_id"]})
    data_key = decrypt_data_key(user_doc["encrypted_data_key"])
    token = decrypt_with_data_key(data_key, cred["encrypted_payload"])

    await db["credentials"].update_one(
        {"business_id": business_id, "provider": provider},
        {"$set": {"last_used_at": datetime.now(timezone.utc)}},
    )
    return token
