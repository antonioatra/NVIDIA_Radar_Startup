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

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from apps.api.deps import db_session, get_briefing_loader, get_progress_source, get_queue
from apps.api.main import app
from apps.worker import resume_graph_job, run_graph_job
from packages.agents.briefing import build_briefing
from packages.agents.progress import END_NODE, ProgressEvent
from packages.db.models import Company, Evidence, Run, Score
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

    acme_score = Score(
        company_id=acme.id,
        run_id="r1",
        classificacao=Classification.AI_NATIVE,
        total=80,
        inception_priority=90,
        data_moat=20,
        workflow_depth=20,
        technical_optimization=20,
        distribution_moat=20,
        just_data_moat="dataset proprietário de prontuários anotados",
    )
    session.add(acme_score)
    session.flush()
    # Evidência de um pilar (entity_type='score', field=<pilar>) — a fonte citável do radar (F5.5).
    session.add(
        Evidence(
            url="https://acme.health/dados",
            snippet="base proprietária com 2M de prontuários rotulados",
            fetched_at=datetime.now(UTC),
            source_title="Acme Health — Tecnologia",
            entity_type="score",
            entity_id=acme_score.id,
            field="data_moat",
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
    acme_rec = RecommendationRow(
        company_id=acme.id,
        run_id="r1",
        tech="NVIDIA NIM",
        justificativa_tecnica="serving otimizado",
        justificativa_negocio="reduz custo",
        prioridade="alta",
        complexidade="media",
        proxima_acao="testar NIM",
        pilar_origem=AIMIPillar.TECHNICAL_OPTIMIZATION,
        # ROI opcional (F6): número degrada gracioso quando ausente; aqui presente.
        roi={
            "throughput_speedup": 3.0,
            "cost_delta_pct": -60.0,
            "baseline": "API externa",
            "optimized": "NIM local",
            "is_live_run": False,
        },
    )
    session.add(acme_rec)
    session.flush()
    # Evidência dos dois lados da recomendação (F4.7): field='gap' (startup) / 'nvidia' (KB).
    session.add(
        Evidence(
            url="https://acme.health/inferencia",
            snippet="usa API externa paga para toda a inferência",
            fetched_at=datetime.now(UTC),
            entity_type="recommendation",
            entity_id=acme_rec.id,
            field="gap",
        )
    )
    session.add(
        Evidence(
            url="https://build.nvidia.com/nim",
            snippet="NIM serve modelos otimizados na própria GPU",
            fetched_at=datetime.now(UTC),
            entity_type="recommendation",
            entity_id=acme_rec.id,
            field="nvidia",
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


# --- company detail (F5.5) ----------------------------------------------------


def _company_id(client: TestClient, nome: str) -> int:
    return next(r["id"] for r in client.get("/companies").json() if r["nome"] == nome)


def test_company_detail_returns_pillars_and_evidence(client: TestClient) -> None:
    cid = _company_id(client, "Acme Health")
    detail = client.get(f"/companies/{cid}").json()

    assert detail["nome"] == "Acme Health"
    assert detail["classificacao"] == "AI-native"
    assert detail["aimi_total"] == 80
    assert detail["nvidia_techs"] == ["NVIDIA NIM"]

    # Os 4 pilares na ordem canônica, com faixa derivada do sub-score (RUBRICA §1).
    pilares = {p["pilar"]: p for p in detail["pilares"]}
    assert [p["pilar"] for p in detail["pilares"]] == [
        "data_moat",
        "workflow_depth",
        "technical_optimization",
        "distribution_moat",
    ]
    data_moat = pilares["data_moat"]
    assert data_moat["score"] == 20
    assert data_moat["band"] == "forte"  # 20 > 18 → forte
    assert data_moat["justificativa"].startswith("dataset proprietário")
    # A evidência do pilar vem com link à fonte (F5.5).
    assert data_moat["evidencias"][0]["url"] == "https://acme.health/dados"
    # Pilar sem evidência persistida degrada gracioso (lista vazia, não erro).
    assert pilares["workflow_depth"]["evidencias"] == []


def test_company_detail_returns_recommendation_cards(client: TestClient) -> None:
    # Cartão da recomendação (§5.5/F5.6): justificativas, pilar de origem, ROI e os dois lados.
    cid = _company_id(client, "Acme Health")
    recs = client.get(f"/companies/{cid}").json()["recomendacoes"]
    assert len(recs) == 1

    nim = recs[0]
    assert nim["tech"] == "NVIDIA NIM"
    assert nim["prioridade"] == "alta"
    assert nim["complexidade"] == "media"
    assert nim["proxima_acao"] == "testar NIM"
    assert nim["pilar_origem"] == "technical_optimization"
    # ROI (F6) presente: ganho de throughput + economia de custo.
    assert nim["roi"]["throughput_speedup"] == 3.0
    assert nim["roi"]["cost_delta_pct"] == -60.0
    assert nim["roi"]["optimized"] == "NIM local"
    # Evidência dos dois lados, cada uma com link à fonte (invariante F4.5).
    assert nim["evidencia_gap"][0]["url"] == "https://acme.health/inferencia"
    assert nim["evidencia_nvidia"][0]["url"] == "https://build.nvidia.com/nim"


def test_company_detail_orders_recommendations_and_roi_optional(
    client: TestClient, session: Session
) -> None:
    # Insere fora de ordem e sem ROI: o detalhe reordena alta→baixa e degrada sem o número.
    bolt_id = _company_id(client, "Bolt Pay")
    for tech, prioridade in (("Tech Baixa", "baixa"), ("Tech Alta", "alta")):
        session.add(
            RecommendationRow(
                company_id=bolt_id,
                run_id="r2",
                tech=tech,
                justificativa_tecnica="jt",
                justificativa_negocio="jn",
                prioridade=prioridade,
                complexidade="baixa",
                proxima_acao="acao",
            )
        )
    session.commit()

    recs = client.get(f"/companies/{bolt_id}").json()["recomendacoes"]
    assert [r["tech"] for r in recs] == ["Tech Alta", "Tech Baixa"]
    assert recs[0]["roi"] is None  # sem ROI → cartão degrada gracioso (F5.6)


def test_company_detail_without_score_has_no_pillars(client: TestClient) -> None:
    cid = _company_id(client, "Cold Start")
    detail = client.get(f"/companies/{cid}").json()
    assert detail["aimi_total"] is None
    assert detail["pilares"] == []


def test_company_detail_404_when_absent(client: TestClient) -> None:
    assert client.get("/companies/999999").status_code == 404


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
