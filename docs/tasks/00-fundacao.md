# F0 — Fundação

**Objetivo:** infraestrutura, contratos de dados e ingestão base — fundação de todas as fases.
**Dependências:** nenhuma. **Marco:** habilita M1.

## Tasks
- [ ] **F0.1** `git init` + `.gitignore` + README + estrutura `apps/packages/data/docs`.
- [ ] **F0.2** `docker-compose.yml`: postgres, qdrant, redis, langfuse, api, worker, frontend, nim(GPU).
- [ ] **F0.3** `.env.example` + carregamento de config (pydantic-settings).
- [ ] **F0.4** NVIDIA Container Toolkit validado (GPU visível no container — `nvidia-smi`).
- [ ] **F0.5** Schemas Pydantic v2 em `packages/schemas`: `StartupProfile`, `Evidence`,
      `AIMIScore`, `Recommendation`, `Briefing`, `GraphState`.
- [ ] **F0.6** Migrações Postgres (SQLModel/Alembic): tabelas `company`, `founder`, `evidence`,
      `score`, `recommendation`, `run`.
- [ ] **F0.7** Cliente Nemotron via `langchain-nvidia-ai-endpoints` (factory Nano/Super) + smoke test.
- [ ] **F0.8** Bootstrap Langfuse (tracing) + wrapper de callback nos LLMs.
- [ ] **F0.9** Seeds: carregar listas de fontes do §9 em `data/seeds/`.

## Tecnologias
PostgreSQL · Qdrant · Redis · Docker Compose · NVIDIA Container Toolkit · Pydantic v2 ·
`langchain-nvidia-ai-endpoints` (Nemotron) · Langfuse.

## DoD
- [ ] `docker compose up` sobe todos os serviços; GPU acessível no container NIM.
- [ ] `python -c "from packages.schemas import StartupProfile"` funciona.
- [ ] Smoke test de chamada ao Nemotron aparece como trace no Langfuse.
