# F3 — RAG NVIDIA com reranking (Entregável 3)

**Objetivo:** base de conhecimento NVIDIA com recuperação híbrida, reranking e citações.
**Dependências:** F0. **Marco:** M3.

## Tasks
- [x] **F3.1** Ingestão das fontes do §10 (docs oficiais, blogs, vídeos transcritos) → `data/knowledge_base`.
      → Espelha as seeds do §9: `data/knowledge_base/sources.yaml` (manifesto — fonte única dos
      metadados: id/tech/url oficial/seção/tipo) + `docs/<id>.md` (snapshot **curado** de cada
      página, texto separado p/ diffs limpos e zero drift). Loader tipado em `packages/rag/ingest.py`:
      `KBSource`/`KBDocument` (Pydantic v2, `frozen`), `load_kb_sources()` valida estrutura/unicidade,
      `ingest()` carimba proveniência (`content_sha256` reusando `content_hash` da F1.9 + `url`) e
      devolve docs prontos p/ o chunking (F3.2); `covered_techs()` serve a cobertura por tech (F3.8).
      **Decisão (fork offline vs rede):** conteúdo curado, **offline e determinístico** (sem
      rede/credencial/GPU, como a espinha verde dos nós F2) — o refresh ao vivo das páginas via
      adapters F1 é hook de rede futuro (a `url` canônica + `captured_at` ficam no manifesto p/
      sustentá-lo), sem antecipar trabalho de outra fase. **Escopo:** §10.2 (17 docs oficiais,
      cobrindo todo o §5.4). Hooks deixados (tipos já previstos em `KBSourceType`, sem reabrir o
      loader): vídeos do §10.1 → F3.1b (`video_transcript`), MONAI → F3.1c, materiais AI-native do
      §10.1 → F3.1d (`grounding`). Testes em `tests/test_ingest.py` (manifesto, proveniência,
      cobertura do núcleo §5.4, determinismo).
- [x] **F3.1b** **Transcrição dos vídeos do §10.1** (playlist de tecnologias, vídeo da comunidade,
      live de benefícios Inception) → texto p/ ingestão. Dogfood do **NVIDIA Riva (ASR)** —
      transforma o Riva de "só recomendável" em tecnologia NVIDIA efetivamente usada pelo TAPI.
      **Fallback de de-risking:** se o Riva NIM não subir a tempo, usar legendas do YouTube ou
      Whisper para a transcrição (a transcrição não é valor central). Preferir Riva pela narrativa,
      mas não deixar o RAG bloqueado pela infra de ASR.
      → Interface **plugável** `Transcriber` em `packages/rag/transcribe.py` (Pydantic `Transcript`/
      `TranscriptSegment`): backend **preferido `RivaTranscriber`** + fallback `YouTubeCaptionTranscriber`/
      `WhisperTranscriber`; `DEFAULT_PREFERENCE` (riva→youtube→whisper) e `transcribe()` que cai de um
      backend p/ o próximo (`TranscriberUnavailable`). **Decisão (fork ASR ao vivo vs offline):**
      honra a F3.1 (curado/determinístico, espinha verde) e o padrão `scraper_use_network` (rede *off*
      por default) — os backends reais são **hooks de rede/GPU** que degradam limpo (testados offline,
      sem travar o CI), e o conteúdo que alimenta o RAG são os **3 snapshots curados** dos vídeos em
      `data/knowledge_base/docs/` (`source_type: video_transcript`, `section: 10.1`, `id` `video-*`),
      citáveis pela `url` canônica do YouTube + `captured_at` (sustentam o refresh via Riva). Reusa o
      loader/`ingest` da F3.1 (tipo já previsto em `KBSourceType`, sem reabrir o loader);
      `transcript_to_markdown` liga o caminho ao vivo ao formato do snapshot. Testes em
      `tests/test_transcribe.py` (contrato tipado, ordem da cadeia, fallback, hooks indisponíveis
      offline, ingestão dos 3 vídeos com proveniência).
- [x] **F3.1c** Incluir **MONAI** na base de conhecimento (citado no §5.5 como alvo de
      recomendação em saúde; sem entrada na KB, o RAG nunca o recuperaria).
      → Entrada `monai` no manifesto (`data/knowledge_base/sources.yaml`) + snapshot curado
      `docs/monai.md` (MONAI Core/Label/Deploy/Model Zoo, FL via NVFlare; quando recomendar em
      saúde). **Decisão (seção/loader):** MONAI é citado no §5.5, **não** no §10, mas tem
      documentação oficial → entra como `source_type: doc` na `section: "10.2"` (a seção "docs"),
      só ADICIONANDO ao manifesto **sem reabrir o loader** (honra o design da F3.1; tipo já
      previsto em `KBSourceType`). `url` canônica `monai.io` + página NVIDIA MONAI em `notes`;
      `access` marca Apache-2.0 / co-liderança NVIDIA+King's College. Recomendável (domínio
      saúde), não dogfooded. Não entra em `CORE_TECHS` (§10.2) — teste dedicado
      `test_monai_is_covered_for_healthcare` em `tests/test_ingest.py` garante que está coberto
      e recuperável (base p/ F3.8).
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
