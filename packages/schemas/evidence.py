"""Evidência e claims com proveniência (F0.5).

Princípio de engenharia nº1 (ARQUITETURA §8): *nenhuma afirmação/score sem fonte
citada e rastreável*. `Evidence` é o átomo de proveniência (URL + hash + `fetched_at`
+ trecho de suporte); `Claim[T]` embrulha qualquer valor extraído carregando as
evidências que o sustentam, para que **cada campo** do `StartupProfile` tenha origem
auditável (governança/LGPD, ARQUITETURA §2).
"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .enums import LegalBasis

T = TypeVar("T")


class Evidence(BaseModel):
    """Um trecho público citável que sustenta uma afirmação ou sub-score.

    Espelha a tabela `evidence` (F0.6). Só dado público; founders apenas info
    profissional (ARQUITETURA §2 — governança).
    """

    model_config = ConfigDict(frozen=True)

    url: HttpUrl = Field(description="URL pública da fonte.")
    snippet: str = Field(description="Trecho citado que sustenta a afirmação.")
    fetched_at: datetime = Field(description="Quando a fonte foi coletada (proveniência).")
    content_hash: str | None = Field(
        default=None,
        description="Hash do conteúdo coletado (detecção de mudança/integridade).",
    )
    source_title: str | None = Field(
        default=None, description="Título/identificação humana da fonte."
    )
    legal_basis: LegalBasis | None = Field(
        default=None,
        description="Base legal LGPD da coleta (F1.13); preenchida p/ dado de founder.",
    )


class Claim(BaseModel, Generic[T]):
    """Um valor extraído + as evidências que o sustentam.

    Usado nos campos do `StartupProfile`: garante que cada afirmação carrega
    proveniência. `confidence` é o grau de certeza da extração (0–1).
    """

    value: T
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @property
    def is_grounded(self) -> bool:
        """True se há ao menos uma evidência citável."""
        return len(self.evidence) > 0
