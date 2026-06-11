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
- [x] **F3.1d** Ingerir os **materiais de AI-native services do §10.1** (Sequoia "services as
      software", Emergence playbook, NVIDIA "5-layer cake") e marcá-los como **grounding da
      rubrica AIMI**: são eles que definem "AI-native vs wrapper" — origem conceitual dos 4
      pilares (F6.1) e da definição do `classifier` (F2.6). Não são só KB de NVIDIA.
      **Reconciliação:** ao ingerir, revisar `docs/RUBRICA-AIMI.md` (F0.11) contra esses materiais
      e ajustar a *redação* dos pilares se preciso — **sem mexer na escala 0–25** nem invalidar os
      rótulos do eval set (F1.12). Se a reconciliação mudar a semântica de um pilar, anotar no doc.
      → 3 entradas `source_type: grounding` na `section: "10.1"` do manifesto + snapshots curados:
      `sequoia-services-as-software.md` (copiloto × autopiloto / "vender o trabalho"),
      `emergence-ai-native-services-playbook.md` (data flywheel + teste "Mirage PMF") e
      `nvidia-ai-5-layer-cake.md` (a aplicação puxa modelos/infra abaixo). URLs canônicas reais
      (sequoiacap.com / emcap.com / blogs.nvidia.com) confirmadas — proveniência citável como os
      vídeos da F3.1b. **Decisão (tech/loader):** `tech` uniforme `"AI-Native (grounding)"` p/ NÃO
      poluir as techs recomendáveis do §5.4 (`CORE_TECHS`); reusa o loader/`ingest` da F3.1 **sem
      reabri-lo** (tipo `grounding` já previsto em `KBSourceType`, como nas F3.1b/c).
      **Reconciliação feita:** `docs/RUBRICA-AIMI.md` — cada pilar (§§2–5) passou a citar sua fonte
      de grounding (P1↔data flywheel, P2↔autopiloto/"você É a implementação", P3↔5-layer cake/corrida
      contra o modelo, P4↔integração/cunha de mão de obra) e o changelog §7 foi fechado: **semântica
      e escala 0–25 confirmadas intactas** (só ajuste de redação) → rótulos do eval (F1.12) válidos.
      Teste dedicado `test_grounding_materials_ground_the_aimi_rubric` em `tests/test_ingest.py`.
- [x] **F3.2** Limpeza/normalização + **chunking semântico**.
      → `packages/rag/chunk.py`: `normalize_text` (NFC, CRLF→LF, apara espaço à direita,
      colapsa linhas em branco — limpeza determinística e sem perda) + `chunk_document`
      que quebra cada `KBDocument` (F3.1) por **seção de markdown** (`# título`+intro, depois
      cada `## seção`), não por janela cega de N chars: a fronteira do chunk segue a do
      conteúdo (um conceito por chunk, sem cortar frase). Modelo `Chunk` (Pydantic v2,
      `frozen`) **herda a proveniência** do doc-pai (`url`/`tech`/`section`/`source_type`/
      `captured_at`) + ganha `breadcrumb` (caminho de títulos), `content_sha256` próprio
      (reusa `content_hash` da F1.9 → dedup no nível do chunk) e `chunk_id` estável
      (`<doc_id>::<NN>`). `contextual_text` prefixa o breadcrumb ao corpo — é o texto que a
      F3.3 embeda (o trecho sabe a que tech/seção pertence); `text` fica puro p/ citação
      (F3.7). **Decisão (offline/determinístico):** honra a espinha verde da F3.1 — puro,
      sem rede/GPU; seção acima de `max_chars` (1200) degrada repartindo por parágrafo, nunca
      no meio de frase (os docs curados cabem com folga: 24 docs → 74 chunks, máx 1166 chars,
      nada repartido). `chunk_kb()` liga F3.1→F3.2 (ingere + chunkifica a KB inteira). Testes
      em `tests/test_chunk.py` (limpeza idempotente, corte por seção, breadcrumb/contexto,
      proveniência auto-suficiente, IDs únicos/estáveis, split por parágrafo, KB real).
- [x] **F3.3** Embeddings com **NeMo Retriever `nv-embedqa-1b-v2`** (multilíngue).
      → `packages/rag/embed.py`: interface **plugável** `Embedder` (Pydantic `EmbeddedChunk`) com
      `embed_passages`/`embed_query` **assimétricos** (o nv-embedqa distingue `input_type`
      passage×query). Backend **preferido** `NVEmbedQA` = NeMo Retriever `llama-nemotron-embed-1b-v2`
      (2048d; sucessor do `nv-embedqa-1b-v2`, EOL 2026-05-18 — ver settings) via catálogo
      build.nvidia.com (`NVIDIA_API_KEY`) ou NIM self-hosted (GPU). **Decisão (fork
      rede/GPU vs offline):** honra a espinha verde determinística travada desde a F3.1 e o padrão
      dos toggles (`scraper_use_network`/`*_use_llm`): o `NVEmbedQA` é **hook de rede/GPU que
      degrada limpo** (`EmbedderUnavailable` sem credencial/endpoint/dep, igual ao `RivaTranscriber`
      da F3.1b), e o **default é o `HashingEmbedder` offline** — feature hashing L2-normalizado,
      reprodutível entre processos (`hashlib`, não o `hash()` randômico) e com **cosseno
      significativo** (vocabulário compartilhado → mais perto), para F3.4/F3.5 rodarem e serem
      testadas sem rede. Troca por config `embeddings_use_nv` (off por default) ou injeção, sem
      tocar o resto do pipeline (peça plugável). Embeda o `contextual_text` (breadcrumb+corpo,
      decisão da F3.2) e carimba o `model` no `EmbeddedChunk` (proveniência do vetor, §8);
      `embed_kb()` liga F3.1→F3.2→F3.3. Testes em `tests/test_embed.py` (contrato/Protocol,
      determinismo+normalização, cosseno por vocabulário, embedda contextual_text c/ proveniência,
      KB real, e o backend real degradando limpo offline).
- [x] **F3.4** Indexação no **Qdrant** (dense + sparse/BM25).
      → `packages/rag/index.py`: índice **híbrido** dos `EmbeddedChunk` (F3.3) — vetor **denso**
      (nv-embedqa) + vetor **esparso/BM25** lexical — pronto p/ a busca híbrida com fusão (F3.5) e
      a citação (F3.7). **Sparse/BM25 puro e determinístico** `BM25Encoder` (mesma filosofia do
      `HashingEmbedder`/F3.3): `fit` ajusta a coorte (df→idf + comprimento médio), `encode_document`
      gera o vetor BM25 (saturação de tf k1=1.5 + normalização por tamanho b=0.75) e `encode_query`
      o vetor binário — o produto interno reconstrói o score BM25 (como o Qdrant casa esparso×esparso),
      **sem `rank-bm25`**, com id de termo via `hashlib` (reproduzível entre processos). **Decisão
      (fork rede vs offline):** honra a espinha verde travada desde a F3.1 e o padrão dos toggles
      (`embeddings_use_nv`/`scraper_use_network`): o `QdrantVectorIndex` é **hook de rede que degrada
      limpo** (`IndexUnavailable` sem `qdrant-client`/servidor, igual ao `NVEmbedQA`/F3.3) e cria a
      coleção híbrida (vetor nomeado `dense` cosseno + esparso `bm25`) inferindo a dimensão do ponto;
      o **default é o `InMemoryVectorIndex`** — guarda os pontos em memória (upsert idempotente por
      `chunk_id` = dedup, como o `content_sha256` da F3.2) p/ a F3.5 buscar/testar sem subir o Qdrant.
      Troca por config `index_use_qdrant` (off por default) ou injeção, sem tocar o resto (peça
      plugável). **Coleção `tapi_kb` separada da coorte** (F3.10 reusa embedder/Qdrant/reranker em
      coleção à parte). Indexa o `contextual_text` (mesma superfície densa, breadcrumb+corpo → tech/
      seção contam no lexical) e o `payload` carrega a proveniência herdada (url/tech/seção/texto/
      hash + modelo do vetor) — recuperação citável (§8). `build_index()` liga F3.1→F3.2→F3.3→F3.4 e
      devolve (índice, encoder ajustado) p/ a F3.5 reusar o encoder na consulta. Testes em
      `tests/test_index.py` (formato esparso ordenado, determinismo, idf raro>comum, casamento
      lexical, ponto híbrido com proveniência, idempotência, KB real, Qdrant degradando limpo).
- [x] **F3.5** **Busca híbrida** (dense + lexical) com fusão de scores.
      → `packages/rag/retrieve.py`: consulta o índice híbrido (F3.4) combinando o sinal **denso**
      (nv-embedqa/F3.3) com o **lexical/BM25** e **funde os dois rankings** num só, devolvendo
      `RetrievedChunk` com a proveniência herdada p/ citar (§8) — base que o reranker (F3.6)
      reordena e o nó `nvidia_rag` (F3.7) responde. **Fusão por Reciprocal Rank Fusion (RRF)**
      (`_rrf_scores`, k=60): junta pela *posição*, não pelo score bruto — o cosseno denso (∈[-1,1])
      e o BM25 (ilimitado) são escalas incomparáveis, e o RRF é robusto a isso; é o **mesmo método
      default do Qdrant**, então a espinha verde e o backend fundem igual (paridade). **Decisão
      (segue o índice/peça plugável, travada desde a F3.1):** sobre o `InMemoryVectorIndex`
      (default/espinha) a fusão roda em Python lendo `index.points` (a superfície que a F3.4 já
      anunciava); sobre o `QdrantVectorIndex` (dogfood) usa a **Query API nativa** (prefetch denso
      + esparso → `FusionQuery(RRF)`), fundindo no servidor e reusando o `_ensure_client` da F3.4 —
      **hook de rede que degrada limpo** (`IndexUnavailable` sem dep/servidor, como `NVEmbedQA`/F3.3).
      Consulta com o **mesmo embedder** que construiu o índice (`embed_query` assimétrico no
      nv-embedqa; offline o `HashingEmbedder` é determinístico/stateless → vetor comparável aos
      pontos). `HybridRetriever` amarra índice+encoder+embedder e expõe `.search()`; `build_retriever()`
      liga F3.1→F3.5 e devolve o recuperador pronto (offline, reproduzível, sem rede). Testes em
      `tests/test_retrieve.py` (fusão RRF premia o que denso+lexical concordam, recuperação por tech,
      casamento lexical exato, proveniência citável, limite/ordenação, determinismo, índice não
      suportado, e o Qdrant degradando limpo offline).
- [x] **F3.6** Interface `Reranker` plugável; impl. **NeMo Reranking NIM** (default no build).
      → `packages/rag/rerank.py`: reordena os `RetrievedChunk` da busca híbrida (F3.5) pela
      **relevância real consulta×trecho** antes da resposta (F3.7). A F3.5 funde dois sinais *de
      recuperação* por posição (RRF); o reranker é um **cross-encoder** que lê consulta+trecho
      **juntos** e estima a relevância de cada par — sinal mais fino que corrige a ordem grosseira
      da fusão antes de gastar contexto do LLM. **Decisão (fork rede/GPU vs offline):** honra a
      espinha verde travada desde a F3.1 e o padrão dos toggles (`embeddings_use_nv`/`index_use_qdrant`):
      o backend **preferido** `NeMoReranker` = NeMo Reranking NIM `llama-nemotron-rerank-1b-v2`
      (sucessor do `nv-rerankqa-1b-v2`, EOL 2026-05-18 — ver settings) via
      build.nvidia.com (`NVIDIA_API_KEY`) ou NIM self-hosted (GPU) é **hook de rede/GPU que degrada
      limpo** (`RerankerUnavailable` sem credencial/endpoint/dep, igual ao `NVEmbedQA`/F3.3 e ao
      `QdrantVectorIndex`/F3.4), e o **default é o `LexicalReranker` offline** — substituto de
      cross-encoder puramente lexical, reprodutível entre processos, que pontua a cobertura dos
      termos da consulta **ponderada pelo idf local da janela de candidatos** (os termos que
      *discriminam* entre os candidatos pesam mais → sinal distinto do BM25 global da F3.5, então
      reordenar muda a ordem de fato) para a F3.7 rodar/testar sem rede. Troca por config
      (`reranker_use_nv`, off por default) ou injeção, sem tocar o resto (peça plugável). **Provider
      plugável** (`reranker_provider`): `nemo` é o default no build; **Cohere Rerank é da F7**
      (comparativo NeMo×Cohere) — caminho reservado aqui, levanta `RerankerUnavailable` até a F7
      ligá-lo (sem antecipar trabalho de outra fase, conforme a nota do doc). `RerankedChunk` aninha
      o `RetrievedChunk` (proveniência herdada citável, §8) + `rerank_score` e expõe o `retrieval_score`
      (transparência: dá p/ ver o rerank corrigindo a fusão). `rerank()`/`get_reranker()` são a
      superfície que o nó `nvidia_rag` (F3.7) chama. Testes em `tests/test_rerank.py` (contrato/Protocol,
      reordenação preservando proveniência, idf local premia termo distintivo, `top_n`, transparência
      do `retrieval_score`, determinismo, entrada vazia, e o NeMo NIM degradando limpo offline).
- [x] **F3.7** Nó **nvidia_rag** no grafo: retrieve → rerank → resposta **com citações**.
      **Construção da query (esclarecimento):** o nó roda **depois** do classifier/AIMI, então a
      query de recuperação é **derivada dos gaps** — sub-scores baixos do `AIMIScore` (sobretudo
      Technical Optimization) + setor/perfil da startup → termos de busca na KB. Assim o
      `evidencia_nvidia` recuperado já é relevante ao gap que o recommender (F4.2) vai justificar.
      Uma recuperação por gap/tech-candidata (não uma genérica). Liga F3 ↔ F4.
      → `packages/agents/nvidia_rag.py`: 6º nó do grafo (entre evidence_validator/F2.7 e
      recommender/F4). `build_rag_queries` deriva **uma busca por gap** dos pilares baixos do AIMI
      (faixa ausente/emergente, score ≤ 12, menor primeiro, teto `MAX_GAPS=3`) mapeados para a tech
      NVIDIA que fecha cada gap (`PILLAR_QUERIES`: P3→NIM/TensorRT-LLM/Triton/graduação, P1→NeMo/
      customização/data flywheel, P2→agentes/NeMo Retriever, P4→Guardrails/AI Enterprise) **+** uma
      busca de **setor** (§5.5, `SECTOR_QUERIES`: saúde→MONAI/Clara, voz→Riva, cyber→Morpheus,
      robótica→Isaac, simulação→Omniverse) — nada de query genérica. `retrieve_evidence` roda
      retrieve (F3.5) → rerank (F3.6, `top_n` por consulta) por query, dedup por `chunk_id` (mantém
      o maior `rerank_score` + a lista de gaps cobertos), ordena por relevância e corta em
      `MAX_CITATIONS=8`; converte o `RerankedChunk` no `RetrievedChunk` de transporte com
      proveniência citável (§8) + rastreabilidade gap→evidência (`pilar`/`gap`/`gaps` no metadado,
      base do `pilar_origem` da F4.1). **Decisão (espinha verde, igual F2.3–F2.7/F3):** offline/
      determinista por default reusando o pipeline plugável da F3 sem reabri-lo (`build_retriever`/
      F3.5 + `get_reranker`/F3.6); os backends de rede/GPU entram pelos toggles já existentes
      (`embeddings_use_nv`/`index_use_qdrant`/`reranker_use_nv`), sem tocar o nó. Sem `aimi`
      (espinha sem classificação) é **no-op limpo** (`{}`, `retrieved` vazio) — grafo verde M2/DoD
      sem alucinar citação. O **grounding da rubrica** (F3.1d) é filtrado da saída (define o AIMI,
      não é tech recomendável). `get_kb_retriever` (lru_cache) reindexa a KB uma vez por processo
      (KB estática). O nó **não escreve NL** — a "resposta com citações" é a evidência anexada;
      a justificativa é o recommender (F4.2). Testes em `tests/test_nvidia_rag.py` (ordem por
      severidade do gap c/ Technical Optimization, setor saúde→MONAI, fallback ao pilar mais baixo,
      ≥2 citações com proveniência/rastreabilidade, grounding filtrado, dedup, determinismo, no-op
      sem diagnóstico, retriever/reranker injetáveis).
- [x] **F3.8** Cobertura: garantir que TODAS as techs do §5.4 **+ MONAI** estão indexadas e recuperáveis,
      **incluindo NeMo Evaluator/avaliação** (o §5.5 cita "avaliação com NeMo" como recomendação de
      governança — precisa ser recuperável, não só o Guardrails). Teste de recuperação por tech.
      → `tests/test_coverage.py`: fecha o outro lado do M3 — a F3.1/`test_ingest.py` já garante que
      cada tech está **no manifesto**; aqui se garante que cada uma é **recuperável pelo pipeline
      real** (F3.1→F3.5, offline/determinístico via `build_retriever`), não só indexada. **Teste de
      recuperação por tech** parametrizado: uma consulta representativa por tech recomendável (as 17
      do §5.4 + MONAI) e asserção de que ela volta na janela de candidatos (`limit=5`, a que alimenta
      o rerank/F3.6→nó/F3.7) **com proveniência citável** (§8) — todas em rank ≤ 2 na espinha verde,
      com folga real (não top-1 frágil). **Completude amarrada ao manifesto:** o mapa de queries tem
      de coincidir com as techs `source_type: doc` (`test_query_map_covers_every_recommendable_doc_tech`)
      — adicionar uma tech `doc` sem query de recuperação quebra o build (mesma disciplina do
      `CORE_TECHS`/F3.1, agora no nível de recuperação). **NeMo Evaluator/avaliação:** o §5.5 recomenda
      governança como **Guardrails + NeMo** (ver `tasks/04-recomendacao.md`), então o Evaluator estava
      diluído num bullet do chunk "Componentes relevantes" do NeMo (junto de Retriever/Customizer/
      Guardrails/Curator) — **promovido a seção própria** `## NeMo Evaluator (avaliação e governança)`
      em `data/knowledge_base/docs/nvidia-nemo.md` → vira **chunk recuperável dedicado** (F3.2 quebra
      por `##`), e `test_evaluation_governance_retrieves_nemo_evaluator` assevera que uma consulta de
      avaliação/governança o recupera, **não só o Guardrails**. **Decisão (espinha verde, igual F3):**
      só conteúdo curado + teste, **sem reabrir o loader** nem adicionar tech a `CORE_TECHS` (o
      Evaluator é componente do NeMo, não item separado do §5.4); grounding do §10.1 (F3.1d) segue
      fora das techs recomendáveis (`test_grounding_material_is_not_a_recommendable_tech`). Cobertura
      já refletida em `docs/COBERTURA-TECNOLOGIAS.md` (linha "NeMo Evaluator / avaliação" → F3.8).
- [x] **F3.9** **Avaliação RAGAS** (faithfulness, context precision/recall, answer relevancy).
      → `packages/eval/ragas.py`: mede a **qualidade do RAG** (F3.1→F3.7) nas **quatro métricas
      RAGAS** sobre um **conjunto de perguntas NVIDIA versionado** (`data/eval/rag/questions.yaml`,
      7 perguntas com `ground_truth` ancorado no texto da KB curada + `reference_techs` p/ a
      cobertura/F3.8) e grava o **baseline de qualidade versionado** (`data/eval/rag/baseline.json`,
      DoD F3). Fecha o princípio "RAGAS no CI" (ARQUITETURA §8): o smoke da F0.10 deixa de ser
      placeholder — o CI roda `python -m packages.eval.ragas --check` (avalia offline e falha em
      drift contra o baseline). **Decisão (espinha verde, igual F3.1–F3.8 e os nós F2):** o default é
      o `LexicalRagasMetrics` — **proxy lexical determinístico** das 4 métricas por sobreposição de
      tokens de conteúdo (stopwords PT+EN removidas, `hashlib` reprodutível entre processos), sem
      rede/GPU/credencial, seguindo as definições do RAGAS (faithfulness = frações da resposta
      ancoradas nos contextos; answer relevancy = cosseno resposta×pergunta; context precision =
      average precision rank-aware; context recall = cobertura da referência). **Juiz LLM é hook de
      rede que degrada limpo** (como `NVEmbedQA`/F3.3, `QdrantVectorIndex`/F3.4, `NeMoReranker`/F3.6):
      o `RagasJudge` usa a lib `ragas` + juiz Nemotron (catálogo build.nvidia.com) + nv-embedqa e
      levanta `RagasUnavailable` sem dep/credencial/rede; troca por config `ragas_use_llm` (off por
      default) ou injeção. O **run LLM-judged consolidado contra os limiares** (faithfulness ≥ 0,80;
      context recall ≥ 0,70) **é a F7.3** — aqui o backend fica reservado/plugável, sem antecipar o
      trabalho da F7 (mesma disciplina do Cohere Rerank na F3.6). **Harness reusável:** a resposta vem
      de um `answer_fn` injetável; o default é o `compose_extractive_answer` (seleciona dos contextos
      as frases mais próximas da pergunta → fiel por construção), para as 4 métricas rodarem ponta a
      ponta hoje sem depender da geração NL (recommender/briefing, F4, plugam depois sem reabrir o
      harness). Reusa o pipeline plugável da F3 sem reabri-lo (`build_retriever`/F3.5 +
      `get_reranker`/F3.6), filtra o grounding da rubrica (F3.1d, igual ao nó F3.7) e tudo é tipado
      (Pydantic) e rastreável (§8): `RagSample` carrega `ContextCitation` com proveniência, o
      `RagasReport` carimba backend/modelo + hash do dataset. **Baseline offline** (n=7):
      faithfulness=1,0 · context_precision=0,976 · context_recall=0,690 · answer_relevancy=0,542
      (mean=0,802) — pisos de sanidade, NÃO os gates da F7.3. Testes em `tests/test_ragas.py` (as 4
      métricas isoladas, compositor extrativo, harness ponta a ponta sobre a KB real, cobertura por
      tech, grounding filtrado, determinismo byte-a-byte, baseline = run fresco, e o juiz LLM
      degradando limpo offline).
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
- [x] Pergunta sobre tech NVIDIA retorna resposta correta com ≥2 citações.
      → Entregue pelo nó `nvidia_rag` (F3.7, retrieve→rerank→evidência citável) e **medido** na
      F3.9: as 7 perguntas NVIDIA do eval set retornam ≥2 contextos com proveniência citável (§8) e
      faithfulness=1,0 (resposta ancorada) no baseline versionado.
- [x] RAGAS roda e gera baseline de qualidade versionado.
      → F3.9: `python -m packages.eval.ragas` grava `data/eval/rag/baseline.json` e o CI confere
      com `--check` (smoke RAGAS ligado, ARQUITETURA §8).
- [ ] *(stretch)* Cohort-RAG (F3.10) responde consultas sobre a coorte com empresas citadas,
      reusando embedder/Qdrant/reranker da KB.
