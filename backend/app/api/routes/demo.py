"""Owner-authorized synthetic data API. Never accepts an uploaded tenant identity."""

from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    Request,
    UploadFile,
)
from pydantic import BaseModel, ConfigDict, Field

from ..deps import get_owned_business
from ...models.business_schemas import BusinessOut
from ...models.task_schemas import to_task_out
from ...services import demo_dataset as datasets
from ...services.tasks import create_task
from ...services.audit import record_audit

router = APIRouter(prefix="/api/businesses/{business_id}/demo", tags=["synthetic demo"])


class Command(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Launch(Command):
    campaign_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    budget_minor: int = Field(strict=True, ge=0, le=10**12)


class Reset(Command):
    digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmation: Literal["RESET SYNTHETIC DEMO"]


@router.post("/imports")
async def import_file(
    request: Request,
    file: UploadFile = File(...),
    format: Literal["json", "csv"] = Form(...),
    action: Literal["preview", "commit"] = Form("preview"),
    expected_digest: str = Form(""),
    business: BusinessOut = Depends(get_owned_business),
):
    try:
        content = await file.read(datasets.MAX_BYTES + 1)
    finally:
        await file.close()
    data = datasets.parse_upload(content, format)
    db = request.app.state.db
    if action == "preview":
        return await datasets.preview(db, business.id, data)
    result = await datasets.commit_import(db, business.id, data, expected_digest)
    await record_audit(
        db,
        business.owner_user_id,
        business.id,
        "demo_imported",
        target_id=result["import_id"],
    )
    return result


@router.get("")
async def dashboard(
    request: Request, business: BusinessOut = Depends(get_owned_business)
):
    docs = (
        await request.app.state.db["demo_datasets"]
        .find({"business_id": business.id, "active": True})
        .to_list(length=100)
    )
    output = []
    for doc in docs:
        tasks = (
            await request.app.state.db["tasks"]
            .find({"business_id": business.id, "demo_import_id": doc["import_id"]})
            .to_list(length=100)
        )
        output.append(
            {
                "import_id": doc["import_id"],
                "digest": doc["digest"],
                "data": doc["data"],
                "tasks": [
                    {
                        **to_task_out(t).model_dump(mode="json"),
                        "proposal_digest": t.get("proposal_digest"),
                        "approval_expires_at": t.get("approval_expires_at"),
                    }
                    for t in tasks
                ],
            }
        )
    return {"synthetic": True, "imports": output}


@router.get("/{import_id}/records/{department}")
async def records(
    import_id: str,
    department: str,
    request: Request,
    business: BusinessOut = Depends(get_owned_business),
):
    return await datasets.department_records(
        request.app.state.db, business.id, import_id, department
    )


@router.get("/{import_id}/references/{department}")
async def references(
    import_id: str,
    department: str,
    request: Request,
    q: str = Query(min_length=1, max_length=500),
    business: BusinessOut = Depends(get_owned_business),
):
    return await datasets.retrieve_references(
        request.app.state.db, business.id, import_id, department, q
    )


@router.post("/{import_id}/launch")
async def launch(
    import_id: str,
    payload: Launch,
    request: Request,
    business: BusinessOut = Depends(get_owned_business),
):
    doc = await datasets.load_dataset(request.app.state.db, business.id, import_id)
    task = await create_task(
        request.app.state.db,
        request.app.state.agent_registry,
        business,
        "marketing",
        "dataset_launch",
        {
            "import_id": import_id,
            "dataset_digest": doc["digest"],
            **payload.model_dump(),
        },
        source="dataset_demo",
        objective="Synthetic product launch",
        success_criteria="Measure fulfilled orders, contribution and goal attainment",
    )
    return to_task_out(task)


@router.get("/{import_id}/reset")
async def reset_preview(
    import_id: str,
    request: Request,
    business: BusinessOut = Depends(get_owned_business),
):
    return await datasets.reset_preview(request.app.state.db, business.id, import_id)


@router.post("/{import_id}/reset")
async def reset(
    import_id: str,
    payload: Reset,
    request: Request,
    business: BusinessOut = Depends(get_owned_business),
):
    return await datasets.reset_demo(
        request.app.state.db, business, import_id, payload.digest
    )
