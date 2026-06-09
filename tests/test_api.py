"""Testes da API HTTP (F5.2) — endpoints do grafo, lista e briefing.

Tudo offline via `app.dependency_overrides`: a fila RQ, a fonte de progresso (SSE), a sessão
SQL (SQLite em memória) e o leitor de briefing entram como stubs — sem broker, Postgres nem
worker. Exercita:
- `POST /runs` / `POST /runs/{id}/resume`: enfileiram o job certo e devolvem o `run_id` (202);
- `GET /runs/{id}`: transmite o progresso como SSE (`text/event-stream`, frames `data:`);
- `GET /companies`: projeta perfil + AIMI e aplica os filtros (setor/AIMI/classe + tech F5.11),
  ordenando por `inception_priority`;
- `GET /briefings/{id}`: serve o relatório em JSON/Markdown/PDF e dá 404 sem briefing.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from apps.api.deps import db_session, get_briefing_loader, get_progress_source, get_queue
from apps.api.main import app
from apps.worker import resume_graph_job, run_graph_job
from packages.agents.briefing import build_briefing
from packages.agents.progress import END_NODE, ProgressEvent
from packages.db.models import Company, Run, Score
from packages.db.models import Recommendation as RecommendationRow
from packages.schemas import AIMIScore, Classification, PillarScore
from packages.schemas.enums import AIMIPillar


class _RecordingQueue:
    """Stub da fila RQ que registra o `enqueue` (sem broker), como em `test_worker`."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def enqueue(self, func, *args, **kwargs) -> None:  # noqa: ANN001 — assina como o RQ
        self.calls.append({"func": func, "args": args, "kwargs": kwargs})


def _aimi(total_pillar: int, classe: Classification) -> AIMIScore:
    def _p(pilar: AIMIPillar) -> PillarScore:
        return PillarScore(pilar=pilar, score=total_pillar, justificativa="sinal")

    return AIMIScore(
        data_moat=_p(AIMIPillar.DATA_MOAT),
        workflow_depth=_p(AIMIPillar.WORKFLOW_DEPTH),
        technical_optimization=_p(AIMIPillar.TECHNICAL_OPTIMIZATION),
        distribution_moat=_p(AIMIPillar.DISTRIBUTION_MOAT),
        classificacao=classe,
    )


def _seed(session: Session) -> None:
    """Duas empresas pontuadas (saúde/fintech) + uma sem score, com techs e recomendações."""
    session.add(Run(id="r1", query="Acme Health"))
    session.add(Run(id="r2", query="Bolt Pay"))

    acme = Company(
        nome="Acme Health",
        setor="saude",
        tecnologias=[{"nome": "OpenAI"}, {"nome": "LangChain"}],
        run_id="r1",
    )
    bolt = Company(nome="Bolt Pay", setor="fintech", tecnologias=[{"nome": "PyTorch"}], run_id="r2")
    cold = Company(nome="Cold Start", setor="saude", tecnologias=[])
    session.add_all([acme, bolt, cold])
    session.flush()

    session.add(
        Score(
            company_id=acme.id,
            run_id="r1",
            classificacao=Classification.AI_NATIVE,
            total=80,
            inception_priority=90,
            data_moat=20,
            workflow_depth=20,
            technical_optimization=20,
            distribution_moat=20,
        )
    )
    session.add(
        Score(
            company_id=bolt.id,
            run_id="r2",
            classificacao=Classification.AI_ENABLED,
            total=40,
            inception_priority=30,
            data_moat=10,
            workflow_depth=10,
            technical_optimization=10,
            distribution_moat=10,
        )
    )
    session.add(
        RecommendationRow(
            company_id=acme.id,
            run_id="r1",
            tech="NVIDIA NIM",
            justificativa_tecnica="serving otimizado",
            justificativa_negocio="reduz custo",
            prioridade="alta",
            complexidade="media",
            proxima_acao="testar NIM",
        )
    )
    session.commit()


@pytest.fixture
def session() -> Session:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        _seed(s)
        yield s


@pytest.fixture
def queue() -> _RecordingQueue:
    return _RecordingQueue()


@pytest.fixture
def client(session: Session, queue: _RecordingQueue):
    app.dependency_overrides[db_session] = lambda: session
    app.dependency_overrides[get_queue] = lambda: queue
    yield TestClient(app)
    app.dependency_overrides.clear()


# --- runs ---------------------------------------------------------------------


def test_create_run_enqueues_and_returns_run_id(client: TestClient, queue: _RecordingQueue) -> None:
    resp = client.post("/runs", json={"query": "Acme AI", "mode": "discovery", "hitl": "auto"})
    assert resp.status_code == 202
    body = resp.json()
    assert body["run_id"] and body["status"] == "pending"

    assert len(queue.calls) == 1
    call = queue.calls[0]
    assert call["func"] is run_graph_job
    assert call["args"] == ("Acme AI",)
    assert call["kwargs"]["job_id"] == body["run_id"]
    assert call["kwargs"]["mode"] == "discovery"
    assert call["kwargs"]["hitl"] == "auto"


def test_create_run_rejects_empty_query(client: TestClient) -> None:
    assert client.post("/runs", json={"query": ""}).status_code == 422


def test_resume_run_enqueues_resume_job(client: TestClient, queue: _RecordingQueue) -> None:
    resp = client.post("/runs/r1/resume", json={"approved": True, "nota": "ok"})
    assert resp.status_code == 202
    assert resp.json() == {"run_id": "r1", "status": "resuming"}

    call = queue.calls[0]
    assert call["func"] is resume_graph_job
    assert call["args"] == ("r1", {"approved": True, "nota": "ok"})
    assert call["kwargs"]["job_id"] == "r1:resume"


def test_stream_run_emits_sse_frames(client: TestClient) -> None:
    events = [
        ProgressEvent(run_id="r1", node="scraper", status="running", pct=20),
        ProgressEvent(run_id="r1", node=END_NODE, status="completed", pct=100),
    ]
    app.dependency_overrides[get_progress_source] = lambda: (lambda run_id: events)

    resp = client.get("/runs/r1")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    assert "data: " in resp.text
    assert "scraper" in resp.text
    assert END_NODE in resp.text


# --- companies ----------------------------------------------------------------


def test_companies_projects_profile_and_aimi(client: TestClient) -> None:
    rows = client.get("/companies").json()
    by_name = {r["nome"]: r for r in rows}

    acme = by_name["Acme Health"]
    assert acme["classificacao"] == "AI-native"
    assert acme["aimi_total"] == 80
    assert acme["inception_priority"] == 90
    assert sorted(acme["tecnologias"]) == ["LangChain", "OpenAI"]
    assert acme["nvidia_techs"] == ["NVIDIA NIM"]
    # Empresa sem score aparece sem diagnóstico (não alucina AIMI).
    assert by_name["Cold Start"]["aimi_total"] is None


def test_companies_ordered_by_inception_priority(client: TestClient) -> None:
    names = [r["nome"] for r in client.get("/companies").json()]
    # priority desc (90, 30) e a sem score por último.
    assert names == ["Acme Health", "Bolt Pay", "Cold Start"]


def test_companies_filter_by_setor(client: TestClient) -> None:
    names = [r["nome"] for r in client.get("/companies?setor=fintech").json()]
    assert names == ["Bolt Pay"]


def test_companies_filter_by_min_aimi_and_classe(client: TestClient) -> None:
    assert [r["nome"] for r in client.get("/companies?min_aimi=50").json()] == ["Acme Health"]
    high = client.get("/companies?classificacao=AI-native").json()
    assert [r["nome"] for r in high] == ["Acme Health"]


def test_companies_filter_by_tech_facets(client: TestClient) -> None:
    # tech que a startup usa (substring, case-insensitive) e tech NVIDIA recomendada (F5.11).
    assert [r["nome"] for r in client.get("/companies?tech=langchain").json()] == ["Acme Health"]
    assert [r["nome"] for r in client.get("/companies?nvidia_tech=nim").json()] == ["Acme Health"]


def test_companies_limit(client: TestClient) -> None:
    assert len(client.get("/companies?limit=1").json()) == 1


# --- briefings ----------------------------------------------------------------


def _briefing():
    # pilares <=6 dispensam evidência (RUBRICA §0); só precisamos de um AIMI válido p/ o relatório.
    return build_briefing(
        _aimi(5, Classification.AI_NATIVE), None, [], empresa="Acme Health", run_id="r1"
    )


def test_briefing_json_md_and_pdf(client: TestClient) -> None:
    app.dependency_overrides[get_briefing_loader] = lambda: (lambda run_id: _briefing())

    js = client.get("/briefings/r1")
    assert js.status_code == 200
    assert js.json()["empresa"] == "Acme Health"

    md = client.get("/briefings/r1?format=md")
    assert md.headers["content-type"].startswith("text/markdown")
    assert "Briefing executivo" in md.text

    pdf = client.get("/briefings/r1?format=pdf")
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")


def test_briefing_404_when_absent(client: TestClient) -> None:
    app.dependency_overrides[get_briefing_loader] = lambda: (lambda run_id: None)
    assert client.get("/briefings/missing").status_code == 404


def test_briefing_rejects_bad_format(client: TestClient) -> None:
    app.dependency_overrides[get_briefing_loader] = lambda: (lambda run_id: _briefing())
    assert client.get("/briefings/r1?format=xml").status_code == 422
