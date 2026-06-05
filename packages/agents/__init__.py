"""Grafo LangGraph e nós dos agentes (F2).

Nós: search_planner, scraper, extractor, classifier, evidence_validator,
nvidia_rag, recommender, gpu_benchmark, briefing. Estado em GraphState; backbone
montado em `graph.py` (F2.1); checkpointer Postgres (F2.2) e HITL via interrupt (F2.8).

Cliente Nemotron (F0.7), prompts versionados (F0.12) e a montagem do grafo (F2.1)
expostos aqui: `from packages.agents import get_chat, get_prompt, run_pipeline`.
"""

from .checkpoint import postgres_checkpointer, run_pipeline_persisted, state_serde
from .graph import PIPELINE, build_graph, compile_graph, run_pipeline
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
    "NODES",
    # search_planner (F2.3)
    "SearchPlan",
    "PrioritizedSource",
    "make_plan",
    "deterministic_plan",
    "detect_mode",
    "resolve_mode",
    # checkpointer Postgres (F2.2)
    "postgres_checkpointer",
    "run_pipeline_persisted",
    "state_serde",
]
