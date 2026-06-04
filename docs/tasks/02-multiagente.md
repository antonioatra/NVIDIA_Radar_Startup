# F2 — Sistema Multi-agente LangGraph (Entregável 2)

**Objetivo:** orquestrar os agentes especializados num grafo com estado, retry e HITL.
**Dependências:** F0, F1. **Marco:** M2.

## Tasks
- [x] **F2.1** `GraphState` (Pydantic) + montagem do grafo em `packages/agents`.
      → `GraphState` já vinha de F0.5 (`schemas/state.py`); aqui entra a **montagem**:
      `packages/agents/graph.py` (`build_graph` monta o `StateGraph(GraphState)` com o
      backbone linear da ARQUITETURA §3 — search_planner→…→briefing; `compile_graph(checkpointer=)`
      deixa o hook da F2.2; `run_pipeline` roda ponta a ponta e devolve o `GraphState` final)
      + `packages/agents/nodes.py` (os 9 nós como **placeholders deterministas**, cada um
      anotado com a task que o preenche: F2.3–F2.7 · F3 · F4 · F6 · F4.4). As arestas
      condicionais (retry F2.7, terminais F2.12/F2.13, HITL F2.8) e o tracing (F2.9) têm
      hook documentado e **não** reordenam a espinha. Teste `tests/test_graph.py`: nós exatos,
      linearidade do backbone, e run end-to-end → rascunho `COMPLETED` sem alucinar campos.
- [x] **F2.2** Checkpointer Postgres (`langgraph-checkpoint-postgres`) p/ resume/retry.
      → `packages/agents/checkpoint.py`: `postgres_checkpointer()` (context manager sobre
      `PostgresSaver.from_conn_string` + `setup()`) persiste o estado por *thread* = `run_id`;
      `checkpointer_conn_string` normaliza a URL p/ o esquema psycopg (tira o `+psycopg` da
      forma SQLAlchemy F0.6). `run_pipeline(checkpointer=)` (F2.1) passa o `thread_id=run_id`;
      `run_pipeline_persisted` é o caminho de produção (worker F2.10). `state_serde()` fixa
      `allowed_msgpack_modules=True` (allow-all) — o checkpoint é dado nosso e confiável, e
      isso evita que um futuro default *strict* do LangGraph bloqueie os submodelos do estado
      (`StartupProfile`/`AIMIScore`/`Briefing`). **As tabelas de checkpoint são geridas pelo
      `setup()` do LangGraph, fora do `SQLModel.metadata`/Alembic (F0.6)** — dois esquemas de
      migração no mesmo banco. Teste `tests/test_checkpoint.py`: round-trip do serde,
      `thread_id=run_id`, e **interrupt→resume** via checkpoint (DoD F2); o caminho Postgres
      real é teste de integração que pula sem banco no ar (`connect_timeout` curto).
- [ ] **F2.3** Nó **search_planner** (Nemotron-Nano): consulta → termos + fontes priorizadas.
      **Contrato de input (esclarecimento):** dois modos — (a) *single-company lookup* (nome/domínio
      de uma empresa) e (b) *discovery por setor/região* (ex.: "fintechs AI em SP"). O planner
      detecta o modo e gera termos/fontes adequados; o modo (b) alimenta o cohort builder (F1.14).
- [ ] **F2.4** Nó **scraper** (map paralelo sobre fontes; usa F1).
- [ ] **F2.5** Nó **extractor** (Nemotron-Super): conteúdo → `StartupProfile` estruturado.
- [ ] **F2.6** Nó **classifier** (Super, reasoning ON): AI-native | AI-enabled | non-AI + sub-scores.
      Emite os 4 sub-scores no schema `AIMIScore` (F0.5) usando uma **rubrica AIMI provisória v0**
      (heurística simples por evidência), sobre a **definição de pilares/escala de `docs/RUBRICA-AIMI.md`
      (F0.11)**. **F6.1 refina** a heurística para a v1 — não muda a definição nem o contrato de saída.
- [ ] **F2.7** Nó **evidence_validator**: regra de N fontes; aresta condicional de retry → scraper.
- [ ] **F2.8** **HITL interrupt** antes do briefing (revisão humana da classificação/recomendação).
      Controlado por flag de modo: `hitl=sync` no *single-company lookup* (interrupt bloqueante);
      `hitl=auto` no **batch/cohort builder (F1.14)** — não bloqueia a fila, só marca para revisão.
- [ ] **F2.9** Tracing Langfuse em todos os nós + métricas de tokens/custo.
- [ ] **F2.10** Orquestração assíncrona via worker (Redis/RQ) p/ runs longos + SSE de progresso.
      **Transporte worker → SSE (esclarecimento):** o worker **publica** eventos num canal
      **Redis pub/sub por `run_id`**; o endpoint SSE da API (F5.2/F5.3) **assina** o canal e
      repassa ao front. Contrato de evento mínimo: `{run_id, node, status, pct, ts}` (+ payload
      opcional). Sem esse canal, o run assíncrono não consegue alimentar o "ao vivo" do F5.3.
- [ ] **F2.11** **Guarda de custo/orçamento de LLM** por run (limite de tokens/chamadas) — os
      créditos grátis do `build.nvidia.com` têm rate limit; evita estouro durante o build.
- [ ] **F2.12** **Estado terminal de baixa confiança:** se após o retry limitado (F2.7) as
      evidências seguem insuficientes, o grafo **não alucina** — encerra num briefing marcado
      "dados insuficientes" (com o que foi achado + lacunas) ou descarte rastreável. Caminho
      terminal explícito no grafo + teste.
- [ ] **F2.13** **Saída para `non-AI` de alta confiança:** a baixa-confiança (F2.12) cobre
      "dados insuficientes"; falta o caminho da empresa **claramente non-AI** (classificada com
      confiança). Roteamento explícito: pular `recommender`/`gpu_benchmark` e emitir um briefing
      **"fora de escopo"** (por que não é alvo Inception + AIMI baixo com evidência), em vez de
      forçar recomendação NVIDIA. O texto sai no Briefing Agent (F4.4). Caminho no grafo + teste.
- [ ] **F2.14** **Cache de chamadas LLM/embeddings** (chave por prompt+modelo+`prompt_version`):
      reduz custo no free tier do `build.nvidia.com` (complementa a guarda de orçamento F2.11) e
      torna runs/eval **reprodutíveis**. Cache local (Redis/disco); invalida quando `prompt_version`
      muda (F0.12). Não cacheia scraping (frescor) — só inferência determinística.

## Tecnologias
LangGraph · checkpointer Postgres · Nemotron (Nano/Super) · Redis/RQ · Langfuse.

## DoD
- [ ] Grafo roda end-to-end (sem RAG ainda) e produz um briefing rascunho.
- [ ] Run interrompido e retomado via checkpoint; retry de evidência funciona.
- [ ] Empresa sem evidência suficiente cai no estado terminal de baixa confiança (não alucina).
- [ ] Empresa `non-AI` de alta confiança gera briefing "fora de escopo" sem forçar recomendação (F2.13).
- [ ] Eventos de progresso publicados em canal Redis por `run_id`, consumíveis via SSE (F2.10).
