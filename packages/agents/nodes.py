"""Nós do grafo multi-agente (F2) — esqueleto.

Cada função é um **nó** do grafo LangGraph (ARQUITETURA §3): recebe o `GraphState`
e devolve um *update parcial* (dict só com os campos que muda). A montagem e as
arestas ficam em `graph.py` (F2.1).

Na F2.1 os corpos são **placeholders deterministas** (sem rede/LLM): provam que o
grafo roda ponta a ponta e produz um briefing rascunho (M2 / DoD "grafo end-to-end
sem RAG ainda"). Cada nó é preenchido pela sua task, anotada no docstring:

- search_planner    → F2.3 (query → termos + fontes priorizadas; ver `search_planner.py`)
- scraper           → F2.4 (map paralelo sobre fontes; usa F1)
- extractor         → F2.5 (Nemotron-Super: docs → StartupProfile + persist)
- classifier        → F2.6 (classe §5.1 + AIMI v0)
- evidence_validator → F2.7 (regra de N fontes; retry via Command; ver `evidence_validator.py`)
- nvidia_rag        → F3   (RAG híbrido Qdrant + NeMo rerank → citações)
- recommender       → F4   (gaps do AIMI × tech NVIDIA)
- gpu_benchmark     → F6   (ROI real na GPU; condicional ★)
- human_review      → F2.8 (HITL interrupt antes do briefing; ver `human_review.py`)
- briefing          → F4.4 (briefing executivo; Guardrails F4.5)

Os updates parciais usam a semântica default do LangGraph (sobrescrita por canal).
Reducers de acumulação (ex.: `raw_docs` no map do scraper) entram com o nó dono.
"""

from __future__ import annotations

from packages.schemas import GraphState, RunStatus

from .classifier import classifier  # F2.6 — implementação real do nó
from .evidence_validator import evidence_validator  # F2.7 — implementação real do nó
from .extractor import extractor  # F2.5 — implementação real do nó
from .human_review import human_review  # F2.8 — implementação real do nó
from .scraper import scraper  # F2.4 — implementação real do nó
from .search_planner import search_planner  # F2.3 — implementação real do nó


def nvidia_rag(state: GraphState) -> dict:
    """F3 — RAG híbrido (dense + BM25 Qdrant) → NeMo rerank → citações da KB."""
    return {}


def recommender(state: GraphState) -> dict:
    """F4 — cruza gaps do AIMI com tech NVIDIA; recomendações com evidência dos 2 lados."""
    return {}


def gpu_benchmark(state: GraphState) -> dict:
    """F6 — GPU Graduation Engine: ROI real (NIM local / matriz). Condicional ★."""
    return {}


def briefing(state: GraphState) -> dict:
    """F4.4 — briefing executivo (Guardrails F4.5).

    Placeholder F2.1: fecha o run com status COMPLETED — o backbone produz um
    rascunho terminal (M2). Os caminhos terminais alternativos (dados insuficientes
    F2.12, fora de escopo F2.13) entram com suas tasks.
    """
    return {"status": RunStatus.COMPLETED}


# Registro nome → função, consumido pela montagem do grafo (graph.py). O `human_review`
# (F2.8) é um nó de **controle HITL** (não um dos 9 agentes), inserido antes do briefing.
NODES = {
    "search_planner": search_planner,
    "scraper": scraper,
    "extractor": extractor,
    "classifier": classifier,
    "evidence_validator": evidence_validator,
    "nvidia_rag": nvidia_rag,
    "recommender": recommender,
    "gpu_benchmark": gpu_benchmark,
    "human_review": human_review,
    "briefing": briefing,
}
