"""Grafo LangGraph e nós dos agentes (F2).

Nós: search_planner, scraper, extractor, classifier, evidence_validator,
nvidia_rag, recommender, briefing. Estado em GraphState; checkpointer Postgres; HITL via interrupt.

Cliente Nemotron (F0.7) e prompts versionados (F0.12) expostos aqui:
`from packages.agents import get_chat, get_prompt`.
"""

from .llm import Profile, get_chat, reasoning_system_message, smoke
from .prompts import PROMPT_NODES, Prompt, get_prompt

__all__ = [
    "get_chat",
    "reasoning_system_message",
    "smoke",
    "Profile",
    "get_prompt",
    "Prompt",
    "PROMPT_NODES",
]
