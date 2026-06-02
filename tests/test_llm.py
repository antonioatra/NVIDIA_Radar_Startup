"""Testes do cliente Nemotron (F0.7).

Validam (offline) o mapeamento perfil→modelo (Nano/Super), os defaults de amostragem,
o endpoint self-hosted (NIM) vs. catálogo build.nvidia.com, o toggle de reasoning e o
cache da factory. O smoke real (rede) só roda com `NVIDIA_API_KEY` presente.
"""

from __future__ import annotations

import pytest
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from packages.agents.llm import get_chat, reasoning_system_message, smoke
from packages.config import get_settings


def test_fast_maps_to_nano() -> None:
    s = get_settings()
    c = get_chat("fast")
    assert isinstance(c, ChatNVIDIA)
    assert c.model == s.nemotron_model_fast
    assert "nano" in c.model
    assert c.temperature == 0.0  # greedy p/ roteamento/normalização


def test_reason_maps_to_super() -> None:
    s = get_settings()
    c = get_chat("reason")
    assert c.model == s.nemotron_model_reason
    assert "super" in c.model
    assert c.temperature == pytest.approx(0.6)  # recomendação NVIDIA p/ reasoning


def test_self_hosted_uses_nim_base_url() -> None:
    s = get_settings()
    c = get_chat("fast", self_hosted=True)
    assert str(c.base_url).rstrip("/") == s.nim_base_url.rstrip("/")


def test_catalog_uses_build_endpoint() -> None:
    c = get_chat("reason")
    assert "integrate.api.nvidia.com" in str(c.base_url)


def test_temperature_override() -> None:
    c = get_chat("reason", temperature=0.0)
    assert c.temperature == 0.0


def test_reasoning_system_message() -> None:
    assert reasoning_system_message(True).content == "detailed thinking on"
    assert reasoning_system_message(False).content == "detailed thinking off"


def test_get_chat_is_cached() -> None:
    assert get_chat("fast") is get_chat("fast")
    assert get_chat("fast") is not get_chat("reason")


@pytest.mark.skipif(
    not get_settings().nvidia_api_key,
    reason="smoke real (F0.7) precisa de NVIDIA_API_KEY",
)
def test_smoke_real() -> None:
    out = smoke("fast")
    assert isinstance(out, str) and out.strip()
