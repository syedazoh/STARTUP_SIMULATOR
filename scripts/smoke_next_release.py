"""Isolated local selected-topology smoke. No Caddy/ACME/cloud/provider actions.
Requires prebuilt fyp-local/rules images and real Docker. Own volumes only.
"""
import json
import os
import base64
import argparse
import time
import hashlib
import platform
from pathlib import Path
import secrets
import subprocess
import tempfile
from uuid import uuid4


def main(components=False,evaluation_output=None):
    root = Path(__file__).resolve().parents[1]
    project = 'fyp-release-' + uuid4().hex[:10]
    volumes = [project+'-'+suffix for suffix in ('mongo','chroma','uploads')]
    values = {'WORKER_IMAGE':os.environ.get('SMOKE_WORKER_IMAGE','startup-simulator-role-worker:fyp-local'),'BACKEND_IMAGE':os.environ.get('SMOKE_BACKEND_IMAGE','startup-simulator-backend:fyp-rules'),
        'FRONTEND_IMAGE':os.environ.get('SMOKE_FRONTEND_IMAGE','startup-simulator-next:fyp-local'),'CADDY_IMAGE':os.environ.get('SMOKE_CADDY_IMAGE','startup-simulator-caddy:fyp-next'),
        'MONGO_ROOT_USERNAME':'test_admin','MONGO_ROOT_PASSWORD':secrets.token_hex(24),
        'MONGO_WORKER_PASSWORD':secrets.token_hex(24), 'SECRET_KEY':secrets.token_hex(32),
        'WORKER_SECRET_KEY':secrets.token_hex(32),'CREDENTIAL_MASTER_KEY':base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
        'WORKER_CREDENTIAL_MASTER_KEY':base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
        'MONGO_VOLUME_NAME':volumes[0],'CHROMA_VOLUME_NAME':volumes[1],'UPLOAD_VOLUME_NAME':volumes[2],
        'APP_DOMAIN':'example.invalid','ACME_EMAIL':'operator@example.invalid','ALLOWED_ORIGINS':'https://example.invalid',
        'NEXT_PUBLIC_SUPABASE_URL':'https://example.supabase.co','NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY':'fixture-key',
        'GROQ_API_KEY':'','RAG_DENSE_ENABLED':'false','RAG_RERANKER_ENABLED':'false'}
    services = ['mongo','backend','ceo','marketing','finance','hr','operations','support','strategy','frontend']
    if components:
        services = ['mongo','backend','ceo','frontend']
    with tempfile.TemporaryDirectory(prefix=project) as directory:
        env_file = Path(directory)/'smoke.env'
        env_file.write_text(''.join(k+'='+v+'\n' for k,v in values.items()));env_file.chmod(0o600)
        compose = ['docker','compose','--env-file',str(env_file),'-p',project,'-f',str(root/'docker-compose.next.yml')]
        for volume in volumes:
            subprocess.run(['docker','volume','create',volume],check=True,stdout=subprocess.DEVNULL)
        runtime_env = {**os.environ, **values}  # Test values override any configured production env.
        try:
            startup=time.perf_counter()
            subprocess.run(compose+['up','-d','--wait','--wait-timeout','180',*services],check=True,env=runtime_env,timeout=600)
            startup_seconds=time.perf_counter()-startup
            code = 'evaluate_outputs='+repr(bool(evaluation_output))+'\ncomponents='+repr(components)+'\n'+'''import json,time,urllib.request,urllib.error,sys
base='http://127.0.0.1:8000';token=None
def call(path,body=None):
 h={'Content-Type':'application/json'}
 if token:h['Authorization']='Bearer '+token
 req=urllib.request.Request(base+path, data=json.dumps(body).encode() if body is not None else None,headers=h)
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
creds={'email':'local-release@example.com','password':'Local-acceptance-12345'}
call('/api/auth/register',creds);token=call('/api/auth/login',creds)['access_token']
bid=call('/api/businesses',{'company_name':'Synthetic release rehearsal','industry':'Software','starting_budget':1000})['id']
root='/api/businesses/'+bid+'/distributed-runs'
run=call(root,{'idempotency_key':'release-smoke','seed':17});url=root+'/'+run['run_id']
if components:
 for attempt in range(30):
  view=call(url)
  if view['roles'][0]['status']=='succeeded':break
  time.sleep(1)
 assert view['roles'][0]['status']=='succeeded'
 assert call(url+'/cancel',{})['status']=='cancelled'
 print(json.dumps({'components_only':True,'api_and_restricted_ceo_message':True,'cancellation':True,'full_seven_role_container_gate':'not_exercised'}))
 sys.exit(0)
for attempt in range(60):
 run=call(url)
 if run['status']=='ready_for_review':break
 if run['status']!='running':raise AssertionError(run['status'])
 time.sleep(1)
assert run['status']=='ready_for_review'
assert all(row['status']=='succeeded' for row in run['roles'])
assert run['roles'][2]['result']['recommended_budget_minor']==10000
task=call(url+'/proposal',{})
assert task['status']=='pending_approval'
result=call('/api/tasks/'+task['id']+'/approve',{'expected_fingerprint':task['approval_fingerprint']})
assert result['status']=='executed'
report=call(url)
assert report['task_status']=='executed' and report['recorded_outcome']
exports=call('/api/businesses/'+bid+'/evidence')
assert len([r for r in exports['records'] if r['record_type']=='role_result'])==7
print(json.dumps({'seven_container_roles':True,'owner_approval_and_execution':True,'evidence_export':True,'mode':'rule_based','task_status':'executed'}))
if evaluate_outputs:
 from scripts.evaluate_role_outputs import evaluate
 print('ROLE_EVALUATION '+json.dumps(evaluate()))
'''
            result = subprocess.run(compose+['exec','-T','backend','python','-c',code],check=True,capture_output=True,text=True,env=runtime_env)
            print(result.stdout.strip())
            if evaluation_output:
                report=json.loads(next(line.removeprefix('ROLE_EVALUATION ') for line in result.stdout.splitlines() if line.startswith('ROLE_EVALUATION ')))
                identifiers=subprocess.check_output(compose+['ps','-q',*services],env=runtime_env,text=True).splitlines()
                resource=subprocess.run(['docker','stats','--no-stream','--format','{{json .}}',*identifiers],capture_output=True,text=True,check=True)
                report['resource_snapshot']=[json.loads(line) for line in resource.stdout.splitlines()]
                report['resource_note']='Single post-workflow/reads snapshot, not peak RSS or model-loaded sizing; CPU percent uses Docker conventions.'
                report['topology_cold_start_seconds']=round(startup_seconds,3)
                report['docker_storage_driver']=subprocess.check_output(['docker','info','--format','{{.Driver}}'],text=True).strip()
                report['host']={'cpu_count':os.cpu_count(),'platform':platform.platform()}
                report['runtime_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
                report['runtime_source_sha256']=hashlib.sha256(b''.join((root/p).read_bytes() for p in ['backend/app/services/distributed.py','backend/app/rag/store.py','backend/app/api/routes/memory.py'])).hexdigest()
                report['evaluation_source_sha256']=hashlib.sha256((root/'backend/scripts/evaluate_role_outputs.py').read_bytes()).hexdigest()
                report['images']={key:{'tag':values[key],'bytes':int(subprocess.check_output(['docker','image','inspect',values[key],'--format','{{.Size}}'],text=True))} for key in ['BACKEND_IMAGE','WORKER_IMAGE','FRONTEND_IMAGE']}
                Path(evaluation_output).parent.mkdir(parents=True,exist_ok=True)
                Path(evaluation_output).write_text(json.dumps(report,indent=2)+'\n')
                print('Saved synthetic evaluation:',evaluation_output)
            subprocess.run(compose+['exec','-T','frontend','node','-e',"fetch('http://127.0.0.1:3000/login').then(r=>{if(!r.ok)process.exit(1)})"],check=True,env=runtime_env)
            print(('Four-service component profile' if components else 'Ten-service private topology')+' and frontend health passed; TLS/Supabase live acceptance is separate.')
        except Exception:
            diagnostic = subprocess.run(compose+['logs','--no-color','--tail','30'],env=runtime_env,capture_output=True,text=True)
            Path('/tmp/startup-release-smoke-diagnostics.log').write_text(diagnostic.stdout+diagnostic.stderr)
            print('Local diagnostics saved to /tmp/startup-release-smoke-diagnostics.log')
            raise
        finally:
            subprocess.run(compose+['down','--remove-orphans'],env=runtime_env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            for volume in volumes:
                subprocess.run(['docker','volume','rm',volume],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--components',action='store_true',help='Only Mongo/API/CEO/frontend; never counts as full topology acceptance')
    parser.add_argument('--evaluation-output',help='Run four labelled cases plus 100 finite read samples; save local evidence JSON')
    args=parser.parse_args()
    if args.components and args.evaluation_output:parser.error('Evaluation requires the complete topology')
    main(args.components,args.evaluation_output)
