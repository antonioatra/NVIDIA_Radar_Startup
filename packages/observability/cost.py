"""Contabilidade de tokens/custo dos LLMs (F2.9).

Complementa o tracing Langfuse (F0.8): enquanto o Langfuse guarda o detalhe **por nó/chamada**
no servidor, aqui fica o **rollup local por run** — tokens e custo estimado — disponível
*offline* (sem Langfuse no ar) e em memória. É a base do **gate de orçamento (F2.11)** e do
que a API/UI mostra de custo.

Como a medição acontece **sem refatorar os nós**: o `UsageRecorder` é um callback LangChain
que escuta `on_llm_end` de qualquer chamada e soma o uso no escopo ativo. O `traced_config`
(F0.8) já o injeta (`USAGE_RECORDER`), então todo LLM que os nós disparam por ele (F2.3/F2.5/
F2.6) é medido. O escopo é aberto pelo `run_pipeline` (`capture_usage`); fora dele o
`record_usage` é **no-op** — chamadas avulsas (smoke F0.7) não vazam contagem global.

**Preços são estimativas de REFERÊNCIA**, não cobrança: o `build.nvidia.com` roda no free tier,
então o `$/token` real fica a calibrar. Servem p/ *visibilidade* e p/ o orçamento (F2.11), e
para a narrativa de ROI (API externa × NIM local, F6). Sobreponíveis via `MODEL_PRICES`.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from langchain_core.callbacks import BaseCallbackHandler

if TYPE_CHECKING:
    from collections.abc import Iterator

    from langchain_core.outputs import LLMResult


@dataclass(frozen=True)
class ModelPrice:
    """Preço estimado por 1M de tokens (USD), separado entrada/saída."""

    input_per_1m: float
    output_per_1m: float


#: Tabela de preços de referência (estimativas, USD/1M tokens) — calibrável. A busca é por
#: *substring* do id do modelo (tolera sufixos de versão: `...nemotron-super-49b-v1`).
MODEL_PRICES: dict[str, ModelPrice] = {
    "nemotron-nano": ModelPrice(0.10, 0.30),
    "nemotron-super": ModelPrice(0.60, 1.80),
    "nv-embedqa": ModelPrice(0.016, 0.0),
    "nv-rerankqa": ModelPrice(0.016, 0.0),
}

#: Preço default quando o modelo não casa nenhuma chave (conservador).
DEFAULT_PRICE = ModelPrice(0.50, 1.50)


def _price_for(model: str) -> ModelPrice:
    name = (model or "").lower()
    for key, price in MODEL_PRICES.items():
        if key in name:
            return price
    return DEFAULT_PRICE


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Custo estimado (USD) de uma chamada, pela tabela de referência. Arredonda a 6 casas."""
    price = _price_for(model)
    cost = input_tokens / 1e6 * price.input_per_1m + output_tokens / 1e6 * price.output_per_1m
    return round(cost, 6)


@dataclass(frozen=True)
class TokenUsage:
    """Uso agregado de LLM: tokens (entrada/saída/total), nº de chamadas e custo estimado."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    calls: int = 0
    cost_usd: float = 0.0

    def merge(self, other: TokenUsage) -> TokenUsage:
        """Soma dois usos (agregação por run)."""
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            calls=self.calls + other.calls,
            cost_usd=round(self.cost_usd + other.cost_usd, 6),
        )

    def as_dict(self) -> dict[str, Any]:
        """Forma serializável p/ `GraphState.trace["usage"]` (checkpoint/API/UI)."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "calls": self.calls,
            "cost_usd": self.cost_usd,
        }

    @classmethod
    def for_call(cls, *, model: str, input_tokens: int, output_tokens: int) -> TokenUsage:
        """Uso de **uma** chamada (calls=1), com custo estimado pela tabela."""
        return cls(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            calls=1,
            cost_usd=estimate_cost(model, input_tokens, output_tokens),
        )


EMPTY_USAGE = TokenUsage()


def _model_of(result: LLMResult) -> str:
    """Id do modelo de um `LLMResult` (p/ a tabela de preço); vazio se indisponível."""
    out = result.llm_output or {}
    model = out.get("model_name") or out.get("model") or ""
    if model:
        return str(model)
    for batch in result.generations:
        for gen in batch:
            meta = getattr(getattr(gen, "message", None), "response_metadata", None) or {}
            if meta.get("model_name"):
                return str(meta["model_name"])
    return ""


def _usage_dict(result: LLMResult) -> dict:
    """Dict de uso de um `LLMResult`, tolerante aos dois formatos (LangChain e OpenAI-like)."""
    # 1) `usage_metadata` padrão do LangChain (input_tokens/output_tokens/total_tokens).
    for batch in result.generations:
        for gen in batch:
            usage = getattr(getattr(gen, "message", None), "usage_metadata", None)
            if usage:
                return dict(usage)
    # 2) `llm_output["token_usage"]` estilo OpenAI (prompt_tokens/completion_tokens).
    return dict((result.llm_output or {}).get("token_usage") or {})


def extract_usage(result: LLMResult) -> TokenUsage:
    """`LLMResult` → `TokenUsage` (calls=1 — chamou-se o LLM, mesmo se não reportar tokens)."""
    usage = _usage_dict(result)
    inp = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
    out = int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
    return TokenUsage.for_call(model=_model_of(result), input_tokens=inp, output_tokens=out)


# --- escopo de captura por run -------------------------------------------------

#: Bucket por contexto/thread; `None` fora de um `capture_usage` (record vira no-op).
_SINK: ContextVar[list[TokenUsage] | None] = ContextVar("tapi_usage_sink", default=None)


class _UsageScope:
    """Handle do escopo: `.total()` soma o que foi registrado até o momento."""

    def total(self) -> TokenUsage:
        total = EMPTY_USAGE
        for usage in _SINK.get() or []:
            total = total.merge(usage)
        return total


@contextmanager
def capture_usage() -> Iterator[_UsageScope]:
    """Abre um escopo de captura; dentro dele `record_usage` acumula. Reset ao sair (sem leak)."""
    token = _SINK.set([])
    try:
        yield _UsageScope()
    finally:
        _SINK.reset(token)


def record_usage(usage: TokenUsage) -> None:
    """Soma `usage` ao escopo ativo; **no-op** fora de um `capture_usage`."""
    bucket = _SINK.get()
    if bucket is not None:
        bucket.append(usage)


class UsageRecorder(BaseCallbackHandler):
    """Callback que mede toda chamada de LLM (`on_llm_end`) no escopo ativo.

    Injetado em `traced_config` (F0.8) → roda junto de qualquer `.invoke` dos nós, sem que eles
    saibam. Stateless (a soma vive no `ContextVar`), então **um singleton** serve todos os runs e
    o LangChain o deduplica por identidade se ele aparecer em níveis aninhados do grafo.
    """

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:  # noqa: ARG002
        record_usage(extract_usage(response))


#: Singleton compartilhado (ver `UsageRecorder`).
USAGE_RECORDER = UsageRecorder()


__all__ = [
    "ModelPrice",
    "MODEL_PRICES",
    "DEFAULT_PRICE",
    "estimate_cost",
    "TokenUsage",
    "EMPTY_USAGE",
    "extract_usage",
    "capture_usage",
    "record_usage",
    "UsageRecorder",
    "USAGE_RECORDER",
]
