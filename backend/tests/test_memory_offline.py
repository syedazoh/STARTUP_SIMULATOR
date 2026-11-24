"""Browsing persisted text must not require an embedding model or network."""
from app.rag.store import DecisionMemoryStore
from app.config import settings


def test_empty_and_saved_browse_do_not_load_embeddings(tmp_path,monkeypatch):
    monkeypatch.setattr(settings,'chroma_persist_dir',str(tmp_path))
    def unavailable():
        raise RuntimeError('Embedding cache unavailable; do not download in this test')
    monkeypatch.setattr('app.rag.store.get_embedding_function',unavailable)
    store=DecisionMemoryStore()
    assert store.get_recent('finance_offline')==[]
    assert store.query_similar('finance_offline','budget')==[]
    # Real Chroma persistence; precomputed synthetic vectors only seed browse data.
    collection=store._client.get_or_create_collection('agent_decisions_finance_offline',embedding_function=None)
    collection.add(ids=['saved'],embeddings=[[1.0,0.0]],documents=['Saved historical budget decision'],
        metadatas=[{'agent_id':'finance_offline','event_type':'budget_request'}])
    assert store.get_recent('finance_offline')[0]['document']=='Saved historical budget decision'

from tests.test_account_isolation import accounts  # noqa: F401


def test_memory_failure_is_explicit_bounded_and_does_not_leak_provider_errors(accounts,monkeypatch):
    c,h,a,_=accounts
    class Unavailable:
        def query_similar(self,*args,**kwargs):
            raise RuntimeError('private_token_should_not_escape')
    monkeypatch.setattr('app.api.routes.memory.get_decision_memory_store',lambda:Unavailable())
    url=f'/api/businesses/{a}/agents/finance/memory'
    result=c.get(url+'?query=budget',headers=h['alice'])
    assert result.status_code==503 and 'embedding model cache' in result.text
    assert 'private_token_should_not_escape' not in result.text
    assert c.get(url+'?k=0',headers=h['alice']).status_code==422
    assert c.get(url+'?k=101',headers=h['alice']).status_code==422
    assert c.get(url,headers=h['bob']).status_code==403
