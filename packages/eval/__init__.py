"""Avaliação (F3.9, F7).

RAGAS (faithfulness, answer relevancy, context precision/recall), eval set de
classificação/AIMI, e comparativo de reranker NeMo vs Cohere (somente na F7).

Eval set rotulado (classificação + AIMI esperado, F1.12) — consumido por F6.4/F7.2:
`from packages.eval import load_eval_set, LabeledStartup, by_classification, by_region`.

Avaliação RAGAS do RAG (F3.9) — espinha verde offline + juiz LLM plugável (F7.3):
`from packages.eval import evaluate_rag, get_evaluator, load_baseline`.
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
from .ragas import (
    BASELINE_FILE,
    QUESTIONS_FILE,
    ContextCitation,
    LexicalRagasMetrics,
    RagasJudge,
    RagasMetrics,
    RagasReport,
    RagasUnavailable,
    RagEvaluator,
    RagQuestion,
    RagSample,
    RagSampleResult,
    answer_relevancy,
    build_sample,
    compose_extractive_answer,
    context_precision,
    context_recall,
    evaluate_rag,
    faithfulness,
    get_evaluator,
    load_baseline,
    load_rag_questions,
    write_baseline,
)

__all__ = [
    "EVAL_DIR",
    "ExpectedPillars",
    "LabeledStartup",
    "load_eval_set",
    "by_classification",
    "by_region",
    "class_distribution",
    "QUESTIONS_FILE",
    "BASELINE_FILE",
    "RagasUnavailable",
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
    "RagQuestion",
    "ContextCitation",
    "RagSample",
    "RagasMetrics",
    "RagSampleResult",
    "RagasReport",
    "RagEvaluator",
    "LexicalRagasMetrics",
    "RagasJudge",
    "get_evaluator",
    "compose_extractive_answer",
    "build_sample",
    "load_rag_questions",
    "evaluate_rag",
    "write_baseline",
    "load_baseline",
]
