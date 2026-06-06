"""Briefings terminais — caminhos de saída que **não forçam recomendação NVIDIA** (F2.12 / F2.13).

Quando o diagnóstico não dá base para o fluxo normal (RAG → recomendação → benchmark), o grafo
encerra num briefing terminal, **sem alucinar**:

- **dados insuficientes (F2.12):** a evidência segue abaixo do piso de N fontes (F2.7) mesmo após
  o retry de coleta esgotar → briefing marcado `dados_insuficientes`, com o que foi apurado +
  as lacunas a cobrir. É o "não afirmar sobre fonte única" (princípio nº1 §8) levado ao desfecho.
- **fora de escopo (F2.13, a fazer):** empresa `non-AI` de alta confiança → briefing
  `fora_de_escopo` (por que não é alvo Inception), sem recomendar tech NVIDIA à força.

O **nó `briefing`** (F4.4, ver `nodes.py`) despacha para cá quando o `status` já chega terminal
(`INSUFFICIENT_DATA` / `OUT_OF_SCOPE`); o caminho normal — diagnóstico + recomendação — é da F4.4.
Determinista/offline: monta o briefing só com o que está no estado (ethos F2.14), sem rede/LLM.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from packages.schemas import Briefing, BriefingStatus

from .evidence_validator import MIN_SOURCES, evidence_sources

if TYPE_CHECKING:
    from packages.schemas import GraphState


def insufficient_data_briefing(state: GraphState, *, min_sources: int = MIN_SOURCES) -> Briefing:
    """Monta o briefing terminal **"dados insuficientes"** (F2.12) a partir do estado.

    Acionado pelo `evidence_validator` (F2.7): após o retry de coleta esgotar, a corroboração
    segue abaixo de `min_sources` hosts independentes. Em vez de classificar/recomendar sobre
    fonte única, o run encerra registrando **o que foi apurado** (nome, AIMI parcial se houver)
    e **as lacunas** — sem recomendação NVIDIA forçada e sem alucinar campos ausentes.
    """
    profile = state.profile
    empresa = (profile.nome if profile is not None else None) or state.query
    n_sources = len(evidence_sources(profile)) if profile is not None else 0

    lacunas = [
        f"corroboração insuficiente: {n_sources} fonte(s) independente(s) coletada(s), "
        f"abaixo do mínimo de {min_sources} para um diagnóstico confiável "
        f"(após {state.retry_count} retry(s) de coleta)."
    ]
    resumo = (
        f"Não foi possível reunir evidência independente suficiente sobre {empresa} para "
        "diagnosticar a maturidade com confiança. Em vez de classificar ou recomendar "
        "tecnologia NVIDIA a partir de fonte única, o run encerra como 'dados insuficientes', "
        "registrando o que foi apurado e as lacunas a cobrir."
    )

    return Briefing(
        empresa=empresa,
        status=BriefingStatus.DADOS_INSUFICIENTES,
        resumo_executivo=resumo,
        aimi=state.aimi,  # o que foi apurado (parcial / baixa confiança); pode ser None
        recomendacoes=[],  # terminal: nada de recomendação NVIDIA forçada
        lacunas=lacunas,
        run_id=state.run_id,
    )


__all__ = ["insufficient_data_briefing"]
