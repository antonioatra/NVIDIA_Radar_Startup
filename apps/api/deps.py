"""Dependências (DI) da API TAPI (F5.2) — recursos de produção, sobrescrevíveis em teste.

Cada provider entrega um recurso vivo por padrão (fila RQ, canal de progresso Redis, sessão
SQL, leitor de briefing) montado a partir da config (F0.3). Os endpoints os recebem via
`Depends`, e os testes trocam por stubs offline com `app.dependency_overrides` — mesmo ethos
de "injetável p/ teste offline" do worker (F2.10) e da persistência (F4.7), sem broker/banco.

A **autenticação** (gate interno por API key/bearer) é a F5.9: entra aqui como uma dependência
aplicada aos endpoints; a F5.2 só monta as rotas e deixa o gancho documentado.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from packages.db.engine import get_session

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from rq import Queue

    from packages.agents.progress import ProgressEvent
    from packages.schemas import Briefing, GraphState

# Sessão SQL por requisição: reusa a dependência do engine (F0.6) — fecha ao fim do escopo.
db_session = get_session


def get_queue() -> Queue:
    """Fila RQ `tapi` ligada ao Redis da config (F0.3) — onde `POST /runs`/`/resume` enfileiram."""
    from apps.worker import default_queue

    return default_queue()


def get_progress_source() -> Callable[[str], Iterable[ProgressEvent]]:
    """Fonte de progresso de um run: assina o canal Redis pub/sub (F2.10) e itera os eventos.

    O `GET /runs/{id}` (SSE, F5.3) embrulha cada `ProgressEvent` em `text/event-stream`. Em
    teste, sobrescreve-se por um gerador de eventos canônicos (sem broker).
    """
    from packages.agents.progress import subscribe_progress
    from packages.config import get_settings

    def _source(run_id: str) -> Iterable[ProgressEvent]:
        from redis import Redis

        client = Redis.from_url(get_settings().redis_url)
        return subscribe_progress(client, run_id)

    return _source


def get_briefing_loader() -> Callable[[str], Briefing | None]:
    """Leitor do briefing de um run (`GET /briefings/{id}`, F5.2): lê do checkpoint (F2.2).

    O briefing final (F4.4) vive no estado persistido da thread `run_id` (não há tabela
    própria); abre o checkpointer Postgres e devolve o `Briefing` do snapshot, ou `None` se o
    run não chegou ao briefing. Em teste, sobrescreve-se por um loader que devolve um `Briefing`.
    """
    from packages.agents.checkpoint import postgres_checkpointer
    from packages.agents.graph import compile_graph
    from packages.schemas import Briefing

    def _load(run_id: str) -> Briefing | None:
        with postgres_checkpointer(setup=False) as cp:
            snapshot = compile_graph(checkpointer=cp).get_state(
                {"configurable": {"thread_id": run_id}}
            )
        data = snapshot.values.get("briefing") if snapshot.values else None
        return Briefing.model_validate(data) if data else None

    return _load


def get_trace_loader() -> Callable[[str], GraphState | None]:
    """Leitor do estado persistido de um run (F5.7) — lê do checkpoint (F2.2) p/ o trace viewer.

    Espelha o `get_briefing_loader`, mas devolve o **estado inteiro** (`GraphState`) para a
    projeção do trace (passos dos agentes + custo, ver `apps/api/trace.py`); `None` se o run não
    tem checkpoint (run inexistente). Em teste, sobrescreve-se por um loader que devolve um
    `GraphState` montado à mão.
    """
    from packages.agents.checkpoint import postgres_checkpointer
    from packages.agents.graph import compile_graph
    from packages.schemas import GraphState

    def _load(run_id: str) -> GraphState | None:
        with postgres_checkpointer(setup=False) as cp:
            snapshot = compile_graph(checkpointer=cp).get_state(
                {"configurable": {"thread_id": run_id}}
            )
        return GraphState.model_validate(snapshot.values) if snapshot.values else None

    return _load


def get_langfuse_url() -> str | None:
    """Host do Langfuse (deep-trace, F0.8) p/ o trace viewer (F5.7) — `None` com o tracing off.

    Sem um `trace_id` persistido não há deep-link por run; expomos o host (quando as duas chaves
    estão setadas, F0.3) como ponto de entrada e mantemos o passo-a-passo do viewer no estado do
    grafo (offline-reproduzível).
    """
    from packages.config import get_settings

    s = get_settings()
    return s.langfuse_host if s.langfuse_enabled else None


__all__ = [
    "db_session",
    "get_queue",
    "get_progress_source",
    "get_briefing_loader",
    "get_trace_loader",
    "get_langfuse_url",
]
