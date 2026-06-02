# F1 — Pipeline de Scraping (Entregável 1)

**Objetivo:** buscar e coletar informações públicas sobre startups a partir de uma consulta,
com proveniência rastreável. **Dependências:** F0. **Marco:** M1.

## Tasks
- [ ] **F1.1** Busca: integração **Tavily** (free tier) → URLs candidatas a partir de termos.
- [x] **F1.2** Adapter **Firecrawl**: extração limpa de páginas p/ RAG.
- [ ] **F1.3** Adapter **Playwright**: sites dinâmicos dependentes de JS.
- [ ] **F1.4** Adapter **trafilatura**: texto principal de blogs/notícias (§9.2).
- [ ] **F1.5** Adapter **BeautifulSoup**: parsing de páginas HTML simples.
- [ ] **F1.6** Crawler **Scrapy**: varredura dos diretórios do §9.1 em escala.
- [ ] **F1.7** Roteador de fetch (estático vs dinâmico) escolhe o adapter certo.
- [ ] **F1.8** `robots.txt` + rate limiting + user-agent identificável (compliance) +
      **guarda de quota de free tier** (Tavily/Firecrawl): contador/limite por run p/ não estourar
      silenciosamente (espelha a guarda de orçamento de LLM em F2.11).
- [ ] **F1.9** Proveniência: salvar `url`, `fetched_at`, hash do conteúdo, snippet → tabela `evidence`.
- [ ] **F1.10** Persistência: upsert de `company`/`founder` (dedup por domínio/CNPJ quando houver).
      **Escopo geográfico = Brasil:** o sourcing já é BR por construção (seeds §9 são diretórios
      brasileiros), mas registrar `country=BR` explícito no perfil e **filtrar** candidatas
      claramente estrangeiras (ex.: sem CNPJ/operação no BR e sem sinal de mercado brasileiro),
      para o discovery por setor/região (F2.3) não vazar empresas fora de escopo.
- [ ] **F1.11** Taxonomia de **sinais AI-native** no sourcing (§2 "sinais de uso intensivo de IA"):
      keywords (LLM/agents/embeddings/RAG/fine-tuning), vagas de ML/AI eng, papers, stack pública.
      Enviesa termos do `search_planner` e pré-filtra candidatas antes da classificação pós-hoc.
- [ ] **F1.12** **Eval set rotulado inicial (~20–30 startups)** em `data/eval/` — cada entrada com
      classificação esperada (AI-native | AI-enabled | non-AI) + AIMI esperado (4 pilares).
      Criado **aqui, cedo**, porque **F6.4** (correlação do índice) e **F7.1/F7.2** (métricas)
      o consomem; F7 apenas **consolida/expande**, não cria do zero. Rótulos por revisão humana
      sobre evidências coletadas (rastreável). **Usa a definição de pilares/escala de
      `docs/RUBRICA-AIMI.md` (F0.11)** como referência de rotulagem — assim o ground-truth não
      depende da heurística de pontuação (v0 F2.6 / v1 F6.1), que pode mudar sem invalidar os rótulos.
- [ ] **F1.13** **LGPD / dado de founder:** restringir coleta de `founders` a **informação
      profissional pública** (nome, cargo, empresa, perfil público). Registrar base legal
      (interesse legítimo, dado público) na tabela `evidence`; não coletar dado sensível.
      Honra robots.txt/ToS das fontes (§9.1, perfis públicos de founders).
- [ ] **F1.14** **Cohort builder (batch sourcing):** transforma o crawl dos diretórios §9 (F1.6)
      numa **fila de empresas candidatas** e roda o grafo em lote, acumulando na tabela `company`.
      É essa tabela acumulada que alimenta o clustering de coorte (F6.5–F6.7) e o eval set (F1.12)
      — não a saída de um run único. Esclarece o salto "run por-empresa → visão de coorte".
      **Política de HITL em lote:** runs batch rodam com `hitl=auto` — o interrupt humano (F2.8)
      **não** bloqueia a fila; empresas de baixa confiança caem no estado terminal (F2.12) e são
      marcadas para revisão posterior. HITL síncrono fica só no *single-company lookup*.
- [ ] **F1.15** **Política de ToS por fonte (robots ≠ ToS):** o DoD promete "nenhuma fonte
      fechada/violação de ToS", mas o §9.1 lista plataformas de dados (Distrito, Cubo, StartSe,
      100 Open Startups) cujos **Termos de Uso** podem proibir scraping mesmo quando o `robots.txt`
      permite. Decisão travada: **priorizar sites/blogs/carreiras oficiais das startups + notícias
      (§9.2)**; usar os diretórios §9.1 **só** onde houver API pública/permissão. Manter uma
      allowlist/denylist de fontes em `data/seeds/` com a base (robots + ToS + base legal) anotada
      por fonte na tabela `evidence` (estende F1.8/F1.13). Fonte sem permissão clara → não coletada.

> **Fora de escopo (v1):** re-crawl periódico / detecção de mudança / frescor das empresas e
> entity resolution avançada ficam para depois — a v1 coleta **sob demanda**. Ver nota em `PLANO.md`.

## Tecnologias
Tavily · Firecrawl · Playwright · trafilatura · BeautifulSoup · Scrapy · PostgreSQL.

## DoD
- [ ] Dada uma consulta, coleta e persiste ≥1 startup com ≥3 evidências rastreáveis.
- [ ] Respeita `robots.txt`; nenhuma fonte fechada/violação de ToS.
- [ ] `data/eval/` tem o conjunto rotulado inicial (≥20 startups) versionado.
- [ ] Coleta de founder limitada a dado profissional público, com base LGPD registrada.
- [ ] Cohort builder roda o crawl §9 em lote e popula a tabela `company` p/ alimentar a coorte.
- [ ] Cada fonte tem decisão de ToS registrada (allowlist/denylist); nenhuma fonte sem permissão é coletada (F1.15).
