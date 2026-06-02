# F7 — Validação Final (transversal / qualidade)

**Objetivo:** consolidar avaliação, comparar rerankers e fechar a qualidade do projeto.
**Dependências:** F3, F4, F6. **Marco:** M7.

## Tasks
- [ ] **F7.1** **Consolidar/expandir** o eval set rotulado criado em **F1.12** (~20–30 startups,
      classificação + AIMI esperados) — revisar rótulos, fechar lacunas. Não cria do zero.
- [ ] **F7.2** Métricas de classificação (accuracy/F1) e correlação do AIMI (consolida F6.4).
      Consolida também os **casos dos 7 exemplos do §5.5 (F4.8)** no relatório de aderência ao brief.
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
