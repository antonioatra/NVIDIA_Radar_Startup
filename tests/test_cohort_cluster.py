"""Testes da camada de coorte — clustering + radar (F6.5–F6.7)."""

from __future__ import annotations

from packages.scoring.cohort_cluster import (
    CohortPoint,
    cluster_cohort,
    is_graduation_ready,
    normalize_cohort,
)


def _pt(i: int, **kw) -> CohortPoint:
    base = dict(id=i, nome=f"Startup {i}", setor="healthtech")
    base.update(kw)
    return CohortPoint(**base)


def test_graduation_ready_star() -> None:
    # AI-native + (data+workflow)/2 alto + Technical Optimization baixo = ★.
    star = _pt(1, classe="AI-native", data_moat=15, workflow_depth=18, technical_optimization=6)
    assert is_graduation_ready(star) is True
    # Technical Optimization alto (ja otimizado) -> nao e alvo de graduacao.
    optimized = _pt(
        2, classe="AI-native", data_moat=15, workflow_depth=18, technical_optimization=20
    )
    assert is_graduation_ready(optimized) is False
    # Nao AI-native -> nunca ★.
    enabled = _pt(3, classe="AI-enabled", data_moat=15, workflow_depth=18, technical_optimization=6)
    assert is_graduation_ready(enabled) is False


def test_normalize_dedup_by_name() -> None:
    pts = [_pt(1, nome="Acme"), _pt(2, nome=" acme "), _pt(3, nome="Beta", setor="  fintech ")]
    out = normalize_cohort(pts)
    assert [p.id for p in out] == [1, 3]  # 2a "acme" deduplicada; 1a vence
    assert out[1].setor == "fintech"  # setor normalizado (strip)


def test_cluster_cohort_empty() -> None:
    res = cluster_cohort([])
    assert res.n_companies == 0
    assert res.clusters == []
    assert res.method == "numpy"


def test_cluster_cohort_groups_and_ranks() -> None:
    # Dois blocos de perfil distintos: healthtech AI-native ★ vs fintech wrapper.
    health = [
        _pt(
            i,
            nome=f"Health {i}",
            setor="healthtech",
            classe="AI-native",
            aimi=70,
            inception_priority=80,
            data_moat=16,
            workflow_depth=18,
            technical_optimization=6,
            tecnologias=["PyTorch", "Triton"],
        )
        for i in range(1, 5)
    ]
    fintech = [
        _pt(
            i,
            nome=f"Fin {i}",
            setor="fintech",
            classe="AI-enabled",
            aimi=30,
            inception_priority=20,
            data_moat=8,
            workflow_depth=7,
            technical_optimization=18,
            tecnologias=["OpenAI API"],
        )
        for i in range(5, 9)
    ]
    res = cluster_cohort(health + fintech, k=2, seed=0)
    assert res.n_companies == 8
    assert len(res.clusters) == 2
    # Ordenado por prontidao: o cluster ★ (graduation-ready) vem primeiro.
    top = res.clusters[0]
    assert top.graduation_ready is True
    assert top.graduation_ready_share >= 0.5
    assert top.classe_dominante == "AI-native"
    assert top.mean_inception > res.clusters[1].mean_inception
    # Todo mundo posicionado no 2D (coords finitas).
    for c in res.clusters:
        for m in c.members:
            assert isinstance(m.x, float) and isinstance(m.y, float)


def test_cluster_cohort_deterministic() -> None:
    pts = [_pt(i, nome=f"S{i}", setor="setor" + str(i % 3)) for i in range(1, 10)]
    a = cluster_cohort(pts, k=3, seed=42)
    b = cluster_cohort(pts, k=3, seed=42)
    assert [(c.id, c.size, c.label) for c in a.clusters] == [
        (c.id, c.size, c.label) for c in b.clusters
    ]


def test_k_capped_to_n() -> None:
    res = cluster_cohort([_pt(1), _pt(2)], k=10)
    assert sum(c.size for c in res.clusters) == 2  # k limitado a n; ninguem perdido
