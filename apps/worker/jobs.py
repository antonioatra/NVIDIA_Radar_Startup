"""Job RQ que roda um run do grafo de forma assíncrona (F2.10).

Runs longos (coleta + 3 chamadas LLM) não cabem no request HTTP — a API (F5.2) só
**enfileira** (`enqueue_run`) e responde o `run_id`; um worker RQ (`rq worker tapi`)
puxa o job e roda o grafo **persistido** (checkpointer Postgres, F2.2), publicando o
progresso no canal Redis pub/sub do run (F2.10/`packages.agents.progress`) que o SSE
da F5.3 assina.

**Conexões nascem dentro do job, não viajam na fila:** o RQ serializa os argumentos
(pickle), então não dá para passar Redis/Postgres vivos pelo enqueue — o job abre o
checkpointer e o cliente Redis a partir do `settings` (F0.3) quando o worker o executa.
Para teste offline, o núcleo (`run_graph_job`) recebe esses recursos **injetados**
(`redis_client`, `open_checkpointer`, `runner`), rodando sem broker nem banco.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from packages.agents.checkpoint import postgres_checkpointer
from packages.agents.progress import RedisProgressPublisher, stream_pipeline
from packages.config import get_settings
from packages.schemas import ExecutionMode, HITLMode

if TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractContextManager

    from langgraph.checkpoint.base import BaseCheckpointSaver
    from redis import Redis
    from rq import Queue

    from packages.agents.progress import ProgressEvent
    from packages.schemas import GraphState

    #: Fábrica de checkpointer: abre um context manager que entrega o saver (ou None offline).
    _OpenCheckpointer = Callable[[], AbstractContextManager[BaseCheckpointSaver | None]]


def _redis_from_settings() -> Redis:
    """Cliente Redis a partir da config (F0.3). Conecta lazy — não toca o broker aqui."""
    from redis import Redis

    return Redis.from_url(get_settings().redis_url)


def _default_checkpointer() -> AbstractContextManager[BaseCheckpointSaver]:
    """Abre o checkpointer Postgres de produção (resume/retry, F2.2)."""
    return postgres_checkpointer()


def run_graph_job(
    query: str,
    *,
    run_id: str | None = None,
    mode: ExecutionMode | str = ExecutionMode.SINGLE_COMPANY,
    hitl: HITLMode | str = HITLMode.SYNC,
    redis_client: Redis | None = None,
    open_checkpointer: _OpenCheckpointer | None = None,
    runner: Callable[..., GraphState] = stream_pipeline,
) -> dict[str, Any]:
    """Roda um run do grafo (persistido) publicando o progresso; devolve um resumo.

    É a função que o worker RQ executa. Coage `mode`/`hitl` de string (sobrevivem ao
    pickle da fila como enum, mas a API/CLI podem mandar texto). Abre o checkpointer
    Postgres e o publisher Redis de produção por default; ambos são **injetáveis** para
    teste offline. O resumo (`{run_id, status, query, needs_review}`) é o retorno do job
    que a API lê (a tabela `run` é atualizada pelo caminho de persistência das fases que
    a tocam — aqui o foco é orquestrar e publicar progresso).
    """
    run_id = run_id or uuid.uuid4().hex
    mode = ExecutionMode(mode)
    hitl = HITLMode(hitl)

    client = redis_client if redis_client is not None else _redis_from_settings()
    publisher: Callable[[ProgressEvent], None] | None = (
        RedisProgressPublisher(client) if client is not None else None
    )
    open_cp = open_checkpointer or _default_checkpointer

    with open_cp() as checkpointer:
        state = runner(
            query,
            run_id=run_id,
            mode=mode,
            hitl=hitl,
            checkpointer=checkpointer,
            on_event=publisher,
        )

    return {
        "run_id": run_id,
        "status": state.status.value,
        "query": query,
        "needs_review": state.needs_review,
    }


def default_queue(*, connection: Redis | None = None) -> Queue:
    """Fila RQ `tapi` ligada ao Redis da config (F0.3). Onde a API enfileira e o worker puxa."""
    from rq import Queue

    return Queue("tapi", connection=connection or _redis_from_settings())


def enqueue_run(
    query: str,
    *,
    queue: Queue,
    run_id: str | None = None,
    mode: ExecutionMode | str = ExecutionMode.SINGLE_COMPANY,
    hitl: HITLMode | str = HITLMode.SYNC,
) -> str:
    """Enfileira um run e devolve o `run_id` (a API responde isso; o SSE acompanha o canal).

    `job_id=run_id` casa o job RQ com o `run_id` (= thread do checkpointer e canal de
    progresso), então o mesmo identificador rastreia o run de ponta a ponta. Só os
    argumentos planos viajam na fila; o job abre Redis/Postgres ao rodar.
    """
    run_id = run_id or uuid.uuid4().hex
    mode = ExecutionMode(mode)
    hitl = HITLMode(hitl)
    queue.enqueue(
        run_graph_job,
        query,
        run_id=run_id,
        mode=mode.value,
        hitl=hitl.value,
        job_id=run_id,
    )
    return run_id
