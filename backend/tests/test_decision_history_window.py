"""Boardroom history uses latest records without leaking another business/run."""
import pytest
from app.database.mongodb import InMemoryDatabase
from app.services.decision_history import read_decision_history

@pytest.mark.asyncio
async def test_recent_window_and_run_are_business_scoped():
    db = InMemoryDatabase()
    for i in range(6):
        await db['decision_logs'].insert_one({'business_id': 'ours', 'simulation_run_id': 'a' if i < 4 else 'b', 'tick': i, 'timestamp': f'2026-11-17T00:00:0{i}Z'})
    await db['decision_logs'].insert_one({'business_id': 'theirs', 'timestamp': '2026-11-18T00:00:00Z'})
    assert [r['tick'] for r in await read_decision_history(db, 'ours', 2, recent=True)] == [4, 5]
    assert [r['tick'] for r in await read_decision_history(db, 'ours', 2, run_id='a', recent=True)] == [2, 3]
    assert [r['tick'] for r in await read_decision_history(db, 'ours', 2)] == [0, 1]

@pytest.mark.asyncio
async def test_history_limit_is_bounded():
    db = InMemoryDatabase()
    for i in range(505):
        await db['decision_logs'].insert_one({'business_id': 'ours', 'tick': i, 'timestamp': str(i).zfill(4)})
    rows = await read_decision_history(db, 'ours', 10000, recent=True)
    assert len(rows) == 500
    assert rows[0]['tick'] == 5
    assert len(await read_decision_history(db, 'ours', -1, recent=True)) == 1
