# F5 — Interface Web (Entregável 5)

**Objetivo:** dashboard para consulta, visualização de empresas/recomendações e export de briefing.
**Dependências:** F2, F4. **Marco:** M5.

## Tasks
- [ ] **F5.1** Setup Next.js (App Router) + TypeScript + Tailwind + shadcn/ui.
- [ ] **F5.2** API FastAPI: endpoints `POST /runs`, `GET /runs/{id}`, `GET /companies`, `/briefings/{id}`.
- [ ] **F5.3** Tela de consulta + acompanhamento **ao vivo** do pipeline via **SSE**.
- [ ] **F5.4** Lista/busca de startups (filtros por setor, AIMI, classificação).
- [ ] **F5.5** Detalhe da startup: **radar AIMI** (4 pilares) + evidências com link à fonte.
- [ ] **F5.6** Cartões de recomendação (§5.5) + número de ROI (vem do F6).
- [ ] **F5.7** Trace viewer: passos dos agentes (consome Langfuse/estado do grafo).
- [ ] **F5.8** Export do briefing em PDF.

## Tecnologias
Next.js · React · TypeScript · Tailwind/shadcn · FastAPI · SSE.

## DoD
- [ ] Fluxo completo navegável: consulta → progresso → empresa → recomendação → export PDF.
