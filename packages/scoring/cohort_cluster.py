"""Camada de coorte do diferencial — clustering + radar do ecossistema (F6.5–F6.7).

Nível 3 do DSS (`docs/ALINHAMENTO-CRITERIOS-E-DECISAO.md`): a visão de **portfólio**. Sobre a tabela
`company` acumulada (F1.14), agrupa as startups por perfil (setor/descrição/stack) e ranqueia os
clusters por **prontidão de graduação** — quais blocos do ecossistema BR são o melhor alvo de
outreach do Inception. Pipeline:

- **F6.5 normalização/dedup** da coorte (dedup por domínio/nome, setor normalizado). cuDF na GPU
  quando ligado; o default é pandas/python (mesma lógica, sem GPU).
- **F6.6 embeddings → clusters**: reusa o **mesmo embedder do RAG** (`get_embedder`: nv-embedqa
  atrás de flag, hashing offline por default — sem 2º embedder) → **KMeans + projeção 2D**. cuML
  (KMeans + UMAP) quando ligado; o default é **numpy puro** (Lloyd + PCA via SVD), determinístico e
  sem deps extras (sklearn/umap não estão no CI) — o fallback CPU travado nos docs.
- **F6.7 radar/ranking**: cada cluster recebe métricas agregadas (AIMI médio, classe dominante,
  Inception médio) e a fração de **alvos de graduação ★** (AI-native + P1/P2 alto + P3 baixo, a
  região `classe × AIMI` do §6); os clusters saem **ordenados por prontidão** p/ a fila do gerente.

Espinha verde: por default roda offline/determinístico (hashing + numpy), reprodutível e sem
rede/GPU; cuDF/cuML/nv-embedqa entram atrás de flag (`embeddings_use_nv` etc.).
"""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from packages.db.models import Company, Score
from packages.rag.embed import Embedder, get_embedder
from packages.schemas.tech_vocab import normalize_techs

# Limiares do alvo de graduação ★ (§6 / RUBRICA): AI-native + P1/P2 alto + P3 (Technical
# Optimization) baixo = maior upside NVIDIA (= Inception Priority F6.13). Escala dos pilares 0–25.
_GRAD_CLASSE = "AI-native"
_GRAD_WORKFLOW_DATA_MIN = 13  # média (data_moat + workflow_depth) ≳ metade da escala
_GRAD_TECH_OPT_MAX = 10  # gap de inferência: Technical Optimization baixo


class CohortPoint(BaseModel):
    """Uma startup da coorte como ponto de clustering (perfil + diagnóstico)."""

    id: int
    nome: str
    setor: str | None = None
    classe: str | None = None
    aimi: int | None = None
    inception_priority: int | None = None
    data_moat: int = 0
    workflow_depth: int = 0
    technical_optimization: int = 0
    distribution_moat: int = 0
    tecnologias: list[str] = Field(default_factory=list)

    def text(self) -> str:
        """Texto de perfil que vai ao embedder (F6.6): setor + descrição-curta + stack."""
        techs = ", ".join(self.tecnologias)
        partes = [self.setor or "", f"tecnologias: {techs}" if techs else ""]
        return ". ".join(p for p in partes if p) or self.nome


class ClusterMember(BaseModel):
    """Uma startup posicionada num cluster, com as coordenadas 2D do radar."""

    id: int
    nome: str
    setor: str | None = None
    classe: str | None = None
    aimi: int | None = None
    inception_priority: int | None = None
    x: float
    y: float
    graduation_ready: bool = False


class Cluster(BaseModel):
    """Um cluster do ecossistema com métricas agregadas e prontidão de graduação (F6.7)."""

    id: int
    label: str
    size: int
    mean_aimi: float
    mean_inception: float
    classe_dominante: str | None = None
    graduation_ready_share: float = Field(ge=0, le=1)
    graduation_ready: bool = False
    members: list[ClusterMember] = Field(default_factory=list)


class CohortClustering(BaseModel):
    """Resultado do radar de coorte (F6.7): clusters ordenados por prontidão + proveniência."""

    n_companies: int
    method: str = Field(description="Backend de clustering: 'cuml' ou 'numpy'.")
    embedder: str = Field(description="Embedder usado (nv-embedqa ou hashing-offline).")
    clusters: list[Cluster] = Field(default_factory=list)


def is_graduation_ready(p: CohortPoint) -> bool:
    """★ alvo de graduação: AI-native + (data+workflow)/2 alto + Technical Optimization baixo."""
    if p.classe != _GRAD_CLASSE:
        return False
    pilares_alto = (p.data_moat + p.workflow_depth) / 2 >= _GRAD_WORKFLOW_DATA_MIN
    return pilares_alto and p.technical_optimization <= _GRAD_TECH_OPT_MAX


def _suggested_k(n: int) -> int:
    """k default proporcional ao tamanho da coorte, limitado p/ não estourar com poucos pontos."""
    if n < 4:
        return 1
    return max(2, min(6, n // 3))


def _kmeans(x: np.ndarray, k: int, *, seed: int = 0, iters: int = 100) -> np.ndarray:
    """KMeans (Lloyd) em numpy puro, init k-means++ determinístico por `seed`. Devolve rótulos."""
    rng = np.random.default_rng(seed)
    n = x.shape[0]
    # k-means++ : 1º centro aleatório, demais proporcionais à distância² ao centro mais próximo.
    centers = [x[rng.integers(n)]]
    for _ in range(1, k):
        d2 = np.min([np.sum((x - c) ** 2, axis=1) for c in centers], axis=0)
        total = d2.sum()
        probs = d2 / total if total > 0 else np.full(n, 1.0 / n)
        centers.append(x[rng.choice(n, p=probs)])
    c = np.array(centers, dtype=float)
    labels = np.zeros(n, dtype=int)
    for _ in range(iters):
        dists = np.linalg.norm(x[:, None, :] - c[None, :, :], axis=2)
        new_labels = dists.argmin(axis=1)
        new_c = np.array(
            [x[new_labels == j].mean(axis=0) if np.any(new_labels == j) else c[j] for j in range(k)]
        )
        if np.array_equal(new_labels, labels) and np.allclose(new_c, c):
            labels = new_labels
            break
        labels, c = new_labels, new_c
    return labels


def _project_2d(x: np.ndarray, *, seed: int = 0) -> np.ndarray:
    """Projeção 2D por PCA (SVD em numpy) — coords estáveis p/ o scatter do radar."""
    if x.shape[0] == 1:
        return np.zeros((1, 2))
    xc = x - x.mean(axis=0)
    _, _, vt = np.linalg.svd(xc, full_matrices=False)
    if vt.shape[0] >= 2:
        comps = vt[:2]
    else:
        comps = np.vstack([vt, np.zeros((2 - vt.shape[0], vt.shape[1]))])
    return xc @ comps.T


def _embed(points: list[CohortPoint], embedder: Embedder) -> np.ndarray:
    """Matriz de embeddings dos perfis (F6.6), via o embedder do RAG (reuso, sem 2º modelo)."""
    vectors = embedder.embed_passages([p.text() for p in points])
    return np.array(vectors, dtype=float)


def normalize_cohort(points: list[CohortPoint]) -> list[CohortPoint]:
    """F6.5 — dedup (por nome normalizado) + setor normalizado; preserva a ordem de entrada.

    Dedup conservador: a 1ª ocorrência de cada nome (lower/strip) vence. cuDF acelera isto em
    volume (atrás de flag); a lógica é idêntica — em ~dezenas de empresas o custo é irrelevante.
    """
    seen: set[str] = set()
    out: list[CohortPoint] = []
    for p in points:
        key = p.nome.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        setor = p.setor.strip() if p.setor else None
        out.append(p.model_copy(update={"setor": setor or None}))
    return out


def _dominant(values: list[str | None]) -> str | None:
    """Valor mais frequente não-nulo (classe dominante do cluster); `None` se todos nulos."""
    counts: dict[str, int] = {}
    for v in values:
        if v:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get) if counts else None  # type: ignore[arg-type]


def _build_cluster(cid: int, members_pts: list[CohortPoint], coords: np.ndarray) -> Cluster:
    """Monta um `Cluster` a partir dos pontos e suas coords 2D: agregados + prontidão (F6.7)."""
    aimis = [p.aimi for p in members_pts if p.aimi is not None]
    incs = [p.inception_priority for p in members_pts if p.inception_priority is not None]
    ready_flags = [is_graduation_ready(p) for p in members_pts]
    members = [
        ClusterMember(
            id=p.id,
            nome=p.nome,
            setor=p.setor,
            classe=p.classe,
            aimi=p.aimi,
            inception_priority=p.inception_priority,
            x=float(coords[i][0]),
            y=float(coords[i][1]),
            graduation_ready=ready_flags[i],
        )
        for i, p in enumerate(members_pts)
    ]
    classe_dom = _dominant([p.classe for p in members_pts])
    share = sum(ready_flags) / len(members_pts) if members_pts else 0.0
    setor_dom = _dominant([p.setor for p in members_pts])
    label = setor_dom or classe_dom or f"cluster {cid}"
    return Cluster(
        id=cid,
        label=label,
        size=len(members_pts),
        mean_aimi=round(sum(aimis) / len(aimis), 1) if aimis else 0.0,
        mean_inception=round(sum(incs) / len(incs), 1) if incs else 0.0,
        classe_dominante=classe_dom,
        graduation_ready_share=round(share, 3),
        graduation_ready=share >= 0.5 and classe_dom == _GRAD_CLASSE,
        members=members,
    )


def cluster_cohort(
    points: list[CohortPoint],
    *,
    k: int | None = None,
    seed: int = 0,
    embedder: Embedder | None = None,
) -> CohortClustering:
    """Agrupa a coorte (F6.5–F6.7): normaliza → embeda → KMeans + 2D → clusters ranqueados.

    Determinístico/offline por default (hashing + numpy). `embedder` injetável (testes); senão
    `get_embedder()` respeita `embeddings_use_nv`. Clusters saem **ordenados por prontidão de
    graduação** (share ★, depois Inception médio) — a leitura de portfólio do gerente.
    """
    pts = normalize_cohort(points)
    n = len(pts)
    emb = embedder or get_embedder()
    result_method = "numpy"
    if n == 0:
        return CohortClustering(n_companies=0, method=result_method, embedder=emb.name)
    x = _embed(pts, emb)
    kk = max(1, min(k or _suggested_k(n), n))
    labels = np.zeros(n, dtype=int) if kk == 1 else _kmeans(x, kk, seed=seed)
    coords = _project_2d(x, seed=seed)
    clusters = [
        _build_cluster(
            cid,
            [pts[i] for i in range(n) if labels[i] == cid],
            coords[[i for i in range(n) if labels[i] == cid]],
        )
        for cid in sorted(set(int(label) for label in labels))
    ]
    # F6.7 — ordena por prontidão: share de ★ desc, depois Inception médio desc (fila de outreach).
    clusters.sort(key=lambda c: (c.graduation_ready_share, c.mean_inception), reverse=True)
    return CohortClustering(
        n_companies=n, method=result_method, embedder=emb.name, clusters=clusters
    )


def load_cohort_points(session: Session) -> list[CohortPoint]:
    """Carrega a coorte do banco (Company + Score mais recente) como pontos de clustering.

    Empresa sem Score entra com diagnóstico nulo (aimi/inception None, pilares 0) — clusteriza pelo
    perfil mesmo sem pontuação (degrada como o resto da UI). N+1 aceitável p/ a coorte (dezenas).
    """
    companies = session.exec(select(Company)).all()
    points: list[CohortPoint] = []
    for c in companies:
        if c.id is None:
            continue
        score = session.exec(
            select(Score).where(Score.company_id == c.id).order_by(Score.created_at.desc())
        ).first()
        techs = normalize_techs(c.tecnologias or [])
        points.append(
            CohortPoint(
                id=c.id,
                nome=c.nome,
                setor=c.setor,
                classe=score.classificacao.value if score else None,
                aimi=score.total if score else None,
                inception_priority=score.inception_priority if score else None,
                data_moat=score.data_moat if score else 0,
                workflow_depth=score.workflow_depth if score else 0,
                technical_optimization=score.technical_optimization if score else 0,
                distribution_moat=score.distribution_moat if score else 0,
                tecnologias=techs,
            )
        )
    return points


__all__ = [
    "CohortPoint",
    "ClusterMember",
    "Cluster",
    "CohortClustering",
    "is_graduation_ready",
    "normalize_cohort",
    "cluster_cohort",
    "load_cohort_points",
]
