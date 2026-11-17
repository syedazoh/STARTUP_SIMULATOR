"""Synthetic retrieval evaluation in an isolated mock database; no LLM/provider calls."""

import argparse
import asyncio
import json
from pathlib import Path
from mongomock_motor import AsyncMongoMockClient
from app.config import settings
from app.services import knowledge


async def evaluate(require_hybrid=False):
    fixture = json.loads(
        (Path(__file__).parents[1] / "tests/fixtures/knowledge_eval.json").read_text()
    )
    db = AsyncMongoMockClient()["isolated_synthetic_eval"]
    settings.rag_allow_model_download = False
    dense_enabled = settings.rag_dense_enabled
    for doc in fixture["documents"]:
        chunks = knowledge.chunk_document(doc["text"], doc["title"], 1)
        vectors = None
        if dense_enabled:
            try:
                vectors = await asyncio.to_thread(
                    knowledge.embed, [c["text"] for c in chunks]
                )
            except Exception:
                if require_hybrid:
                    raise RuntimeError(
                        "Warm embedding cache before requiring hybrid evaluation"
                    ) from None
        for i, c in enumerate(chunks):
            c["vector"] = vectors[i] if vectors else None
        await db["knowledge_documents"].insert_one(
            {
                "document_id": doc["key"],
                "business_id": "synthetic",
                "version": 1,
                "title": doc["title"],
                "status": "ready",
                "departments": [doc["department"]],
                "embedding_model": settings.rag_embedding_model,
                "updated_at": "2026-11-17",
                "chunks": chunks,
            }
        )
    rows = []
    for case in fixture["cases"]:
        settings.rag_dense_enabled = False
        settings.rag_reranker_enabled = False
        base = await knowledge.search(
            db, "synthetic", case["department"], case["query"], 5
        )
        settings.rag_dense_enabled = dense_enabled
        settings.rag_reranker_enabled = True
        actual = await knowledge.search(
            db, "synthetic", case["department"], case["query"], 5
        )
        if (
            require_hybrid
            and case["expected_key"]
            and (actual["mode"] != "hybrid" or actual["reranker"] != "cross_encoder")
        ):
            raise RuntimeError("Required hybrid/cross-encoder models did not execute")

        def grade(r):
            keys = [c["document_id"] for c in r["results"]]
            return case["expected_key"] in keys if case["expected_key"] else not keys

        rows.append(
            {
                **case,
                "baseline_pass": grade(base),
                "pipeline_pass": grade(actual),
                "mode": actual["mode"],
                "reranker": actual["reranker"],
                "retrieved": [c["document_id"] for c in actual["results"]],
            }
        )
    return {
        "synthetic": True,
        "cases": len(rows),
        "baseline_pass": sum(r["baseline_pass"] for r in rows),
        "pipeline_pass": sum(r["pipeline_pass"] for r in rows),
        "notes": "Retrieval coverage and department isolation only, not factual entailment or real customer quality.",
        "results": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-hybrid", action="store_true")
    parser.add_argument("--min-pass", type=int, default=0)
    parser.add_argument("--output", default="knowledge-evaluation.json")
    args = parser.parse_args()
    report = asyncio.run(evaluate(args.require_hybrid))
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}))
    if report["pipeline_pass"] < args.min_pass:
        raise SystemExit("Retrieval evaluation below requested threshold")
