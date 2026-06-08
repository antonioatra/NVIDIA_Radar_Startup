"""Persistência das recomendações nas tabelas relacionais (F4.7).

Ponte entre o nó **recommender** (F4.2/F4.3, que devolve `Recommendation` com evidência dos
dois lados) e o schema relacional (F0.6: `recommendation` + a tabela `evidence` polimórfica).
É a contraparte do `persist_profile` (F1.10) para a saída do motor de recomendação: grava
cada recomendação na tabela `recommendation` e **liga a evidência dos dois lados** na tabela
`evidence` — o lado startup (`evidencia_gap`) com `field='gap'`, o lado NVIDIA
(`evidencia_nvidia`, citações da KB) com `field='nvidia'`, ambos sob
`entity_type='recommendation'` / `entity_id=<rec.id>`. Sustenta a auditoria do §8: a decisão
prescrita fica rastreável até as duas fontes que a justificam.

O invariante "evidência dos dois lados" já é garantido pelo schema
(`Recommendation._require_both_sides`, F0.5) e reforçado pelo Guardrails (F4.5); aqui ele só
é **materializado** — toda recomendação que chega tem `gap` **e** `nvidia` para gravar.

**Idempotente** (mesmo ethos do upsert de perfil, F1.10): re-rodar a persistência do mesmo run
não duplica — a recomendação casa por `(run_id, company_id, tech)` e é **enriquecida** em hit;
a evidência dedup por (url, hash, alvo) via `persist_evidence`. Assim o worker (F2.10) pode
reprocessar um run sem inflar linhas. **Puro/offline** salvo a persistência, que roda via
sessão injetada (testável em SQLite). Faz `flush`, não `commit`: a transação é do caller
(worker F2.10 / API F5), como em todo o resto da camada de persistência.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from sqlmodel import select

from packages.db.models import Evidence
from packages.db.models import Recommendation as RecommendationRow
from packages.scraping.provenance import persist_evidence

if TYPE_CHECKING:
    from sqlmodel import Session

    from packages.schemas.evidence import Evidence as EvidenceSchema
    from packages.schemas.recommendation import Recommendation

# `entity_type` da evidência de recomendação na tabela polimórfica (F0.6).
_ENTITY = "recommendation"


def persist_recommendations(
    session: Session,
    recommendations: Sequence[Recommendation],
    *,
    company_id: int,
    run_id: str | None = None,
) -> list[RecommendationRow]:
    """Persiste as recomendações (+ evidência dos dois lados) — F4.7.

    Para cada `Recommendation` (saída do recommender, F4.2/F4.3): faz upsert idempotente da
    linha `recommendation` por `(run_id, company_id, tech)` e registra a evidência de cada
    lado na tabela `evidence` (`field='gap'` lado startup, `field='nvidia'` lado KB). Devolve
    as linhas persistidas, na ordem de entrada. `flush` (não `commit`): a transação é do caller.
    """
    rows: list[RecommendationRow] = []
    for rec in recommendations:
        row = _upsert_recommendation(session, rec, company_id=company_id, run_id=run_id)
        _record_recommendation_evidence(session, row, rec)
        rows.append(row)
    return rows


def _upsert_recommendation(
    session: Session, rec: Recommendation, *, company_id: int, run_id: str | None
) -> RecommendationRow:
    """Upsert idempotente da linha `recommendation` por `(run_id, company_id, tech)`.

    Em hit **enriquece** (a recomendação mais recente do mesmo run/empresa/tech prevalece,
    sem duplicar); em miss insere. `flush` p/ materializar o `id` (alvo da evidência).
    """
    row = session.exec(
        select(RecommendationRow).where(
            RecommendationRow.company_id == company_id,
            RecommendationRow.run_id == run_id,
            RecommendationRow.tech == rec.tech,
        )
    ).first()
    if row is None:
        row = RecommendationRow(company_id=company_id, run_id=run_id, tech=rec.tech)
        session.add(row)

    row.justificativa_tecnica = rec.justificativa_tecnica
    row.justificativa_negocio = rec.justificativa_negocio
    row.prioridade = rec.prioridade
    row.complexidade = rec.complexidade
    row.proxima_acao = rec.proxima_acao
    row.pilar_origem = rec.pilar_origem
    # ROI (F6) é opcional e mora em JSON; serializa só o que houver.
    row.roi = rec.roi.model_dump() if rec.roi else None

    session.flush()
    return row


def _record_recommendation_evidence(
    session: Session, row: RecommendationRow, rec: Recommendation
) -> None:
    """Registra a evidência dos **dois lados** na tabela `evidence` (auditável, §8).

    `field` distingue o lado: `'gap'` (startup — o que no perfil/AIMI motiva) e `'nvidia'`
    (citações da KB recuperadas pelo RAG). Dedup por (url, hash, alvo) via `persist_evidence`.
    """
    for field, evidence_list in (("gap", rec.evidencia_gap), ("nvidia", rec.evidencia_nvidia)):
        for ev in evidence_list:
            persist_evidence(session, _evidence_row(ev, entity_id=row.id, field=field))


def _evidence_row(ev: EvidenceSchema, *, entity_id: int, field: str) -> Evidence:
    """Converte a `Evidence` do schema numa linha da tabela `evidence` (alvo = recomendação).

    Preserva a proveniência que a evidência já carrega (base legal LGPD / política de ToS),
    sem re-derivar nada: o lado `gap` vem do perfil (já anotado em F1.10/F1.13/F1.15) e o lado
    `nvidia` da KB recuperada (F3.7).
    """
    return Evidence(
        url=str(ev.url),
        snippet=ev.snippet,
        fetched_at=ev.fetched_at,
        content_hash=ev.content_hash,
        source_title=ev.source_title,
        entity_type=_ENTITY,
        entity_id=entity_id,
        field=field,
        legal_basis=ev.legal_basis.value if ev.legal_basis else None,
        source_policy=ev.source_policy,
    )


__all__ = ["persist_recommendations"]
