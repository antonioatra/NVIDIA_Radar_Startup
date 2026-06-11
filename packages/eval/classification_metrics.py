"""Métricas de classificação (F7.2) — accuracy + macro-F1 do classifier vs rótulos (F1.12).

Irmã do `aimi_correlation` (F6.4): onde aquele mede o **índice** (AIMI ordena como o rótulo?),
este mede a **classe** (§5.1: AI-native | AI-enabled | non-AI). Reusa o mesmo sinal que a
produção vê do lado público — o `profile_for` só-de-descrição + `heuristic_score` (v1, F6.1) —
e compara a `classificacao` **predita** com a **rotulada** (ground-truth de `data/eval/`).

Reporta o que o §7 cobra: **accuracy** (global) e **macro-F1** (média não-ponderada do F1 por
classe — trata as 3 classes igual, sem deixar a classe majoritária mascarar as raras), com a
**matriz de confusão** (gold → predito) por baixo p/ ver *onde* erra. Gate: macro-F1 ≥ **0,75**
(meta do §7, revisável com dados). O núcleo (`macro_f1`/`confusion_matrix`/`class_prf`) opera
sobre sequências `gold`/`pred` — testável com casos conhecidos, sem tocar o eval set. Puro/
offline/determinístico, em Python puro (sem scikit-learn, fora do CI), como a espinha do F2–F6.

A correlação do AIMI (F6.4) e a aderência dos 7 casos §5.5 (F4.8) seguem em seus harnesses;
a **F7.5** consolida os três num `docs/AVALIACAO.md` único.
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from packages.schemas.enums import Classification

from .aimi_correlation import predicted_aimi
from .dataset import LabeledStartup, load_eval_set

#: Gate da classificação (§7): macro-F1 ≥ 0,75 no eval set (F1.12).
MACRO_F1_THRESHOLD = 0.75


def predicted_class(entry: LabeledStartup) -> Classification:
    """Classe **predita** pela heurística v1 (F6.1) sobre o perfil só-de-descrição da entrada.

    Reusa o `predicted_aimi` (F6.4) — mesma fixture só-de-descrição (`profile_for`) e mesma
    `heuristic_score` — e extrai a `classificacao`. Predição e índice saem do **mesmo** passo.
    """
    return predicted_aimi(entry).classificacao


def confusion_matrix(
    gold: Sequence[Classification], pred: Sequence[Classification]
) -> dict[str, dict[str, int]]:
    """Matriz de confusão `gold → {pred: contagem}` sobre **todas** as 3 classes (§5.1).

    Linhas e colunas cobrem o taxonomia inteira (zeros explícitos), p/ o relatório mostrar
    *onde* o erro cai (ex.: AI-native confundido com AI-enabled) sem buracos.
    """
    if len(gold) != len(pred):
        raise ValueError(f"séries de tamanhos diferentes: {len(gold)} != {len(pred)}")
    matrix = {g.value: dict.fromkeys((c.value for c in Classification), 0) for g in Classification}
    for g, p in zip(gold, pred, strict=True):
        matrix[g.value][p.value] += 1
    return matrix


def class_prf(
    gold: Sequence[Classification], pred: Sequence[Classification], target: Classification
) -> tuple[float, float, float]:
    """Precision/recall/F1 de **uma** classe (one-vs-rest).

    Convenção p/ denominador zero (classe sem predições ou sem suporte): a métrica vale `0.0`
    em vez de indefinida — explícito e comparável, com o `support` no relatório p/ contexto.
    """
    if len(gold) != len(pred):
        raise ValueError(f"séries de tamanhos diferentes: {len(gold)} != {len(pred)}")
    tp = sum(1 for g, p in zip(gold, pred, strict=True) if g is target and p is target)
    fp = sum(1 for g, p in zip(gold, pred, strict=True) if g is not target and p is target)
    fn = sum(1 for g, p in zip(gold, pred, strict=True) if g is target and p is not target)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return round(precision, 6), round(recall, 6), round(f1, 6)


def accuracy(gold: Sequence[Classification], pred: Sequence[Classification]) -> float:
    """Fração de acertos global (§7). Levanta em séries de tamanhos diferentes ou vazias."""
    if len(gold) != len(pred):
        raise ValueError(f"séries de tamanhos diferentes: {len(gold)} != {len(pred)}")
    if not gold:
        raise ValueError("accuracy exige ao menos 1 ponto.")
    hits = sum(1 for g, p in zip(gold, pred, strict=True) if g is p)
    return round(hits / len(gold), 6)


def macro_f1(gold: Sequence[Classification], pred: Sequence[Classification]) -> float:
    """Macro-F1 = média **não-ponderada** do F1 sobre as classes **com suporte** no gold.

    Trata cada classe presente igual (a majoritária não domina). Classes sem nenhuma entrada
    rotulada não entram na média — não se mede recall de uma classe que o eval set não contém.
    """
    present = [c for c in Classification if any(g is c for g in gold)]
    if not present:
        raise ValueError("macro-F1 exige ao menos uma classe com suporte no gold.")
    f1s = [class_prf(gold, pred, c)[2] for c in present]
    return round(sum(f1s) / len(present), 6)


class ClassMetrics(BaseModel):
    """Precision/recall/F1 + suporte de uma classe — a linha por-classe do relatório."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    classificacao: str
    support: int = Field(ge=0, description="Nº de entradas rotuladas nesta classe (gold).")
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    f1: float = Field(ge=0.0, le=1.0)


class EntryPrediction(BaseModel):
    """Predito × rotulado de uma entrada — a linha rastreável da classificação (§8)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    nome: str
    gold: str
    predicted: str
    correct: bool


class ClassificationReport(BaseModel):
    """Relatório de classificação (F7.2) — accuracy + macro-F1 + confusão; a F7.5 consolida."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    n: int
    accuracy: float = Field(ge=0.0, le=1.0)
    macro_f1: float = Field(ge=0.0, le=1.0)
    per_class: tuple[ClassMetrics, ...]
    confusion: dict[str, dict[str, int]] = Field(description="gold → {predito: contagem}.")
    per_entry: tuple[EntryPrediction, ...]
    meets_threshold: bool = Field(description=f"macro_f1 ≥ {MACRO_F1_THRESHOLD} (gate §7).")


def evaluate_classification(
    entries: Sequence[LabeledStartup] | None = None,
) -> ClassificationReport:
    """Avalia a classificação predita (heurística v1) vs os rótulos do eval set (F1.12).

    Roda `predicted_class` **uma vez** por entrada (perfil só-de-descrição) e agrega accuracy,
    F1 por classe (one-vs-rest), macro-F1 e a matriz de confusão. Default = todo o eval set.
    """
    entries = tuple(entries) if entries is not None else load_eval_set()
    gold = [e.classificacao for e in entries]
    pred = [predicted_class(e) for e in entries]

    support = {c: sum(1 for g in gold if g is c) for c in Classification}
    per_class = tuple(
        ClassMetrics(
            classificacao=c.value,
            support=support[c],
            precision=p,
            recall=r,
            f1=f1,
        )
        for c in Classification
        for (p, r, f1) in [class_prf(gold, pred, c)]
    )
    per_entry = tuple(
        EntryPrediction(
            id=e.id, nome=e.nome, gold=g.value, predicted=p.value, correct=g is p
        )
        for e, g, p in zip(entries, gold, pred, strict=True)
    )
    mf1 = macro_f1(gold, pred)
    return ClassificationReport(
        n=len(entries),
        accuracy=accuracy(gold, pred),
        macro_f1=mf1,
        per_class=per_class,
        confusion=confusion_matrix(gold, pred),
        per_entry=per_entry,
        meets_threshold=mf1 >= MACRO_F1_THRESHOLD,
    )


def _print_report(report: ClassificationReport) -> None:
    mark = "OK " if report.meets_threshold else "XX "
    print(
        f"{mark}Classificação×rótulos (F7.2): macro-F1={report.macro_f1} "
        f"(gate ≥ {MACRO_F1_THRESHOLD}, accuracy={report.accuracy}, n={report.n})"
    )
    for m in report.per_class:
        print(
            f"   {m.classificacao:11} support={m.support:2}  "
            f"P={m.precision:.3f} R={m.recall:.3f} F1={m.f1:.3f}"
        )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI da classificação (F7.2): avalia offline e falha (exit 1) abaixo do gate §7."""
    report = evaluate_classification()
    _print_report(report)
    return 0 if report.meets_threshold else 1


__all__ = [
    "MACRO_F1_THRESHOLD",
    "predicted_class",
    "confusion_matrix",
    "class_prf",
    "accuracy",
    "macro_f1",
    "ClassMetrics",
    "EntryPrediction",
    "ClassificationReport",
    "evaluate_classification",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
