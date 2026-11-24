"""Bounded, allowlisted evidence exports; never serialize arbitrary payloads."""
import csv
import io
import json
import math
from datetime import datetime, timezone

FIELDS = ('record_type', 'record_id', 'timestamp', 'business_id', 'run_id', 'task_id',
    'event_id', 'event_type', 'source', 'agent', 'sender', 'receiver', 'status', 'reasoning', 'outcome')
OUTCOME_FIELDS = {'status', 'approved', 'financial_amount', 'amount_approved',
    'headcount_approved', 'quantity_approved', 'customers_acquired', 'revenue',
    'expenses', 'mode', 'recommended_budget_minor', 'synthetic'}


def text(value):
    return str(value).replace('\x00', '')[:4000] if isinstance(value, (str, int, float, bool)) else ''


def timestamp(value):
    if isinstance(value, (int, float)):
        try:
            value = datetime.fromtimestamp(value, timezone.utc)
        except (ValueError, OverflowError, OSError):
            return ''
    if isinstance(value, datetime):
        return (value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value).isoformat()
    return text(value)


def outcome(value):
    if not isinstance(value, dict):
        return {}
    return {k: text(v) if isinstance(v, str) else v for k, v in value.items() if k in OUTCOME_FIELDS and
        isinstance(v, (str, int, float, bool)) and
        not (isinstance(v, float) and not math.isfinite(v))}


def record(kind, doc, business_id):
    data = doc.get('data') or {}
    result = doc.get('result') or data.get('result') or {}
    if not isinstance(result, dict):
        result = {}
    review = doc.get('ceo_review') or {}
    message = (doc.get('payload') or {}) if kind == 'role_result' else {}
    return {
        'record_type': kind, 'record_id': text(doc.get('job_id') or doc.get('task_id') or doc.get('event_id') or str(doc.get('_id', ''))),
        'timestamp': timestamp(doc.get('timestamp') or doc.get('updated_ts') or doc.get('created_at')),
        'business_id': business_id, 'run_id': text(doc.get('run_id') or doc.get('simulation_run_id') or message.get('correlation_id')),
        'task_id': text(doc.get('task_id') or data.get('task_id')),
        'event_id': text(doc.get('event_id') or message.get('event_id')),
        'event_type': text(doc.get('event_type') or doc.get('action_type') or doc.get('kind')),
        'source': text(doc.get('source') or ('distributed_simulation' if kind == 'role_result' else '')),
        'agent': text(doc.get('agent') or message.get('role')),
        'sender': text(doc.get('sender')), 'receiver': text(doc.get('receiver')),
        'status': text(doc.get('status') or result.get('status') or 'not_recorded'),
        'reasoning': text(result.get('reasoning') or result.get('reason') or review.get('reason') or data.get('title')),
        'outcome': outcome(result),
    }


async def evidence(db, business_id, kind='all', limit=500):
    sources = {'decision': ('decision_logs', 'timestamp'), 'event': ('collaboration_events', 'timestamp'),
        'task': ('tasks', 'created_at'), 'role_result': ('background_jobs', 'updated_ts')}
    rows = []
    truncated = False
    for category, (collection, order) in sources.items():
        if kind not in {'all', category}:
            continue
        query = {'business_id': business_id}
        if category == 'role_result':
            query['kind'] = 'role_work'
        docs = await db[collection].find(query).sort(order, -1).to_list(length=limit+1)
        truncated |= len(docs) > limit
        rows.extend(record(category, d, business_id) for d in docs[:limit])
    rows.sort(key=lambda r: (r['timestamp'], r['record_type'], r['record_id']), reverse=True)
    return {'schema_version': 1, 'business_id': business_id,
        'exported_at': datetime.now(timezone.utc).isoformat(), 'limit': limit,
        'truncated': truncated or len(rows) > limit, 'records': rows[:limit]}


def csv_text(bundle):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=FIELDS)
    writer.writeheader()
    for record in bundle['records']:
        cells = {}
        for key in FIELDS:
            value = record.get(key, '')
            value = json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True) if isinstance(value, dict) else str(value)
            # CSV quoting does not prevent spreadsheet formula execution.
            if value.startswith(('\t', '\r', '\n')) or value.lstrip().startswith(('=', '+', '-', '@')):
                value = "'" + value
            cells[key] = value
        writer.writerow(cells)
    return stream.getvalue()
