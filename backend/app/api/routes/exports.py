"""Tenant-authorized, bounded decision/event/task/role evidence downloads."""
from typing import Literal
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, Response
from ..deps import get_owned_business
from ...services.exports import evidence, csv_text

router = APIRouter(prefix='/api/businesses/{business_id}/evidence', tags=['evidence exports'])


@router.get('')
async def download(request: Request, business=Depends(get_owned_business),
    format: Literal['json', 'csv'] = 'json',
    kind: Literal['all', 'decision', 'event', 'task', 'role_result'] = 'all',
    limit: int = Query(default=500, ge=1, le=500)):
    bundle = await evidence(request.app.state.db, business.id, kind, limit)
    headers = {'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff',
        'Content-Disposition': f'attachment; filename="simulator-evidence.{format}"',
        'X-Export-Truncated': str(bundle['truncated']).lower()}
    if format == 'csv':
        return Response(csv_text(bundle), media_type='text/csv; charset=utf-8', headers=headers)
    return JSONResponse(bundle, headers=headers)
