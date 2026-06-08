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
- recommender       → F4.2/F4.3 (gaps do AIMI × evidência NVIDIA; ver `recommender.py`)
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
from .nvidia_rag import nvidia_rag  # F3.7 — implementação real do nó
from .recommender import recommender  # F4.2/F4.3 — implementação real do nó
from .scraper import scraper  # F2.4 — implementação real do nó
from .search_planner import search_planner  # F2.3 — implementação real do nó
from .terminals import (  # F2.12 / F2.13 — briefings terminais
    insufficient_data_briefing,
    out_of_scope_briefing,
)


def gpu_benchmark(state: GraphState) -> dict:
    """F6 — GPU Graduation Engine: ROI real (NIM local / matriz). Condicional ★."""
    return {}


def briefing(state: GraphState) -> dict:
    """F4.4 — briefing executivo (Guardrails F4.5).

    Despacha por status terminal, marcado antes pelo evidence_validator (F2.7) ao saltar
    RAG/recomendação direto p/ cá:
    - `INSUFFICIENT_DATA` (F2.12) → briefing **"dados insuficientes"** (o que foi apurado +
      lacunas), `terminals.insufficient_data_briefing`;
    - `OUT_OF_SCOPE` (F2.13) → briefing **"fora de escopo"** (non-AI de alta confiança: por que
      não é alvo Inception + AIMI baixo com evidência), `terminals.out_of_scope_briefing`.
    Nenhum força recomendação NVIDIA nem alucina. O briefing **normal** (F4.4, diagnóstico +
    recomendação) entra com sua task; por ora o caminho normal fecha o run em COMPLETED
    (placeholder F2.1, rascunho M2).
    """
    if state.status is RunStatus.INSUFFICIENT_DATA:
        return {"briefing": insufficient_data_briefing(state)}  # status já é terminal
    if state.status is RunStatus.OUT_OF_SCOPE:
        return {"briefing": out_of_scope_briefing(state)}  # status já é terminal
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
