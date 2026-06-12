# F1 — Pipeline de Scraping (Entregável 1)

**Objetivo:** buscar e coletar informações públicas sobre startups a partir de uma consulta,
com proveniência rastreável. **Dependências:** F0. **Marco:** M1.

## Tasks
- [x] **F1.1** Busca: integração **Tavily** (free tier) → URLs candidatas a partir de termos.
- [x] **F1.2** Adapter **Firecrawl**: extração limpa de páginas p/ RAG.
- [x] **F1.3** Adapter **Playwright**: sites dinâmicos dependentes de JS.
- [x] **F1.4** Adapter **trafilatura**: texto principal de blogs/notícias (§9.2).
- [x] **F1.5** Adapter **BeautifulSoup**: parsing de páginas HTML simples.
- [x] **F1.6** Crawler **Scrapy**: varredura dos diretórios do §9.1 em escala.
- [x] **F1.7** Roteador de fetch (estático vs dinâmico) escolhe o adapter certo.
- [x] **F1.8** `robots.txt` + rate limiting + user-agent identificável (compliance) +
      **guarda de quota de free tier** (Tavily/Firecrawl): contador/limite por run p/ não estourar
      silenciosamente (espelha a guarda de orçamento de LLM em F2.11).
- [x] **F1.9** Proveniência: salvar `url`, `fetched_at`, hash do conteúdo, snippet → tabela `evidence`.
- [x] **F1.10** Persistência: upsert de `company`/`founder` (dedup por domínio/CNPJ quando houver).
      **Escopo geográfico = Brasil:** o sourcing já é BR por construção (seeds §9 são diretórios
      brasileiros), mas registrar `country=BR` explícito no perfil e **filtrar** candidatas
      claramente estrangeiras (ex.: sem CNPJ/operação no BR e sem sinal de mercado brasileiro),
      para o discovery por setor/região (F2.3) não vazar empresas fora de escopo.
- [x] **F1.11** Taxonomia de **sinais AI-native** no sourcing (§2 "sinais de uso intensivo de IA"):
      keywords (LLM/agents/embeddings/RAG/fine-tuning), vagas de ML/AI eng, papers, stack pública.
      Enviesa termos do `search_planner` e pré-filtra candidatas antes da classificação pós-hoc.
      → `packages/scraping/signals.py`: léxico em 4 categorias (`model_ai`/`ml_hiring`/`research`/
      `public_stack`) com peso e dica de pilar AIMI; `bias_query` (enviesa a busca) + `prefilter`
      (descarta non-AI óbvias antes do F2.6, poupa quota F2.11). Prompt `search_planner` reforça o viés.
- [x] **F1.12** **Eval set rotulado inicial (~20–30 startups)** em `data/eval/` — cada entrada com
      classificação esperada (AI-native | AI-enabled | non-AI) + AIMI esperado (4 pilares).
      Criado **aqui, cedo**, porque **F6.4** (correlação do índice) e **F7.1/F7.2** (métricas)
      o consomem; F7 apenas **consolida/expande**, não cria do zero. Rótulos por revisão humana
      sobre evidências coletadas (rastreável). **Usa a definição de pilares/escala de
      `docs/RUBRICA-AIMI.md` (F0.11)** como referência de rotulagem — assim o ground-truth não
      depende da heurística de pontuação (v0 F2.6 / v1 F6.1), que pode mudar sem invalidar os rótulos.
      → `data/eval/labeled_startups.yaml` (24 fixtures-semente `synthetic: true`, cobrindo as 5
      regiões do plano `classe × AIMI`; AIMI total 14–79; classes 15/5/4) + loader Pydantic em
      `packages/eval/dataset.py` (`load_eval_set`, valida coerência direcional) + enum `PlaneRegion`.
      Inclui `expected_nvidia_techs` (contrato do eval de recomendação, F7.2b). Entradas reais
      (`synthetic: false`) exigem `evidence_urls` e entram via revisão humana (F1.14 + F7.1).
- [x] **F1.13** **LGPD / dado de founder:** restringir coleta de `founders` a **informação
      profissional pública** (nome, cargo, empresa, perfil público). Registrar base legal
      (interesse legítimo, dado público) na tabela `evidence`; não coletar dado sensível.
      Honra robots.txt/ToS das fontes (§9.1, perfis públicos de founders).
      → `packages/scraping/lgpd.py`: `sanitize_founder` descarta founder com dado sensível
      (Art. 5, II) no núcleo (nome/cargo) e **redige** o `background` (CPF/contato/idade/
      estado civil/religião/etc.); `upsert_founder` aplica o guard (devolve `None` = não
      coleta). Enum `LegalBasis` + coluna `evidence.legal_basis` (migração `c3a2f1b4d5e6`):
      evidência de founder carimba `legitimo_interesse` (Art. 7 IX/§4). Compliance de fetch
      (robots/ToS) segue em F1.8/F1.15; aqui é a camada de **minimização de dado**.
- [x] **F1.14** **Cohort builder (batch sourcing):** transforma o crawl dos diretórios §9 (F1.6)
      numa **fila de empresas candidatas** e roda o grafo em lote, acumulando na tabela `company`.
      É essa tabela acumulada que alimenta o clustering de coorte (F6.5–F6.7) e o eval set (F1.12)
      — não a saída de um run único. Esclarece o salto "run por-empresa → visão de coorte".
      **Política de HITL em lote:** runs batch rodam com `hitl=auto` — o interrupt humano (F2.8)
      **não** bloqueia a fila; empresas de baixa confiança caem no estado terminal (F2.12) e são
      marcadas para revisão posterior. HITL síncrono fica só no *single-company lookup*.
      → `packages\agents\cohort.py` (+ `tests\test_cohort.py`): orquestrador em lote que **reusa** o
      que já existe — não reimplementa coleta, grafo nem persistência. **Descoberta**
      (`discover_candidates`): crawl (F1.6) das seeds `allow` (programas/portfólios + notícias §9.2,
      via `collectable_seeds`/gate de ToS F1.15) e `candidate_domains` extrai os **links de saída**
      das páginas → fila de domínios de startup (dedup, exclui o host da seed/subdomínios e a denylist
      de rede-social/infra). **Perfilagem:** `run_pipeline` (F2, injetável) por empresa. **Persistência
      idempotente:** reusa `persist_profile` (F1.10 — escopo BR/F2.13) + `persist_score` /
      `persist_recommendations` (F4.7/F6.13). **Política auto-HITL travada:** `hitl=AUTO`, **sessão
      fresca por empresa** (a falha de uma não envenena as outras — continue-on-error), baixa confiança
      (F2.12 `INSUFFICIENT_DATA`) / fora de escopo (F2.13 `OUT_OF_SCOPE`) → `needs_review` sem bloquear
      a fila; devolve `CohortReport` auditável. **Testável offline:** extração pura + laço com
      `runner`/`crawl_fn`/`session_factory` injetados + SQLite in-memory (sem rede nem reactor Twisted);
      o crawl Scrapy e o pipeline real entram por injeção/flag. CLI
      `python -m packages.agents.cohort [--db sqlite:///… | --limit N | --dry-run]` — `--db` aceita
      SQLite e roda **sem Postgres** (F0.2 adiado); o caminho real exige `SCRAPER_USE_NETWORK=true`
      (+ flags de LLM p/ classe/AIMI reais). Destrava a **expansão real do eval (F7.1)** e a coorte do
      diferencial (F6.5–F6.7). **Gate verde:** `ruff` limpo e `pytest` **737 passed, 4 skipped**
      (+8 testes do cohort).
- [x] **F1.15** **Política de ToS por fonte (robots ≠ ToS):** o DoD promete "nenhuma fonte
      fechada/violação de ToS", mas o §9.1 lista plataformas de dados (Distrito, Cubo, StartSe,
      100 Open Startups) cujos **Termos de Uso** podem proibir scraping mesmo quando o `robots.txt`
      permite. Decisão travada: **priorizar sites/blogs/carreiras oficiais das startups + notícias
      (§9.2)**; usar os diretórios §9.1 **só** onde houver API pública/permissão. Manter uma
      allowlist/denylist de fontes em `data/seeds/` com a base (robots + ToS + base legal) anotada
      por fonte na tabela `evidence` (estende F1.8/F1.13). Fonte sem permissão clara → não coletada.
      → allowlist/denylist já nas seeds (`data/seeds/`, policy/robots/tos_scraping/legal_basis por
      fonte). `packages/scraping/source_policy.py`: gate de ToS por URL (`SourcePolicyGate`,
      `guard`/`verdict`) p/ o caminho do roteador (F1.7) — bloqueia §9.1 `api_only`/`deny`, libera
      `allow` + site oficial não-listado; espelha o `collectable_seeds` do crawler (F1.6). Coluna
      `evidence.source_policy` (migração `d4b3a2c1e0f5`): a persistência carimba `<fonte>:<policy>`
      por evidência (ex.: `unlisted:allow`, `brazil-journal:allow`). Robots/rate-limit segue F1.8.

> **Fora de escopo (v1):** re-crawl periódico / detecção de mudança / frescor das empresas e
> entity resolution avançada ficam para depois — a v1 coleta **sob demanda**. Ver nota em `PLANO.md`.

## Tecnologias
Tavily · Firecrawl · Playwright · trafilatura · BeautifulSoup · Scrapy · PostgreSQL.

## DoD
- [ ] Dada uma consulta, coleta e persiste ≥1 startup com ≥3 evidências rastreáveis.
- [x] Respeita `robots.txt` (F1.8); nenhuma fonte fechada/violação de ToS (F1.15).
- [x] `data/eval/` tem o conjunto rotulado inicial (≥20 startups) versionado.
- [x] Coleta de founder limitada a dado profissional público, com base LGPD registrada.
- [ ] Cohort builder roda o crawl §9 em lote e popula a tabela `company` p/ alimentar a coorte.
- [x] Cada fonte tem decisão de ToS registrada (allowlist/denylist); nenhuma fonte sem permissão é coletada (F1.15).
