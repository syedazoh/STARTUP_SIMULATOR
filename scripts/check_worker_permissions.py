"""Start a disposable authenticated Mongo container; verify worker least privilege.
Never connects to configured project storage or reads .env. Requires docker+pymongo.
"""
import json
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
from uuid import uuid4
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError


def main():
    name = 'startup-worker-permissions-' + uuid4().hex[:12]
    script = Path(__file__).resolve().parents[1] / 'docker/mongo/analysis-user.js'
    root_password, worker_password = secrets.token_hex(24), secrets.token_hex(24)
    with tempfile.TemporaryDirectory(prefix='startup-permissions-') as directory:
        env_file = Path(directory) / 'test.env'
        env_file.write_text(f'MONGO_INITDB_ROOT_USERNAME=test_admin\nMONGO_INITDB_ROOT_PASSWORD={root_password}\nMONGO_WORKER_PASSWORD={worker_password}\n')
        env_file.chmod(0o600)
        admin = worker = None
        try:
            subprocess.run(['docker','run','-d','--name',name,'--env-file',str(env_file),
                '-p','127.0.0.1::27017','-v',f'{script}:/docker-entrypoint-initdb.d/analysis-user.js:ro','mongo:7'], check=True, stdout=subprocess.DEVNULL)
            port = int(subprocess.check_output(['docker','port',name,'27017'], text=True).strip().rsplit(':',1)[1])
            admin = MongoClient('127.0.0.1', port, username='test_admin', password=root_password,
                authSource='admin', serverSelectionTimeoutMS=1000)
            worker = MongoClient('127.0.0.1', port, username='analysis_worker', password=worker_password,
                authSource='startup_simulator', serverSelectionTimeoutMS=1000)
            deadline = time.monotonic()+35
            while True:
                try:
                    worker.admin.command('ping')
                    db = worker.startup_simulator
                    db.background_jobs.find_one({})  # Requires initialized user, not anonymous ping.
                    break
                except (OperationFailure, ServerSelectionTimeoutError):
                    if time.monotonic() >= deadline: raise
                    time.sleep(.2)
            db = admin.startup_simulator
            db.background_jobs.insert_one({'_id':'synthetic-job','status':'queued'})
            db.financial_accounts.insert_one({'_id':'synthetic-business','cash_minor':10000})
            db.agent_snapshots.insert_one({'_id':'synthetic-snapshot','state':{'employee_count':2}})
            assert worker.startup_simulator.agent_snapshots.find_one({'_id':'synthetic-snapshot'})['state']['employee_count']==2
            assert worker.startup_simulator.financial_accounts.find_one({'_id':'synthetic-business'})['cash_minor']==10000
            assert worker.startup_simulator.background_jobs.find_one_and_update({'_id':'synthetic-job'}, {'$set':{'status':'running'}},return_document=ReturnDocument.AFTER)['status']=='running'
            worker.startup_simulator.role_worker_health.update_one({'_id':'test-worker'},{'$set':{'heartbeat_ts':time.time()}},upsert=True)
            denied = []
            for collection in ['financial_accounts','businesses','distributed_runs','agent_snapshots','tasks','credentials','users']:
                try:
                    worker.startup_simulator[collection].update_one({'_id':'forbidden'},{'$set':{'test':True}},upsert=True)
                except OperationFailure as exc:
                    assert exc.code==13
                    denied.append(collection)
                else:
                    raise AssertionError('Worker obtained forbidden write authority')
            for collection in ['credentials','users','tasks']:
                try:
                    worker.startup_simulator[collection].find_one({})
                except OperationFailure as exc:
                    assert exc.code==13
                else:
                    raise AssertionError('Worker obtained private account/task reads')
            # Verify dump/restore only inside this disposable synthetic container.
            backup_command = 'mongodump --host 127.0.0.1 --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --db startup_simulator --archive=/tmp/acceptance.archive.gz --gzip >/dev/null 2>&1 && mongorestore --host 127.0.0.1 --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --archive=/tmp/acceptance.archive.gz --gzip --nsFrom="startup_simulator.*" --nsTo="restore_acceptance.*" >/dev/null 2>&1'
            subprocess.run(['docker','exec',name,'sh','-c',backup_command],check=True)
            assert admin.restore_acceptance.financial_accounts.find_one({'_id':'synthetic-business'}) == db.financial_accounts.find_one({'_id':'synthetic-business'})
            print(json.dumps({'mongo_dump_restore_verified':True,'isolated_mongo':True,'role_claim_and_health_write':True,
                'business_context_read':True,'forbidden_writes_denied':denied,'private_auth_reads_denied':True}))
        finally:
            if admin: admin.close()
            if worker: worker.close()
            subprocess.run(['docker','rm','-fv',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


if __name__ == '__main__':
    main()
