# F7 — Validação Final (transversal / qualidade)

**Objetivo:** consolidar avaliação, comparar rerankers e fechar a qualidade do projeto.
**Dependências:** F3, F4, F6. **Marco:** M7.

## Tasks
- [ ] **F7.1** **Consolidar/expandir** o eval set rotulado criado em **F1.12** (~20–30 startups,
      classificação + AIMI esperados) — revisar rótulos, fechar lacunas. Não cria do zero.
- [x] **F7.2** Métricas de classificação (accuracy/F1) e correlação do AIMI (consolida F6.4).
      Consolida também os **casos dos 7 exemplos do §5.5 (F4.8)** no relatório de aderência ao brief.
      → `packages\eval\classification_metrics.py` (+ `tests\test_classification_metrics.py`):
      harness irmão do `aimi_correlation` (F6.4) — reusa o **mesmo** `profile_for` só-de-descrição
      e compara a `classificacao` predita × rotulada. Núcleo puro/offline (sem scikit-learn):
      `accuracy`, `class_prf` (P/R/F1 one-vs-rest), `macro_f1` (média não-ponderada sobre classes
      com suporte — não deixa a majoritária mascarar as raras) e `confusion_matrix` (gold→predito,
      taxonomia inteira). **Preditor injetável** (`evaluate_classification(predict=…)`): default =
      `predicted_class` (heurística offline, o que roda no CI); `llm_predicted_class` mede o
      **Nemotron-Super real** (F2.6, mesmo caminho de produção, com fallback à heurística). CLI
      `python -m packages.eval.classification_metrics [--llm]` (exit 1 abaixo do gate §7 ≥ 0,75).
      **Os dois números (n=24), medidos:**
      | Caminho | macro-F1 | accuracy | AI-native R |
      |---|---|---|---|
      | Heurística offline (piso/CI) | **0,38** ❌ | 0,375 | **0,20** |
      | **Nemotron-Super real** (produção) | **0,875** ✅ | 0,917 | **0,933** |

      *Leitura honesta:* o **caminho de produção bate a meta** (0,875 ≥ 0,75) — o 0,38 era só o
      **substituto determinístico offline**, que rebaixa AI-native porque `_classify_class` exige
      Workflow Depth > 8 e a prosa-só sub-prediz essa magnitude (o mesmo limite que o F6.4 documenta
      p/ o índice). O Super, com reasoning, lê o *papel* da IA na descrição e recupera AI-native
      (recall 0,20 → 0,933). **Limite que permanece:** o eval set é 100% sintético (`synthetic:
      true`) — é "modelo real sobre dados de fixture"; torná-lo real é a **F7.1**. A consolidação
      dos três (classificação + AIMI/F6.4 + 7 casos/F4.8) num relatório único é da **F7.5**.
      **Gate verde (testes offline):** `ruff` limpo e `pytest` **687 passed, 4 skipped** (10 testes
      novos; o `--llm` faz rede e fica fora do CI). Medição real do Super rodada ao vivo (2026-06-11).
- [x] **F7.2b** **Eval da recomendação (held-out, não só os 7 exemplos):** sobre o eval set (F1.12),
      medir se as techs NVIDIA recomendadas batem com as esperadas por empresa — precision/recall
      de techs e taxa de recomendação com evidência dos dois lados (F4.3). Fecha a lacuna do
      Entregável 4 ter qualidade aferida só por casos canônicos.
      → `packages\eval\recommendation_metrics.py` (+ `tests\test_recommendation_metrics.py`): harness
      irmão da classificação (F7.2) e da correlação (F6.4) — alimenta o recommender com o **AIMI
      rotulado** (ground-truth, **não** o predito: isola a prescrição do erro do índice, que o F6.4
      mede à parte), o perfil só-de-descrição (`profile_for`) e uma **recuperação de recall máximo**
      (`full_recall_retrieval`/F4.8 — isola a prescrição do recall do RAG, medido na RAGAS/F7.3), e
      cruza techs **produzidas × `expected_nvidia_techs`** (substring, tolerante a parentético). `non-AI`
      é **fora de escopo** (F2.13 pula a recomendação): 4 excluídas, **20 in-scope**. Reporta
      **precision** (pega super-recomendação), **recall**, **F1** (micro), **taxa dos dois lados** (F4.5)
      e **recorte por região** (RUBRICA §6). Núcleo puro/offline (`_matches`, `_prf`); **sem `--llm`** —
      a *seleção* de techs é determinística (regras F4.1), o Super (F4.2) só refina a redação, então a
      métrica é **idêntica online/offline** e roda 100% no CI (≠ classificador/F7.2, onde o LLM muda a
      predição). **Medido (n=20 in-scope, 97 recomendações):**
      | Recorte | precision | recall | F1 |
      |---|---|---|---|
      | **alvo_graduacao** (a coorte que importa, F6.13) | 0,53 | **0,78** ✅ | 0,63 |
      | periférico / wrapper (AIMI baixo) | ~0,06 | 1,00 | ~0,11 |
      | maduro | 0,08 | **0,17** ❌ | 0,11 |
      | **geral** | **0,23** | **0,69** | 0,34 |

      *Leitura honesta:* **dois lados = 1,0** — o invariante duro (F4.5) vale nas 97 recomendações ✅. O
      **recall onde importa bate a meta** (alvos de graduação 0,78 ≥ 0,70): a graduação
      NIM/TensorRT/Triton **sempre** sai. O recall **geral** (0,69) é puxado pelo **maduro 0,17** — o
      rótulo espera `NVIDIA AI Enterprise` para empresa madura, mas a regra (F4.1) só dispara AI
      Enterprise num **gap de P4**, e madura tem P4 forte → não dispara. A **precision baixa (0,23) é
      super-recomendação**: a regra dispara em todo gap (~5 techs/empresa), os rótulos esperam 0–4 —
      concentra-se nas regiões de AIMI baixo (wrapper/periférico, que esperam ~0). Ambos são **mismatch
      regra↔rótulo a reconciliar na F7.1** (ex.: o rótulo pede `RAPIDS` p/ radiologia, mas a regra —
      corretamente — prescreve Clara/MONAI no domínio de imagem; FN que é, na verdade, rótulo a revisar).
      **Gate verde (offline):** `ruff` limpo e `pytest` **700 passed, 4 skipped** (+7 testes novos; o
      smoke real F0.7 falha à parte por um 500 do NIM hospedado — infra externa, não exercita F7.2b).
- [x] **F7.2c** **Faithfulness do briefing (texto final):** o briefing é o artefato que o gerente
      lê, mas hoje só passa pelo gate binário do Guardrails (F4.5). Medir **fidelidade do texto
      gerado às evidências citadas** (RAGAS faithfulness sobre o briefing, não só sobre o RAG) —
      garante que afirmações/ROI no relatório não extrapolam as fontes. Amostra do eval set (F1.12).
      → `packages\eval\briefing_faithfulness.py` (+ `tests\test_briefing_faithfulness.py`): harness
      irmão de F7.2/F7.2b/F6.4 — reusa a `ragas.faithfulness` (frações de frases ancoradas nos
      contextos) sobre o **briefing** (F4.4). A distinção que dá sentido à métrica: **afirmações =
      os 4 campos que o briefing GERA** (`resumo_executivo` + os 3 eixos do §2 = os `_REFINABLE`, o
      que o Super reescreve); **fontes = o aterramento** (bloco AIMI com justificativas+snippets +
      recomendações com snippets dos 2 lados/F4.3 + os fatos **fixos** do programa Inception e do
      **framework de decisão** `classe × AIMI`/ALINHAMENTO §5/§8 — domínio documentado que a prosa
      *aplica*, não inventa). Os 4 campos **não** entram no próprio contexto (sem circularidade): a
      métrica pega o **net-new** (ROI/cliente/funding alegado fora das fontes). **Tem `--llm`** (≠
      F7.2b): aqui o LLM **muda o texto** (reescreve os 4 campos) → a fidelidade **pode** degradar; o
      scorer é o mesmo proxy nos dois modos, só o texto troca (espinha × Super refinado). `non-AI`
      fora de escopo (F2.13): 20 in-scope, 4 excluídas. **Medido (n=20 in-scope, espinha offline):**
      | Recorte | faithfulness |
      |---|---|
      | **média (gate)** | **0,870** ✅ (≥ 0,80; min 0,786) |
      | `resumo_executivo` (síntese factual) | 0,967 |
      | `acao_comercial` (aplica o framework) | 1,000 |
      | `acao_tecnica` (ancorada na `proxima_acao`) | 0,817 |
      | `acao_comunitaria` (programa Inception) | 0,800 |

      *Leitura honesta:* a **espinha determinista bate a meta** (0,870 ≥ 0,80) porque só **reafirma**
      diagnóstico/recomendações/programa/framework — é fiel **por construção** (anti-alucinação, o
      invariante do projeto); o número offline é o **piso/guard de regressão** do CI (se a espinha
      passar a afirmar algo sem fonte, cai). O valor que **importa medir ao vivo** é o do `--llm` (o
      Super reescreve e pode derivar) — provado nos testes por um adapter `refine` fake: injetar uma
      afirmação sem fonte **derruba** a faithfulness, um refino fiel a **preserva**. A faithfulness
      com **juiz LLM** (lib `ragas` + Nemotron) sobre o briefing é a consolidação da **F7.3** (backend
      `RagasJudge` reservado). **Gate verde:** `ruff` limpo e `pytest` **709 passed, 4 skipped** (+9
      testes; o smoke real F0.7 falha à parte por um 500 do NIM hospedado — infra externa).
- [ ] **F7.3** RAGAS consolidado sobre o conjunto de perguntas NVIDIA.

> **Metas de qualidade (baseline, revisáveis com dados).** Para evitar "qualidade aferida sem
> meta", o relatório (F7.5) reporta cada métrica contra um alvo declarado — número final é o que
> os dados mostrarem, mas o alvo torna o resultado interpretável:
> - **Classificação (F7.2):** macro-F1 ≥ **0,75** no eval set.
> - **AIMI (F7.2/F6.4):** correlação de Spearman ≥ **0,70** com os rótulos de F1.12.
> - **Recomendação (F7.2b):** precision/recall de techs ≥ **0,70**; **100%** das recomendações
>   com evidência dos dois lados (garantido pelo Guardrails F4.5 — meta dura, não estatística).
> - **RAG (F7.3):** RAGAS faithfulness ≥ **0,80**; context recall ≥ **0,70**.
> - **Briefing (F7.2c):** faithfulness do texto final às evidências ≥ **0,80**.
> Metas abaixo do alvo são reportadas como limitação honesta, não escondidas.
- [ ] **F7.4** **Comparativo de reranker: NeMo Retriever vs Cohere Rerank** (qualidade × custo ×
      latência) — aqui entra a Cohere trial key, só nesta fase. **O brief nomeia a Cohere no §5.3**,
      então este comparativo é item de **destaque** no relatório (F7.5): justifica a escolha do
      NeMo no build com dados, não por omissão. Ver `docs/COBERTURA-TECNOLOGIAS.md`.
- [ ] **F7.5** Relatório de avaliação (`docs/AVALIACAO.md`) com resultados versionados.
- [ ] **F7.6** Hardening: tratamento de erro, timeouts, limites de custo de LLM.
- [ ] **F7.7** README final + instruções de reprodução + demo script.

## Tecnologias
RAGAS · Cohere Rerank (validação) · NeMo Retriever · Langfuse.

## DoD
- [ ] Relatório mostra baseline de qualidade + decisão final de reranker com dados (NeMo vs Cohere).
- [ ] Eval da recomendação (F7.2b) reportado, não só os 7 exemplos do §5.5.
- [x] Faithfulness do briefing final medida e reportada (F7.2c), não só o gate do Guardrails.
- [ ] Projeto reproduzível por um terceiro a partir do README.
