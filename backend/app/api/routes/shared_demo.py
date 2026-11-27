from fastapi import APIRouter,Depends,Request
from ..deps import get_current_user
from ...services.shared_demo import create
from ...core.rate_limit import RateLimiter,rate_limit_dependency
router=APIRouter(prefix='/api/workflow-demo',tags=['fictional demo'])
@router.post('',dependencies=[Depends(rate_limit_dependency(RateLimiter(max_requests=10,window_seconds=60)))])
async def create_demo(request:Request,user=Depends(get_current_user)):
    return await create(request,user)
