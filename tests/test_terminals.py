"""Testes dos briefings terminais (F2.12 — dados insuficientes).

Tudo offline/determinista. Exercita:
- `insufficient_data_briefing`: monta o briefing terminal a partir do estado (status
  `dados_insuficientes`, empresa do perfil ou query, lacunas com a contagem de fontes,
  AIMI passado adiante, **sem** recomendação NVIDIA forçada);
- o nó `briefing` despachando por status: `INSUFFICIENT_DATA` → terminal; senão → COMPLETED;
- o **caminho no grafo** (F2.7→F2.12): perfil com corroboração abaixo do piso e retry esgotado
  → o run salta RAG/recomendação/benchmark e encerra em `INSUFFICIENT_DATA` com o briefing
  terminal — sem alucinar.
"""

from __future__ import annotations

from datetime import UTC, datetime

from packages.agents import compile_graph, insufficient_data_briefing
from packages.agents.nodes import NODES
from packages.schemas import (
    BriefingStatus,
    Claim,
    Evidence,
    GraphState,
    RunStatus,
    StartupProfile,
)

_FETCHED = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)


def _profile(*ev_urls: str, nome: str = "Acme AI") -> StartupProfile:
    return StartupProfile(
        nome=nome,
        descricao=Claim[str](
            value="o que a empresa faz",
            evidence=[
                Evidence(url=u, snippet="trecho", fetched_at=_FETCHED, content_hash="h")
                for u in ev_urls
            ],
        ),
    )


# ----------------------------------------------------- helper: monta o briefing terminal


def test_insufficient_data_briefing_from_profile() -> None:
    state = GraphState(
        run_id="r1",
        query="Acme AI",
        profile=_profile("https://acme.ai/sobre"),
        retry_count=2,
        status=RunStatus.INSUFFICIENT_DATA,
    )
    b = insufficient_data_briefing(state)

    assert b.status is BriefingStatus.DADOS_INSUFICIENTES
    assert b.empresa == "Acme AI"  # nome do perfil, não a query
    assert b.recomendacoes == []  # terminal: nada de recomendação NVIDIA forçada
    assert b.run_id == "r1"
    assert len(b.lacunas) == 1
    lacuna = b.lacunas[0]
    assert "1 fonte" in lacuna  # 1 host independente coletado
    assert "mínimo de 2" in lacuna
    assert "2 retry" in lacuna


def test_insufficient_data_briefing_falls_back_to_query_without_profile() -> None:
    # Defensivo: sem perfil, a empresa é a query e a contagem de fontes é 0.
    state = GraphState(run_id="r2", query="empresa desconhecida")
    b = insufficient_data_briefing(state)
    assert b.empresa == "empresa desconhecida"
    assert b.aimi is None
    assert "0 fonte" in b.lacunas[0]


# --------------------------------------------------------- nó briefing despacha por status


def test_briefing_node_emits_terminal_on_insufficient_data() -> None:
    state = GraphState(
        run_id="r3",
        query="Acme AI",
        profile=_profile("https://acme.ai"),
        status=RunStatus.INSUFFICIENT_DATA,
    )
    update = NODES["briefing"](state)
    assert "status" not in update  # status terminal já vem do evidence_validator
    assert update["briefing"].status is BriefingStatus.DADOS_INSUFICIENTES


def test_briefing_node_completes_on_normal_path() -> None:
    # Caminho normal (placeholder F4.4): fecha o run em COMPLETED, sem briefing terminal.
    state = GraphState(run_id="r4", query="Acme AI", status=RunStatus.RUNNING)
    update = NODES["briefing"](state)
    assert update == {"status": RunStatus.COMPLETED}


# ------------------------------------------------------- caminho no grafo (F2.7 → F2.12)


def test_graph_routes_to_terminal_when_evidence_insufficient() -> None:
    # Perfil presente com 1 fonte (< piso de 2) e sem orçamento de retry (max_retries=0):
    # o evidence_validator deve saltar ao briefing terminal, pulando RAG/recomendação.
    init = GraphState(
        run_id="run-insuf",
        query="Acme AI",
        profile=_profile("https://acme.ai"),
        max_retries=0,
    )
    out = GraphState.model_validate(compile_graph().invoke(init, {}))

    assert out.status is RunStatus.INSUFFICIENT_DATA
    assert out.briefing is not None
    assert out.briefing.status is BriefingStatus.DADOS_INSUFICIENTES
    assert out.briefing.recomendacoes == []  # não forçou recomendação
    assert out.recommendations == []  # RAG/recommender foram pulados
    assert any("evidência insuficiente" in e for e in out.errors)
