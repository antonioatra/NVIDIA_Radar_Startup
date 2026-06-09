"""API HTTP do TAPI (FastAPI) — F5.2.

A camada que o front (F5.3+) consome e a fronteira do grafo multi-agente para o mundo. Os
runs longos (coleta + LLM) **não** cabem no request: `POST /runs` só **enfileira** (worker RQ,
F2.10) e devolve o `run_id`; `GET /runs/{id}` transmite o progresso ao vivo por **SSE** (canal
Redis pub/sub do worker); `POST /runs/{id}/resume` retoma o grafo após o HITL (F2.8/F5.10);
`GET /companies` serve a lista filtrável (F5.4/F5.11) e `GET /briefings/{id}` o relatório
executivo (F4.4) em JSON/Markdown/PDF (F4.6, base do export F5.8).

Recursos vivos (fila, Redis, sessão SQL, leitor de briefing) entram por **dependência**
(`apps/api/deps.py`), sobrescrevíveis em teste. A **autenticação** (gate interno) é a F5.9 —
aplicada como dependência sobre estes endpoints; aqui ficam só as rotas.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Annotated, Any

from fastapi import Body, Depends, FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse, Response, StreamingResponse
from rq import Queue
from sqlmodel import Session

from apps.worker import enqueue_resume, enqueue_run
from packages.agents.briefing import render_markdown, render_pdf
from packages.agents.progress import ProgressEvent
from packages.schemas import Briefing

from .companies import list_companies
from .deps import db_session, get_briefing_loader, get_progress_source, get_queue
from .schemas import CompanyOut, RunAccepted, RunRequest

app = FastAPI(title="TAPI API", version="0.1.0")

QueueDep = Annotated[Queue, Depends(get_queue)]
SessionDep = Annotated[Session, Depends(db_session)]
_ProgressSource = Callable[[str], Iterable[ProgressEvent]]
ProgressSourceDep = Annotated[_ProgressSource, Depends(get_progress_source)]
BriefingLoaderDep = Annotated[Callable[[str], Briefing | None], Depends(get_briefing_loader)]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# --- runs ---------------------------------------------------------------------


@app.post("/runs", status_code=202)
def create_run(req: RunRequest, queue: QueueDep) -> RunAccepted:
    """Enfileira um run do grafo (worker RQ, F2.10) e devolve o `run_id` p/ acompanhar via SSE."""
    run_id = enqueue_run(req.query, queue=queue, mode=req.mode, hitl=req.hitl)
    return RunAccepted(run_id=run_id, status="pending")


def _sse(events: Iterable[ProgressEvent]) -> Iterable[str]:
    """Serializa cada `ProgressEvent` como um frame SSE (`data: <json>\\n\\n`)."""
    for event in events:
        yield f"data: {event.model_dump_json()}\n\n"


@app.get("/runs/{run_id}")
def stream_run(run_id: str, source: ProgressSourceDep) -> StreamingResponse:
    """Acompanha um run ao vivo (SSE): assina o canal de progresso (F2.10) e repassa ao front."""
    return StreamingResponse(_sse(source(run_id)), media_type="text/event-stream")


@app.post("/runs/{run_id}/resume", status_code=202)
def resume_run(
    run_id: str,
    queue: QueueDep,
    decision: Annotated[dict | None, Body()] = None,
) -> RunAccepted:
    """Retoma um run pausado no HITL sync (F2.8) com a decisão do gerente (F5.10) via worker."""
    enqueue_resume(run_id, decision or {}, queue=queue)
    return RunAccepted(run_id=run_id, status="resuming")


# --- companies ----------------------------------------------------------------


@app.get("/companies")
def get_companies(
    session: SessionDep,
    setor: Annotated[str | None, Query()] = None,
    classificacao: Annotated[str | None, Query()] = None,
    min_aimi: Annotated[int | None, Query(ge=0, le=100)] = None,
    tech: Annotated[str | None, Query(description="Tech que a startup usa (F5.11).")] = None,
    nvidia_tech: Annotated[str | None, Query(description="Tech NVIDIA recomendada (F5.11).")] = (
        None
    ),
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[CompanyOut]:
    """Lista as startups (perfil + AIMI) filtráveis por setor/AIMI/classe (F5.4) e tech (F5.11)."""
    return list_companies(
        session,
        setor=setor,
        classificacao=classificacao,
        min_aimi=min_aimi,
        tech=tech,
        nvidia_tech=nvidia_tech,
        limit=limit,
    )


# --- briefings ----------------------------------------------------------------


@app.get("/briefings/{run_id}")
def get_briefing(
    run_id: str,
    load: BriefingLoaderDep,
    format: Annotated[str, Query(pattern="^(json|md|pdf)$")] = "json",
) -> Any:
    """Relatório executivo de um run (F4.4) em JSON | Markdown | PDF (F4.6 — export F5.8).

    O briefing vem do estado persistido do run (checkpoint, F2.2); `404` se o run ainda não
    chegou ao briefing. `md`/`pdf` reusam os renderizadores deterministas do nó (F4.4/F4.6).
    """
    briefing = load(run_id)
    if briefing is None:
        raise HTTPException(status_code=404, detail="briefing não encontrado para o run")
    if format == "md":
        return PlainTextResponse(render_markdown(briefing), media_type="text/markdown")
    if format == "pdf":
        return Response(
            render_pdf(briefing),
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="briefing-{run_id}.pdf"'},
        )
    return briefing
