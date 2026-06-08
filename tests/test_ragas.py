"""Testes da avaliação RAGAS do RAG NVIDIA (F3.9).

Cobrem (1) as quatro métricas RAGAS no proxy lexical determinístico — faithfulness,
answer relevancy, context precision (rank-aware) e context recall —, (2) o compositor
extrativo da resposta, (3) o harness ponta a ponta sobre a KB real (offline/determinístico,
via `build_retriever`/F3.5 + `get_reranker`/F3.6), (4) o baseline versionado batendo com um
run fresco (regressão + DoD "baseline versionado") e (5) o juiz LLM degradando limpo offline.

Tudo na espinha verde (HashingEmbedder + BM25 in-memory + LexicalReranker): sem rede/GPU.
"""

from __future__ import annotations

import pytest

from packages.eval.ragas import (
    LexicalRagasMetrics,
    RagasJudge,
    RagasMetrics,
    RagasUnavailable,
    RagQuestion,
    RagSample,
    answer_relevancy,
    build_sample,
    compose_extractive_answer,
    context_precision,
    context_recall,
    evaluate_rag,
    faithfulness,
    get_evaluator,
    load_baseline,
    load_rag_questions,
)
from packages.rag import build_retriever, get_reranker

GROUNDING_TECH = "AI-Native (grounding)"  # F3.1d — define o AIMI, não é tech recomendável


# --- fixtures (constrói a KB uma vez) -----------------------------------------


@pytest.fixture(scope="module")
def retriever():
    """Retriever híbrido sobre a KB real (offline/determinístico), uma vez por módulo."""
    return build_retriever()


@pytest.fixture(scope="module")
def reranker():
    return get_reranker()


@pytest.fixture(scope="module")
def report(retriever, reranker):
    """Relatório RAGAS offline sobre a KB real — reusado pelos testes de agregação/cobertura."""
    return evaluate_rag(retriever=retriever, reranker=reranker)


# --- métricas (proxy lexical determinístico) ----------------------------------


def test_faithfulness_penalizes_hallucination() -> None:
    contexts = ["O NVIDIA NIM serve modelos em produção com inferência otimizada."]
    grounded = "O NVIDIA NIM serve modelos em produção com inferência otimizada."
    hallucinated = grounded + " A startup faturou um bilhão de reais ontem."
    assert faithfulness(grounded, contexts) == 1.0
    assert faithfulness(hallucinated, contexts) < 1.0  # a frase inventada não está no contexto
    assert faithfulness("", contexts) == 0.0  # resposta vazia não ancora nada


def test_answer_relevancy_rewards_on_topic() -> None:
    question = "O que o NVIDIA NIM faz pela inferência?"
    on_topic = "O NVIDIA NIM acelera a inferência em produção."
    off_topic = "A robótica industrial usa simulação tridimensional."
    assert answer_relevancy(on_topic, question) > answer_relevancy(off_topic, question)
    assert 0.0 <= answer_relevancy(on_topic, question) <= 1.0


def test_context_precision_is_rank_aware() -> None:
    ground_truth = "alpha beta gamma delta"
    relevant = "alpha beta gamma cobrem a referência"
    noise = "zeta eta theta iota nada a ver"
    first = context_precision([relevant, noise], ground_truth)
    last = context_precision([noise, relevant], ground_truth)
    assert first > last  # contexto relevante no topo vale mais (average precision)
    assert first == 1.0
    assert context_precision([noise, noise], ground_truth) == 0.0  # nenhum relevante


def test_context_recall_measures_coverage() -> None:
    ground_truth = "O NIM serve modelos. O Triton aplica batching dinamico."
    full = ["NIM serve modelos otimizados", "Triton aplica batching dinamico continuo"]
    partial = ["NIM serve modelos otimizados"]
    assert context_recall(full, ground_truth) == 1.0
    assert context_recall(partial, ground_truth) < 1.0
    assert context_recall([], ground_truth) == 0.0


def test_metrics_are_bounded() -> None:
    m = LexicalRagasMetrics().score(
        RagSample(
            question_id="x",
            question="O que e o NIM?",
            answer="O NIM serve modelos otimizados.",
            contexts=("O NIM serve modelos otimizados em producao.",),
            ground_truth="O NIM serve modelos otimizados.",
            citations=(),
            retrieved_techs=(),
        )
    )
    assert all(0.0 <= v <= 1.0 for v in m.model_dump().values())
    assert 0.0 <= m.mean <= 1.0


# --- compositor extrativo -----------------------------------------------------


def test_extractive_answer_is_faithful_to_contexts() -> None:
    contexts = (
        "O NVIDIA NIM empacota a inferencia em microsservicos.",
        "O Omniverse faz simulacao tridimensional para gemeos digitais.",
    )
    answer = compose_extractive_answer("O que o NVIDIA NIM faz pela inferencia?", contexts)
    assert "NIM" in answer  # puxa a frase do contexto relevante a pergunta
    assert faithfulness(answer, contexts) == 1.0  # extrativo => fiel por construcao
    assert compose_extractive_answer("qualquer", ()) == ""  # sem contexto, sem resposta


# --- conjunto de perguntas versionado -----------------------------------------


def test_questions_load_unique_and_cached() -> None:
    questions = load_rag_questions()
    assert len(questions) >= 5
    assert len({q.id for q in questions}) == len(questions)
    assert all(isinstance(q, RagQuestion) and q.ground_truth for q in questions)
    assert load_rag_questions() is load_rag_questions()  # lru_cache


# --- backend plugável ---------------------------------------------------------


def test_get_evaluator_toggle() -> None:
    assert isinstance(get_evaluator(), LexicalRagasMetrics)  # default = espinha verde
    assert isinstance(get_evaluator(prefer_llm=False), LexicalRagasMetrics)
    assert isinstance(get_evaluator(prefer_llm=True), RagasJudge)


def test_ragas_judge_degrades_clean_offline() -> None:
    # Hook de rede F3.9: sem a lib ragas/credencial (ou sem rede), o juiz levanta RagasUnavailable
    # e a avaliacao cai no LexicalRagasMetrics — nunca trava o CI (run LLM-judged e a F7.3).
    sample = RagSample(
        question_id="x",
        question="O que e o NIM?",
        answer="O NIM serve modelos.",
        contexts=("O NIM serve modelos.",),
        ground_truth="O NIM serve modelos.",
        citations=(),
        retrieved_techs=(),
    )
    with pytest.raises(RagasUnavailable):
        RagasJudge(api_key="dummy").score(sample)


# --- harness ponta a ponta sobre a KB real ------------------------------------


def test_evaluate_rag_offline_baseline_quality(report) -> None:
    assert report.backend == "lexical-offline"
    assert report.n_samples == len(load_rag_questions())
    agg = report.aggregate
    # Pisos de sanidade (NAO os limiares de gate da F7.3) — a avaliacao produz sinal real:
    assert agg.faithfulness >= 0.9  # respostas extrativas => muito fieis
    assert agg.context_precision >= 0.8  # recuperacao traz o relevante no topo
    assert agg.context_recall >= 0.5  # contextos cobrem boa parte da referencia
    assert agg.answer_relevancy >= 0.3  # respostas aderentes a pergunta
    assert all(r.metrics.faithfulness >= 0.9 for r in report.per_sample)


def test_each_question_retrieves_a_reference_tech(report) -> None:
    # Rastreabilidade da cobertura (F3.8): cada pergunta recupera ao menos uma tech esperada.
    for r in report.per_sample:
        if r.reference_techs:
            assert set(r.reference_techs) & set(r.retrieved_techs), (
                f"{r.question_id}: esperava uma de {r.reference_techs}, veio {r.retrieved_techs}"
            )


def test_grounding_is_filtered_from_contexts(report) -> None:
    # O grounding da rubrica (F3.1d) define o AIMI, nao e tech recomendavel — fica fora dos
    # contextos avaliados (mesmo filtro do no nvidia_rag/F3.7).
    for r in report.per_sample:
        assert GROUNDING_TECH not in r.retrieved_techs


def test_evaluation_is_deterministic(retriever, reranker) -> None:
    first = evaluate_rag(retriever=retriever, reranker=reranker)
    second = evaluate_rag(retriever=retriever, reranker=reranker)
    assert first == second  # espinha verde => reproduzivel byte-a-byte


def test_sample_carries_citable_provenance(retriever, reranker) -> None:
    question = next(q for q in load_rag_questions() if q.id == "q-nim-graduacao")
    sample = build_sample(question, retriever=retriever, reranker=reranker)
    assert sample.contexts and sample.citations
    assert all(c.url.startswith("http") and c.chunk_id for c in sample.citations)  # §8


# --- baseline versionado (regressao + DoD) ------------------------------------


def test_baseline_matches_fresh_offline_run(retriever, reranker) -> None:
    # DoD F3: baseline de qualidade versionado. O smoke RAGAS no CI roda este mesmo caminho
    # (python -m packages.eval.ragas --check) — drift no pipeline/KB sem regravar o baseline quebra.
    fresh = evaluate_rag(retriever=retriever, reranker=reranker)
    baseline = load_baseline()
    assert baseline == fresh
    assert isinstance(baseline.aggregate, RagasMetrics)
