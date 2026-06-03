# F3 — RAG NVIDIA com reranking (Entregável 3)

**Objetivo:** base de conhecimento NVIDIA com recuperação híbrida, reranking e citações.
**Dependências:** F0. **Marco:** M3.

## Tasks
- [ ] **F3.1** Ingestão das fontes do §10 (docs oficiais, blogs, vídeos transcritos) → `data/knowledge_base`.
- [ ] **F3.1b** **Transcrição dos vídeos do §10.1** (playlist de tecnologias, vídeo da comunidade,
      live de benefícios Inception) → texto p/ ingestão. Dogfood do **NVIDIA Riva (ASR)** —
      transforma o Riva de "só recomendável" em tecnologia NVIDIA efetivamente usada pelo TAPI.
      **Fallback de de-risking:** se o Riva NIM não subir a tempo, usar legendas do YouTube ou
      Whisper para a transcrição (a transcrição não é valor central). Preferir Riva pela narrativa,
      mas não deixar o RAG bloqueado pela infra de ASR.
- [ ] **F3.1c** Incluir **MONAI** na base de conhecimento (citado no §5.5 como alvo de
      recomendação em saúde; sem entrada na KB, o RAG nunca o recuperaria).
- [ ] **F3.1d** Ingerir os **materiais de AI-native services do §10.1** (Sequoia "services as
      software", Emergence playbook, NVIDIA "5-layer cake") e marcá-los como **grounding da
      rubrica AIMI**: são eles que definem "AI-native vs wrapper" — origem conceitual dos 4
      pilares (F6.1) e da definição do `classifier` (F2.6). Não são só KB de NVIDIA.
      **Reconciliação:** ao ingerir, revisar `docs/RUBRICA-AIMI.md` (F0.11) contra esses materiais
      e ajustar a *redação* dos pilares se preciso — **sem mexer na escala 0–25** nem invalidar os
      rótulos do eval set (F1.12). Se a reconciliação mudar a semântica de um pilar, anotar no doc.
- [ ] **F3.2** Limpeza/normalização + **chunking semântico**.
- [ ] **F3.3** Embeddings com **NeMo Retriever `nv-embedqa-1b-v2`** (multilíngue).
- [ ] **F3.4** Indexação no **Qdrant** (dense + sparse/BM25).
- [ ] **F3.5** **Busca híbrida** (dense + lexical) com fusão de scores.
- [ ] **F3.6** Interface `Reranker` plugável; impl. **NeMo Reranking NIM** (default no build).
- [ ] **F3.7** Nó **nvidia_rag** no grafo: retrieve → rerank → resposta **com citações**.
      **Construção da query (esclarecimento):** o nó roda **depois** do classifier/AIMI, então a
      query de recuperação é **derivada dos gaps** — sub-scores baixos do `AIMIScore` (sobretudo
      Technical Optimization) + setor/perfil da startup → termos de busca na KB. Assim o
      `evidencia_nvidia` recuperado já é relevante ao gap que o recommender (F4.2) vai justificar.
      Uma recuperação por gap/tech-candidata (não uma genérica). Liga F3 ↔ F4.
- [ ] **F3.8** Cobertura: garantir que TODAS as techs do §5.4 **+ MONAI** estão indexadas e recuperáveis,
      **incluindo NeMo Evaluator/avaliação** (o §5.5 cita "avaliação com NeMo" como recomendação de
      governança — precisa ser recuperável, não só o Guardrails). Teste de recuperação por tech.
- [ ] **F3.9** **Avaliação RAGAS** (faithfulness, context precision/recall, answer relevancy).
- [ ] **F3.10** *(stretch)* **Cohort-RAG (recuperação sobre a coorte de startups):** índice de
      busca sobre a **tabela `company` acumulada** (F1.14) + perfis/evidências — **distinto** da KB
      NVIDIA (F3.1), mas **reusa** o mesmo embedder `nv-embedqa` (F3.3), o Qdrant (F3.4, coleção
      separada), a busca híbrida (F3.5) e o reranker (F3.6). Um nó **Nemotron** extrai filtros
      estruturados da pergunta (setor, faixa de AIMI, sub-scores, tech) **+** faz busca semântica →
      empresas com **citação à evidência**. Serve o chat de descoberta da UI (F5.12); Guardrails
      garante que nenhuma empresa é retornada sem fonte (princípio nº1).

> Cohere Rerank: **não** aqui. Entra na F7 como comparativo. Ver `docs/COBERTURA-TECNOLOGIAS.md`.

## Tecnologias
NeMo Retriever (embed + rerank NIM) · Qdrant · BM25 · RAGAS · PostgreSQL · **Riva (ASR p/ transcrição)**.

## DoD
- [ ] Pergunta sobre tech NVIDIA retorna resposta correta com ≥2 citações.
- [ ] RAGAS roda e gera baseline de qualidade versionado.
- [ ] *(stretch)* Cohort-RAG (F3.10) responde consultas sobre a coorte com empresas citadas,
      reusando embedder/Qdrant/reranker da KB.
