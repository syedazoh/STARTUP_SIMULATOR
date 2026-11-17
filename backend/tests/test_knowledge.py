import asyncio
from tests.test_account_isolation import accounts  # noqa: F401
from tests.test_automation_api import configured_worker_without_loop  # noqa: F401
from app.services import jobs, knowledge
from app.config import settings


def indexed(accounts):
    c, h, a, b = accounts
    r = c.post(
        f"/api/businesses/{a}/knowledge",
        headers=h["alice"],
        json={
            "key": "policy",
            "title": "Budget policy",
            "text": "# Campaigns\n\nCampaign spending above 500 dollars requires owner approval.",
            "departments": ["finance"],
        },
    )
    assert r.status_code == 202, r.text
    assert (
        asyncio.run(jobs.run_once(c.app.state.db, c.app.state.agent_registry))["status"]
        == "succeeded"
    )
    return c, h, a, b, r.json()["payload"]["document_id"]


def test_authorized_sources_fallback_and_abstention(accounts):
    c, h, a, b, doc = indexed(accounts)
    body = {"query": "campaign spending approval", "department": "finance"}
    r = c.post(
        f"/api/businesses/{a}/knowledge/answer", headers=h["alice"], json=body
    ).json()
    assert (
        r["answer_mode"] == "extractive_fallback"
        and r["citations"][0]["document_id"] == doc
    )
    assert (
        c.post(
            f"/api/businesses/{a}/knowledge/search", headers=h["bob"], json=body
        ).status_code
        == 403
    )
    assert (
        c.post(
            f"/api/businesses/{b}/knowledge/search", headers=h["bob"], json=body
        ).json()["results"]
        == []
    )
    body["department"] = "hr"
    assert (
        c.post(
            f"/api/businesses/{a}/knowledge/search", headers=h["alice"], json=body
        ).json()["results"]
        == []
    )
    body.update(department="finance", query="extraterrestrial bananas")
    assert c.post(
        f"/api/businesses/{a}/knowledge/answer", headers=h["alice"], json=body
    ).json()["abstain"]


def test_reindex_delete_and_late_job_do_not_resurrect(accounts):
    c, h, a, b, doc = indexed(accounts)
    r = c.post(
        f"/api/businesses/{a}/knowledge/{doc}/reindex?version=1", headers=h["alice"]
    )
    assert r.status_code == 202 and r.json()["payload"]["version"] == 2
    assert (
        c.delete(
            f"/api/businesses/{a}/knowledge/{doc}?version=1", headers=h["alice"]
        ).status_code
        == 409
    )
    assert (
        c.delete(
            f"/api/businesses/{a}/knowledge/{doc}?version=2", headers=h["alice"]
        ).status_code
        == 200
    )
    assert (
        asyncio.run(jobs.run_once(c.app.state.db, c.app.state.agent_registry))[
            "result"
        ]["status"]
        == "superseded"
    )
    assert (
        c.post(
            f"/api/businesses/{a}/knowledge/search",
            headers=h["alice"],
            json={"query": "campaign approval", "department": "finance"},
        ).json()["results"]
        == []
    )


def test_hybrid_reranking_and_scope(accounts, monkeypatch):
    c, h, a, b, doc = indexed(accounts)
    monkeypatch.setattr(settings, "rag_dense_enabled", True)
    monkeypatch.setattr(settings, "rag_reranker_enabled", True)
    monkeypatch.setattr(knowledge, "embed", lambda texts: [[1.0, 0.0] for t in texts])
    seen = []

    def rank(q, texts):
        seen.extend(texts)
        return [1.0 for _ in texts]

    monkeypatch.setattr(knowledge, "rerank", rank)
    assert (
        c.post(
            f"/api/businesses/{a}/knowledge/{doc}/reindex?version=1", headers=h["alice"]
        ).status_code
        == 202
    )
    asyncio.run(jobs.run_once(c.app.state.db, c.app.state.agent_registry))
    r = c.post(
        f"/api/businesses/{a}/knowledge/search",
        headers=h["alice"],
        json={"query": "campaign approval", "department": "finance"},
    ).json()
    assert r["mode"] == "hybrid" and r["reranker"] == "cross_encoder" and seen
    assert (
        c.post(
            f"/api/businesses/{a}/knowledge/search",
            headers=h["alice"],
            json={"query": "campaign approval", "department": "hr"},
        ).json()["results"]
        == []
    )


def test_source_deleted_during_generation_is_not_exposed(accounts, monkeypatch):
    c, h, a, b, doc = indexed(accounts)

    class Model:
        def with_structured_output(self, schema):
            return self

        async def ainvoke(self, prompt):
            await knowledge.delete_document(c.app.state.db, a, doc, 1)
            raise RuntimeError("Provider failed after source deleted")

    monkeypatch.setattr(knowledge, "get_groq_llm", lambda: Model())
    r = c.post(
        f"/api/businesses/{a}/knowledge/answer",
        headers=h["alice"],
        json={"query": "campaign approval", "department": "finance"},
    ).json()
    assert r["abstain"] and r["results"] == [] and r["citations"] == []


def test_chunks_keep_bounded_heading_and_version():
    chunks = knowledge.chunk_document(
        "# Hiring\n\n" + "candidate evidence " * 500, "HR", 3
    )
    assert len(chunks) > 1 and all(
        c["version"] == 3 and c["section"] == "Hiring" and len(c["text"]) <= 4000
        for c in chunks
    )


def test_invalid_query_vector_falls_back_instead_of_returning_nan(
    accounts, monkeypatch
):
    c, h, a, b, doc = indexed(accounts)
    monkeypatch.setattr(settings, "rag_dense_enabled", True)
    asyncio.run(
        c.app.state.db["knowledge_documents"].update_one(
            {"document_id": doc}, {"$set": {"chunks.0.vector": [1.0, 0.0]}}
        )
    )
    monkeypatch.setattr(knowledge, "embed", lambda texts: [[float("nan"), 0.0]])
    r = c.post(
        f"/api/businesses/{a}/knowledge/search",
        headers=h["alice"],
        json={"query": "campaign approval", "department": "finance"},
    )
    assert (
        r.status_code == 200
        and r.json()["mode"] == "lexical"
        and r.json()["dense_status"] == "unavailable"
    )
    assert r.json()["results"]


def test_changed_embedding_model_requires_reindex_before_hybrid_mode(
    accounts, monkeypatch
):
    c, h, a, b, doc = indexed(accounts)
    asyncio.run(
        c.app.state.db["knowledge_documents"].update_one(
            {"document_id": doc}, {"$set": {"chunks.0.vector": [1.0, 0.0]}}
        )
    )
    monkeypatch.setattr(settings, "rag_dense_enabled", True)
    monkeypatch.setattr(settings, "rag_embedding_model", "different-embedding-model")
    called = []

    def unexpected(texts):
        called.append(True)
        return [[1.0, 0.0]]

    monkeypatch.setattr(knowledge, "embed", unexpected)
    result = c.post(
        f"/api/businesses/{a}/knowledge/search",
        headers=h["alice"],
        json={"query": "campaign approval", "department": "finance"},
    ).json()
    assert (
        result["mode"] == "lexical"
        and result["dense_status"] == "unavailable"
        and not called
    )
