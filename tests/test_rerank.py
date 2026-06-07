"""Testes do reranking NeMo NIM plugável (F3.6).

Cobrem, todos offline (sem rede/servidor/GPU, sobre a espinha verde da F3.5):

1. **Contrato plugável** (`Reranker`/`get_reranker`): o default offline satisfaz o Protocol;
   o provider real é selecionável e Cohere fica reservado p/ a F7.
2. **Reordenação lexical** (`LexicalReranker`): pontua relevância consulta×trecho pelo idf local
   da janela, preserva a proveniência citável (§8), respeita `top_n`, expõe o `retrieval_score`
   (transparência) e é determinístico.
3. **Backend real degrada limpo** (`NeMoReranker`): sem credencial/dep o rerank levanta
   `RerankerUnavailable`, não trava o build.
"""

from __future__ import annotations

import pytest

from packages.rag import (
    LexicalReranker,
    NeMoReranker,
    RerankedChunk,
    Reranker,
    RerankerUnavailable,
    build_retriever,
    get_reranker,
    rerank,
)

# --- Contrato plugável ----------------------------------------------------------------------


def test_default_reranker_is_offline_and_satisfies_protocol() -> None:
    reranker = get_reranker()
    assert isinstance(reranker, LexicalReranker)
    assert isinstance(reranker, Reranker)  # runtime_checkable Protocol
    assert reranker.name == "lexical-offline" and reranker.model


def test_prefer_nv_selects_the_nemo_backend() -> None:
    reranker = get_reranker(prefer_nv=True)
    assert isinstance(reranker, NeMoReranker)
    assert reranker.name == "nv-rerankqa"


def test_cohere_provider_is_reserved_for_f7(monkeypatch: pytest.MonkeyPatch) -> None:
    # Cohere Rerank é o comparativo da F7, não está ligado aqui (provider reservado).
    from packages.config import get_settings

    monkeypatch.setattr(get_settings(), "reranker_provider", "cohere")
    with pytest.raises(RerankerUnavailable):
        get_reranker(prefer_nv=True)


# --- Reordenação lexical sobre a KB real ----------------------------------------------------


def test_rerank_reorders_and_keeps_provenance() -> None:
    retriever = build_retriever()
    query = "inferência de modelos em GPU NVIDIA"
    retrieved = retriever.search(query, limit=8)
    reranked = rerank(query, retrieved)
    assert reranked and len(reranked) == len(retrieved)
    # mesma população de chunks, só reordenada (nenhum trecho inventado/perdido).
    assert {r.chunk_id for r in reranked} == {r.chunk_id for r in retrieved}
    for r in reranked:
        assert isinstance(r, RerankedChunk)
        assert r.url.startswith("http") and r.tech and r.text  # proveniência citável (§8)
        assert r.payload["chunk_id"] == r.chunk_id
    # ordenado por rerank_score desc (a ordenação final que a F3.7 consome).
    scores = [r.rerank_score for r in reranked]
    assert scores == sorted(scores, reverse=True)


def test_rerank_surfaces_a_chunk_matching_distinctive_terms() -> None:
    retriever = build_retriever()
    # termo distintivo presente em poucos chunks → o idf local o premia, sobe no rerank.
    assert any("triton" in p.payload["text"].lower() for p in retriever.index.points)
    retrieved = retriever.search("Triton TensorRT NIM", limit=10)
    reranked = rerank("Triton TensorRT NIM", retrieved)
    top = reranked[0]
    assert top.rerank_score > 0
    # o melhor reordenado cobre os termos da consulta no seu texto/contexto.
    surface = (top.title + " " + top.text).lower()
    assert any(term in surface for term in ("triton", "tensorrt", "nim"))


def test_rerank_respects_top_n() -> None:
    retriever = build_retriever()
    query = "RAG com reranking e citações"
    retrieved = retriever.search(query, limit=8)
    reranked = rerank(query, retrieved, top_n=3)
    assert len(reranked) == 3
    # são os 3 de maior rerank_score, na ordem.
    full = rerank(query, retrieved)
    assert [r.chunk_id for r in reranked] == [r.chunk_id for r in full[:3]]


def test_rerank_exposes_retrieval_score_for_transparency() -> None:
    retriever = build_retriever()
    query = "NVIDIA NIM microsserviço de inferência"
    retrieved = retriever.search(query, limit=5)
    reranked = rerank(query, retrieved)
    by_id = {r.chunk_id: r.score for r in retrieved}
    for r in reranked:
        # o score fundido (RRF) da F3.5 segue acessível ao lado do rerank_score.
        assert r.retrieval_score == by_id[r.chunk_id]


def test_rerank_is_deterministic_across_builds() -> None:
    query = "treinar e servir modelos com NeMo"
    first = rerank(query, build_retriever().search(query, limit=6))
    second = rerank(query, build_retriever().search(query, limit=6))
    assert [r.chunk_id for r in first] == [r.chunk_id for r in second]
    assert [r.rerank_score for r in first] == [r.rerank_score for r in second]


def test_rerank_on_empty_input_returns_empty() -> None:
    assert rerank("qualquer consulta", []) == ()


# --- Backend real degrada limpo offline -----------------------------------------------------


def test_nemo_reranker_degrades_cleanly_without_credentials() -> None:
    # Hook de rede/GPU: sem NVIDIA_API_KEY/NIM o rerank levanta RerankerUnavailable (offline).
    reranker = NeMoReranker(api_key="")
    retrieved = build_retriever().search("inferência GPU", limit=3)
    with pytest.raises(RerankerUnavailable):
        reranker.rerank("inferência GPU", retrieved)
