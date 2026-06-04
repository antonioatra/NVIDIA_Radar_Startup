"""Eval set rotulado de startups — schema + loader (F1.12).

Conjunto de ground-truth (~20–30 startups) com **classificação** (§5.1) e **AIMI
esperado** (4 pilares × 0–25) por empresa, criado **cedo** porque F6.4 (correlação do
índice) e F7.1/F7.2 (métricas) o **consomem** — F7 só consolida/expande, não cria do
zero. Os rótulos seguem a **definição** de `docs/RUBRICA-AIMI.md` (F0.11), nunca a
heurística de pontuação (v0 F2.6 / v1 F6.1): a escala 0–25 é imutável, então mudar a
heurística não invalida o ground-truth.

A anotação carrega também a **região do plano `classe × AIMI`** (`PlaneRegion`, o "Mapa
de decisão" da RUBRICA §6 / ALINHAMENTO) — separa explicitamente *wrapper* (região,
não classe) do *alvo de graduação* ★ (AI-native, P1/P2 alto, **P3 baixo** = maior
upside NVIDIA, F6.13). `expected_nvidia_techs` é opcional e antecipa o contrato do eval
de recomendação (F7.2b: techs esperadas por empresa).

Os dados vivem em `data/eval/*.yaml` (versionados, human-reviewed). O loader valida a
**coerência direcional** da anotação (ex.: um `non-AI` não pode ter Workflow Depth alto
*por IA*; um alvo de graduação tem P3 baixo) — checagem de sanidade da rotulagem, **não**
o corte calibrado da decisão (esse é F6.4). Puro/offline, como o loader de seeds (F0.9).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from packages.schemas.aimi import band_for
from packages.schemas.enums import AIMIBand, AIMIPillar, Classification, PlaneRegion

# data/eval/ na raiz do repo (packages/eval/dataset.py -> parents[2] == raiz).
EVAL_DIR = Path(__file__).resolve().parents[2] / "data" / "eval"

# Limiares **direcionais** da anotação (sanidade da rotulagem, NÃO o corte de decisão —
# esse é calibrado no eval, F6.4). "Estabelecido" começa em 13; P3 "baixo" = ≤ 8.
_ESTABELECIDO_MIN = 13
_P3_BAIXO_MAX = 8

# Classe estruturalmente exigida por região (definicional, não numérico).
_REGION_CLASS: dict[PlaneRegion, Classification] = {
    PlaneRegion.FORA_ESCOPO: Classification.NON_AI,
    PlaneRegion.PERIFERICO: Classification.AI_ENABLED,
    PlaneRegion.WRAPPER: Classification.AI_NATIVE,
    PlaneRegion.ALVO_GRADUACAO: Classification.AI_NATIVE,
    PlaneRegion.MADURO: Classification.AI_NATIVE,
}


class ExpectedPillars(BaseModel):
    """AIMI esperado: 4 pilares × 0–25 (RUBRICA §§2–5). `total` = soma (0–100)."""

    model_config = ConfigDict(extra="forbid")

    data_moat: int = Field(ge=0, le=25)
    workflow_depth: int = Field(ge=0, le=25)
    technical_optimization: int = Field(ge=0, le=25)
    distribution_moat: int = Field(ge=0, le=25)

    @property
    def total(self) -> int:
        """AIMI total esperado (0–100) — fonte de verdade da correlação F6.4."""
        return (
            self.data_moat
            + self.workflow_depth
            + self.technical_optimization
            + self.distribution_moat
        )

    def band(self, pillar: AIMIPillar) -> AIMIBand:
        """Faixa (RUBRICA §1) do pilar — `pillar.value` casa o nome do campo."""
        return band_for(getattr(self, pillar.value))


class LabeledStartup(BaseModel):
    """Uma startup rotulada por revisão humana (ground-truth do eval set)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    nome: str
    setor: str
    descricao: str
    pais: str = "BR"
    classificacao: Classification
    region: PlaneRegion
    aimi: ExpectedPillars
    expected_nvidia_techs: list[str] = Field(
        default_factory=list,
        description="Techs NVIDIA esperadas por empresa (eval de recomendação, F7.2b).",
    )
    rationale: str = Field(description="Justificativa do rótulo, ancorada na RUBRICA.")
    evidence_urls: list[str] = Field(
        default_factory=list, description="Fontes públicas que sustentam o rótulo (rastreável)."
    )
    synthetic: bool = Field(
        default=False,
        description="True = fixture-semente ancorada na rubrica (sem fonte ao vivo); "
        "False = empresa real e exige evidence_urls.",
    )
    notes: str = ""

    @model_validator(mode="after")
    def _check_coherence(self) -> LabeledStartup:
        # Estrutural: a região fixa a classe (definicional).
        expected = _REGION_CLASS[self.region]
        if self.classificacao is not expected:
            raise ValueError(
                f"{self.id}: região {self.region.value} exige classe {expected.value}, "
                f"veio {self.classificacao.value}."
            )
        wf = self.aimi.workflow_depth
        p3 = self.aimi.technical_optimization
        p1p2 = max(self.aimi.data_moat, wf)  # o "P1 ou P2" do alvo de graduação
        # Direcional (sanidade, não o corte F6.4): non-AI não é AI-native "por IA".
        if self.classificacao is Classification.NON_AI and wf > _P3_BAIXO_MAX:
            raise ValueError(
                f"{self.id}: non-AI não pode ter Workflow Depth alto por IA (coerência direcional)."
            )
        if self.region in (PlaneRegion.WRAPPER, PlaneRegion.ALVO_GRADUACAO) and p3 > _P3_BAIXO_MAX:
            raise ValueError(
                f"{self.id}: região {self.region.value} pressupõe P3 baixo (≤{_P3_BAIXO_MAX}); "
                f"veio {p3} (100% API externa é o gap NVIDIA)."
            )
        if self.region is PlaneRegion.ALVO_GRADUACAO and p1p2 < _ESTABELECIDO_MIN:
            raise ValueError(
                f"{self.id}: alvo de graduação exige P1 ou P2 ≥ {_ESTABELECIDO_MIN} (estabelecido)."
            )
        if self.region is PlaneRegion.MADURO and p3 < _ESTABELECIDO_MIN:
            raise ValueError(
                f"{self.id}: maduro exige P3 estabelecido (≥{_ESTABELECIDO_MIN}): stack própria."
            )
        # Rastreabilidade: empresa real precisa de fonte; fixture-semente é dispensada.
        if not self.synthetic and not self.evidence_urls:
            raise ValueError(f"{self.id}: entrada real (synthetic=false) exige ≥1 evidence_url.")
        return self


@lru_cache
def load_eval_set() -> tuple[LabeledStartup, ...]:
    """Carrega (cacheado) todas as entradas de `data/eval/*.yaml`. IDs são únicos."""
    entries: list[LabeledStartup] = []
    seen: set[str] = set()
    for path in sorted(EVAL_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for raw in data.get("entries", []):
            entry = LabeledStartup.model_validate(raw)
            if entry.id in seen:
                raise ValueError(f"id de eval duplicado: {entry.id!r}")
            seen.add(entry.id)
            entries.append(entry)
    if not entries:
        raise ValueError(f"nenhuma entrada de eval carregada de {EVAL_DIR}")
    return tuple(entries)


def by_classification(classificacao: Classification) -> tuple[LabeledStartup, ...]:
    """Entradas de uma classe (§5.1) — base do macro-F1 (F7.2)."""
    return tuple(e for e in load_eval_set() if e.classificacao is classificacao)


def by_region(region: PlaneRegion) -> tuple[LabeledStartup, ...]:
    """Entradas de uma região do plano `classe × AIMI` (RUBRICA §6)."""
    return tuple(e for e in load_eval_set() if e.region is region)


def class_distribution() -> dict[Classification, int]:
    """Contagem por classe — diagnóstico de balanceamento do conjunto."""
    dist = dict.fromkeys(Classification, 0)
    for e in load_eval_set():
        dist[e.classificacao] += 1
    return dist


__all__ = [
    "EVAL_DIR",
    "ExpectedPillars",
    "LabeledStartup",
    "load_eval_set",
    "by_classification",
    "by_region",
    "class_distribution",
]
