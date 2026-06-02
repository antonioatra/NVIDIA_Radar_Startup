# F0 — Fundação

**Objetivo:** infraestrutura, contratos de dados e ingestão base — fundação de todas as fases.
**Dependências:** nenhuma. **Marco:** habilita M1.

## Tasks
- [x] **F0.1** `git init` + `.gitignore` + README + estrutura `apps/packages/data/docs`.
- [ ] **F0.2** `docker-compose.yml`: postgres, qdrant, redis, langfuse, api, worker, frontend, nim(GPU).
- [x] **F0.3** `.env.example` + carregamento de config (pydantic-settings) em `packages/config`.
- [x] **F0.4** NVIDIA Container Toolkit validado (GPU visível no container — `nvidia-smi`).
      Verificado ao vivo (2026-06-02): `docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04
      nvidia-smi` → RTX 3050 (4GB) visível no container. Toolkit via Docker Desktop 4.76 + backend
      WSL2/Ubuntu. Obs.: o serviço `nim` (Nemotron Nano 8B) **não** roda nesta GPU de 4GB — o serving
      self-hosted fica para host com VRAM suficiente (F6); o passthrough de GPU em si está validado.
- [x] **F0.5** Schemas Pydantic v2 em `packages/schemas`: `StartupProfile`, `Evidence`,
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
- [x] **F0.6** Migrações Postgres (SQLModel/Alembic): tabelas `company`, `founder`, `evidence`,
      `score`, `recommendation`, `run`. Modelos em `packages/db`; founders normalizados,
      produtos/clientes/tecnologias/funding em JSON; `evidence` polimórfica (entity_type/id/field).
- [x] **F0.7** Cliente Nemotron via `langchain-nvidia-ai-endpoints` (factory Nano/Super) + smoke test.
- [x] **F0.8** Bootstrap Langfuse (tracing) + wrapper de callback nos LLMs.
      Langfuse **v3** (SDK 4.x / `langfuse.langchain.CallbackHandler`) — o callback do v2
      importa caminhos legados removidos no langchain 1.0, incompatível com o stack da F0.7.
      `packages/observability`: `traced_config(node, prompt_version, run_id)` injeta callback
      + metadata no `.invoke(config=...)`; tudo no-op sem chaves. compose: serviço v3
      (web+worker+ClickHouse+MinIO).
- [x] **F0.9** Seeds: carregar listas de fontes do §9 em `data/seeds/`.
      `directories.yaml` (§9.1) · `news.yaml` (§9.2) · `programs.yaml` (descoberta) + `README.md`
      com schema/política. Cada fonte anota `policy` (allow/api_only/deny) + robots + ToS + base legal
      (F1.15). Loader tipado `packages/scraping/seeds.py` (`load_sources/allowlist/denylist/by_type`),
      valida consistência (allow ⇏ ToS proibido) e IDs únicos.
- [x] **F0.10** **CI leve** (GitHub Actions): lint (ruff) + testes (pytest) + smoke RAGAS no push.
      Sustenta o princípio "RAGAS no CI" (ARQUITETURA §8) e as "contribuições constantes" do §11.
      Mantém o pipeline barato (sem GPU no CI; jobs de GPU rodam local/sob demanda).
      `.github/workflows/ci.yml` + `requirements-ci.txt` (subconjunto enxuto) + `pyproject.toml`
      (ruff line-length 100 / E,F,W,I,B,UP, ignore UP042; pytest pythonpath). Smoke RAGAS é
      **placeholder consciente até F3** (sem pipeline RAG ainda). Local: `ruff check` limpo, 51 testes verdes.
- [x] **F0.11** **Rubrica AIMI — definição (não a heurística):** documento `docs/RUBRICA-AIMI.md`
      com a **semântica dos 4 pilares** (Data Moat · Workflow Depth · Technical Optimization ·
      Distribution) e a **escala 0–25** de cada um. Criado **cedo** porque o eval set (F1.12)
      rotula "AIMI esperado" e precisa de uma definição estável antes de existir qualquer modelo.
      Separa **definição** (aqui, fixa) da **heurística de pontuação** (v0 em F2.6, refinada p/ v1
      em F6.1). Grounding conceitual vem dos materiais de AI-native do §10.1 (ingeridos em F3.1d);
      este doc é o rascunho de trabalho até esse grounding, depois é reconciliado, sem mudar a escala.
- [x] **F0.12** **Gestão de prompts:** templates dos nós LLM versionados em
      `packages/agents/prompts/` (1 arquivo por nó: search_planner, extractor, classifier,
      recommender, briefing), com `prompt_version` carimbado no trace Langfuse e na tabela `run`.
      Garante reprodutibilidade e que o eval (F7) saiba contra qual versão de prompt mediu.
      Registry (`registry.py`) carrega `<node>.md` (frontmatter version/model/reasoning/output_lang
      + corpo=system); `Prompt.version_tag` (`<node>@v1`) vai p/ `traced_config(prompt_version=…)`
      e p/ `run.prompt_version`; `content_sha` p/ drift/cache (F2.14).
- [x] **F0.13** **Idioma de saída = PT-BR:** config global (`OUTPUT_LANG=pt-BR`) — briefing,
      recomendações e UI em português (público é o gerente de Startups & VCs da NVIDIA Brasil).
      Embeddings seguem multilíngues (KB NVIDIA é majoritariamente EN; consultas/perfis em PT).

## Tecnologias
PostgreSQL · Qdrant · Redis · Docker Compose · NVIDIA Container Toolkit · Pydantic v2 ·
`langchain-nvidia-ai-endpoints` (Nemotron) · Langfuse · GitHub Actions (CI).

## DoD
- [~] `docker compose up` sobe todos os serviços; GPU acessível no container NIM.
      GPU no container **validada** (F0.4, 2026-06-02). Pendente: `build:` de `api`/`worker`/`frontend`
      ainda sem Dockerfile (apps são stubs até F4/F5) e o NIM não cabe na GPU de 4GB local.
- [x] `python -c "from packages.schemas import StartupProfile"` funciona.
- [x] Smoke test de chamada ao Nemotron aparece como trace no Langfuse.
      Verificado ao vivo (2026-06-02): `smoke('fast'/'reason')` → Nemotron Nano/Super retornam OK;
      traces `smoke:fast`/`smoke:reason` aparecem na API do Langfuse v3 (auth_check True).
- [~] CI verde no push: lint + testes + smoke RAGAS (sem GPU). Workflow pronto; lint+testes
      validados localmente (ruff limpo, 51 verdes). "Verde no push" só confirma ao subir pro GitHub;
      smoke RAGAS é placeholder até F3.
- [x] `docs/RUBRICA-AIMI.md` define os 4 pilares e a escala 0–25 (consumível por F1.12).
- [x] Prompts versionados em `packages/agents/prompts/`; `prompt_version` aparece no trace.
