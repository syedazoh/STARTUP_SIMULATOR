from pathlib import Path

import pytest
from fastapi import HTTPException

from app.database.mongodb import InMemoryDatabase
from app.services.demo_dataset import parse_upload, preview, commit_import, load_dataset

ROOT = Path(__file__).resolve().parents[2] / "datasets/product-launch-v1"


def test_csv_and_json_have_same_canonical_content():
    assert parse_upload((ROOT / "dataset.csv").read_bytes(), "csv") == parse_upload(
        (ROOT / "dataset.json").read_bytes(), "json"
    )


def test_invalid_csv_identifies_row_and_field():
    with pytest.raises(HTTPException) as exc:
        parse_upload(b"record_type,record_json\nsales,not-json", "csv")
    assert exc.value.status_code == 422
    assert exc.value.detail[0]["row"] == 2


@pytest.mark.asyncio
async def test_preview_commit_duplicate_and_isolation():
    db = InMemoryDatabase()
    data = parse_upload((ROOT / "dataset.json").read_bytes(), "json")
    result = await preview(db, "alice-business", data)
    assert await db["demo_datasets"].count_documents({}) == 0
    first = await commit_import(db, "alice-business", data, result["digest"])
    second = await commit_import(db, "alice-business", data, result["digest"])
    assert first["import_id"] == second["import_id"]
    assert second["duplicate"] is True
    assert await db["demo_datasets"].count_documents({}) == 1
    with pytest.raises(HTTPException) as exc:
        await load_dataset(db, "bob-business", first["import_id"])
    assert exc.value.status_code == 404
    with pytest.raises(HTTPException):
        await commit_import(db, "alice-business", data, "changed-after-preview")
    changed = data.model_copy(deep=True)
    changed.company.name = "Changed"
    with pytest.raises(HTTPException) as exc:
        await commit_import(
            db,
            "alice-business",
            changed,
            (await preview(db, "alice-business", changed))["digest"],
        )
    assert exc.value.status_code == 409


def test_invalid_numeric_csv_reports_physical_row():
    content = (
        (ROOT / "dataset.csv")
        .read_text()
        .replace('""quantity"": 150', '""quantity"": -1')
    )
    with pytest.raises(HTTPException) as exc:
        parse_upload(content.encode(), "csv")
    assert exc.value.detail[0]["row"] is not None
    assert "quantity" in exc.value.detail[0]["field"]


@pytest.mark.asyncio
async def test_reference_access_filters_before_ranking():
    from app.services.demo_dataset import retrieve_references

    db = InMemoryDatabase()
    data = parse_upload((ROOT / "dataset.json").read_bytes(), "json")
    from app.models.demo_dataset import Reference

    data.references.append(
        Reference(
            id="hr-private",
            title="Private candidate policy",
            version=1,
            department="hr",
            text="Candidate retention rules",
        )
    )
    check = await preview(db, "owner", data)
    imported = await commit_import(db, "owner", data, check["digest"])
    finance = await retrieve_references(
        db, "owner", imported["import_id"], "finance", "candidate retention"
    )
    hr = await retrieve_references(
        db, "owner", imported["import_id"], "hr", "candidate retention"
    )
    assert "hr-private" not in {r["citation"]["document_id"] for r in finance}
    assert "hr-private" in {r["citation"]["document_id"] for r in hr}


@pytest.mark.asyncio
async def test_concurrent_imports_create_one_snapshot():
    import asyncio

    db = InMemoryDatabase()
    data = parse_upload((ROOT / "dataset.json").read_bytes(), "json")
    check = await preview(db, "owner", data)
    results = await asyncio.gather(
        *(commit_import(db, "owner", data, check["digest"]) for _ in range(8))
    )
    assert len({r["import_id"] for r in results}) == 1
    assert await db["demo_datasets"].count_documents({}) == 1


@pytest.mark.parametrize(
    "content,format",
    [
        (b"{", "json"),
        (b"\xff", "json"),
        (b"record_type,record_json\nmetadata,{}\nmetadata,{}", "csv"),
    ],
)
def test_malformed_files_are_actionable(content, format):
    with pytest.raises(HTTPException) as exc:
        parse_upload(content, format)
    assert exc.value.status_code == 422
    assert exc.value.detail[0]["field"]


def test_oversize_file_fails_before_parsing():
    with pytest.raises(HTTPException) as exc:
        parse_upload(b"x" * (1024 * 1024 + 1), "json")
    assert exc.value.status_code == 413
