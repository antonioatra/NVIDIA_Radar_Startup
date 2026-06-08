# F4 — Motor de Recomendação (Entregável 4)

**Objetivo:** cruzar o perfil/gaps da startup com as tecnologias NVIDIA e gerar a recomendação
estruturada + briefing executivo. **Dependências:** F2, F3. **Marco:** M4.

## Enquadramento — a camada de apoio à decisão (DSS)

Este entregável é o **núcleo do apoio à decisão** do TAPI: converte o diagnóstico (perfil + AIMI,
F2/F6.1) em **ação para o gerente de Startups & VCs / Inception**. Opera no **nível 1** de um
sistema de apoio à decisão de três níveis (visão completa em
[`../ALINHAMENTO-CRITERIOS-E-DECISAO.md`](../ALINHAMENTO-CRITERIOS-E-DECISAO.md)):

| Nível | Pergunta de decisão | Método | Onde |
|---|---|---|---|
| **1. Por empresa** | *O que ofereço a esta startup?* | gap (AIMI) × tech NVIDIA (RAG) → `Recommendation` + ROI | **F4 (aqui)** + F6.11 |
| 2. Priorização | *Quem abordo primeiro?* | Inception Priority 0–100 | F6.13 |
| 3. Portfólio | *Onde está o ecossistema?* | clustering de coorte → radar | F6.5–F6.7 |

O método do nível 1 é o loop **diagnosticar → prescrever → quantificar**: o pilar fraco do AIMI
(sobretudo **P3 Technical Optimization**) **dispara** a recomendação (F6.3); o RAG traz a evidência
NVIDIA citável; o GPU Graduation Engine (F6.11) anexa o **ROI**. A confiabilidade da decisão vem de
**evidência dos dois lados** (invariante de schema + Guardrails F4.5): nenhuma recomendação sem
`evidencia_gap` **E** `evidencia_nvidia`.

## Tasks
- [x] **F4.1** Mapa de regras gap → tech NVIDIA (base nos exemplos do §5.5).
      → `packages/agents/recommend_rules.py`: a **espinha determinística** do recommender (F4.2) —
      converte o diagnóstico (AIMI/F2.6 + perfil) em **techs candidatas** no formato §5.5, cada uma
      ligada ao **gap que a motiva**. É o complemento do `nvidia_rag` (F3.7): o nó deriva os gaps em
      **consultas de recuperação** (busca a evidência); aqui os mesmos gaps viram a **prescrição**
      (qual tech recomendar) — o recommender (F4.2) cruza candidata × citação `evidencia_nvidia`
      casadas por `kb_tech` e fecha a `Recommendation` (F4.3) com evidência dos **dois lados**. Dois
      eixos: `PILLAR_RULES` (gap do AIMI → tech que o fecha — P3→NIM/TensorRT-LLM/Triton [graduação
      API→stack, latência/"atendimento via API"], P1→NeMo customização/Curator, P2→NeMo Retriever,
      P4→Guardrails/NeMo Evaluator/AI Enterprise [governança]) e `SECTOR_RULES` (domínio §5.5 →
      saúde→Clara/MONAI, voz→Riva, cyber→Morpheus, robótica→Isaac/Omniverse, simulação→Omniverse,
      **dados tabulares→RAPIDS/cuDF/cuML** — eixo exclusivo daqui, sem query equivalente no F3.7).
      `match_techs(aimi, profile)` aplica as regras (gaps por severidade + setor), dedup por
      `(kb_tech, tech)` preservando ordem, e devolve `TechCandidate` com `pilar_origem` + `triggers`.
      **Decisão (espinha verde, igual F2.3–F2.7/F3):** puro/offline/determinístico, sem rede/GPU/LLM
      — justificativas e `proxima_acao` são **esqueletos coerentes** que já fecham o contrato §5.5
      sem rede (o recommender Nemotron os refina com a evidência, F4.2). A seleção de gaps **reusa
      `gap_pillars`** (promovido de privado no F3.7) → consistência gap↔evidência (não recomenda
      gap sem evidência recuperada, e vice-versa). `kb_tech` é o nome **exato** da KB (manifesto
      F3.1): `test_every_rule_tech_exists_in_the_kb` o amarra às techs `source_type: doc` (mesma
      disciplina do `CORE_TECHS`/F3.1 e do mapa de queries/F3.8 — regra com tech inexistente quebra
      o build). Testes em `tests/test_recommend_rules.py` (amarra à KB, cobertura dos 4 pilares,
      ordem por severidade com `pilar_origem`, setor anexado sem pilar, fallback do pilar mais baixo,
      determinismo, e aderência a 5 dos 7 exemplos §5.5 — o ponta-a-ponta dos 7 é a F4.8).
- [x] **F4.2** Nó **recommender** (Nemotron-Super, reasoning ON): consome AIMI + RAG → recomendações.
      O `evidencia_nvidia` vem da recuperação **dirigida pelos gaps** do AIMI feita no `nvidia_rag`
      (F3.7) — o recommender cruza gap (lado startup) × citação da KB (lado NVIDIA), não recupera de novo.
      → `packages/agents/recommender.py`: o nó (sétimo do grafo, entre `nvidia_rag`/F3.7 e
      `gpu_benchmark`/F6). `build_recommendations` cruza as **candidatas** do `match_techs` (F4.1) ×
      as **citações** do `state.retrieved` (F3.7) casadas por **`kb_tech`** (`metadata["tech"]`), e
      monta a `Recommendation` (F4.3) a partir do esqueleto §5.5 da regra. **Espinha verde, igual ao
      classifier/F2.6:** caminho **determinista/offline é o default**; o Super (`recommender@v1`,
      F0.12) é **plugável** atrás de `settings.recommender_use_llm` (+ chave) **ou** de um adapter
      `recommend=` injetado e **só refina a redação** (justificativas/`proxima_acao`/prioridade),
      caindo de volta na espinha a qualquer falha de rede/JSON (`recommend_with_llm` degrada p/
      `None`). A **evidência dos dois lados nunca vem do LLM** — é sempre a determinista
      (anti-alucinação). Sem `aimi` (espinha offline) o nó é **no-op limpo** (`{}`) — grafo verde
      ponta a ponta (M2/DoD). Carimba `trace["recommender"]` (n + techs). Testes em
      `tests/test_recommender.py` (cruzamento por tech, fallback, data do manifesto, refino LLM
      preservando evidência, no-op, e ponta-a-ponta `nvidia_rag → recommender` no RAG real).
- [x] **F4.3** Saída estruturada (§5.5): tech · justificativa técnica · justificativa de negócio ·
      prioridade · complexidade · próxima ação · **evidências dos dois lados** (`evidencia_gap`
      do perfil/AIMI da startup **+** `evidencia_nvidia`, citações da KB recuperadas pelo RAG que
      justificam a tech — schema `Recommendation` de F0.5). Sem um dos lados, F4.5 bloqueia.
      → O contrato `Recommendation` (schema F0.5) já existia; aqui ele é **preenchido** pelo
      recommender (F4.2) com a evidência **resolvida dos dois lados**: `evidencia_nvidia` = citações
      da KB casadas por `kb_tech`, **datadas** pelo `captured_at` do manifesto (F3.1) — determinístico,
      sem `now()`, cortado em `MAX_NVIDIA_EVIDENCE`; `evidencia_gap` = evidência do **pilar-gap** (se
      houver), com fallback ao **perfil público** (descrição/stack) num gap de *ausência* (P3 de um
      wrapper, score ≤6 sem evidência no pilar — para a recomendação mais valiosa, graduação
      API→stack, não cair por falta do lado-startup), e o **domínio declarado** (setor/descrição)
      numa tech de setor (§5.5). O nó **só emite** o que tem **ambos** os lados — o mesmo invariante
      do `Recommendation._require_both_sides` (F0.5) que o Guardrails (F4.5) reforça no briefing:
      candidata sem citação NVIDIA (ou sem evidência de gap) é **descartada**, não alucinada.
- [x] **F4.4** Nó **briefing** (Briefing Agent): relatório executivo (JSON + Markdown) **em PT-BR**
      (F0.13) com próximas-ações nos **três eixos do §2 — comercial, técnica e comunitária**
      (Inception: onboarding, créditos, comunidade, eventos, GTM). **Variante "fora de escopo"**
      (F2.13): para empresa `non-AI` de alta confiança, emite briefing explicando por que não é
      alvo Inception (sem forçar recomendação NVIDIA).
      → `packages/agents/briefing.py`: o **décimo e último** nó do grafo (depois do `human_review`/
      F2.8). Sintetiza diagnóstico (perfil + AIMI/F2.6) + prescrição (recomendações/F4.2-F4.3) num
      `Briefing` (schema F0.5) **em PT-BR**, com os três eixos do §2: `acao_comercial` (timing de
      outreach pela região do plano `classe × AIMI` — alvo de graduação API→stack tem o maior
      upside), `acao_tecnica` (ancorada na `proxima_acao` da recomendação de **maior prioridade** +
      roadmap) e `acao_comunitaria` (onboarding/créditos Inception atados às techs prescritas).
      **JSON + Markdown:** o contrato `Briefing` é o JSON; `render_markdown` é a **view** PT-BR
      derivada do mesmo objeto (render determinístico → JSON↔Markdown coerentes; base do PDF/F4.6 e
      do front/F5), cobrindo também as variantes terminais (lacunas). **Decisão (espinha verde, igual
      classifier/F2.6 e recommender/F4.2):** determinista/offline por default; o Super (`briefing@v1`,
      F0.12) é **plugável** atrás de `settings.briefing_use_llm` (+ chave) **ou** de um adapter
      `refine=` injetado e **só refina a redação** (resumo + os três eixos), caindo na espinha a
      qualquer falha de rede/JSON. O **diagnóstico e as recomendações nunca vêm do LLM** — são sempre
      os do estado, já aterrados em evidência dos dois lados (anti-alucinação; o invariante que o
      Guardrails/F4.5 reforça). As **variantes terminais** (F2.12/F2.13) seguem em `terminals.py`;
      o nó despacha por status e cobre o **caminho normal**. Sem `aimi` (espinha offline sem
      classificação) é **no-op limpo** (só fecha o run em COMPLETED, sem briefing) — grafo verde
      ponta a ponta (M2/DoD) sem alucinar relatório sem base. Testes em `tests/test_briefing.py`
      (espinha + 3 eixos com ramificação comercial, Markdown incl. terminal, refino LLM preservando
      diagnóstico/recomendações, no-op sem aimi, ponta a ponta no grafo real até o briefing normal).
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
- [x] Para uma startup, gera recomendação no formato §5.5 com evidências citadas dos **dois lados**
      (gap da startup + citação da KB NVIDIA). → recommender (F4.2/F4.3); ponta-a-ponta verde no
      `tests/test_recommender.py::test_node_end_to_end_over_real_rag`.
- [ ] Guardrails bloqueia recomendação sem evidência suficiente (faltando qualquer um dos lados).
- [x] Briefing sai em PT-BR. → `build_briefing`/`render_markdown` (F4.4) emitem o `Briefing` (JSON)
      e a view Markdown em PT-BR (`idioma="pt-BR"`), com os três eixos do §2; verde em
      `tests/test_briefing.py`.
