# F3 — RAG NVIDIA com reranking (Entregável 3)

**Objetivo:** base de conhecimento NVIDIA com recuperação híbrida, reranking e citações.
**Dependências:** F0. **Marco:** M3.

## Tasks
- [ ] **F3.1** Ingestão das fontes do §10 (docs oficiais, blogs, vídeos transcritos) → `data/knowledge_base`.
- [ ] **F3.2** Limpeza/normalização + **chunking semântico**.
- [ ] **F3.3** Embeddings com **NeMo Retriever `nv-embedqa-1b-v2`** (multilíngue).
- [ ] **F3.4** Indexação no **Qdrant** (dense + sparse/BM25).
- [ ] **F3.5** **Busca híbrida** (dense + lexical) com fusão de scores.
- [ ] **F3.6** Interface `Reranker` plugável; impl. **NeMo Reranking NIM** (default no build).
- [ ] **F3.7** Nó **nvidia_rag** no grafo: retrieve → rerank → resposta **com citações**.
- [ ] **F3.8** Cobertura: garantir que TODAS as techs do §5.4 estão indexadas e recuperáveis.
- [ ] **F3.9** **Avaliação RAGAS** (faithfulness, context precision/recall, answer relevancy).

> Cohere Rerank: **não** aqui. Entra na F7 como comparativo. Ver `docs/COBERTURA-TECNOLOGIAS.md`.

## Tecnologias
NeMo Retriever (embed + rerank NIM) · Qdrant · BM25 · RAGAS · PostgreSQL.

## DoD
- [ ] Pergunta sobre tech NVIDIA retorna resposta correta com ≥2 citações.
- [ ] RAGAS roda e gera baseline de qualidade versionado.
