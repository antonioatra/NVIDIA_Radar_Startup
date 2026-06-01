# F7 — Validação Final (transversal / qualidade)

**Objetivo:** consolidar avaliação, comparar rerankers e fechar a qualidade do projeto.
**Dependências:** F3, F4, F6. **Marco:** M7.

## Tasks
- [ ] **F7.1** Eval set rotulado (~20–30 startups) com classificação + AIMI esperados.
- [ ] **F7.2** Métricas de classificação (accuracy/F1) e correlação do AIMI.
- [ ] **F7.3** RAGAS consolidado sobre o conjunto de perguntas NVIDIA.
- [ ] **F7.4** **Comparativo de reranker: NeMo Retriever vs Cohere Rerank** (qualidade × custo ×
      latência) — aqui entra a Cohere trial key, só nesta fase.
- [ ] **F7.5** Relatório de avaliação (`docs/AVALIACAO.md`) com resultados versionados.
- [ ] **F7.6** Hardening: tratamento de erro, timeouts, limites de custo de LLM.
- [ ] **F7.7** README final + instruções de reprodução + demo script.

## Tecnologias
RAGAS · Cohere Rerank (validação) · NeMo Retriever · Langfuse.

## DoD
- [ ] Relatório mostra baseline de qualidade + decisão final de reranker com dados.
- [ ] Projeto reproduzível por um terceiro a partir do README.
