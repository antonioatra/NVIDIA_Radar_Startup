"""Montagem do grafo multi-agente LangGraph (F2.1).

O estado é o `GraphState` (F0.5, `schemas/state.py`); aqui ficam as **arestas**: o
backbone linear da ARQUITETURA §3 (query → search_planner → ... → briefing). O fluxo
linear do §6 do brief vira grafo — o paralelismo, o retry condicional e o HITL entram
nas tasks seguintes, com hooks já documentados aqui:

- checkpointer Postgres (resume/retry)        → F2.2 (param `checkpointer` de `compile_graph`)
- aresta condicional de retry evidence→scraper → F2.7
- estado terminal de baixa confiança           → F2.12
- saída non-AI fora de escopo                   → F2.13
- HITL interrupt antes do briefing              → F2.8
- tracing Langfuse por nó + custo               → F2.9

`from packages.agents import build_graph, compile_graph, run_pipeline`.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from langgraph.graph import END, START, StateGraph

from packages.schemas import ExecutionMode, GraphState, HITLMode

from .nodes import NODES

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.graph.state import CompiledStateGraph

# Espinha dorsal (ARQUITETURA §3). As arestas condicionais (retry F2.7, terminais
# F2.12/F2.13, HITL F2.8) entram depois sem reordenar esta sequência.
PIPELINE: tuple[str, ...] = (
    "search_planner",
    "scraper",
    "extractor",
    "classifier",
    "evidence_validator",
    "nvidia_rag",
    "recommender",
    "gpu_benchmark",
    "briefing",
)


def build_graph() -> StateGraph:
    """Monta (sem compilar) o `StateGraph` sobre `GraphState` com o backbone linear.

    Devolve o builder de propósito: a F2.2 compila com o checkpointer Postgres e o
    builder segue reutilizável (compilar com/sem checkpointer, inspecionar em teste).
    """
    g = StateGraph(GraphState)
    for name in PIPELINE:
        g.add_node(name, NODES[name])

    g.add_edge(START, PIPELINE[0])
    for src, dst in zip(PIPELINE, PIPELINE[1:], strict=False):
        g.add_edge(src, dst)
    g.add_edge(PIPELINE[-1], END)
    return g


def compile_graph(*, checkpointer: BaseCheckpointSaver | None = None) -> CompiledStateGraph:
    """Compila o grafo. `checkpointer` é o hook da F2.2 (Postgres → resume/retry)."""
    return build_graph().compile(checkpointer=checkpointer)


def run_pipeline(
    query: str,
    *,
    run_id: str | None = None,
    mode: ExecutionMode = ExecutionMode.SINGLE_COMPANY,
    hitl: HITLMode = HITLMode.SYNC,
) -> GraphState:
    """Roda o grafo ponta a ponta e devolve o `GraphState` final (rascunho — M2).

    Helper síncrono, sem checkpointer (a orquestração assíncrona worker/SSE é F2.10).
    Na F2.1 os nós são placeholders deterministas, então não há rede nem LLM.
    """
    init = GraphState(
        run_id=run_id or uuid.uuid4().hex,
        query=query,
        mode=mode,
        hitl=hitl,
    )
    result = compile_graph().invoke(init)
    return result if isinstance(result, GraphState) else GraphState.model_validate(result)
