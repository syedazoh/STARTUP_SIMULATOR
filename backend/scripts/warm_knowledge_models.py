"""Explicit download/cache step. Run from backend with PYTHONPATH=."""

from app.config import settings
from app.services.knowledge import embedding_model, reranker_model

if __name__ == "__main__":
    settings.rag_allow_model_download = True
    embedding_model()
    reranker_model()
    print("Embedding and cross-encoder caches ready. Keep runtime downloads disabled.")
