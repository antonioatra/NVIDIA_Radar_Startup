"""RAG NVIDIA com reranking (F3).

Ingest -> chunk semântico -> embeddings (NeMo Retriever nv-embedqa) -> Qdrant (dense+sparse/BM25)
-> busca híbrida -> Reranker (interface plugável; default NeMo NIM, Cohere só na F7) -> citações.
"""
