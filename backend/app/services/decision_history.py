"""Bounded business-owned history windows for the log and live boardroom."""

async def read_decision_history(db, business_id, limit=500, run_id=None, recent=False):
    query = {"business_id": business_id}
    if run_id:
        query["simulation_run_id"] = run_id
    limit = max(1, min(limit, 500))
    cursor = db["decision_logs"].find(query)
    cursor = cursor.sort("timestamp", -1) if recent else cursor.sort("tick", 1)
    docs = await cursor.limit(limit).to_list(length=limit)
    if recent:
        docs.reverse()
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs
