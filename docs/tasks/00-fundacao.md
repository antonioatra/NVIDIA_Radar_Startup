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
      - `StartupProfile` cobre **todas** as dimensões do §2: `empresa`, `produto`, `setor`,
        `clientes`, `funding`, `founders`, `tecnologias` (cada campo com proveniência/evidência).
        `funding` alimenta a prontidão de coorte (F6.7); `clientes`/distribuição alimentam os
        pilares Distribution e Data Moat do AIMI (F6.1).
      - `Recommendation` carrega **evidência dos dois lados** (princípio "tudo com evidência"):
        `evidencia_gap` (lado startup — o que no perfil/AIMI motiva a recomendação) e
        `evidencia_nvidia` (citações da KB recuperadas pelo RAG que justificam a tech). Os dois
        são listas de `Evidence`; o Guardrails (F4.5) bloqueia recomendação sem **ambos**.
      - `Briefing` tem próximas-ações nos **três eixos do §2**: `acao_comercial`, `acao_tecnica`
        e `acao_comunitaria` (onboarding/créditos/eventos/comunidade do Inception).
      - `AIMIScore` inclui `inception_priority` (0–100) — score de prioridade de outreach (F6.13),
        derivado de potencial × upside NVIDIA. Calculado na F6, mas o campo já entra no contrato.
- [ ] **F0.6** Migrações Postgres (SQLModel/Alembic): tabelas `company`, `founder`, `evidence`,
      `score`, `recommendation`, `run`.
- [ ] **F0.7** Cliente Nemotron via `langchain-nvidia-ai-endpoints` (factory Nano/Super) + smoke test.
- [ ] **F0.8** Bootstrap Langfuse (tracing) + wrapper de callback nos LLMs.
- [ ] **F0.9** Seeds: carregar listas de fontes do §9 em `data/seeds/`.
- [ ] **F0.10** **CI leve** (GitHub Actions): lint (ruff) + testes (pytest) + smoke RAGAS no push.
      Sustenta o princípio "RAGAS no CI" (ARQUITETURA §8) e as "contribuições constantes" do §11.
      Mantém o pipeline barato (sem GPU no CI; jobs de GPU rodam local/sob demanda).
- [x] **F0.11** **Rubrica AIMI — definição (não a heurística):** documento `docs/RUBRICA-AIMI.md`
      com a **semântica dos 4 pilares** (Data Moat · Workflow Depth · Technical Optimization ·
      Distribution) e a **escala 0–25** de cada um. Criado **cedo** porque o eval set (F1.12)
      rotula "AIMI esperado" e precisa de uma definição estável antes de existir qualquer modelo.
      Separa **definição** (aqui, fixa) da **heurística de pontuação** (v0 em F2.6, refinada p/ v1
      em F6.1). Grounding conceitual vem dos materiais de AI-native do §10.1 (ingeridos em F3.1d);
      este doc é o rascunho de trabalho até esse grounding, depois é reconciliado, sem mudar a escala.
- [ ] **F0.12** **Gestão de prompts:** templates dos nós LLM versionados em
      `packages/agents/prompts/` (1 arquivo por nó: search_planner, extractor, classifier,
      recommender, briefing), com `prompt_version` carimbado no trace Langfuse e na tabela `run`.
      Garante reprodutibilidade e que o eval (F7) saiba contra qual versão de prompt mediu.
- [ ] **F0.13** **Idioma de saída = PT-BR:** config global (`OUTPUT_LANG=pt-BR`) — briefing,
      recomendações e UI em português (público é o gerente de Startups & VCs da NVIDIA Brasil).
      Embeddings seguem multilíngues (KB NVIDIA é majoritariamente EN; consultas/perfis em PT).

## Tecnologias
PostgreSQL · Qdrant · Redis · Docker Compose · NVIDIA Container Toolkit · Pydantic v2 ·
`langchain-nvidia-ai-endpoints` (Nemotron) · Langfuse · GitHub Actions (CI).

## DoD
- [ ] `docker compose up` sobe todos os serviços; GPU acessível no container NIM.
- [ ] `python -c "from packages.schemas import StartupProfile"` funciona.
- [ ] Smoke test de chamada ao Nemotron aparece como trace no Langfuse.
- [ ] CI verde no push: lint + testes + smoke RAGAS (sem GPU).
- [x] `docs/RUBRICA-AIMI.md` define os 4 pilares e a escala 0–25 (consumível por F1.12).
- [ ] Prompts versionados em `packages/agents/prompts/`; `prompt_version` aparece no trace.
