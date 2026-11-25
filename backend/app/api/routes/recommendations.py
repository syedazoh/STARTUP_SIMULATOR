from fastapi import APIRouter,Depends,Request
from ..deps import get_owned_business
from ...models.business_schemas import BusinessOut
from ...models.recommendation_schemas import RecommendationIn,RecommendationDecision,RecommendationRevision
from ...services import recommendations
from ...core.rate_limit import RateLimiter,rate_limit_dependency
router=APIRouter(prefix='/api/businesses/{business_id}/recommendations',tags=['recommendations'])
limit=Depends(rate_limit_dependency(RateLimiter(max_requests=30,window_seconds=60)))
@router.get('')
async def list_saved(request:Request,business:BusinessOut=Depends(get_owned_business)):return await recommendations.list_saved(request.app.state.db,business)
@router.post('',dependencies=[limit])
async def create(payload:RecommendationIn,request:Request,business:BusinessOut=Depends(get_owned_business)):return await recommendations.create(request.app.state.db,request.app.state.agent_registry,business,payload)
@router.post('/{plan_id}/decision',dependencies=[limit])
async def decide(plan_id:str,payload:RecommendationDecision,request:Request,business:BusinessOut=Depends(get_owned_business)):return await recommendations.decide(request.app.state.db,request.app.state.agent_registry,business,plan_id,payload)
@router.put('/{plan_id}',dependencies=[limit])
async def revise(plan_id:str,payload:RecommendationRevision,request:Request,business:BusinessOut=Depends(get_owned_business)):return await recommendations.revise(request.app.state.db,request.app.state.agent_registry,business,plan_id,payload)
