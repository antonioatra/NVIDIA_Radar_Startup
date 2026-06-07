"""Configuração central do TAPI (F0.3).

Carrega o ambiente (`.env` / variáveis de processo) de forma tipada com
`pydantic-settings`. É a fonte única de config consumida por todas as camadas:
migrações/DB (F0.6), cliente Nemotron (F0.7), Langfuse (F0.8), RAG (F3), API/worker
(F5/F2). Os nomes espelham `.env.example` (case-insensitive).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

RerankerProvider = Literal["nemo", "cohere"]
CacheBackend = Literal["disk", "redis"]


class Settings(BaseSettings):
    """Configuração da aplicação, validada a partir do ambiente."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- LLM / NVIDIA -----------------------------------------------------------
    nvidia_api_key: str = Field(default="", description="Chave build.nvidia.com (Nemotron/NIM).")
    nemotron_model_fast: str = "nvidia/llama-3.1-nemotron-nano-8b-v1"
    nemotron_model_reason: str = "nvidia/llama-3.3-nemotron-super-49b-v1"
    nv_embed_model: str = "nvidia/llama-3.2-nv-embedqa-1b-v2"
    nv_rerank_model: str = "nvidia/llama-3.2-nv-rerankqa-1b-v2"

    # NIM self-hosted (GPU local) — opcional no build, usado no F6.
    nim_base_url: str = "http://localhost:8000/v1"

    # search_planner (F2.3): por padrão é determinista/offline (reproduzível, sem rede).
    # Ligue p/ deixar o Nemotron-Nano refinar o plano de coleta (requer nvidia_api_key).
    planner_use_llm: bool = Field(
        default=False, description="search_planner (F2.3) usa o Nano p/ refinar o plano."
    )

    # extractor (F2.5): por padrão offline (no-op limpo — espinha reproduzível sem rede).
    # Ligue p/ o nó estruturar os docs com o Nemotron-Super (requer nvidia_api_key).
    extractor_use_llm: bool = Field(
        default=False, description="extractor (F2.5) usa o Super p/ estruturar o StartupProfile."
    )

    # classifier (F2.6): por padrão usa a heurística AIMI v0 determinista/offline (reproduzível).
    # Ligue p/ o nó diagnosticar classe+AIMI com o Nemotron-Super (requer nvidia_api_key).
    classifier_use_llm: bool = Field(
        default=False, description="classifier (F2.6) usa o Super p/ pontuar classe + AIMI."
    )

    # Embeddings da KB (F3.3): por padrão usa o HashingEmbedder offline/determinista (espinha
    # verde — reproduzível, sem rede/GPU). Ligue p/ embedar com o NeMo Retriever nv-embedqa de
    # verdade (catálogo build.nvidia.com com nvidia_api_key, ou NIM self-hosted/GPU).
    embeddings_use_nv: bool = Field(
        default=False, description="Embeddings da KB (F3.3) usam o NeMo Retriever nv-embedqa."
    )

    # Reranker: nemo (default no build) | cohere (somente validação F7).
    reranker_provider: RerankerProvider = "nemo"
    cohere_api_key: str = Field(default="", description="Só na F7 (trial).")

    # --- Busca / scraping -------------------------------------------------------
    tavily_api_key: str = ""
    firecrawl_api_key: str = ""

    # scraper (F2.4): por padrão é offline (no-op limpo, espinha reproduzível sem rede).
    # Ligue p/ o nó coletar de verdade via adapters F1 (requer tavily/firecrawl + Playwright).
    scraper_use_network: bool = Field(
        default=False, description="scraper (F2.4) coleta as fontes de verdade (rede/F1)."
    )

    # --- HITL (F2.8) ------------------------------------------------------------
    # Por padrão o grafo roda **sem** pausa humana (espinha verde, M2/DoD). Ligue p/ o nó
    # human_review pausar antes do briefing: bloqueante no modo sync (single-company, exige
    # checkpointer/F2.2 p/ o interrupt→resume) e não-bloqueante no modo auto (batch/cohort,
    # F1.14 — só marca `needs_review`). O modo vem de `GraphState.hitl`, não daqui.
    hitl_enabled: bool = Field(
        default=False, description="human_review (F2.8) pausa p/ revisão humana antes do briefing."
    )

    # --- Guarda de orçamento de LLM por run (F2.11) -----------------------------
    # Os créditos grátis do build.nvidia.com têm rate limit; este teto **aborta a próxima
    # chamada** quando o run atinge o limite (os nós degradam p/ o determinista, sem estourar).
    # Off por default (espinha verde/M2); ligue + defina ao menos um teto (0 = sem teto naquela
    # dimensão). A guarda só arma se `llm_budget_enabled` e algum teto > 0.
    llm_budget_enabled: bool = Field(
        default=False, description="Guarda de orçamento de LLM por run (F2.11)."
    )
    llm_max_calls: int = Field(
        default=0, ge=0, description="Máx. de chamadas de LLM por run (0 = sem teto)."
    )
    llm_max_tokens: int = Field(
        default=0, ge=0, description="Máx. de tokens (in+out) por run (0 = sem teto)."
    )
    llm_max_cost_usd: float = Field(
        default=0.0, ge=0, description="Máx. de custo estimado por run em USD (0 = sem teto)."
    )

    # --- Cache de inferência LLM por prompt+modelo+versão (F2.14) ----------------
    # Cacheia a saída crua dos nós LLM (search_planner/extractor/classifier): poupa o rate
    # limit do free tier (complementa F2.11) e torna runs/eval REPRODUTÍVEIS. Invalida sozinho
    # quando o prompt muda (content_sha) ou a versão sobe (F0.12). NÃO cacheia scraping (frescor).
    # Off por default (espinha verde/M2); backend em disco (default) ou Redis (opt-in).
    llm_cache_enabled: bool = Field(
        default=False, description="Cache de inferência LLM por prompt+modelo+versão (F2.14)."
    )
    llm_cache_backend: CacheBackend = "disk"
    llm_cache_dir: str = Field(
        default=".cache/llm", description="Diretório do cache de LLM em disco (F2.14)."
    )
    llm_cache_ttl_seconds: int = Field(
        default=0, ge=0, description="Expiração do cache de LLM em s (0 = sem expiração)."
    )

    # --- Dados ------------------------------------------------------------------
    postgres_url: str = "postgresql://tapi:tapi@localhost:5432/tapi"
    qdrant_url: str = "http://localhost:6333"
    redis_url: str = "redis://localhost:6379/0"

    # --- Observabilidade --------------------------------------------------------
    langfuse_host: str = "http://localhost:3001"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    # --- Auth da ferramenta (gate interno — F5.9) -------------------------------
    tapi_api_token: str = ""

    # --- Idioma de saída (F0.13) ------------------------------------------------
    output_lang: str = Field(default="pt-BR", description="Idioma de briefing/recs/UI.")

    # --- Derivados --------------------------------------------------------------
    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_url(self) -> str:
        """URL do Postgres com driver psycopg v3 explícito (SQLModel/Alembic, F0.6)."""
        if self.postgres_url.startswith("postgresql+"):
            return self.postgres_url
        return self.postgres_url.replace("postgresql://", "postgresql+psycopg://", 1)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def langfuse_enabled(self) -> bool:
        """Tracing só liga com as duas chaves presentes (F0.8)."""
        return bool(self.langfuse_public_key and self.langfuse_secret_key)


@lru_cache
def get_settings() -> Settings:
    """Retorna a config (cacheada). Use isto em vez de instanciar `Settings()`."""
    return Settings()
