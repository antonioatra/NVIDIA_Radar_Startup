# F4 — Motor de Recomendação (Entregável 4)

**Objetivo:** cruzar o perfil/gaps da startup com as tecnologias NVIDIA e gerar a recomendação
estruturada + briefing executivo. **Dependências:** F2, F3. **Marco:** M4.

## Tasks
- [ ] **F4.1** Mapa de regras gap → tech NVIDIA (base nos exemplos do §5.5).
- [ ] **F4.2** Nó **recommender** (Nemotron-Super, reasoning ON): consome AIMI + RAG → recomendações.
- [ ] **F4.3** Saída estruturada (§5.5): tech · justificativa técnica · justificativa de negócio ·
      prioridade · complexidade · próxima ação · **evidências**.
- [ ] **F4.4** Nó **briefing** (Briefing Agent): relatório executivo (JSON + Markdown) com
      próximas-ações nos **três eixos do §2 — comercial, técnica e comunitária** (Inception:
      onboarding, créditos, comunidade, eventos, GTM).
- [ ] **F4.5** **NeMo Guardrails** no briefing: rails contra recomendação sem evidência/alucinação.
- [ ] **F4.6** Export PDF do briefing (server-side).
- [ ] **F4.7** Persistir `recommendation` + ligação com evidências no Postgres.

## Tecnologias
Nemotron-Super · NeMo Guardrails · PostgreSQL · (gancho p/ ROI do F6).

## DoD
- [ ] Para uma startup, gera recomendação no formato §5.5 com evidências citadas.
- [ ] Guardrails bloqueia recomendação sem evidência suficiente.
