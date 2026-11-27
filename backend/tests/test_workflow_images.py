"""Mock PNG generation; asserts shared jobs, authorization, revisions and recovery."""
import io
from uuid import uuid4
from PIL import Image
from fastapi import HTTPException
from tests.test_agent_workflow import client,setup
from app.services import workflow_images,jobs
from app.config import settings
from app.models.business_schemas import BusinessOut


def png():
    out=io.BytesIO();Image.new('RGB',(32,32),(80,40,100)).save(out,'PNG');return out.getvalue()

def test_two_roles_use_same_generation_job_download_revision_and_failure_retry(client,monkeypatch):
    owner,other,bid,root=setup(client);monkeypatch.setattr(settings,'background_jobs_enabled',True);monkeypatch.setattr(settings,'openai_api_key','fixture-only-not-a-key')
    calls=[];fail=[False]
    async def generate(prompt,parent_bytes=None,key=None):
        calls.append((prompt,bool(parent_bytes),key))
        if fail[0]:raise workflow_images.ImageRejected(422,'Injected fixture image failure')
        return png(),'mock-image-provider'
    monkeypatch.setattr(workflow_images,'generate',generate)
    # Exercise the actual durable queue's worker/lease/handler path.
    import asyncio
    async def work():return await jobs.run_once(client.app.state.db,client.app.state.agent_registry)
    for role in ['marketing','strategy']:
        body={'request_id':str(uuid4()),'brief':'Illustrate a fictional desk kit concept, purple and beige.'}
        path=root+f'/{role}/images';one=client.post(path,headers=owner,json=body);assert one.status_code==200,one.text
        assert client.post(path,headers=owner,json=body).json()['job_id']==one.json()['job_id']
        result=client.portal.call(work);assert result['status']=='succeeded',result;aid=result['result']['artifact_id']
        image_url=root+f'/{role}/artifacts/{aid}/image';image=client.get(image_url,headers=owner);assert image.status_code==200;assert image.content==png();assert image.headers['content-type']=='image/png'
        assert client.get(image_url,headers=other).status_code==403
        assert client.get(image_url+'?download=true',headers=owner).headers['content-disposition'].startswith('attachment')
        assert 'image_bytes' not in str(client.get(root+f'/{role}/conversation',headers=owner).json())
        revision=client.post(path,headers=owner,json={'request_id':str(uuid4()),'brief':'Change the background to warm beige.','parent_artifact_id':aid});assert revision.status_code==200,revision.text
        result=client.portal.call(work);assert result['status']=='succeeded';assert calls[-1][1] is True
        assert client.get(image_url,headers=owner).content==png(),'Original image must remain unchanged'
        foreign=client.post(root+'/finance/images',headers=owner,json={'request_id':str(uuid4()),'brief':'Revise the image.','parent_artifact_id':aid});assert foreign.status_code==404
    fail[0]=True;failed=client.post(root+'/operations/images',headers=owner,json={'request_id':str(uuid4()),'brief':'Illustrate a delivery checklist.'}).json();result=client.portal.call(work);assert result['status']=='failed'
    fail[0]=False;retry=client.post(f'/api/businesses/{bid}/jobs/{failed["job_id"]}/retry',headers=owner);assert retry.status_code==200,retry.text
    recovered=client.portal.call(work);assert recovered['status']=='succeeded';assert recovered['job_id']==failed['job_id']
    assert client.post(root+'/finance/images',headers=owner,json={'request_id':str(uuid4()),'brief':'Draw a sales chart.'}).status_code==422

def test_recovered_image_job_never_regenerates_an_uncertain_provider_request(client,monkeypatch):
    owner,other,bid,root=setup(client);monkeypatch.setattr(settings,'background_jobs_enabled',True);monkeypatch.setattr(settings,'openai_api_key','fixture-only')
    calls=[]
    async def uncertain(*args,**kwargs):
        calls.append(1);raise jobs.Uncertain('Injected unknown provider outcome')
    monkeypatch.setattr(workflow_images,'generate',uncertain)
    queued=client.post(root+'/finance/images',headers=owner,json={'request_id':str(uuid4()),'brief':'Illustrate a fictional budget decision.'}).json()
    async def work():return await jobs.run_once(client.app.state.db,client.app.state.agent_registry)
    result=client.portal.call(work);assert result['status']=='reconciliation_required';assert len(calls)==1
    response=client.post(f'/api/businesses/{bid}/jobs/{queued["job_id"]}/retry',headers=owner);assert response.status_code==409
    assert len(calls)==1


def test_fixed_origin_image_adapter_validates_response_and_classifies_provider_errors(monkeypatch):
    import asyncio,base64,httpx
    monkeypatch.setattr(settings,'openai_api_key','fixture-private-value')
    original=httpx.AsyncClient
    requests=[];response_code=[200]
    def handler(request):
        requests.append(request)
        assert request.url.host=='api.openai.com'
        assert request.headers['authorization']=='Bearer fixture-private-value'
        assert request.headers['idempotency-key']=='stable-fixture-key'
        if response_code[0]!=200:return httpx.Response(response_code[0],json={'error':'Untrusted diagnostics must not reach UI'})
        return httpx.Response(200,json={'data':[{'b64_json':base64.b64encode(png()).decode()}]})
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs))
    async def check():
        content,provider=await workflow_images.generate('Fictional concept',key='stable-fixture-key');assert content==png();assert provider.startswith('openai:')
        await workflow_images.generate('Warm beige revision',parent_bytes=png(),key='stable-fixture-key')
        assert requests[-1].url.path=='/v1/images/edits';assert 'multipart/form-data' in requests[-1].headers['content-type']
        import pytest
        response_code[0]=429
        with pytest.raises(workflow_images.ImageRejected):await workflow_images.generate('Concept',key='stable-fixture-key')
        response_code[0]=503
        with pytest.raises(jobs.Uncertain):await workflow_images.generate('Concept',key='stable-fixture-key')
    asyncio.run(check())
