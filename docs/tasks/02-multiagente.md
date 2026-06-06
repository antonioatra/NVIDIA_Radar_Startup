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
- [x] **F2.3** Nó **search_planner** (Nemotron-Nano): consulta → termos + fontes priorizadas.
      **Contrato de input (esclarecimento):** dois modos — (a) *single-company lookup* (nome/domínio
      de uma empresa) e (b) *discovery por setor/região* (ex.: "fintechs AI em SP"). O planner
      detecta o modo e gera termos/fontes adequados; o modo (b) alimenta o cohort builder (F1.14).
      → `packages/agents/search_planner.py`: `SearchPlan`/`PrioritizedSource` (Pydantic, saída
      tipada) + `detect_mode`/`resolve_mode` (heurística pura: domínio/nome → single; pistas de
      setor/categoria/`-techs` → discovery; honra um `discovery` declarado, nunca rebaixa). O nó
      escreve `mode` (detectado, p/ o cohort builder F1.14), `search_terms` e `sources` (achatadas
      p/ o scraper F2.4) e marca o run `RUNNING`. **Decisão de design (política headless b/d):** o
      caminho **determinista/offline** é o **default** — grafo roda ponta a ponta sem
      rede/credenciais/GPU (M2/DoD) e runs ficam reprodutíveis (ethos F2.14); a peça **LLM**
      (Nemotron-Nano + prompt `search_planner@v1`, F0.12) é **plugável** atrás de
      `settings.planner_use_llm` (default off, requer chave), com **fallback** ao determinista a
      qualquer falha/JSON inválido. Discovery enviesa os termos por sinais AI-native
      (`signals.bias_query`, F1.11), mantendo a query original 1ª; single-company não força viés
      sobre nome próprio (prompt v1). Fontes honram a **política de ToS travada** (F1.15): site
      oficial + notícias §9.2 (allow); diretórios §9.1 só como **pista de descoberta** (`api_only`,
      nunca `deny`). Teste `tests/test_search_planner.py`: detecção de modo, plano por modo
      (query sempre 1ª; `deny` fora), parsing do JSON do Nano, e o nó offline → update parcial
      coerente. O caminho LLM real é opt-in (sem teste de rede, no padrão da fase).
- [x] **F2.4** Nó **scraper** (map paralelo sobre fontes; usa F1).
      → `packages/agents/scraper.py`: `scrape_sources` (núcleo testável) faz o **MAP paralelo**
      sobre `state.sources` (achatadas pelo planner F2.3) num `ThreadPoolExecutor` (coleta é
      I/O-bound) e devolve `raw_docs` (`RawDocument`, F0.5) + `errors`. Cada fonte vira URL(s):
      **URL** direta → roteador F1.7 (`route`/`fetch`); **termo de busca** → Tavily (F1.1) → top-K
      liberadas. Toda URL passa pelo **gate de ToS travado (F1.15)** antes do fetch (`verdict`):
      `api_only`/`deny` (§9.1) é **pulada** e registrada em `errors`, nunca coletada direto; o
      **intent** do roteador é inferido do tipo §9 (news→`article`, directory/program→`structured`,
      demais→`clean`). Proveniência mínima (F1.9) viaja no doc (`url`+`fetched_at`+`content_hash`+
      `source_type`=cadeia de adapters). **Decisão de design (b/d):** o MAP é **dentro do nó** (pool
      de threads), **não** fan-out LangGraph (`Send`+reducer) — mantém o scraper como **um** nó da
      espinha linear (F2.1) que o retry `evidence_validator→scraper` (F2.7) vai ancorar; resultado
      **reordenado pela ordem das fontes** e deduplicado por `(url, content_hash)` → **determinista**
      apesar das threads (ethos F2.14). Como no planner, **offline é o default**: sem adapters
      injetados e com `scraper_use_network` off (flag nova no settings) o nó é **no-op limpo** (`{}`,
      espinha verde M2/DoD); a coleta real é plugável por `fetch=`/`search=` (testes/worker F2.10) ou
      pela flag (produção). Erros **acumulam** em `state.errors` sem derrubar o run. `nodes.py` passa
      a importar o nó real (some o placeholder F2.1). Teste `tests/test_scraper.py`: map/ordem, gate
      ToS (deny+api_only), intent por tipo, termo→top-K, dedup, falhas de fetch/busca não-fatais, e o
      nó (no-op offline, update parcial, acúmulo de erros). Caminho de rede real fica opt-in (sem
      teste de rede, padrão da fase).
- [x] **F2.5** Nó **extractor** (Nemotron-Super): conteúdo → `StartupProfile` estruturado.
      → `packages/agents/extractor.py`: `parse_profile` (núcleo puro/offline) converte o JSON do
      Super num `StartupProfile` (F0.5) tipado, cobrindo as dimensões do §2 (empresa/produto/setor/
      clientes/funding/founders/tecnologias) com **proveniência por campo** (`Claim`/`Evidence`,
      princípio nº1 §8). A proveniência **não** é confiada ao LLM: ele cita `(url, trecho)`; o
      `fetched_at`/`content_hash` vêm do `raw_doc` casado (real, F1.9) e o `source_policy` da
      política de ToS travada (F1.15, `source_policy.annotate`) — auditável mesmo se o modelo errar
      datas; o snippet passa por `make_snippet` (cita, não copia). Parser **tolerante** (no padrão do
      `_parse_plan` F2.3): escalar aceita valor cru **ou** `{value, evidence, confidence}`, campos
      desconhecidos são ignorados (montagem campo a campo apesar do `extra="forbid"`), itens
      malformados pulados (url inválida de founder/evidência descartada sem derrubar), e `nome` cai
      na query se faltar; `source_urls` é a proveniência **agregada** das fontes realmente coletadas,
      não o que o modelo alegar. **Decisão de design (b/d, igual F2.3/F2.4):** **offline é o
      default** — sem `raw_docs` (espinha sem rede) **ou** com o LLM off, o nó é no-op limpo (`{}`,
      `profile=None`) → grafo verde ponta a ponta (M2/DoD, `test_graph` exige `profile is None`) e
      runs reprodutíveis (F2.14); a peça LLM (Nemotron-Super, **reasoning ON**, `extractor@v1`/F0.12)
      é **plugável** atrás de `settings.extractor_use_llm`+chave (flag nova) **ou** de um adapter
      `extract=` injetado (testes/worker F2.10), com **degradação p/ `None`** sem alucinar a qualquer
      falha de rede/JSON/validação — a suficiência de evidência fica para o evidence_validator (regra
      de N fontes, F2.7), não aqui. A **persistência** que o scraper (F2.4) anota como "do extractor"
      entra como **hook injetável `persist=`** desligado por padrão (o backbone não toca o banco); o
      worker liga `persist_profile` (F1.10, dedup CNPJ>domínio>nome + escopo BR) a uma `Session`,
      e a falha de persistência vira erro rastreável sem perder o perfil. `nodes.py` importa o nó
      real (some o placeholder F2.1); exposto só `parse_profile`/`extract_profile` no pacote (o nó
      via `NODES`, evitando shadowing do submódulo). Teste `tests/test_extractor.py`: mapeamento de
      todas as dimensões, proveniência ancorada nos docs, tolerância (campo desconhecido, url de
      founder/evidência inválida, nome ausente→query, evidência sem url/snippet, url não-coletada),
      `extract_profile` (sucesso + degradação None em JSON ruim/adapter que levanta), e o nó (no-op
      offline, update com `extract` injetado, acúmulo de erro na não-extração, hook de persist
      chamado, falha de persist não-fatal). Caminho LLM real é opt-in (sem teste de rede, padrão da fase).
- [x] **F2.6** Nó **classifier** (Super, reasoning ON): AI-native | AI-enabled | non-AI + sub-scores.
      Emite os 4 sub-scores no schema `AIMIScore` (F0.5) usando uma **rubrica AIMI provisória v0**
      (heurística simples por evidência), sobre a **definição de pilares/escala de `docs/RUBRICA-AIMI.md`
      (F0.11)**. **F6.1 refina** a heurística para a v1 — não muda a definição nem o contrato de saída.
      → `packages/agents/classifier.py`: `heuristic_score` (núcleo puro/offline) lê os sinais
      estruturados do `StartupProfile` (F2.5) e emite o `AIMIScore` — a **classe** (§5.1) pelo
      *papel* da IA (descrição/produtos + Workflow Depth, **não** pelo total) e os **4 pilares
      0–25** pela RUBRICA, **cada sub-score colado à evidência** do próprio perfil. A trava de
      evidência (RUBRICA §0, princípio nº1 §8) é honrada de duas formas: o `PillarScore` já levanta
      se `score>6` sem evidência, e a heurística **rebaixa proativamente a ≤6** quando não há fonte
      relevante (`_band_score(has_evidence=...)`). **"Wrapper" emerge como região**, não classe:
      P3 (Technical Optimization) cai a ≤6 quando só há sinal de **API externa crua** (sem stack
      própria) — o gatilho de graduação (RUBRICA §4) — enquanto a classe segue `AI-native`. Teto de
      humildade da **v0**: nenhum pilar entra na faixa Forte/Defensável (19–25) — esse julgamento é
      da v1/eval (F6.1/F6.4); a escala 0–25 do schema fica intacta (`V0_SCORE_CEILING=18`). **Decisão
      de design (b/d, igual F2.3/F2.4/F2.5):** **offline é o default** — a heurística determinista é a
      própria v0 (sem rede/LLM/GPU, runs reprodutíveis, F2.14); sem `profile` (espinha sem extração)
      o nó é **no-op limpo** (`{}`, `aimi=None`) → grafo verde ponta a ponta (M2/DoD), sem alucinar
      score sem entrada. A peça LLM (Nemotron-Super, **reasoning ON**, `classifier@v1`/F0.12) é
      **plugável** atrás de `settings.classifier_use_llm`+chave (flag nova) **ou** de um adapter
      `classify=` injetado (testes/worker F2.10), **com fallback à heurística** a qualquer falha de
      rede/JSON/validação (`make_aimi` → `classify_with_llm` degrada p/ `None`). No caminho LLM,
      `parse_score` **ancora a evidência citada na proveniência real do perfil** (reusa a `Evidence`
      existente por url; url nova ganha `source_policy`/F1.15) e rebaixa a ≤6 o sub-score que o modelo
      alegar sem citar. `nodes.py` importa o nó real (some o placeholder F2.1); o pacote expõe
      `heuristic_score`/`parse_score`/`classify_with_llm`/`make_aimi` (o nó via `NODES`, evitando
      shadowing do submódulo). Teste `tests/test_classifier.py`: classe nos 3 cenários (AI-native com
      stack própria, wrapper AI-native + P3 baixo, non-AI), trava de evidência (>6 sem fonte → ≤6, e a
      classe cai p/ AI-enabled sem confiança), teto v0, P4 por enterprise+captação; `parse_score`
      (grounding na proveniência do perfil, url nova com policy, cap sem evidência, alias de classe);
      `classify_with_llm` (degradação None em JSON ruim/adapter que levanta); `make_aimi` (heurística
      default, LLM injetado, fallback, flag ligada); e o nó (no-op sem perfil, `aimi` com perfil,
      `classify=` injetado). Caminho LLM real é opt-in (sem teste de rede, padrão da fase).
- [x] **F2.7** Nó **evidence_validator**: regra de N fontes; aresta condicional de retry → scraper.
      → `packages/agents/evidence_validator.py`: quinto nó (entre classifier/F2.6 e nvidia_rag/F3).
      A **regra de N fontes** é um gate de **largura** — `is_sufficient` exige ≥ `MIN_SOURCES`
      (=2) **hosts independentes** sustentando o diagnóstico (`evidence_sources` une
      `profile.all_evidence` + `source_urls`, normaliza host por `www.`/minúsculo: `site.com` e
      `www.site.com` contam como **uma** fonte; auto-relato não corrobora). Complementa, sem
      sobrepor, a trava de **profundidade** do classifier (`PillarScore` >6 exige evidência) —
      juntas realizam o princípio nº1 §8. **Decisão de design (b/d):** o nó roteia por
      `langgraph.types.Command` (atualiza estado **e** decide a rota atomicamente), não por
      `add_conditional_edges`: assim `retry_count` fica **limpo** (incrementa só na re-coleta,
      limitado por `can_retry` ⇒ nunca passa de `max_retries`) e some a ambiguidade de fronteira
      (uma aresta releria `can_retry` já pós-incremento, confundindo a última tentativa com o
      esgotamento). Por isso o `evidence_validator` **não** recebe aresta estática de saída na
      montagem (`graph.CONDITIONAL_OUT`): as duas pontas — retry→`scraper` (re-amplia a coleta,
      F2.4 substitui `raw_docs`) e segue→`nvidia_rag` — vêm do `goto` do nó. **Offline é o
      default** (igual F2.3–F2.6): sem `profile` (espinha sem extração) **segue limpo** — nada a
      corroborar, e re-coletar sem rede seria loop sem ganho (M2/DoD verde, sem alucinar). Quando
      o retry esgota e a evidência segue insuficiente, **não trava nem alucina**: segue com uma
      **nota rastreável** em `errors` — a F2.12 fará desse caso o briefing terminal "dados
      insuficientes" e a F2.13 a saída `non-AI`, ambas lendo o veredito/erro daqui sem mudar a
      regra. `nodes.py` importa o nó real (some o placeholder F2.1); o pacote expõe
      `evidence_sources`/`is_sufficient`/`MIN_SOURCES` (o nó via `NODES`, evitando shadowing).
      Teste `tests/test_evidence_validator.py`: contagem de hosts (dedup `www`, união
      evidência+`source_urls`, limiar), roteamento nos 4 ramos (sem perfil, suficiente, retry com
      orçamento, esgotado com nota), o **loop terminando** em exatamente `max_retries` re-coletas
      (DoD F2), e coerência das constantes de rota com a espinha; `tests/test_graph.py` ganha a
      saída condicional (sem aresta estática do evidence_validator).
- [x] **F2.8** **HITL interrupt** antes do briefing (revisão humana da classificação/recomendação).
      Controlado por flag de modo: `hitl=sync` no *single-company lookup* (interrupt bloqueante);
      `hitl=auto` no **batch/cohort builder (F1.14)** — não bloqueia a fila, só marca para revisão.
      → `packages/agents/human_review.py`: novo nó de **controle HITL** (penúltimo da espinha,
      entre `gpu_benchmark`/F6 e `briefing`/F4.4 — revisão *antes* de o briefing ser escrito).
      `review_payload` monta o resumo que o humano revisa (classe §5.1 + AIMI + recs), só com o
      que já está no estado e **sem alucinar** campos ausentes (run offline → `None`/`[]`). O
      **modo** vem de `state.hitl` (F2.3): `auto` (batch/cohort F1.14) **não bloqueia** — marca o
      novo campo `GraphState.needs_review` (revisão assíncrona do lote) e segue; `sync`
      (single-company) chama `langgraph.types.interrupt(payload)` — **pausa bloqueante** que
      retoma via `Command(resume=<decisão>)`, com a decisão registrada em `trace["human_review"]`
      (auditável). **Decisão de design (b/d, igual F2.3–F2.7):** **offline é o default** — o gate
      `settings.hitl_enabled` (flag nova) nasce **off**, então o nó é **no-op limpo** (`{}`) e a
      espinha roda ponta a ponta sem pausa (M2/DoD; os testes da fase seguem verdes, inclusive o
      `interrupt_before=["briefing"]` da F2.2). A pausa é **plugável** pela flag **ou** pelo param
      injetável `enabled=` (testes/worker F2.10). **Gatear por flag — não pela mera presença do
      checkpointer (F2.2):** o checkpointer habilita resume/retry sozinho, então um run persistido
      **sem** revisão (CI, reprocesso em lote) não deve travar à espera de gente — a flag separa
      "persisto o estado" de "exijo um humano no loop" (e mantém verde o teste do F2.2 que persiste
      em modo `sync`). O nó **não roteia** (sem `Command goto`): saída estática p/ o `briefing` em
      todo caminho (offline, auto, pós-resume do sync); mapear "interrupt pendente → status
      `awaiting_review`" na tabela `run` é do worker (F2.10), e os terminais alternativos (dados
      insuficientes F2.12, fora de escopo F2.13) ramificam antes. `nodes.py` registra o nó (10
      entradas: 9 agentes + controle HITL) e `graph.py` o insere na `PIPELINE`; o pacote expõe
      `review_payload` (o nó via `NODES`, evitando shadowing). Teste `tests/test_human_review.py`:
      payload (resumo + não-alucinação), no-op desligado (param e default), `auto` marca sem
      bloquear (+ run ponta a ponta completa e marcado), `sync` via grafo compilado + `InMemorySaver`
      (pausa antes do briefing com o payload no interrupt → resume com a decisão no `trace`, DoD F2),
      e a posição estática na espinha; `tests/test_graph.py`/`test_checkpoint.py` seguem verdes.
- [x] **F2.9** Tracing Langfuse em todos os nós + métricas de tokens/custo.
      → Duas camadas sobre o bootstrap da F0.8 (`packages/observability/`). **(1) Tracing de
      todos os nós:** `run_pipeline` (graph.py) passa o `traced_config(node=RUN_NAME, run_id=...)`
      no `.invoke` do grafo — sob o trace raiz `tapi_pipeline`, o callback do Langfuse cria **um
      span por nó** (inclui os nós sem LLM: scraper, evidence_validator, human_review, …), não só
      as 3 chamadas LLM que a F0.8 já traçava por `traced_config` (F2.3/F2.5/F2.6). **(2) Métricas
      de tokens/custo:** novo `packages/observability/cost.py` — `TokenUsage` (input/output/total/
      calls/cost_usd, `merge`/`for_call`), `MODEL_PRICES` + `estimate_cost` (tabela de **referência**
      por substring do modelo — estimativa p/ orçamento/ROI, não cobrança; free tier), `extract_usage`
      (lê `usage_metadata` do LangChain **ou** `token_usage` OpenAI-like), e um `UsageRecorder`
      (callback `on_llm_end`) que soma o uso no escopo ativo. **Decisão de design:** o recorder é
      **embutido no `traced_config`** (`USAGE_RECORDER`, singleton) — então **mede sem refatorar os
      nós**: toda chamada que os adapters disparam por `traced_config` é contabilizada; o escopo é
      aberto por `run_pipeline` (`capture_usage`, via `ContextVar` — reset por run, sem leak) e o
      rollup vai p/ `trace["usage"]`. Singleton + dedup por identidade do LangChain evita dupla
      contagem nos níveis aninhados do grafo. **Offline é o default (M2/DoD):** sem LLM não há
      `on_llm_end` → `trace` fica intacto; os callbacks ficam só com o medidor local (inócuo sem
      Langfuse). O detalhe por nó é autoritativo no Langfuse; o rollup em estado é a **base do gate
      de orçamento (F2.11)**. `traced_config` passou a sempre carregar o `USAGE_RECORDER` (Langfuse
      só quando ligado). Testes: `tests/test_cost.py` (estimate_cost por tabela/default/embeddings,
      `TokenUsage` merge/for_call, `extract_usage` nos 2 formatos + calls=1 sem tokens, `capture_usage`/
      `record_usage` acumulam no escopo e no-op fora dele + reset entre escopos, `UsageRecorder.
      on_llm_end`, e `run_pipeline` offline sem uso × com uso carimbado via nó fake); `tests/test_tracing.py`
      ganha o medidor no `traced_config` (ligado e desligado).
- [x] **F2.10** Orquestração assíncrona via worker (Redis/RQ) p/ runs longos + SSE de progresso.
      **Transporte worker → SSE (esclarecimento):** o worker **publica** eventos num canal
      **Redis pub/sub por `run_id`**; o endpoint SSE da API (F5.2/F5.3) **assina** o canal e
      repassa ao front. Contrato de evento mínimo: `{run_id, node, status, pct, ts}` (+ payload
      opcional). Sem esse canal, o run assíncrono não consegue alimentar o "ao vivo" do F5.3.
      → Duas peças. **(1) `packages/agents/progress.py`** — a fronteira worker↔SSE: `ProgressEvent`
      (contrato tipado `{run_id, node, status, pct, ts}` + `extra`, `extra="forbid"`),
      `stream_pipeline` (irmão *streaming* do `run_pipeline`/F2.1) e o transporte Redis
      (`progress_channel`, `RedisProgressPublisher`, `subscribe_progress`). O `stream_pipeline`
      roda o grafo com `.stream(stream_mode=["updates","values"])`: o **updates** dá o nó que
      acabou → um `ProgressEvent` por nó (`status="running"`, `pct` pela posição na espinha) num
      hook injetável `on_event`; o **values** acumula o estado cheio → estado final devolvido (e
      a estampa de custo, reusando o `traced_config`+`capture_usage` da F2.9, span por nó +
      `trace["usage"]`). Sentinelas (`__interrupt__`) são puladas no updates e tiradas do values
      (estado é `extra="forbid"`). Ao fim, **um evento terminal** `node="__end__"`/`pct=100` com o
      desfecho real — e aqui entra a responsabilidade que a F2.8 delegou ao worker: **interrupt
      HITL sync pendente → `awaiting_review`** (detectado por `compiled.get_state(config).next`
      não-vazio, que só existe com checkpointer); senão o `status` do estado final
      (`completed`/`insufficient_data`/`out_of_scope`, F2.12/F2.13). **(2) `apps/worker/jobs.py`**
      — `run_graph_job` (o job que o `rq worker tapi` puxa: roda o grafo **persistido**/F2.2
      publicando no canal), `enqueue_run` (a API/F5.2 só enfileira e responde o `run_id`;
      `job_id=run_id` casa job RQ ↔ checkpointer ↔ canal) e `default_queue`. **Decisão de design
      (b/d, igual F2.3–F2.9):** **offline é o default** — sem `on_event` o `stream_pipeline` só
      roda o grafo (já offline/reproduzível, M2/DoD), o Redis só entra quando um cliente é passado,
      e publicar é **best-effort** (engole `RedisError` — progresso é telemetria, não pode derrubar
      o run). **Conexões nascem dentro do job, não viajam na fila:** o RQ serializa os argumentos
      (pickle), então só argumentos planos (`query`/`run_id`/`mode`/`hitl` como string) vão no
      enqueue; o job abre Redis/Postgres do `settings` (F0.3) ao rodar — e recebe esses recursos
      **injetados** (`redis_client`/`open_checkpointer`/`runner`) p/ teste offline sem broker nem
      banco. **Fronteira de escopo travada (não invade F5.3):** o worker fica com o lado *publish*
      + o consumidor `subscribe_progress` (gerador que itera o canal até o `__end__`); o **endpoint
      SSE** `GET /runs/{id}` que o embrulha é da F5.3. Exports novos no pacote (`stream_pipeline`,
      `ProgressEvent`, `progress_channel`, `RedisProgressPublisher`, `subscribe_progress`) e em
      `apps/worker`. Testes `tests/test_progress.py` (round-trip do evento, `progress_channel` por
      run, `_pct` pela espinha, `stream_pipeline` offline → evento por nó + terminal `completed`/
      estado COMPLETED + sem-sink não quebra, interrupt HITL → terminal `awaiting_review` parando
      antes do briefing, `RedisProgressPublisher` publica JSON no canal + engole erro de broker,
      `subscribe_progress` itera até o terminal e fecha o pubsub) e `tests/test_worker.py`
      (`run_graph_job` roda o grafo + publica progresso com Redis stub e checkpointer nulo, coerção
      de `mode`/`hitl` string, run_id gerado; `enqueue_run` enfileira `run_graph_job` com
      `job_id=run_id` só com argumentos planos). Worker/Redis/Postgres reais ficam opt-in (sem
      teste de broker/banco, padrão da fase).
- [x] **F2.11** **Guarda de custo/orçamento de LLM** por run (limite de tokens/chamadas) — os
      créditos grátis do `build.nvidia.com` têm rate limit; evita estouro durante o build.
      → Estende o rollup de custo da F2.9 (`packages/observability/cost.py`): `LLMBudget`
      (teto por `max_calls`/`max_tokens`/`max_cost_usd`; `check(usage)` devolve o **motivo** do
      estouro ou `None`; `is_unbounded`), `BudgetExceeded` e o callback `BudgetGuard`/`BUDGET_GUARD`.
      `capture_usage(budget=)` arma o guard no escopo (novo `ContextVar` `_BUDGET`, irmão do
      `_SINK`); `budget_from_settings` lê os 4 campos novos do settings (F0.3, `llm_budget_enabled`
      + tetos, **off por default**, `0` = sem teto naquela dimensão). **Decisão de design (b/d,
      mesma mecânica da F2.9):** o guard é **singleton injetado no `traced_config`** (junto do
      `USAGE_RECORDER`) — então **mede e limita sem refatorar os nós**; antes de cada chamada
      (`on_chat_model_start`/`on_llm_start`) compara o uso acumulado do escopo com o teto e, se já
      atingido, levanta `BudgetExceeded` ⇒ **a chamada nunca chega à rede** (poupa o rate limit do
      free tier). `raise_error = True` faz o LangChain **propagar** (em vez de só logar) — e fica
      **isolado no guard, não no `UsageRecorder`**: uma falha de *medição* nunca deve derrubar um
      run, só a guarda de *orçamento* aborta de propósito. Os nós LLM (F2.3/F2.5/F2.6) já degradam
      para o determinista a qualquer falha, então o run **segue offline, sem alucinar** — a guarda
      **não trava nem força um terminal** (isso é F2.12/F2.13): o estouro vira **nota rastreável**
      via `stamp_usage` (novo helper em `graph.py`, compartilhado por `run_pipeline`/`stream_pipeline`),
      que carimba `trace["usage"]` (F2.9) e, no estouro, `trace["budget"]={limited,reason}` + uma
      linha em `errors`. **Offline é o default (igual F2.3–F2.10):** sem teto (gate off / `budget=None`)
      o guard é no-op e a espinha roda verde ponta a ponta (M2/DoD); `run_pipeline`/`stream_pipeline`
      ganham o param injetável `budget` (`None` → `budget_from_settings`). O teto é **soft na chamada
      que cruza** (só sabido no `on_llm_end`) e **hard na seguinte** — barra a *próxima*, então o
      gasto fica em ~teto, não estoura. Exports novos em `packages/observability`
      (`LLMBudget`/`BudgetExceeded`/`budget_from_settings`/`BUDGET_GUARD`). Teste
      `tests/test_budget.py`: `LLMBudget.check` (3 dimensões + `None` sob o teto + `is_unbounded`),
      `budget_from_settings` (off default, liga com teto, ligado-sem-teto → `None`), `BudgetGuard`
      (no-op fora de escopo/sob o teto, aborta ao atingir em `on_chat_model_start`/`on_llm_start`,
      `raise_error`), e integração `run_pipeline`/`stream_pipeline` com um nó "guloso" (simula
      chamadas atrás do guard) → chamadas **limitadas** ao teto + `trace["budget"]`/`errors`
      carimbados, caso sem estouro só `usage`, e offline-com-teto não carimba nada; `tests/test_tracing.py`
      passa a contar o guard na lista de callbacks do `traced_config`.
- [x] **F2.12** **Estado terminal de baixa confiança:** se após o retry limitado (F2.7) as
      evidências seguem insuficientes, o grafo **não alucina** — encerra num briefing marcado
      "dados insuficientes" (com o que foi achado + lacunas) ou descarte rastreável. Caminho
      terminal explícito no grafo + teste.
      → `packages/agents/terminals.py` (novo): `insufficient_data_briefing` monta o briefing
      terminal **"dados insuficientes"** a partir do estado — `status=dados_insuficientes`
      (`BriefingStatus`), `empresa` do perfil (cai na query se faltar), **o que foi apurado**
      (`aimi` parcial, pode ser `None`) e as **lacunas** (contagem real de fontes independentes
      < piso + nº de retries), **sem recomendação NVIDIA** (`recomendacoes=[]`) e sem alucinar
      campos ausentes (determinista/offline, ethos F2.14). **Caminho terminal explícito no grafo:**
      o `evidence_validator` (F2.7) ganha o 3º alvo de `Command` `TERMINAL_TARGET="briefing"` —
      quando o retry de coleta esgota e a corroboração segue < N hosts, marca o run
      `INSUFFICIENT_DATA`, deixa a nota rastreável em `errors` e **salta direto ao `briefing`**
      (pula RAG/recomendação/benchmark/HITL — sem corroboração não há o que recomendar); o `Literal`
      do retorno passa a `["scraper","nvidia_rag","briefing"]` (saída só por `goto`, sem aresta
      estática — `build_graph().edges` intacto, `CONDITIONAL_OUT` inalterado). O nó `briefing`
      (nodes.py, placeholder de F4.4) **despacha por status**: `INSUFFICIENT_DATA` → emite o
      terminal; senão fecha em `COMPLETED` (rascunho M2 inalterado). **Offline é o default
      (igual F2.3–F2.11):** sem perfil (espinha sem extração) o evidence_validator segue limpo →
      `COMPLETED`/briefing `None` (M2/DoD intacto); o terminal só dispara com perfil presente +
      evidência insuficiente após o retry esgotar. `insufficient_data_briefing` exportado no pacote
      (o nó via `NODES`; o terminal `OUT_OF_SCOPE` da F2.13 reusa `terminals.py`). Testes
      `tests/test_terminals.py`: helper (status/empresa/lacunas/sem recomendação + fallback p/ query
      sem perfil), nó despachando por status (terminal vs. COMPLETED), e o **grafo ponta a ponta**
      (perfil de 1 fonte + `max_retries=0` → run `INSUFFICIENT_DATA` + briefing terminal,
      RAG/recommender pulados, nota em `errors`); `tests/test_evidence_validator.py` atualizado
      (branch esgotado → `TERMINAL_TARGET`+`INSUFFICIENT_DATA`, loop termina no terminal, coerência
      da constante com a espinha). Cobre o DoD F2 "empresa sem evidência suficiente cai no terminal
      de baixa confiança (não alucina)".
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
