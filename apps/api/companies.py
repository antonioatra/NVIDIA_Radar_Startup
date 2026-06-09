"""Consulta da lista de empresas para o `GET /companies` (F5.2; facetas F5.4/F5.11).

Projeta a tabela `company` (§2) cruzada com o `Score` (AIMI/classe/inception_priority) do
run **mais recente** e com as techs recomendadas (`recommendation`, F4.3), aplicando os
filtros da lista: setor/AIMI/classe (F5.4) + as duas facetas de tecnologia (F5.11) — a tech
que a startup **usa** (`Company.tecnologias`, sinais F1.11/F2.5) e a tech NVIDIA
**recomendada**. A ordenação default é por `inception_priority` desc (a fila de outreach do
gerente, F6.13), com o AIMI como desempate.

Determinístico e portável (SQLite no teste, Postgres em prod): carrega as linhas e resolve
"score mais recente por empresa" + facetas de tech em Python — o volume é de ferramenta
interna e o match de tech é por substring case-insensitive (a normalização de vocabulário
controlado fica na F5.11). `flush`/leitura só; a sessão é do caller (dependência da API).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import select

from packages.db.models import Company, Evidence, Score
from packages.db.models import Recommendation as RecommendationRow
from packages.schemas.aimi import band_for
from packages.schemas.enums import AIMIPillar

from .schemas import CompanyDetailOut, CompanyOut, EvidenceOut, PillarOut

if TYPE_CHECKING:
    from sqlmodel import Session

# Pilares do AIMI na ordem canônica (RUBRICA §1) → coluna do sub-score + coluna da
# justificativa no `Score` (F0.6). É a ordem em que o radar (F5.5) desenha os eixos.
_PILLAR_COLUMNS: tuple[tuple[AIMIPillar, str, str], ...] = (
    (AIMIPillar.DATA_MOAT, "data_moat", "just_data_moat"),
    (AIMIPillar.WORKFLOW_DEPTH, "workflow_depth", "just_workflow_depth"),
    (AIMIPillar.TECHNICAL_OPTIMIZATION, "technical_optimization", "just_technical_optimization"),
    (AIMIPillar.DISTRIBUTION_MOAT, "distribution_moat", "just_distribution_moat"),
)


def _tech_names(tecnologias: list) -> list[str]:
    """Nomes das techs que a startup usa (a partir do JSON `{nome, categoria, uso, ...}`)."""
    names: list[str] = []
    for t in tecnologias:
        nome = t.get("nome") if isinstance(t, dict) else t
        if nome:
            names.append(str(nome))
    return names


def _matches(needle: str | None, haystack: list[str]) -> bool:
    """Faceta de tech: `needle` casa (substring, case-insensitive) com algum nome da lista."""
    if not needle:
        return True
    low = needle.lower()
    return any(low in name.lower() for name in haystack)


def _latest_scores(session: Session) -> dict[int, Score]:
    """Score AIMI mais recente por `company_id` (o diagnóstico vigente da empresa)."""
    latest: dict[int, Score] = {}
    for sc in session.exec(select(Score)).all():
        cur = latest.get(sc.company_id)
        if cur is None or sc.created_at > cur.created_at:
            latest[sc.company_id] = sc
    return latest


def _recommended_techs(session: Session) -> dict[int, list[str]]:
    """Techs NVIDIA recomendadas por `company_id` (faceta (b) do filtro F5.11)."""
    techs: dict[int, list[str]] = {}
    for row in session.exec(select(RecommendationRow)).all():
        techs.setdefault(row.company_id, []).append(row.tech)
    return techs


def _sort_key(company: CompanyOut) -> tuple:
    """Ordena por inception_priority desc, AIMI desc (None por último) e nome asc."""
    ip, aimi = company.inception_priority, company.aimi_total
    return (ip is None, -(ip or 0), aimi is None, -(aimi or 0), company.nome.lower())


def list_companies(
    session: Session,
    *,
    setor: str | None = None,
    classificacao: str | None = None,
    min_aimi: int | None = None,
    tech: str | None = None,
    nvidia_tech: str | None = None,
    limit: int = 50,
) -> list[CompanyOut]:
    """Lista as empresas projetadas + filtradas para a UI (F5.4/F5.11).

    Filtros (todos opcionais, combinam em AND): `setor` (igualdade case-insensitive),
    `classificacao` (classe AIMI, ex.: "AI-native"), `min_aimi` (total ≥ corte, exige score),
    `tech` (a startup usa) e `nvidia_tech` (recomendada). Ordena por `inception_priority` e
    corta em `limit`. Empresa sem score só aparece quando nenhum filtro de diagnóstico a exige.
    """
    scores = _latest_scores(session)
    rec_techs = _recommended_techs(session)

    out: list[CompanyOut] = []
    for company in session.exec(select(Company)).all():
        sc = scores.get(company.id)
        usadas = _tech_names(company.tecnologias)
        nvidia = rec_techs.get(company.id, [])

        if setor and (company.setor or "").lower() != setor.lower():
            continue
        if classificacao and (
            sc is None or sc.classificacao.value.lower() != classificacao.lower()
        ):
            continue
        if min_aimi is not None and (sc is None or sc.total < min_aimi):
            continue
        if not _matches(tech, usadas) or not _matches(nvidia_tech, nvidia):
            continue

        out.append(
            CompanyOut(
                id=company.id,
                nome=company.nome,
                setor=company.setor,
                pais=company.pais,
                website=company.website,
                classificacao=sc.classificacao.value if sc is not None else None,
                aimi_total=sc.total if sc is not None else None,
                inception_priority=sc.inception_priority if sc is not None else None,
                tecnologias=usadas,
                nvidia_techs=nvidia,
            )
        )

    out.sort(key=_sort_key)
    return out[:limit]


def _latest_score_for(session: Session, company_id: int) -> Score | None:
    """O `Score` AIMI mais recente de **uma** empresa (o diagnóstico vigente p/ o detalhe)."""
    latest: Score | None = None
    for sc in session.exec(select(Score).where(Score.company_id == company_id)).all():
        if latest is None or sc.created_at > latest.created_at:
            latest = sc
    return latest


def _score_evidence(session: Session, score_id: int) -> dict[str, list[EvidenceOut]]:
    """Evidência de um score agrupada por pilar (`evidence.field`), para o radar (F5.5).

    Lê as linhas `evidence` com `entity_type='score'`/`entity_id=<score>` e indexa por `field`
    (o pilar que a fonte sustenta). Pode vir vazia — a persistência do AIMI ainda não grava
    essas linhas; o detalhe degrada graciosamente (mostra o sub-score sem o link).
    """
    grouped: dict[str, list[EvidenceOut]] = {}
    rows = session.exec(
        select(Evidence).where(
            Evidence.entity_type == "score", Evidence.entity_id == score_id
        )
    ).all()
    for ev in rows:
        grouped.setdefault(ev.field or "", []).append(
            EvidenceOut(url=ev.url, snippet=ev.snippet, source_title=ev.source_title)
        )
    return grouped


def get_company_detail(session: Session, company_id: int) -> CompanyDetailOut | None:
    """Detalhe de uma startup (F5.5): perfil + radar AIMI (4 pilares) com evidência por pilar.

    Achata a `Company` (§2) com o `Score` mais recente — os 4 sub-scores, suas faixas
    (`band_for`), justificativas e as fontes citáveis (agrupadas por pilar) — e as techs NVIDIA
    recomendadas (F4.3). `None` quando a empresa não existe (404 na rota). Empresa sem score sai
    com `pilares=[]` e o diagnóstico nulo (degrada como a lista). `flush`/leitura só.
    """
    company = session.get(Company, company_id)
    if company is None:
        return None

    sc = _latest_score_for(session, company_id)
    nvidia = [
        row.tech
        for row in session.exec(
            select(RecommendationRow).where(RecommendationRow.company_id == company_id)
        ).all()
    ]

    pilares: list[PillarOut] = []
    if sc is not None:
        evidence = _score_evidence(session, sc.id)
        for pilar, score_col, just_col in _PILLAR_COLUMNS:
            value = getattr(sc, score_col)
            pilares.append(
                PillarOut(
                    pilar=pilar.value,
                    score=value,
                    band=band_for(value).value,
                    justificativa=getattr(sc, just_col),
                    evidencias=evidence.get(pilar.value, []),
                )
            )

    return CompanyDetailOut(
        id=company.id,
        nome=company.nome,
        setor=company.setor,
        pais=company.pais,
        website=company.website,
        descricao=company.descricao,
        ano_fundacao=company.ano_fundacao,
        classificacao=sc.classificacao.value if sc is not None else None,
        aimi_total=sc.total if sc is not None else None,
        inception_priority=sc.inception_priority if sc is not None else None,
        confidence=sc.confidence if sc is not None else None,
        heuristic_version=sc.heuristic_version if sc is not None else None,
        pilares=pilares,
        nvidia_techs=nvidia,
    )


__all__ = ["list_companies", "get_company_detail"]
