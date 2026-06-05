"""Progresso ao vivo do run — eventos por nó + canal Redis pub/sub (F2.10).

O worker (`apps/worker`, F2.10) roda o grafo num job assíncrono e **publica** o
progresso num canal **Redis pub/sub por `run_id`**; o endpoint SSE da API (F5.2/F5.3)
**assina** o canal e repassa ao front. Este módulo é a fronteira entre os dois:

- `ProgressEvent` — contrato mínimo do evento (`{run_id, node, status, pct, ts}` + `extra`).
- `stream_pipeline` — roda o grafo com `.stream()` e dispara um `ProgressEvent` por nó
  num hook injetável `on_event` (o publisher). Espelha o `run_pipeline` (F2.1): mesmo
  `traced_config`/`capture_usage` (F2.9), mas emite progresso enquanto anda.
- `progress_channel` / `RedisProgressPublisher` / `subscribe_progress` — o transporte: o
  publisher serializa o evento e dá `PUBLISH` no canal; o subscriber é o **consumidor**
  que a F5.3 embrulha em SSE. O cliente Redis é **injetado** (testável sem broker).

**Offline é o default (igual F2.3–F2.9):** sem `on_event` o stream só roda o grafo (que
já é offline/reproduzível, M2/DoD); o Redis só entra quando um cliente é passado. Publicar
é **best-effort** — uma falha de broker (`RedisError`) não derruba o run; o progresso é
telemetria, não o resultado.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import BaseModel, ConfigDict, Field
from redis.exceptions import RedisError

from packages.schemas import ExecutionMode, GraphState, HITLMode, RunStatus

from .graph import PIPELINE, RUN_NAME, compile_graph

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from langgraph.checkpoint.base import BaseCheckpointSaver
    from redis import Redis

#: Nó sentinela do **evento terminal** (run encerrou/pausou). O consumidor SSE (F5.3) o
#: lê para fechar o stream; `status` carrega o desfecho real (completed/awaiting_review/…).
END_NODE = "__end__"

#: Prefixo do canal pub/sub; um canal por `run_id` (isola os assinantes de cada run).
CHANNEL_PREFIX = "tapi:progress:"


def progress_channel(run_id: str) -> str:
    """Nome do canal Redis pub/sub do run (publisher e subscriber concordam aqui)."""
    return f"{CHANNEL_PREFIX}{run_id}"


def _now() -> datetime:
    return datetime.now(UTC)


class ProgressEvent(BaseModel):
    """Evento de progresso de um run (contrato worker → SSE, F2.10).

    `node` é o nó que acabou de rodar (ou `END_NODE` no evento terminal); `status` é o
    estado do run no momento (`RunStatus`); `pct` é a posição na espinha (0–100). `extra`
    leva payload opcional sem quebrar o contrato mínimo.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str
    node: str
    status: str = Field(description="Estado do run no evento (valor de RunStatus).")
    pct: int | None = Field(default=None, ge=0, le=100)
    ts: datetime = Field(default_factory=_now)
    extra: dict = Field(default_factory=dict)


class ProgressPublisher(Protocol):
    """Sink de progresso: recebe cada `ProgressEvent`. O `on_event` do `stream_pipeline`."""

    def __call__(self, event: ProgressEvent) -> None: ...


def _pct(node: str) -> int | None:
    """Progresso (0–100) pela posição do nó na espinha (F2.1). Sentinelas → None."""
    if node not in PIPELINE:
        return None
    return round((PIPELINE.index(node) + 1) / len(PIPELINE) * 100)


def stream_pipeline(
    query: str,
    *,
    run_id: str | None = None,
    mode: ExecutionMode = ExecutionMode.SINGLE_COMPANY,
    hitl: HITLMode = HITLMode.SYNC,
    checkpointer: BaseCheckpointSaver | None = None,
    on_event: Callable[[ProgressEvent], None] | None = None,
) -> GraphState:
    """Roda o grafo com `.stream()`, emitindo um `ProgressEvent` por nó, e devolve o estado.

    Variante streaming do `run_pipeline` (F2.1) para o worker (F2.10): reusa o mesmo
    `traced_config` (span por nó, F2.9) e o `capture_usage` (rollup de tokens em
    `trace["usage"]`). Usa `stream_mode=["updates","values"]`: o **updates** dá o nome do
    nó que acabou (→ evento por nó, `status="running"`), o **values** acumula o estado
    cheio (→ estado final + estampa de custo). Sentinelas do LangGraph (`__interrupt__`,
    …) são puladas.

    Ao fim, emite **um evento terminal** (`node=END_NODE`, `pct=100`) com o desfecho real:
    se o grafo pausou para HITL sync (F2.8 — `checkpointer` presente e há nó pendente),
    o status é `awaiting_review`; senão, o `status` do estado final
    (`completed`/`insufficient_data`/`out_of_scope`, F2.12/F2.13). Sem `on_event` nada é
    publicado (offline default); o grafo roda igual ao `run_pipeline`.
    """
    from packages.observability import capture_usage, traced_config

    run_id = run_id or uuid.uuid4().hex
    init = GraphState(run_id=run_id, query=query, mode=mode, hitl=hitl)

    config = traced_config(node=RUN_NAME, run_id=run_id)
    if checkpointer is not None:
        config["configurable"] = {"thread_id": run_id}

    def _emit(node: str, status: str, pct: int | None) -> None:
        if on_event is not None:
            on_event(ProgressEvent(run_id=run_id, node=node, status=status, pct=pct))

    compiled = compile_graph(checkpointer=checkpointer)
    latest: dict[str, Any] | None = None
    with capture_usage() as usage:
        for stream_mode, chunk in compiled.stream(init, config, stream_mode=["updates", "values"]):
            if stream_mode == "values":
                # No interrupt (F2.8) o chunk de values carrega um `__interrupt__` extra; o
                # estado é `extra="forbid"`, então fica só com os campos próprios do estado.
                latest = {k: v for k, v in chunk.items() if not k.startswith("__")}
                continue
            for node in chunk:  # updates: {node: update} — espinha linear (1 chave)
                if node.startswith("__"):  # __interrupt__ etc. não é nó da espinha
                    continue
                _emit(node, RunStatus.RUNNING.value, _pct(node))
        total = usage.total()

    # Pausa HITL sync (F2.8) só existe com checkpointer; nó pendente ⇒ awaiting_review.
    interrupted = checkpointer is not None and bool(compiled.get_state(config).next)

    state = GraphState.model_validate(latest) if latest is not None else init
    if total.calls:
        state = state.model_copy(update={"trace": {**state.trace, "usage": total.as_dict()}})

    final_status = RunStatus.AWAITING_REVIEW.value if interrupted else state.status.value
    _emit(END_NODE, final_status, 100)
    return state


class RedisProgressPublisher:
    """`ProgressPublisher` que dá `PUBLISH` do evento (JSON) no canal pub/sub do run.

    O cliente Redis é **injetado** (produção: `redis.Redis.from_url(settings.redis_url)`;
    teste: um stub que registra os `publish`). Publicar é **best-effort**: uma falha de
    broker (`RedisError`) é engolida — o progresso é telemetria e não pode derrubar o run.
    """

    def __init__(self, client: Redis) -> None:
        self._client = client

    def __call__(self, event: ProgressEvent) -> None:
        try:
            self._client.publish(progress_channel(event.run_id), event.model_dump_json())
        except RedisError:
            pass  # broker indisponível não derruba o run (progresso é best-effort)


def subscribe_progress(
    client: Redis, run_id: str, *, timeout: float | None = None
) -> Iterator[ProgressEvent]:
    """Assina o canal do run e itera os `ProgressEvent` até o terminal (`END_NODE`).

    **Consumidor** do canal — a F5.3 embrulha isto num endpoint SSE (`GET /runs/{id}`).
    O cliente Redis é injetado; `timeout` (s) limita a espera por mensagem (None = bloqueia
    até a próxima). Mensagens não-`message` (confirmação de subscribe) são ignoradas.
    """
    pubsub = client.pubsub()
    pubsub.subscribe(progress_channel(run_id))
    try:
        while True:
            msg = pubsub.get_message(ignore_subscribe_messages=True, timeout=timeout)
            if msg is None:
                if timeout is not None:
                    break  # estourou a espera sem evento — devolve o controle ao chamador
                continue
            event = ProgressEvent.model_validate_json(msg["data"])
            yield event
            if event.node == END_NODE:
                break
    finally:
        pubsub.close()
