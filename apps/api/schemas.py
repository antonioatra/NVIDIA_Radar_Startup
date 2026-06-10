"""DTOs da API TAPI (F5.2) — contratos de request/response dos endpoints HTTP.

Separados dos contratos de domínio (`packages.schemas`): aqui mora só o que cruza a
fronteira HTTP — o corpo do `POST /runs` e a projeção de empresa da lista (F5.4/F5.11) —
enquanto o `Briefing` (F4.4) e os enums (F0.5) são reusados direto na resposta.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from packages.schemas import ExecutionMode, HITLMode


class RunRequest(BaseModel):
    """Corpo do `POST /runs`: a consulta + o modo de execução/HITL (F2.3/F2.8)."""

    query: str = Field(
        min_length=1, description="Nome/domínio (single) ou setor/região (discovery)."
    )
    mode: ExecutionMode = ExecutionMode.SINGLE_COMPANY
    hitl: HITLMode = HITLMode.SYNC


class RunAccepted(BaseModel):
    """Resposta de enfileiramento (`POST /runs` e `/resume`): o `run_id` p/ acompanhar via SSE."""

    run_id: str
    status: str


class CompanyOut(BaseModel):
    """Projeção de empresa para a lista (F5.4/F5.11): perfil + diagnóstico AIMI mais recente.

    Achata `Company` (§2) + o `Score` (AIMI/classe/inception_priority) do run mais recente, com
    as `tecnologias` que a startup usa (nomes normalizados dos sinais F1.11/F2.5) e as
    `nvidia_techs` recomendadas (F4.3) — as duas facetas de tech do filtro F5.11. Os campos de
    diagnóstico são opcionais: empresa coletada mas ainda não pontuada aparece sem AIMI.
    """

    id: int
    nome: str
    setor: str | None = None
    pais: str = "BR"
    website: str | None = None
    classificacao: str | None = None
    aimi_total: int | None = None
    inception_priority: int | None = None
    tecnologias: list[str] = Field(default_factory=list)
    nvidia_techs: list[str] = Field(default_factory=list)


class EvidenceOut(BaseModel):
    """Fonte citável de um sub-score (tabela `evidence`, §8): o link que sustenta o pilar."""

    url: str
    snippet: str
    source_title: str | None = None


class PillarOut(BaseModel):
    """Um pilar do AIMI no detalhe (F5.5): sub-score 0–25 + faixa + justificativa + fontes.

    `pilar` é a chave técnica (`AIMIPillar`, ex.: 'data_moat'); o rótulo PT-BR é da UI. `band`
    vem de `band_for` (RUBRICA §1). As `evidencias` são as linhas `evidence` do score com
    `field=<pilar>` — vazia até a persistência do AIMI gravá-las (a UI degrada sem links).
    """

    pilar: str
    score: int = Field(ge=0, le=25)
    band: str
    justificativa: str | None = None
    evidencias: list[EvidenceOut] = Field(default_factory=list)


class ROIOut(BaseModel):
    """ROI quantificado de uma recomendação (GPU Graduation Engine, F6) — opcional (F5.6).

    Projeta o `roi` JSON da `recommendation` (serializado de `ROIEstimate`, F0.5). Todos os
    campos são opcionais: a recomendação **degrada graciosamente** sem ROI (a UI mostra o cartão
    sem o número enquanto a matriz/benchmark do F6 não existir). Convenção de sinal: delta
    **negativo = melhora** (menos latência / menos custo).
    """

    throughput_speedup: float | None = None
    latency_p95_delta_pct: float | None = None
    cost_delta_pct: float | None = None
    baseline: str | None = None
    optimized: str | None = None
    benchmark_source: str | None = None
    is_live_run: bool = False


class RecommendationOut(BaseModel):
    """Cartão de recomendação no detalhe (§5.5/F5.6): tech + justificativas + evidência dos 2 lados.

    Projeta a `recommendation` (F4.3) com a **evidência dos dois lados** (tabela `evidence`:
    `field='gap'` lado startup / `field='nvidia'` lado KB) e o `roi` opcional (F6). `prioridade`/
    `complexidade` são os valores PT-BR do §5.5; `pilar_origem` é a chave técnica (`AIMIPillar`),
    com o rótulo PT-BR na UI. A lista vem ordenada por prioridade (alta→baixa), como no briefing.
    """

    tech: str
    prioridade: str
    complexidade: str
    justificativa_tecnica: str
    justificativa_negocio: str
    proxima_acao: str
    pilar_origem: str | None = None
    roi: ROIOut | None = None
    evidencia_gap: list[EvidenceOut] = Field(default_factory=list)
    evidencia_nvidia: list[EvidenceOut] = Field(default_factory=list)


class CompanyDetailOut(BaseModel):
    """Detalhe de uma startup (F5.5/F5.6): perfil + radar AIMI + cartões de recomendação.

    Estende a projeção da lista (`CompanyOut`) com a descrição/ano e o **breakdown** do AIMI —
    os 4 sub-scores, suas justificativas e as fontes citáveis (F5.5) — mais os **cartões de
    recomendação** (`recomendacoes`, F5.6) com evidência dos dois lados e ROI opcional.
    `pilares`/`recomendacoes` vêm vazias quando a empresa ainda não foi pontuada/recomendada
    (mesma degradação graciosa da lista: sem AIMI, sem radar; sem recomendação, sem cartão).
    `nvidia_techs` segue como o resumo (só os nomes) das techs recomendadas.
    """

    id: int
    nome: str
    setor: str | None = None
    pais: str = "BR"
    website: str | None = None
    descricao: str | None = None
    ano_fundacao: int | None = None
    classificacao: str | None = None
    aimi_total: int | None = None
    inception_priority: int | None = None
    confidence: float | None = None
    heuristic_version: str | None = None
    pilares: list[PillarOut] = Field(default_factory=list)
    nvidia_techs: list[str] = Field(default_factory=list)
    recomendacoes: list[RecommendationOut] = Field(default_factory=list)


__all__ = [
    "RunRequest",
    "RunAccepted",
    "CompanyOut",
    "EvidenceOut",
    "PillarOut",
    "ROIOut",
    "RecommendationOut",
    "CompanyDetailOut",
]
