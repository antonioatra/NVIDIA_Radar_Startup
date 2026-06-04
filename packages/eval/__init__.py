"""Avaliação (F3.9, F7).

RAGAS (faithfulness, context precision/recall), eval set de classificação/AIMI,
e comparativo de reranker NeMo vs Cohere (somente na F7).

Eval set rotulado (classificação + AIMI esperado, F1.12) — consumido por F6.4/F7.2:
`from packages.eval import load_eval_set, LabeledStartup, by_classification, by_region`.
"""

from .dataset import (
    EVAL_DIR,
    ExpectedPillars,
    LabeledStartup,
    by_classification,
    by_region,
    class_distribution,
    load_eval_set,
)

__all__ = [
    "EVAL_DIR",
    "ExpectedPillars",
    "LabeledStartup",
    "load_eval_set",
    "by_classification",
    "by_region",
    "class_distribution",
]
