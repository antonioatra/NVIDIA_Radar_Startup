"""RAG NVIDIA com reranking (F3).

Ingest -> chunk semântico -> embeddings (NeMo Retriever nv-embedqa) -> Qdrant (dense+sparse/BM25)
-> busca híbrida -> Reranker (interface plugável; default NeMo NIM, Cohere só na F7) -> citações.

Ingestão das fontes do §10 (F3.1): `from packages.rag import ingest, load_kb_sources`.
Transcrição dos vídeos do §10.1 (F3.1b): `from packages.rag import transcribe, Transcriber`.
Chunking semântico (F3.2): `from packages.rag import chunk_kb, Chunk`.
Embeddings nv-embedqa (F3.3): `from packages.rag import embed_kb, get_embedder, Embedder`.
"""

from .chunk import (
    Chunk,
    chunk_document,
    chunk_documents,
    chunk_kb,
    normalize_text,
)
from .embed import (
    DEFAULT_OFFLINE_DIM,
    NV_EMBEDQA_DIM,
    EmbeddedChunk,
    Embedder,
    EmbedderUnavailable,
    HashingEmbedder,
    NVEmbedQA,
    embed_chunks,
    embed_kb,
    embed_query,
    get_embedder,
)
from .ingest import (
    KBDocument,
    KBSection,
    KBSource,
    KBSourceType,
    covered_techs,
    ingest,
    load_kb_sources,
)
from .transcribe import (
    DEFAULT_PREFERENCE,
    RivaTranscriber,
    Transcriber,
    TranscriberUnavailable,
    Transcript,
    TranscriptSegment,
    WhisperTranscriber,
    YouTubeCaptionTranscriber,
    build_transcriber_chain,
    transcribe,
    transcript_to_markdown,
)

__all__ = [
    "KBSource",
    "KBDocument",
    "KBSection",
    "KBSourceType",
    "load_kb_sources",
    "ingest",
    "covered_techs",
    "Chunk",
    "normalize_text",
    "chunk_document",
    "chunk_documents",
    "chunk_kb",
    "NV_EMBEDQA_DIM",
    "DEFAULT_OFFLINE_DIM",
    "Embedder",
    "EmbedderUnavailable",
    "EmbeddedChunk",
    "HashingEmbedder",
    "NVEmbedQA",
    "get_embedder",
    "embed_chunks",
    "embed_query",
    "embed_kb",
    "DEFAULT_PREFERENCE",
    "TranscriberUnavailable",
    "TranscriptSegment",
    "Transcript",
    "Transcriber",
    "RivaTranscriber",
    "YouTubeCaptionTranscriber",
    "WhisperTranscriber",
    "build_transcriber_chain",
    "transcribe",
    "transcript_to_markdown",
]
