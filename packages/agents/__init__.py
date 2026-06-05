"""Grafo LangGraph e nós dos agentes (F2).

Nós: search_planner, scraper, extractor, classifier, evidence_validator,
nvidia_rag, recommender, gpu_benchmark, human_review (HITL/F2.8), briefing. Estado em
GraphState; backbone montado em `graph.py` (F2.1); checkpointer Postgres (F2.2).

Cliente Nemotron (F0.7), prompts versionados (F0.12) e a montagem do grafo (F2.1)
expostos aqui: `from packages.agents import get_chat, get_prompt, run_pipeline`.
"""

from .checkpoint import postgres_checkpointer, run_pipeline_persisted, state_serde
from .classifier import classify_with_llm, heuristic_score, make_aimi, parse_score
from .evidence_validator import (
    MIN_SOURCES,
    evidence_sources,
    is_sufficient,
)
from .extractor import extract_profile, parse_profile
from .graph import CONDITIONAL_OUT, PIPELINE, build_graph, compile_graph, run_pipeline
from .human_review import review_payload
from .llm import Profile, get_chat, reasoning_system_message, smoke
from .nodes import NODES
from .prompts import PROMPT_NODES, Prompt, get_prompt
from .search_planner import (
    PrioritizedSource,
    SearchPlan,
    detect_mode,
    deterministic_plan,
    make_plan,
    resolve_mode,
)

__all__ = [
    # LLM (F0.7)
    "get_chat",
    "reasoning_system_message",
    "smoke",
    "Profile",
    # prompts (F0.12)
    "get_prompt",
    "Prompt",
    "PROMPT_NODES",
    # grafo (F2.1)
    "build_graph",
    "compile_graph",
    "run_pipeline",
    "PIPELINE",
    "CONDITIONAL_OUT",
    "NODES",
    # search_planner (F2.3)
    "SearchPlan",
    "PrioritizedSource",
    "make_plan",
    "deterministic_plan",
    "detect_mode",
    "resolve_mode",
    # extractor (F2.5) — o nó é acessado via NODES (evita shadowing do submódulo)
    "extract_profile",
    "parse_profile",
    # classifier (F2.6) — o nó é acessado via NODES (evita shadowing do submódulo)
    "heuristic_score",
    "parse_score",
    "classify_with_llm",
    "make_aimi",
    # evidence_validator (F2.7) — o nó é acessado via NODES (evita shadowing do submódulo)
    "evidence_sources",
    "is_sufficient",
    "MIN_SOURCES",
    # human_review (F2.8) — o nó é acessado via NODES (evita shadowing do submódulo)
    "review_payload",
    # checkpointer Postgres (F2.2)
    "postgres_checkpointer",
    "run_pipeline_persisted",
    "state_serde",
]
