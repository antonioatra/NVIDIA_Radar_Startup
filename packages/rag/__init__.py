"""RAG NVIDIA com reranking (F3).

Ingest -> chunk semântico -> embeddings (NeMo Retriever nv-embedqa) -> Qdrant (dense+sparse/BM25)
-> busca híbrida -> Reranker (interface plugável; default NeMo NIM, Cohere só na F7) -> citações.

Ingestão das fontes do §10 (F3.1): `from packages.rag import ingest, load_kb_sources`.
Transcrição dos vídeos do §10.1 (F3.1b): `from packages.rag import transcribe, Transcriber`.
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
