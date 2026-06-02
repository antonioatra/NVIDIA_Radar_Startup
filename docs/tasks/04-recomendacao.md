# F4 — Motor de Recomendação (Entregável 4)

**Objetivo:** cruzar o perfil/gaps da startup com as tecnologias NVIDIA e gerar a recomendação
estruturada + briefing executivo. **Dependências:** F2, F3. **Marco:** M4.

## Tasks
- [ ] **F4.1** Mapa de regras gap → tech NVIDIA (base nos exemplos do §5.5).
- [ ] **F4.2** Nó **recommender** (Nemotron-Super, reasoning ON): consome AIMI + RAG → recomendações.
      O `evidencia_nvidia` vem da recuperação **dirigida pelos gaps** do AIMI feita no `nvidia_rag`
      (F3.7) — o recommender cruza gap (lado startup) × citação da KB (lado NVIDIA), não recupera de novo.
- [ ] **F4.3** Saída estruturada (§5.5): tech · justificativa técnica · justificativa de negócio ·
      prioridade · complexidade · próxima ação · **evidências dos dois lados** (`evidencia_gap`
      do perfil/AIMI da startup **+** `evidencia_nvidia`, citações da KB recuperadas pelo RAG que
      justificam a tech — schema `Recommendation` de F0.5). Sem um dos lados, F4.5 bloqueia.
- [ ] **F4.4** Nó **briefing** (Briefing Agent): relatório executivo (JSON + Markdown) **em PT-BR**
      (F0.13) com próximas-ações nos **três eixos do §2 — comercial, técnica e comunitária**
      (Inception: onboarding, créditos, comunidade, eventos, GTM). **Variante "fora de escopo"**
      (F2.13): para empresa `non-AI` de alta confiança, emite briefing explicando por que não é
      alvo Inception (sem forçar recomendação NVIDIA).
- [ ] **F4.5** **NeMo Guardrails** no briefing: rails contra recomendação sem evidência/alucinação.
      Regra explícita: bloqueia recomendação que não tenha **`evidencia_gap` E `evidencia_nvidia`**.
- [ ] **F4.6** Export PDF do briefing (server-side).
- [ ] **F4.7** Persistir `recommendation` + ligação com evidências no Postgres.
- [ ] **F4.8** **Casos de teste dos 7 exemplos do §5.5** (aderência ao brief): assevera que o
      recommender produz o esperado — voz→Riva+NIM; dados tabulares→RAPIDS/cuDF/cuML;
      saúde→Clara/MONAI/NIM/Guardrails/AI Enterprise; atendimento via API→NIM/Guardrails/Triton+benchmark;
      robotics→Isaac/Omniverse; latência→Triton/TensorRT-LLM/batching; governança→Guardrails+NeMo.
      Vive em `packages/eval` (consolidado na F7.2).

## Tecnologias
Nemotron-Super · NeMo Guardrails · PostgreSQL · (gancho p/ ROI do F6).

## DoD
- [ ] Para uma startup, gera recomendação no formato §5.5 com evidências citadas dos **dois lados**
      (gap da startup + citação da KB NVIDIA).
- [ ] Guardrails bloqueia recomendação sem evidência suficiente (faltando qualquer um dos lados).
- [ ] Briefing sai em PT-BR.
