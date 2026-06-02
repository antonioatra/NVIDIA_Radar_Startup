"""Factory de clientes Nemotron (F0.7).

Dois perfis de modelo, conforme ARQUITETURA §"Modelos Nemotron por tarefa":
- **fast** → **Nano**: `search_planner`, roteamento de scraping, normalização.
- **reason** → **Super**: `extractor`, `classifier`, `recommender`, `briefing`
  (reasoning ligado por system message, ver `reasoning_system_message`).

Consome a config central (F0.3): chave, nomes de modelo e `nim_base_url`. O callback
do Langfuse (F0.8) **não** entra aqui — é passado em tempo de `.invoke(config=...)`
pelos nós (F2), para que o mesmo cliente cacheado sirva runs com traces distintos.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from langchain_core.messages import SystemMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from packages.config import get_settings

Profile = Literal["fast", "reason"]

# Toggle de raciocínio do Nemotron: controlado por system message dedicado,
# não por parâmetro do cliente. Nano roda sempre OFF; Super liga conforme a tarefa.
_THINKING_ON = "detailed thinking on"
_THINKING_OFF = "detailed thinking off"

# Defaults de amostragem por perfil (recomendação NVIDIA p/ Nemotron):
# reasoning ON → temperature 0.6 / top_p 0.95; roteamento/normalização → greedy.
_SAMPLING: dict[Profile, dict[str, float]] = {
    "fast": {"temperature": 0.0, "top_p": 1.0},
    "reason": {"temperature": 0.6, "top_p": 0.95},
}


def reasoning_system_message(enabled: bool = True) -> SystemMessage:
    """System message que liga/desliga o reasoning do Nemotron-Super.

    Os nós (F2) prefixam isto no prompt versionado (F0.12): `reason`/Super liga
    conforme a tarefa (classifier/recommender/briefing); `fast`/Nano não usa.
    """
    return SystemMessage(content=_THINKING_ON if enabled else _THINKING_OFF)


@lru_cache
def get_chat(
    profile: Profile = "fast",
    *,
    self_hosted: bool = False,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> ChatNVIDIA:
    """Cliente Nemotron por perfil (F0.7), cacheado por combinação de argumentos.

    - `fast`   → Nano (`NEMOTRON_MODEL_FAST`).
    - `reason` → Super (`NEMOTRON_MODEL_REASON`); ligue o reasoning com
      `reasoning_system_message`.

    `self_hosted=True` aponta para o NIM local (GPU, `NIM_BASE_URL`); caso contrário
    usa o catálogo build.nvidia.com com `NVIDIA_API_KEY`. `temperature` sobrepõe o
    default do perfil.
    """
    s = get_settings()
    model = s.nemotron_model_fast if profile == "fast" else s.nemotron_model_reason
    sampling = _SAMPLING[profile]

    kwargs: dict = {
        "model": model,
        "temperature": sampling["temperature"] if temperature is None else temperature,
        "top_p": sampling["top_p"],
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if self_hosted:
        kwargs["base_url"] = s.nim_base_url
    elif s.nvidia_api_key:
        kwargs["api_key"] = s.nvidia_api_key

    return ChatNVIDIA(**kwargs)


def smoke(profile: Profile = "fast") -> str:
    """Smoke test (F0.7): chamada real mínima ao Nemotron; retorna o texto.

    Requer `NVIDIA_API_KEY`. Usado pelo `__main__` e pelo teste de integração (pulado
    sem chave). Com o Langfuse ligado (F0.8), a chamada vai com o callback de tracing
    e aparece como trace — critério de DoD da F0.8.
    """
    from langchain_core.messages import HumanMessage

    from packages.observability import flush_tracing, traced_config

    messages: list = []
    if profile == "reason":
        messages.append(reasoning_system_message(True))
    messages.append(HumanMessage(content="Responda apenas com a palavra: OK"))
    out = get_chat(profile).invoke(messages, config=traced_config(node=f"smoke:{profile}")).content
    flush_tracing()
    return out


if __name__ == "__main__":  # pragma: no cover
    import sys

    if not get_settings().nvidia_api_key:
        sys.exit("NVIDIA_API_KEY ausente — configure o .env antes do smoke test (F0.7).")
    for _profile in ("fast", "reason"):
        print(f"[{_profile}] ->", smoke(_profile).strip()[:200])
