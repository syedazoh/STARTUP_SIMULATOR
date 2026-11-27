from hashlib import sha256
import json
from fastapi import APIRouter,Depends,File,Form,UploadFile,Request,HTTPException
from ..deps import get_owned_business
from ...services import retail_data
router=APIRouter(prefix='/api/businesses/{business_id}/retail',tags=['retail'])
@router.post('/preview')
async def preview(request:Request,file:UploadFile=File(...),format:str=Form('csv'),business=Depends(get_owned_business)):
    result=retail_data.parse(await file.read(retail_data.MAX_BYTES+1),format)
    result['digest']=sha256(json.dumps(result['rows'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {**result,'rows':result['rows'][:10],'summary':retail_data.summarize(result['rows'])}
@router.post('/import')
async def commit(request:Request,file:UploadFile=File(...),format:str=Form('csv'),expected_digest:str=Form(...),business=Depends(get_owned_business)):
    return await retail_data.import_rows(request.app.state.db,business,await file.read(retail_data.MAX_BYTES+1),format,expected_digest)
@router.get('')
async def report(request:Request,business=Depends(get_owned_business)):
    result=await retail_data.latest(request.app.state.db,business.id)
    return {k:v for k,v in result.items() if k not in {'_id','rows'}} if result else {'summary':None,'message':'No historical retail slice imported for this business.'}
