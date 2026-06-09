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

from packages.db.models import Company, Score
from packages.db.models import Recommendation as RecommendationRow

from .schemas import CompanyOut

if TYPE_CHECKING:
    from sqlmodel import Session


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


__all__ = ["list_companies"]
