"""Disposable REAL application + native auth + fixture DB/model/image providers.
Never deploy. No live account, persistent database, provider credentials or emails.
"""
import os
if os.environ.get('SIMULATOR_FIXTURE_ONLY') != '1':
    raise SystemExit('Requires SIMULATOR_FIXTURE_ONLY=1 for isolated acceptance only.')
import io
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from cryptography.fernet import Fernet
os.environ.update(GROQ_API_KEY='', OPENAI_API_KEY='fixture-only', SECRET_KEY=secrets.token_urlsafe(40), CREDENTIAL_MASTER_KEY=Fernet.generate_key().decode(), DEBUG='true', SUPABASE_AUTH_ENABLED='false', MONGODB_URL='mongodb://fixture-only', MONGODB_DB_NAME='shared_workflow_acceptance', BACKGROUND_JOBS_ENABLED='true', RAG_DENSE_ENABLED='false', RAG_RERANKER_ENABLED='false', RAG_ALLOW_MODEL_DOWNLOAD='false', CHROMA_PERSIST_DIR='/tmp/shared-workflow-chroma', ALLOWED_ORIGINS='http://localhost:3025,http://localhost:5175')
from mongomock_motor import AsyncMongoMockClient
import app.database.mongodb as mongodb
mongo = AsyncMongoMockClient()
mongodb.AsyncIOMotorClient = lambda *a, **kw: mongo
from app.main import app
from app.core.crypto import encrypt_data_key, generate_data_key
from app.core.security import hash_password
from app.services import agent_workflow, workflow_images
from app.models.workflow_schemas import WorkflowReply, Recommendation, Option
from PIL import Image
import uvicorn

class FixtureModel:
    def with_structured_output(self, schema):
        return self
    async def ainvoke(self, prompt):
        question=prompt.split('QUESTION ',1)[-1].split('\nREFERENCE ',1)[0]
        revision = 'revise' in question.lower() or 'change' in question.lower()
        return WorkflowReply(spoken_response='Synthetic provider fixture: review this proposed launch draft.', recommendation=Recommendation(what='Revised small launch proposal.' if revision else 'Review a small launch proposal.', why_now='Synthetic provider fixture: validate saved funds, positioning and capacity before owner review.', decision_needed='Owner reviews the exact saved submission; this recommendation authorizes nothing.', options=[Option(title='Small test',description='Validate assumptions before scaling.'), Option(title='Wait',description='Resolve missing evidence first.')], assumptions=['Browser acceptance provider double; not a live model answer.'], proposed_steps=['Check the saved goal.','Confirm the deadline.'], image_brief='Illustrate a fictional desk kit in purple and warm beige.'))
agent_workflow.get_groq_llm=lambda:FixtureModel()
async def image(prompt,parent_bytes=None,key=None):
    if 'fail fixture' in prompt.lower():
        raise workflow_images.ImageRejected(422,'Injected provider rejection; revise the brief before retrying.')
    out=io.BytesIO();Image.new('RGB',(192,128),(100,63,130) if not parent_bytes else (211,192,154)).save(out,'PNG')
    return out.getvalue(),'mock-image-provider'
workflow_images.generate=image
original=app.router.lifespan_context
@asynccontextmanager
async def lifespan(application):
    async with original(application):
        db=application.state.db;now=datetime.now(timezone.utc)
        for uid,email in [('workflow-owner','workflow@example.com'),('other-owner','other@example.com')]:
            await db['users'].insert_one({'user_id':uid,'email':email,'hashed_password':hash_password('fixture-password'),'role':'owner','encrypted_data_key':encrypt_data_key(generate_data_key()),'created_at':now})
        for bid,owner in [('original-business','workflow-owner'),('private-business','other-owner')]:
            await db['businesses'].insert_one({'business_id':bid,'owner_user_id':owner,'company_name':'Original synthetic company','industry':'Software','starting_budget':900,'starting_customer_base':0,'starting_headcount':5,'starting_resources':0,'enabled_agents':['ceo','finance','marketing','hr','operations'],'created_at':now})
        yield
app.router.lifespan_context=lifespan
if __name__=='__main__':uvicorn.run(app,host='0.0.0.0',port=8013,log_level='warning')
