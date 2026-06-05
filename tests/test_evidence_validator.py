"""Testes do nó evidence_validator (F2.7).

Tudo offline/determinista. Exercita:
- `evidence_sources`/`is_sufficient`: contagem de fontes **independentes** (host distinto,
  `www.` normalizado), unindo `all_evidence` + `source_urls`;
- o nó roteando por `Command`: sem perfil → segue; ≥ N hosts → segue; insuficiente com
  orçamento → retry ao scraper (incrementa `retry_count`, marca RUNNING); insuficiente e
  esgotado → segue com nota rastreável (sem alucinar, sem loop);
- o **loop de retry termina** em exatamente `max_retries` re-coletas (DoD F2 "retry funciona");
- coerência das constantes de roteamento com a espinha (`graph.PIPELINE`).
"""

from __future__ import annotations

from datetime import UTC, datetime

from packages.agents import evidence_sources, is_sufficient
from packages.agents.evidence_validator import (
    CONTINUE_TARGET,
    MIN_SOURCES,
    RETRY_TARGET,
    evidence_validator,
)
from packages.agents.graph import PIPELINE
from packages.schemas import Claim, Evidence, GraphState, RunStatus, StartupProfile

_FETCHED = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)


def _ev(url: str) -> Evidence:
    return Evidence(url=url, snippet="trecho", fetched_at=_FETCHED, content_hash="h")


def _profile(*ev_urls: str, source_urls: list[str] | None = None) -> StartupProfile:
    """Perfil cuja proveniência são as URLs dadas (evidência da descrição + fontes agregadas)."""
    return StartupProfile(
        nome="X",
        descricao=Claim[str](value="o que a empresa faz", evidence=[_ev(u) for u in ev_urls]),
        source_urls=source_urls or [],
    )


def _state(profile: StartupProfile | None, **kw) -> GraphState:
    return GraphState(run_id="r1", query="X", profile=profile, **kw)


# --------------------------------------------------------- contagem de fontes (regra de N)


def test_evidence_sources_counts_distinct_hosts_normalizing_www() -> None:
    # mesmo host por caminhos diferentes + www → UMA fonte (auto-relato, não corrobora).
    prof = _profile("https://acme.ai/sobre", "https://www.acme.ai/produtos")
    assert evidence_sources(prof) == {"acme.ai"}
    assert not is_sufficient(prof)


def test_evidence_sources_unites_evidence_and_source_urls() -> None:
    # corroboração real: descrição citada em acme.ai + fonte agregada de outro veículo.
    prof = _profile("https://acme.ai/sobre", source_urls=["https://braziljournal.com/x"])
    assert evidence_sources(prof) == {"acme.ai", "braziljournal.com"}
    assert is_sufficient(prof)


def test_is_sufficient_respects_min_sources_threshold() -> None:
    prof = _profile("https://a.com", "https://b.com", "https://c.com")
    assert is_sufficient(prof)  # 3 ≥ 2 (default)
    assert not is_sufficient(prof, min_sources=4)


# ------------------------------------------------------------------------ roteamento do nó


def test_node_no_profile_continues_without_retry() -> None:
    # espinha offline (sem extração): nada a corroborar → segue limpo, sem retry/erro.
    cmd = evidence_validator(_state(None))
    assert cmd.goto == CONTINUE_TARGET
    assert cmd.update is None


def test_node_sufficient_continues() -> None:
    cmd = evidence_validator(_state(_profile("https://a.com", "https://b.com")))
    assert cmd.goto == CONTINUE_TARGET
    assert cmd.update is None


def test_node_insufficient_with_budget_retries_to_scraper() -> None:
    cmd = evidence_validator(_state(_profile("https://a.com"), retry_count=0, max_retries=2))
    assert cmd.goto == RETRY_TARGET
    assert cmd.update == {"retry_count": 1, "status": RunStatus.RUNNING}


def test_node_insufficient_exhausted_continues_with_traceable_note() -> None:
    cmd = evidence_validator(_state(_profile("https://a.com"), retry_count=2, max_retries=2))
    assert cmd.goto == CONTINUE_TARGET
    assert len(cmd.update["errors"]) == 1
    note = cmd.update["errors"][0]
    assert "evidência insuficiente" in note
    assert "1 fonte" in note  # contou 1 host independente


# --------------------------------------------------- o loop termina (DoD: retry funciona)


def test_retry_loop_terminates_after_max_retries() -> None:
    # Pior caso: o re-scrape nunca acha fonte nova (perfil de 1 host fica fixo). O loop deve
    # bater no scraper exatamente max_retries vezes e então seguir — sem laço infinito.
    max_retries = 2
    state = _state(_profile("https://a.com"), max_retries=max_retries)
    routes: list[str] = []
    for _ in range(max_retries + 5):  # cota de segurança contra loop infinito no teste
        cmd = evidence_validator(state)
        routes.append(cmd.goto)
        state = state.model_copy(update=cmd.update or {})  # imita o overwrite do LangGraph
        if cmd.goto == CONTINUE_TARGET:
            break

    assert routes == [RETRY_TARGET, RETRY_TARGET, CONTINUE_TARGET]
    assert state.retry_count == max_retries  # contador limpo: nunca passa do orçamento
    assert len(state.errors) == 1  # nota só no passo terminal


def test_retry_disabled_when_max_retries_zero() -> None:
    # max_retries=0 ⇒ sem orçamento: insuficiente segue direto com nota (não re-coleta).
    cmd = evidence_validator(_state(_profile("https://a.com"), max_retries=0))
    assert cmd.goto == CONTINUE_TARGET
    assert "errors" in cmd.update


# -------------------------------------------------------- coerência com a espinha (graph.py)


def test_routing_targets_match_pipeline() -> None:
    assert RETRY_TARGET in PIPELINE
    assert CONTINUE_TARGET in PIPELINE
    # o caminho normal é o nó imediatamente seguinte na espinha; o retry volta ao scraper.
    i = PIPELINE.index("evidence_validator")
    assert PIPELINE[i + 1] == CONTINUE_TARGET
    assert PIPELINE.index(RETRY_TARGET) < i
    assert MIN_SOURCES >= 2
