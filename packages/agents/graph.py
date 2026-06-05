"""Montagem do grafo multi-agente LangGraph (F2.1).

O estado é o `GraphState` (F0.5, `schemas/state.py`); aqui ficam as **arestas**: o
backbone linear da ARQUITETURA §3 (query → search_planner → ... → briefing). O fluxo
linear do §6 do brief vira grafo — o paralelismo, o retry condicional e o HITL entram
nas tasks seguintes, com hooks já documentados aqui:

- checkpointer Postgres (resume/retry)        → F2.2 (param `checkpointer` de `compile_graph`)
- retry condicional evidence→scraper           → F2.7 (via `Command` do nó; ver `CONDITIONAL_OUT`)
- HITL interrupt antes do briefing              → F2.8 (nó `human_review`; ver `human_review.py`)
- estado terminal de baixa confiança           → F2.12
- saída non-AI fora de escopo                   → F2.13
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

# Espinha dorsal (ARQUITETURA §3): os 9 agentes + o nó de controle HITL `human_review`
# (F2.8), inserido antes do briefing. O retry condicional (F2.7) e os terminais
# (F2.12/F2.13) ramificam por `Command` sem reordenar esta sequência.
PIPELINE: tuple[str, ...] = (
    "search_planner",
    "scraper",
    "extractor",
    "classifier",
    "evidence_validator",
    "nvidia_rag",
    "recommender",
    "gpu_benchmark",
    "human_review",
    "briefing",
)

# Nós que roteiam a própria saída por `Command` (F2.7): o evidence_validator decide entre
# voltar ao scraper (retry de evidência) e seguir ao nvidia_rag, então NÃO recebe aresta
# estática de saída — as duas pontas são alcançadas pelo `goto` do nó (ver evidence_validator.py).
CONDITIONAL_OUT: frozenset[str] = frozenset({"evidence_validator"})

#: Nome do trace raiz do run no Langfuse (F2.9) — sob ele aparecem os spans por nó.
RUN_NAME = "tapi_pipeline"


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
        if src in CONDITIONAL_OUT:
            continue  # saída condicional via Command (F2.7) — sem aresta estática
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
    checkpointer: BaseCheckpointSaver | None = None,
) -> GraphState:
    """Roda o grafo ponta a ponta e devolve o `GraphState` final (rascunho — M2).

    Helper síncrono (a orquestração assíncrona worker/SSE é F2.10). Os nós são offline por
    default (sem rede/LLM), então o tracing é inócuo localmente.

    **Tracing + custo (F2.9):** o `.invoke` leva o `traced_config` do run — sob o trace raiz
    `RUN_NAME`, o callback do Langfuse (F0.8) cria **um span por nó** quando ligado; offline,
    os callbacks ficam só com o medidor local. O `capture_usage` abre o escopo onde o
    `USAGE_RECORDER` (embutido no `traced_config` que os nós LLM usam) soma tokens/custo;
    o rollup do run é carimbado em `trace["usage"]`. Sem LLM (espinha offline) não há uso —
    `trace` fica intacto (M2/DoD verde). O detalhe por nó é autoritativo no Langfuse; o
    rollup em estado é a base do gate de orçamento (F2.11).

    Com `checkpointer` (F2.2), o estado é persistido por *thread* (`thread_id=run_id`),
    habilitando resume/retry — use `run_pipeline_persisted` p/ abrir o saver Postgres.
    """
    from packages.observability import capture_usage, traced_config

    run_id = run_id or uuid.uuid4().hex
    init = GraphState(run_id=run_id, query=query, mode=mode, hitl=hitl)

    config = traced_config(node=RUN_NAME, run_id=run_id)
    if checkpointer is not None:
        config["configurable"] = {"thread_id": run_id}

    with capture_usage() as usage:
        result = compile_graph(checkpointer=checkpointer).invoke(init, config)
        total = usage.total()

    state = result if isinstance(result, GraphState) else GraphState.model_validate(result)
    if total.calls:
        state = state.model_copy(update={"trace": {**state.trace, "usage": total.as_dict()}})
    return state
