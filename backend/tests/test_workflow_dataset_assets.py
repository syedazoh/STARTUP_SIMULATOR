"""Dataset assets cannot silently drift between the importer and demo clients."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_demo_copies_and_conversation_split():
    sample = (ROOT / 'datasets/shared-launch-v2/dataset.json').read_bytes()
    for path in ['backend/app/data/shared-launch-v2.json','frontend/public/datasets/shared-launch-v2.json','web/public/datasets/shared-launch-v2.json']:
        assert (ROOT/path).read_bytes() == sample
    from app.services.demo_dataset import parse_upload
    assert parse_upload((ROOT/'datasets/shared-launch-v2/dataset.csv').read_bytes(),'csv') == parse_upload(sample,'json')
    corpus=json.loads((ROOT/'datasets/agent-conversations-v1/examples.json').read_text())
    rows=corpus['examples'];assert len(rows)==40;assert len({r['id'] for r in rows})==40
    for role in ['ceo','finance','marketing','operations','strategy']:
        cases=[r for r in rows if r['agent']==role];assert len(cases)==8
        assert sum(r['split']=='held_out' for r in cases)==2
        assert all(r['synthetic'] and r['conversation'] and r['checks'] for r in cases)
