"""Independent analysis worker. Never constructs an AgentRegistry or executes tasks."""
import argparse
import asyncio
import time
import socket
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
from .models.distributed_schemas import ROLES
from .services.distributed import run_once


async def serve(role, once=False, healthcheck=False):
    client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    try:
        await client.admin.command('ping')  # No volatile fallback for workers.
        db = client[settings.mongodb_db_name]
        worker_id = socket.gethostname()
        if healthcheck:
            health = await db['role_worker_health'].find_one({'_id': worker_id})
            if not health or time.time() - health['heartbeat_ts'] > 60:
                raise RuntimeError('Worker heartbeat is stale')
            return
        while True:
            await db['role_worker_health'].update_one({'_id': worker_id}, {'$set': {
                'role': role, 'heartbeat_ts': time.time()}}, upsert=True)
            worked = await run_once(db, role)
            if once:
                return
            if not worked:
                await asyncio.sleep(1)
    finally:
        client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--role', choices=ROLES)
    parser.add_argument('--healthcheck', action='store_true')
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    if not args.healthcheck and not args.role:
        parser.error('--role is required unless --healthcheck is used')
    asyncio.run(serve(args.role, args.once, args.healthcheck))
