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


__all__ = ["RunRequest", "RunAccepted", "CompanyOut"]
