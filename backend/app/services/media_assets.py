"""Bounded technical image validation and conditional task attachment.

This is not a brand assessment. Video awaits a bounded decoder/provider flow.
"""

import hashlib
import io
import os
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError
from pymongo import ReturnDocument
from starlette.concurrency import run_in_threadpool

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
FORMATS = {
    "JPEG": ({".jpg", ".jpeg"}, "image/jpeg"),
    "PNG": ({".png"}, "image/png"),
    "WEBP": ({".webp"}, "image/webp"),
}


def _safe_filename(filename: str) -> str:
    return os.path.basename((filename or "").replace("\\", "/")) or "upload"


def _validate_image(content, filename, media_type, content_type):
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 10 MiB limit")
    if media_type != "image":
        raise HTTPException(
            status_code=422,
            detail="Only validated images are supported; video review is not available",
        )
    if not content:
        raise HTTPException(status_code=422, detail="Upload an image with content")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as image:
                fmt, size = image.format, image.size
                if fmt not in FORMATS or size[0] * size[1] > MAX_IMAGE_PIXELS:
                    raise ValueError("unsupported format or dimensions")
                if getattr(image, "n_frames", 1) != 1:
                    raise ValueError("animated images are not supported")
                image.verify()
            with Image.open(io.BytesIO(content)) as image:
                image.load()
        extensions, detected_type = FORMATS[fmt]
        if Path(_safe_filename(filename)).suffix.lower() not in extensions:
            raise ValueError("filename does not match image format")
        if content_type and content_type != detected_type:
            raise ValueError("declared type does not match image format")
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise HTTPException(
            status_code=422,
            detail="Upload a valid, non-animated JPEG, PNG or WebP image within 20 million pixels",
        ) from exc
    return {"content_type": detected_type, "width": size[0], "height": size[1]}


async def upload_asset(
    db,
    business_id: str,
    task: Dict[str, Any],
    filename: str,
    content: bytes,
    media_type: str,
    content_type=None,
) -> Dict[str, Any]:
    metadata = await run_in_threadpool(
        _validate_image, content, filename, media_type, content_type
    )
    asset_id = str(uuid4())
    business_dir = UPLOAD_DIR / business_id
    # Keep client filenames out of storage keys (also avoids overlong paths).
    file_path = (
        business_dir / f"{asset_id}{Path(_safe_filename(filename)).suffix.lower()}"
    )
    review = {
        "verdict": "approved",
        "basis": "technical_validation",
        "notes": "Image content validated. Brand suitability has not been assessed; owner approval is still required.",
    }
    doc = {
        "asset_id": asset_id,
        "business_id": business_id,
        "task_id": task["task_id"],
        "uploaded_by": "owner",
        "file_ref": str(file_path),
        "media_type": media_type,
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
        **metadata,
        "agent_review": review,
        "uploaded_at": datetime.now(timezone.utc),
    }
    business_dir.mkdir(parents=True, exist_ok=True)
    cas_started = False
    attachment_rejected = False
    try:
        await run_in_threadpool(file_path.write_bytes, content)
        await db["media_assets"].insert_one(doc)
        cas_started = True
        claimed = await db["tasks"].find_one_and_update(
            {
                "task_id": task["task_id"],
                "business_id": business_id,
                "status": "awaiting_asset",
                "ceo_authorized": True,
                "asset_id": task.get("asset_id"),
            },
            {
                "$set": {
                    "asset_id": asset_id,
                    "asset_sha256": doc["sha256"],
                    "status": "pending_approval",
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if claimed is None:
            attachment_rejected = True
            raise HTTPException(
                status_code=409,
                detail="Task changed during upload; refresh before trying again",
            )
    except BaseException:
        # A network/cancellation failure during CAS has an unknown outcome.
        # Preserve its evidence rather than deleting an asset the task may own.
        if not cas_started or attachment_rejected:
            file_path.unlink(missing_ok=True)
            await db["media_assets"].delete_one({"asset_id": asset_id})
        raise
    return doc
