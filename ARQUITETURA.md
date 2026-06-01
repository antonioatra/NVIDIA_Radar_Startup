# TAPI — Arquitetura Técnica

**Projeto:** NVIDIA Startup AI Radar
**Produto:** TAPI — plataforma multi-agente que mapeia startups brasileiras AI-native, diagnostica maturidade técnica e prescreve a stack NVIDIA adequada, com evidência rastreável e ROI quantificado.
**Documento:** arquitetura de referência (v1) — base para os 6 entregáveis.

---

## 0. Tese do produto

O case critica startups "wrapper de LLM" (uma API atrás de uma UI, sem dado proprietário,
workflow ou otimização). O **TAPI não é wrapper**: o moat está na orquestração multi-agente,
no dataset proprietário coletado, no RAG com evidência e no motor de recomendação — o LLM é
só o miolo. Mais: **o próprio TAPI roda na stack NVIDIA** (Nemotron + NeMo Retriever + NIM
self-hosted na GPU), virando prova viva da jornada que recomenda: começar via API e **graduar
para a stack otimizada**.

**Espaço em branco no mercado:** Harmonic, Specter, Tracxn, PitchBook, Dealroom e CB Insights
são bases de *sourcing* (firmographics, funding, sinais de time). Nenhuma faz **diagnóstico
técnico de maturidade AI + prescrição de stack com evidência + ROI quantificado**. É aí que o
TAPI vive.

---

## 1. Decisões de stack (kickoff)

| Eixo | Decisão | Razão |
|---|---|---|
| Cérebro dos agentes | **NVIDIA Nemotron** via `build.nvidia.com` (créditos grátis) | Dogfooding; reasoning toggle; sem plano pago |
| Self-hosted | **NIM/vLLM na GPU local** (diferencial) | Demonstra graduação API → stack otimizada |
| Vector DB | **Qdrant** (dense + sparse/BM25 nativo) | Híbrido nativo, named vectors |
| Dados estruturados | **PostgreSQL** (+ pgvector opcional) | Empresas, founders, evidências, scores |
| Embeddings | **NeMo Retriever `nv-embedqa-1b-v2`** | Multilíngue (PT-BR), grátis |
| Reranking | **NeMo Retriever `nv-rerankqa-1b-v2`** (dev/testes, grátis) · **Cohere Rerank** (validação final) | Plugável; NeMo durante o build, Cohere entra só no fim p/ benchmark comparativo |
| Frontend | **Next.js + React + TypeScript + Tailwind/shadcn** | Entrega polida, streaming de pipeline |
| Backend | **FastAPI + SSE** | Stream do progresso dos agentes |

### Modelos Nemotron por tarefa (custo x raciocínio)
- **Nano** (rápido/barato): `search_planner`, roteamento de scraping, normalização.
- **Super** (`reasoning ON`): `extractor`, `classifier`, `recommender`, `briefing`.
- **Ultra** (opcional): só se a classificação exigir raciocínio multi-passo pesado.

---

## 2. Tecnologias que faltavam alinhar (gaps fora do brief)

| Camada | Decisão | Por quê |
|---|---|---|
| Orquestração | LangGraph + **checkpointer Postgres** + **interrupts (HITL)** | Retry, resume e intervenção humana (§5.1) |
| LLM SDK | `langchain-nvidia-ai-endpoints` | Integração nativa Nemotron/NIM |
| Busca web | **Tavily** (free tier) | O brief lista fontes, não o motor de busca |
| Contrato de dados | **Pydantic v2** (`StartupProfile` com proveniência) | Extração estruturada confiável |
| Guardrails | **NeMo Guardrails** no Briefing | On-narrative; evita recomendação alucinada |
| Observabilidade | **Langfuse** (self-host grátis) | Depuração de multi-agente |
| Avaliação | **RAGAS** (faithfulness, context precision/recall) + eval set de classificação + eval de rerankers | §5.3.9 exige avaliação de qualidade |
| Data eng (GPU) | **RAPIDS/cuDF** (dedup/normalização) + **cuML** (clustering setorial) | Usa GPU, on-narrative, alimenta o Índice |
| Fila | **Redis + worker** (RQ) | Pipeline longo não cabe em request síncrono |
| Deploy | **Docker Compose** + NVIDIA Container Toolkit | Postgres/Qdrant/Redis/API/worker/front/NIM |
| Governança | Tabela de evidências (URL, hash, `fetched_at`) | Só dado público, rastreável (LGPD) |

---

## 3. Arquitetura de IA — grafo LangGraph

O fluxo linear do §6 do brief vira um grafo com paralelismo, retry condicional e HITL.

```
            ┌────────────────────────── STATE (Pydantic / TypedDict) ──────────────────────────┐
            │ query · sources · raw_docs · profile · evidence · aimi_scores ·                   │
            │ retrieved · recommendations · benchmark · briefing · trace                        │
            └───────────────────────────────────────────────────────────────────────────────────┘

 [query]
   → search_planner   (Nemotron-Nano)      termos + fontes priorizadas (Tavily + diretórios §9)
   → scraper          (MAP paralelo)        Firecrawl | Playwright(dinâmico) | trafilatura | BS4
   → extractor        (Nemotron-Super)      → StartupProfile estruturado + proveniência
   → [persist Postgres]                     upsert empresa/founders/evidências
   → classifier       (Super, reason ON)    AI-native | AI-enabled | non-AI + AIMI sub-scores
   → evidence_validator                     ── insuficiente? → loop p/ scraper (retry limitado)
   → nvidia_rag                             híbrido (dense + BM25 Qdrant) → NeMo rerank → citações
   → recommender      (Super, reason ON)    gaps (AIMI) × tech NVIDIA → recomendações estruturadas
   → gpu_benchmark    (condicional) ★       diferencial: ROI real (NIM local / matriz de benchmark)
   → [HITL interrupt]                        humano revisa classificação/recomendação
   → briefing         (NeMo Guardrails)      briefing executivo → JSON + PDF
```

### Saída da recomendação (§5.5)
tech NVIDIA · justificativa técnica · justificativa de negócio · prioridade · complexidade ·
próxima ação · evidências — **+ número de ROI** quando há gap de inferência (vem do diferencial).

---

## 4. RAG NVIDIA com reranking (§5.3)

Pipeline: ingestão (docs §10) → limpeza → **chunking semântico** → embeddings (`nv-embedqa`) →
Qdrant (dense + sparse/BM25) → **busca híbrida** → **NeMo rerank** → geração com **citações** →
**avaliação RAGAS**. Reranker atrás de uma interface (`Reranker.rerank(query, docs)`): durante
o build/testes usa **NeMo NIM (grátis)**; o **Cohere Rerank entra só na validação final** do
projeto, num mini-eval comparativo (NeMo vs Cohere) sobre o nosso dataset.

**Base de conhecimento:** todas as tecnologias do §5.4 (Inception, NIM, NeMo/Guardrails, Triton,
TensorRT-LLM, RAPIDS/cuDF/cuML, CUDA, Riva, Omniverse, Isaac, Clara, Morpheus, AI Enterprise),
ingeridas das fontes oficiais do §10.

---

## 5. Diferencial (Entregável 6) — "TAPI Maturity Index + GPU Graduation Engine"

Combinação: o **Índice diagnostica**, o **Recommender prescreve**, o **GPU Engine quantifica**.
Loop completo "diagnosticar → prescrever → quantificar" que nenhuma ferramenta do mundo faz.

### 5.1 Espinha dorsal — AI-Native Maturity Index (AIMI v1)
Score 0–100, 4 pilares de 0–25, derivados da própria definição AI-native vs wrapper do case:

| Pilar | Mede | Sinal de gap NVIDIA |
|---|---|---|
| **Data Moat** | dados proprietários / feedback loops | — |
| **Workflow Depth** | automação multi-passo, agentes, integrações | NeMo Guardrails, agentes |
| **Technical Optimization** | inferência/fine-tuning/serving próprios vs API crua | **NIM, TensorRT-LLM, Triton, RAPIDS** |
| **Distribution & Moat** | GTM claro, integração enterprise, lock-in | AI Enterprise |

- Cada sub-score **exigido com evidência** (Evidence Validator) → explicável e auditável
  ("score de crédito de AI-nativeness"). Versionado (AIMI v1).
- O pilar **Technical Optimization baixo dispara as recomendações NVIDIA** → o Índice
  *alimenta* o recommender, não decora. Acoplamento arquitetural limpo.

### 5.2 Camada de coorte (RAPIDS/cuML)
`cuDF` normaliza/deduplica a coorte coletada; `cuML` (KMeans + UMAP sobre embeddings de
setor/perfil) **clusteriza** o ecossistema → **Radar/ranking** de quais clusters são mais
"graduation-ready" pro Inception. Dá ao gerente uma **visão de portfólio**, não consultas avulsas.

### 5.3 Prova quantificada — GPU Graduation Engine
Para startups com Technical Optimization baixo + recomendação de NIM/TensorRT-LLM:
- Mede **na GPU local** (NIM/vLLM + TensorRT-LLM vs API externa): tokens/s, p50/p95 de
  latência, throughput em batch, e estima **$/1M tokens self-hosted vs API**.
- **Escopo realista:** pré-computar uma **matriz de benchmark** (poucos tamanhos de modelo ×
  workloads) **uma vez** na GPU e armazenar; o engine **mapeia** o perfil da startup p/ a célula
  mais próxima → ROI no briefing. "Run ao vivo" vira **botão de demo** (1 modelo, ex. Nemotron-Nano),
  não requisito por request.
- Linha no briefing: *"Migrar atendimento (~Xk tokens/dia) de [API] p/ NIM self-hosted:
  ~Nx throughput, p95 −M%, custo −K%."*

---

## 6. Estrutura de repositório (proposta)

```
tapi/
  docker-compose.yml          postgres · qdrant · redis · api · worker · frontend · nim(GPU) · langfuse
  .env.example
  apps/
    api/                      FastAPI + SSE
    worker/                   runtime LangGraph
    frontend/                 Next.js
  packages/
    schemas/                  contratos Pydantic (StartupProfile, Recommendation, Briefing)
    agents/                   nós + state do grafo
    scraping/                 adapters firecrawl/playwright/trafilatura/bs4 + provenance
    rag/                      ingest · chunk · embed · hybrid_retrieve · rerank(plugável)
    scoring/                  AIMI (índice de maturidade)
    benchmark/                GPU graduation engine + geração da matriz (RAPIDS)
    eval/                     RAGAS + eval de classificação + eval de rerankers
  data/
    knowledge_base/           fontes NVIDIA (§10) p/ ingestão
    seeds/                    seed lists de startups (§9)
  notebooks/                  geração da matriz de benchmark
```

---

## 7. Roadmap mapeado aos entregáveis

| # | Entregável | Inclui |
|---|---|---|
| 1 | Pipeline de scraping | Tavily + Firecrawl/Playwright/trafilatura, provenance, persist Postgres |
| 2 | Multi-agente LangGraph | grafo completo, checkpointer, HITL, observabilidade Langfuse |
| 3 | RAG NVIDIA + rerank | ingestão §10, híbrido Qdrant, NeMo rerank, citações, RAGAS |
| 4 | Motor de recomendação | AIMI → gaps × tech NVIDIA, saída §5.5 estruturada |
| 5 | Interface web | Next.js: dashboard, radar AIMI, trace de pipeline, export PDF |
| 6 | **Diferencial** | AIMI + clustering de coorte + GPU Graduation Engine (ROI real) |

---

## 8. Princípios de engenharia
- **Tudo com evidência:** nenhuma afirmação/score sem fonte citada e rastreável.
- **Plugável onde há trade-off:** reranker, LLM endpoint (API ↔ NIM local).
- **Avaliação contínua:** eval set rotulado (~20–30 startups) + RAGAS no CI.
- **Graduação demonstrável:** mesmo binário roda em API (build.nvidia.com) ou NIM self-hosted.
- **Contribuições constantes** no repo (§11): commits incrementais por entregável.

---

### Fontes (validação da stack)
- NeMo Retriever (embedding/reranking NIMs): https://developer.nvidia.com/nemo-retriever
- Reranking NIM: https://docs.nvidia.com/nim/nemo-retriever/text-reranking/latest/overview.html
- Nemotron (open reasoning, API catalog grátis): https://developer.nvidia.com/nemotron
- NVIDIA RAG Blueprint / NIM APIs: https://build.nvidia.com/
- Benchmark de mercado (sourcing): https://harmonic.ai/ · https://www.tryspecter.com/
