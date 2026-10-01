"""Media asset upload + automated agent review (the requires_asset task path).

Uploaded files are saved to local disk under UPLOAD_DIR — fine for this
single-process dev setup, but swap for real object storage (S3 or similar)
before this handles real user uploads in prod, since local disk won't
survive a redeploy or scale past one instance.

_review_asset is a placeholder standing in for a real brand-fit/content
review model: Phase 4 ships the upload -> review -> task-transition wiring;
the review itself is a deterministic stub so the demo doesn't depend on an
external vision API.
"""
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
VALID_MEDIA_TYPES = {"image", "video"}


def _safe_filename(filename: str) -> str:
    """Strips any directory component from a client-supplied filename.

    filename comes straight from the multipart upload and is otherwise used
    to build a disk path (see upload_asset below) — without this, a filename
    like "../../etc/passthrough.png" would let the upload escape UPLOAD_DIR.
    """
    name = os.path.basename((filename or "").replace("\\", "/"))
    if not name or name in {".", ".."}:
        return "upload"
    return name


def _review_asset(filename: str, media_type: str) -> Dict[str, str]:
    if media_type not in VALID_MEDIA_TYPES:
        return {"verdict": "reshoot_requested", "notes": f"Unsupported media type: {media_type}"}
    if not filename:
        return {"verdict": "reshoot_requested", "notes": "No filename supplied — please re-upload."}
    return {"verdict": "approved", "notes": "Looks on-brand and ready to post."}


async def upload_asset(
    db, business_id: str, task: Dict[str, Any], filename: str, content: bytes, media_type: str
) -> Dict[str, Any]:
    asset_id = str(uuid4())
    business_dir = UPLOAD_DIR / business_id
    business_dir.mkdir(parents=True, exist_ok=True)
    file_ref = str(business_dir / f"{asset_id}_{_safe_filename(filename)}")
    with open(file_ref, "wb") as f:
        f.write(content)

    review = _review_asset(filename, media_type)
    doc = {
        "asset_id": asset_id,
        "business_id": business_id,
        "task_id": task["task_id"],
        "uploaded_by": "owner",
        "file_ref": file_ref,
        "media_type": media_type,
        "agent_review": review,
        "uploaded_at": datetime.now(timezone.utc),
    }
    await db["media_assets"].insert_one(doc)

    # Only an approved review clears the task to move into the normal
    # approval queue; a rejection or reshoot request sends it back to
    # awaiting_asset so the owner can upload again.
    next_status = "pending_approval" if review["verdict"] == "approved" else "awaiting_asset"
    await db["tasks"].update_one(
        {"task_id": task["task_id"]},
        {"$set": {"asset_id": asset_id, "status": next_status}},
    )
    return doc
