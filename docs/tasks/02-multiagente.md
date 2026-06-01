# F2 — Sistema Multi-agente LangGraph (Entregável 2)

**Objetivo:** orquestrar os agentes especializados num grafo com estado, retry e HITL.
**Dependências:** F0, F1. **Marco:** M2.

## Tasks
- [ ] **F2.1** `GraphState` (Pydantic) + montagem do grafo em `packages/agents`.
- [ ] **F2.2** Checkpointer Postgres (`langgraph-checkpoint-postgres`) p/ resume/retry.
- [ ] **F2.3** Nó **search_planner** (Nemotron-Nano): consulta → termos + fontes priorizadas.
- [ ] **F2.4** Nó **scraper** (map paralelo sobre fontes; usa F1).
- [ ] **F2.5** Nó **extractor** (Nemotron-Super): conteúdo → `StartupProfile` estruturado.
- [ ] **F2.6** Nó **classifier** (Super, reasoning ON): AI-native | AI-enabled | non-AI + sub-scores.
- [ ] **F2.7** Nó **evidence_validator**: regra de N fontes; aresta condicional de retry → scraper.
- [ ] **F2.8** **HITL interrupt** antes do briefing (revisão humana da classificação).
- [ ] **F2.9** Tracing Langfuse em todos os nós + métricas de tokens/custo.
- [ ] **F2.10** Orquestração assíncrona via worker (Redis/RQ) p/ runs longos + SSE de progresso.
- [ ] **F2.11** **Guarda de custo/orçamento de LLM** por run (limite de tokens/chamadas) — os
      créditos grátis do `build.nvidia.com` têm rate limit; evita estouro durante o build.

## Tecnologias
LangGraph · checkpointer Postgres · Nemotron (Nano/Super) · Redis/RQ · Langfuse.

## DoD
- [ ] Grafo roda end-to-end (sem RAG ainda) e produz um briefing rascunho.
- [ ] Run interrompido e retomado via checkpoint; retry de evidência funciona.
