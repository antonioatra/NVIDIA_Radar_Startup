# F1 — Pipeline de Scraping (Entregável 1)

**Objetivo:** buscar e coletar informações públicas sobre startups a partir de uma consulta,
com proveniência rastreável. **Dependências:** F0. **Marco:** M1.

## Tasks
- [ ] **F1.1** Busca: integração **Tavily** (free tier) → URLs candidatas a partir de termos.
- [ ] **F1.2** Adapter **Firecrawl**: extração limpa de páginas p/ RAG.
- [ ] **F1.3** Adapter **Playwright**: sites dinâmicos dependentes de JS.
- [ ] **F1.4** Adapter **trafilatura**: texto principal de blogs/notícias (§9.2).
- [ ] **F1.5** Adapter **BeautifulSoup**: parsing de páginas HTML simples.
- [ ] **F1.6** Crawler **Scrapy**: varredura dos diretórios do §9.1 em escala.
- [ ] **F1.7** Roteador de fetch (estático vs dinâmico) escolhe o adapter certo.
- [ ] **F1.8** `robots.txt` + rate limiting + user-agent identificável (compliance).
- [ ] **F1.9** Proveniência: salvar `url`, `fetched_at`, hash do conteúdo, snippet → tabela `evidence`.
- [ ] **F1.10** Persistência: upsert de `company`/`founder` (dedup por domínio/CNPJ quando houver).

## Tecnologias
Tavily · Firecrawl · Playwright · trafilatura · BeautifulSoup · Scrapy · PostgreSQL.

## DoD
- [ ] Dada uma consulta, coleta e persiste ≥1 startup com ≥3 evidências rastreáveis.
- [ ] Respeita `robots.txt`; nenhuma fonte fechada/violação de ToS.
