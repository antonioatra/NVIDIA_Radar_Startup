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
      + `heuristic_score` (v1) e compara a `classificacao` predita × rotulada. Núcleo puro/offline
      (sem scikit-learn): `accuracy`, `class_prf` (P/R/F1 one-vs-rest), `macro_f1` (média
      não-ponderada sobre classes com suporte — não deixa a majoritária mascarar as raras) e
      `confusion_matrix` (gold→predito, taxonomia inteira). CLI `python -m
      packages.eval.classification_metrics` (exit 1 abaixo do gate §7 macro-F1 ≥ 0,75).
      **Resultado honesto (piso determinístico offline):** macro-F1 **0,38** (accuracy 0,375,
      n=24) — **abaixo** do gate. *Por quê:* AI-native tem recall **0,20** porque `_classify_class`
      exige Workflow Depth > 8 p/ AI-native, e o perfil só-de-descrição **sub-prediz** essa
      magnitude (o **mesmo** limite que o F6.4 documenta p/ o índice: a prosa sem campos
      estruturados rebaixa a maturidade). É o piso do caminho **heurístico/offline**, não do
      classificador de produção (LLM Super, F2.6, `classifier_use_llm`), que não roda no CI. §7
      manda reportar abaixo-do-alvo como **limitação honesta** — feito; a calibração do corte de
      classe é candidata a follow-up (ver nota abaixo). A consolidação dos três (classificação +
      AIMI/F6.4 + 7 casos/F4.8) num relatório único é da **F7.5** (`AVALIACAO.md`).
      **Gate verde (testes):** `ruff` limpo e `pytest` **687 passed, 4 skipped** (10 testes novos:
      accuracy/PRF/macro-F1/confusão com valores conhecidos, validações, e o harness rastreável
      sobre o eval set com `meets_threshold` coerente).
- [ ] **F7.2b** **Eval da recomendação (held-out, não só os 7 exemplos):** sobre o eval set (F1.12),
      medir se as techs NVIDIA recomendadas batem com as esperadas por empresa — precision/recall
      de techs e taxa de recomendação com evidência dos dois lados (F4.3). Fecha a lacuna do
      Entregável 4 ter qualidade aferida só por casos canônicos.
- [ ] **F7.2c** **Faithfulness do briefing (texto final):** o briefing é o artefato que o gerente
      lê, mas hoje só passa pelo gate binário do Guardrails (F4.5). Medir **fidelidade do texto
      gerado às evidências citadas** (RAGAS faithfulness sobre o briefing, não só sobre o RAG) —
      garante que afirmações/ROI no relatório não extrapolam as fontes. Amostra do eval set (F1.12).
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
- [ ] Faithfulness do briefing final medida e reportada (F7.2c), não só o gate do Guardrails.
- [ ] Projeto reproduzível por um terceiro a partir do README.
