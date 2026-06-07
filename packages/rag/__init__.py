"""RAG NVIDIA com reranking (F3).

Ingest -> chunk semântico -> embeddings (NeMo Retriever nv-embedqa) -> Qdrant (dense+sparse/BM25)
-> busca híbrida -> Reranker (interface plugável; default NeMo NIM, Cohere só na F7) -> citações.

Ingestão das fontes do §10 (F3.1): `from packages.rag import ingest, load_kb_sources`.
"""

from .ingest import (
    KBDocument,
    KBSection,
    KBSource,
    KBSourceType,
    covered_techs,
    ingest,
    load_kb_sources,
)

__all__ = [
    "KBSource",
    "KBDocument",
    "KBSection",
    "KBSourceType",
    "load_kb_sources",
    "ingest",
    "covered_techs",
]
