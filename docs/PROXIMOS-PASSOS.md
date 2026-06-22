# Próximos passos para fechar o TAPI

> **Estado em 2026-06-17.** O núcleo testável dos 7 entregáveis está feito. As metas do §7 batem nas
> **24 fixtures**; com as **8 reais curadas** (F7.1) no headline, o **AIMI volta a passar (0,705 ≥ 0,70)**
> ao pontuar a real sobre a **evidência raspada completa** (lever F7.1, não a descrição de 1 linha); só a
> classificação (0,72) segue logo abaixo (AI-enabled n=6). A recomendação melhora — detalhado em
> [AVALIACAO.md](AVALIACAO.md). **Frente de profundidade B (chat premium) entregue (2026-06-17):** busca
> semântica de texto livre + citação por empresa no `/discover`. Tudo que resta abaixo é
> **stretch gated por recurso** (volume de coorte, GPU, dependência ou chave externa), **não** código de
> base faltando. Este documento detalha cada frente: estado real, o que falta, os passos e o bloqueio.

## Visão geral

| # | Frente | Estado | Bloqueio real | Esforço | Prioridade |
|---|---|---|---|---|---|
| A | **Validar a stack + chat ao vivo** | ✅ **validado ao vivo** (coorte real + radar coerente + consulta resiliente) | — | feito | ✅ |
| B | **Chat "premium" (F3.10/F5.12)** | ✅ **busca semântica + citação entregues** (SSE adiado) | Volume amplia o ganho | feito (core) | Média |
| C | **Radar de coorte — qualidade p/ demo (F6.7+)** | (a)(b)(d) ✅ ao vivo; falta só **(c) ★** | AIMI gated por evidência (créditos) | ~créditos | **Alta (demo)** |
| D | **GPU Graduation Engine (F6.8–F6.12)** | Engine + ROI no produto (UI + **texto do briefing**) ✅; falta só medição real | Endpoint NIM grátis congestionado (ver §D) | ~medição | Média/Baixa |
| F | **Recursos externos (F7.3, F7.4)** | Degradam limpo | Chave / dep | ~1–2 h cada | Baixa |

> **Já entregue (fora do escopo de próximos passos):**
> - **E** — Eval real → ground-truth (F7.1), 8/9 reais curadas a `human` no headline (commit `13cdc48`).
> - **A** — **validação ao vivo (2026-06-16):** coorte real construída (`cohort.db`, 10 empresas com
>   perfil + AIMI + 41 recs), stack no ar (`run.ps1`), `/radar` + `/coorte` + `/radar/[id]` navegáveis.
> - **Consulta resiliente (F5.3+)** — o run sobrevive a sair/voltar da tela (`GET /runs/{id}/status` +
>   localStorage; ver §A).
> - **C-a/C-b/C-d** — radar **coerente ao vivo**: descrição no embedding, `nv-embedqa` (com degradação
>   p/ hashing), nomes honestos e `k` default ajustado. Par de identidade (Unico+Idwall) agora junto.
>   Só o **★ (C-c)** segue gated por evidência (créditos).
> - **B** — **chat premium / cohort-RAG (2026-06-17):** `/discover` ganhou busca **semântica** de texto
>   livre (setor/domínio que o vocabulário não cobre) + **citação de evidência por empresa**, cosseno em
>   memória (offline determinístico + nv-embed atrás de flag). SSE/reranker/índice dedicado adiados (§B).

**Caminho mínimo para "fechar e demonstrar":** ~~A~~ ✅ → ~~B (chat premium)~~ ✅ **feito**.
**Caminho completo:** ~~A~~ ✅ → ~~B~~ ✅ → D → F. **Restam:** C-c (★, créditos), D (medição real,
gated por GPU) e a F opcional.

---

## A. Validar a stack e o chat ao vivo  *(✅ FEITO — 2026-06-16)*

**Estado.** ✅ **Validado ao vivo.** A coorte real foi construída (`cohort.db`, 10 empresas com perfil
+ AIMI + 41 recomendações), a stack subiu (`run.ps1`) e `/radar` + `/coorte` + `/radar/[id]` estão
navegáveis com dados reais. As flags do caminho real ficam na `.env` (`SCRAPER_USE_NETWORK`,
`EXTRACTOR_USE_LLM`, `CLASSIFIER_USE_LLM`, `RECOMMENDER_USE_LLM`, `BRIEFING_USE_LLM`, `EMBEDDINGS_USE_NV`;
Langfuse off no build em lote). **`INDEX_USE_QDRANT` fica off** — a coleção da KB é 256-dim e o
`nv-embedqa` é 2048; o RAG ao vivo do recommender exigiria **re-indexar a KB em 2048** (item aberto,
abaixo). As recs servidas hoje vêm **persistidas** do build, não do RAG ao vivo.

**O que falta.** Nada para a demo navegável. *(Os passos abaixo ficam como runbook de reprodução.)*

**Passos (runbook).**
1. Gerar a coorte real (run ao vivo, ~10–15 min, usa créditos build.nvidia.com):
   ```powershell
   # .env com NVIDIA_API_KEY, TAVILY_API_KEY, FIRECRAWL_API_KEY
   python -m packages.agents.cohort --seed --db sqlite:///data/cohort.db
   ```
2. Subir a stack completa e abrir a UI:
   ```powershell
   .\scripts\run.ps1     # up --build → alembic → seed_postgres → abre o navegador
   ```
3. Conferir em `localhost:3000`:
   - `/radar` lista as empresas ordenadas por Inception Priority.
   - `/descoberta` responde aos exemplos ("gap de inferência", "AI-native maduras", "TensorRT", "AIMI acima de 40").
   - `/radar/[id]` abre o detalhe AIMI (4 pilares + evidências) e as recomendações.
4. Tirar 3–4 screenshots para o material do case (radar, chat com resposta, detalhe AIMI).

**Bloqueio.** Nenhum. **Resultado.** Demo navegável de ponta a ponta com dados reais.

> ✅ **Entregue nesta sessão — consulta resiliente a sair/voltar da tela (F5.3+).** A consulta
> longa já rodava no worker (F2.10) e **sobrevivia** à navegação; o que faltava era a UI
> reencontrá-la. Agora `GET /runs/{id}/status` (combina o status do **job RQ** — autoritativo p/
> "ainda rodando" — com o checkpoint F2.2) diz à UI a fase do run sem pendurar no SSE, e o console
> guarda o run em andamento (localStorage, TTL 12 h): ao voltar, **rodando** → reabre o stream;
> **pausado/terminado** → hidrata o desfecho + a escada de nós do trace (o pub/sub não reentrega o
> que passou); **falhou/órfão** → descarta. Testes: `test_run_status_*` (5 fases) + tsc/eslint
> verdes. Por que importava: a coleta+LLM demora, e fechar a aba dava a impressão de perder o run.

---

## B. Chat "premium" — cohort-RAG semântico (F3.10/F5.12)  *(✅ core entregue — 2026-06-17)*

**Estado.** ✅ **Busca semântica + citação por empresa entregues** (`packages/agents/cohort_rag.py`).
O `/discover` agora faz **dois estágios honestos**: (1) `parse_query` recorta *quem entra* pelos
filtros estruturados (tech NVIDIA / classe / piso de AIMI — inalterado); (2) `rank_discovery` decide
*como ordenar* — se a pergunta traz **texto livre** que o vocabulário não cobre (`residual_query`
não-vazio: setor/domínio como "fraude", "agro", "healthtech") **re-ordena por similaridade
semântica** e **cita a evidência** que sustenta cada match; senão mantém a ordem por Inception
Priority (comportamento anterior preservado). Fecha o gap documentado **"setor/região livre"** + a
**citação por empresa no chat**. A UI mostra o chip "busca semântica", a relevância por cartão e a
fonte citada (link externo) abaixo de cada empresa.

**Disciplina (espinha verde).** Cosseno em **numpy, em memória** (espelha o radar de coorte F6.5) —
**não toca o Qdrant**, logo **sem** o conflito 256×2048 do índice da KB. Offline = `HashingEmbedder`
determinístico (CI); `embeddings_use_nv` liga o `nv-embedqa` real. Testes: `test_cohort_rag.py` (14)
+ `test_api.py::test_discover_modo_{filtro,semantico}` — verdes offline (hashing) **e** com nv-embed.

**O que ficou adiado (honesto):**
- **Streaming SSE** — a parte cara (Next.js 16 + reuso do canal do console F5.3) e a que **menos
  agrega a n≈10**; o `fetch` único responde rápido. Adiado de propósito, não meio-feito. Quando
  fizer: trocar o `fetch` do `chat.tsx` por `EventSource` (padrão do `console.tsx`).
- **Reranker NeMo no caminho do chat** — o cosseno + a citação léxica bastam na escala atual; o
  reranker (F3.6) entra quando a coorte crescer (o ganho de reordenar só aparece com dezenas+).
- **Índice Qdrant dedicado da coorte** — desnecessário enquanto o cosseno em memória cobre dezenas;
  vira a opção de escala (junto com re-indexar a KB em 2048, item §C) quando o volume justificar.

**Bloqueio restante.** Nenhum para o core; **volume de coorte só amplia o ganho** (com mais empresas
o ranking semântico e o reranker brilham mais). **Decisão:** o premium está entregue como capacidade
real e testada; SSE/reranker/índice dedicado seguem como evoluções de escala, não dívida de base.

---

## C. Radar de coorte — qualidade para demo *(reaberto após feedback técnico, 2026-06-15)*

**Estado.** ✅ **(a)(b)(d) feitos e validados ao vivo (2026-06-16)** — o radar de `/coorte` mostra
clusters **coerentes** sobre a coorte real (par de identidade Unico+Idwall junto, par de dados
Cortex+Aquarela). Resta **só (c)** — o ★ — gated por evidência (créditos). Detalhe por item:

- **(a) O texto do clustering ignorava a descrição** — ✅ **feito.** `CohortPoint` agora carrega
  `company.descricao` (`load_cohort_points`) e `text()` a inclui (encurtada por `_DESC_CHARS` p/ não
  dominar o bag-of-words). Clusteriza-se o que a empresa **faz**, não a *string do setor* — o maior
  dreno de coerência. Testes: `test_text_includes_descricao`.
- **(b) Embeddings hashing-offline** (default da espinha verde) não têm semântica — ✅ **resolvido
  por flag.** Ligar `nv-embedqa` (`embeddings_use_nv`) no radar **basta**: o clustering é numpy em
  memória, **não** toca o Qdrant, então **não há** o conflito de dimensão (256×2048) que aparece só
  no RAG do recommender (`index_use_qdrant`, esse sim gated). Validado sobre o `cohort.db` real (10
  empresas): com nv-embedqa o par de identidade (Unico+Idwall) e o de dados (Cortex+Aquarela) se
  separam; com hashing grudavam por token ("Tecnologia de…"). **+ k default ajustado** (`_suggested_k`:
  `n//3` → ~`n/2`, teto 8) — `k=3` era grosseiro p/ 10 domínios distintos. Teste: `test_suggested_k_*`.
- **(c) "Prontas ★ = 0%" + AIMI baixo (31–43)** — mesma causa raiz dos outliers do eval (Unico/Kunumi):
  o AIMI de produção é **gated por evidência** (RUBRICA §0: sub-score > 6 exige citação) e o scrape
  por-empresa é raso → o Nemotron (corretamente) não sobe P1/P4 sem fonte. **Fix honesto:** coletar
  **mais evidência por empresa** (mais fontes Tavily/Firecrawl) e re-pontuar — **não** afrouxar a
  rubrica (isso alucina). Conferir Gupy/Idwall/Unico caindo em `alvo_graduacao ★` depois. *(gated: créditos)*
  → **CAUSA-RAIZ CORRIGIDA (2026-06-18): era ANCORAGEM DO PROMPT, não falta de evidência.** A
  hipótese "mais evidência" foi **testada e falsificada**: a flag `scrape_deep_evidence` (consultas
  por pilar + mais fontes/docs) rodou ao vivo (`cohort_deep.db`) e os pilares **não se moveram** —
  Gupy ganhou 0→11 clientes citados e seguiu `12/9/6/15`; o `max_docs=9` ainda **estourou o teto F7.6**
  e derrubou Hand Talk/Idwall por timeout. O `12/9/6/15` plano vinha do **exemplo JSON do
  `classifier.md`**, que trazia literalmente `data_moat:12, workflow:9, tech:6, dist:15` — o Super
  (reasoning) escrevia justificativa diferenciada mas **copiava os números do exemplo** (few-shot
  anchoring), e o prompt **não tinha âncoras de banda** p/ mapear evidência→score. **Fix (`classifier@v3`):**
  âncoras de banda (0–6 ausente · 7–12 emergente · 13–18 estabelecido · 19–25 forte+≥2 fontes) +
  nota "não copie os números do exemplo" + exemplo diferenciado. **Validado A/B ao vivo** (mesma
  fixture rica): `eval-alvo-01` data_moat **12→16** (rótulo humano 20), workflow 9→10; o wrapper raso
  **fica em 6** (sem inflar — o gate §0 segura). **C-c FECHADA (2026-06-20):** coorte re-rodada com v3
  (scrape raso) e **★ adotado (0→3: Semantix/Unico/Aquarela)**, Postgres reseed + api/worker rebuild,
  confirmado ao vivo.
  → **Polish (2026-06-20):** (1) o **dead-end `scrape_deep_evidence` foi revertido** (revert de
  `9498a93`) — ele não movia os pilares e carregava a regressão latente de timeout `max_docs=9`; a coorte
  roda **raso** por padrão. (2) As âncoras de banda v3 também levantaram o **P3 (`technical_optimization`)**,
  que ficou ruidoso (swings por run: Idwall 6→15, Aquarela 15→7) e disqualificava alvos AI-native fortes
  do ★ (alvo de graduação = P3 baixo). **Fix (`classifier@v4`):** trava de P3 no prompt — fica em 0–6 a
  menos que haja evidência citada **explícita** de stack de inferência própria (self-host/serving p.ex.
  Triton/TensorRT/vLLM/NIM, fine-tuning, quantização/batching em produção); consumir API externa crua
  mantém P3 baixo de propósito (espelha `RUBRICA-AIMI.md §4`). **Coorte re-rodada com v4 e ADOTADA ao
  vivo (2026-06-20):** P3 caiu p/ a banda Ausente em toda a coorte (Idwall 15→5, Gupy 16→5, Kunumi
  18→0, Pareto 18→0), **0 timeouts** (scrape raso não estoura o teto F7.6) e o **★ passou a Idwall +
  Neurotech + Semantix** — o Idwall (que o P3=15 disqualificava) graduou, exatamente o alvo do fix.
  Postgres reseed + api/worker rebuild, confirmado em `/cohort/clusters`. **Caveat do draw:** este
  scrape regrediu por ruído de evidência (não P3) Pareto (60→0, ev=4, gate §0 segurou), Unico
  (AI-native→AI-enabled) e Aquarela (data_moat 13→8, perdeu ★) — variância inerente do scrape raso, não
  do prompt; uma re-rodada futura pode recuperá-los (créditos).
- **(d) Nome do cluster por setor dominante** (`label = setor_dom`) — ✅ **feito.** `_cluster_label`
  só usa o setor quando ele domina (≥60% dos membros, `_LABEL_DOMINANT_SHARE`); abaixo disso nomeia
  pela **mistura** (top-2 setores, ex.: `fintech · healthtech`) em vez de mentir com um só. Empate
  desempatado por ordem alfabética (determinístico). Testes: `test_cluster_label_{dominant_sector,heterogeneous}`.

**Sequência:** ~~(a)+(d) [código grátis]~~ ✅ → ~~(b) [flag `embeddings_use_nv` + k default]~~ ✅ → (c)
[re-run da coorte com mais fontes, **créditos**]. **Bloqueio restante:** só (c) — mais evidência por
empresa p/ calibrar o ★ (AIMI gated por evidência, RUBRICA §0). **Esforço restante.** ~créditos da coorte.

**Itens abertos descobertos na validação ao vivo (2026-06-16):**
- ~~**Re-indexar a KB do RAG em 2048 dims**~~ ✅ **feito (2026-06-21)** — `scripts/reindex_kb.py`
  dropa a coleção `tapi_kb` (256, hashing) e a reconstrói em **2048** embedando a KB com o
  `nv-embedqa` real (75 pontos). Smoke ao vivo: `EMBEDDINGS_USE_NV=true INDEX_USE_QDRANT=true` →
  `build_retriever().search(...)` recupera com **citação** (TensorRT-LLM score 1.0, URLs reais),
  sem o antigo `Vector dimension error 256≠2048`. **Agora dá p/ ligar `INDEX_USE_QDRANT=true`** e ter
  o recommender RAG ao vivo com citação (as recs servidas hoje seguem **persistidas** do build, o que
  basta p/ a demo; o caminho ao vivo fica destravado). *Caveat de custo:* `build_retriever()` re-embeda
  a KB no nv-embedqa a cada chamada — com Qdrant ligado, cada run gasta ~créditos (75 chunks); ok p/ demo.
- ~~**Cosmético (1 linha):** `_dominant` desempata classe por ordem de inserção~~ ✅ **feito
  (2026-06-16)** — num cluster 1×1 (ex.: Unico non-AI + Idwall AI-native) o `classe_dominante`
  desempata agora pela classe **mais madura** (AI-native > AI-enabled > non-AI, `_CLASSE_MATURITY`),
  mais fiel ao DSS (e não suprime a prontidão ★); a frequência ainda manda quando há maioria. Testes:
  `test_classe_dominante_{breaks_tie_by_maturity,frequency_beats_maturity}`.

---

## D. GPU Graduation Engine (F6.8–F6.12) — a maior fatia, **e não precisa ser paga**

### "É pago?" — esclarecendo o bloqueio

**Não para o que o case precisa.** As ferramentas do engine são **gratuitas e open-source**:
**TensorRT-LLM**, **Triton Inference Server**, **vLLM** (fallback) e **RAPIDS/cuDF/cuML** rodam
na sua **GPU local** sem licença. O que é pago é a **NVIDIA AI Enterprise** (suporte/SLA de
produção para NIM) — **desnecessária** para gerar a matriz de benchmark e o ROI de um case. O
build.nvidia.com (Nemotron) já roda em créditos grátis. Resumo:

| Componente | Custo | Necessário para fechar? |
|---|---|---|
| TensorRT-LLM / Triton / vLLM (serving otimizado) | **Grátis (OSS)** | Sim (ou fallback vLLM) |
| RAPIDS / cuDF / cuML | **Grátis (OSS)** | Clustering de coorte (stretch GPU; CPU já entregue) |
| NIM self-hosted (NGC dev tier) | Grátis para dev | Opcional (vLLM substitui) |
| NVIDIA AI Enterprise (NIM produção) | **Pago** | **Não** |

Ou seja: o bloqueio real é **montar e medir na sua GPU** (esforço/risco), não dinheiro.

### Estado no código  *(atualizado 2026-06-14 — engine construído, gated por flag)*

O engine de ROI **já foi construído** (commit do F6.9–F6.11): `packages/benchmark/matrix.py`
(matriz + cost model + `roi_for` → `ROIEstimate`), o nó `gpu_benchmark` (antes stub) anexa o ROI às
recs de graduação **atrás de `GPU_BENCHMARK_USE_MATRIX=true`** (no-op por padrão = espinha verde), e
o downstream (persist → API → UI `RoiStrip`) já consumia. **Decisão tomada (host grátis + on-
narrative):** o lado otimizado é o **NIM hospedado no build.nvidia.com** (créditos grátis = TensorRT-
LLM+Triton de verdade), não self-host em 4 GB. **Só falta a medição real:** rodar
`python scripts/bench_nim.py --tier medium` (sua `NVIDIA_API_KEY`) — ele mede o NIM e grava a célula
com `is_live_run=true`. A matriz versionada (`data/benchmark/matrix.json`) é **ilustrativa** até lá.

> **Medição tentada (2026-06-16) — endpoint grátis congestionado, não gravado.** A chave funciona,
> mas o tier grátis do build.nvidia.com está saturado: uma chamada curta (16 tokens) levou **227 s**,
> e cada chamada do `bench_nim.py` estoura o teto de 180 s. Gravar isso daria throughput **~0,07 tok/s**
> (dominado pela fila, **mais lento que o baseline**) — um número desonesto sobre o NIM. Decisão
> coerente com o princípio de proveniência da `matrix.py` ("nada aparece como medido enquanto não
> for"): **não gravei**; a matriz segue ilustrativa (`is_live_run=false`, rótulo explícito). Re-tentar
> quando o endpoint estiver menos carregado (ou apontar `--model` para um NIM dedicado).

**O que você precisa fazer (passos):**
1. `python scripts/bench_nim.py --tier medium` (mede o Nemotron-Nano-8B hospedado; opcional `--tier large --model ...super-49b...`).
2. Ajustar o lado **baseline** da célula no `matrix.json` para o preço/latência da API externa que a startup-alvo usa hoje (o número de comparação).
3. Rodar um run com `GPU_BENCHMARK_USE_MATRIX=true` → o ROI aparece no cartão da UI (`/radar/[id]`).
4. ~~*(Opcional)* Adicionar a linha de ROI numérica no **texto** do briefing~~ ✅ **feito (2026-06-16)** — `_rec_lines` (Markdown) + `render_pdf` cravam o ROI (throughput/custo/p95 + `baseline → otimizado` + proveniência `medido ao vivo`×`matriz de benchmark` + fonte) com paridade ao `RoiStrip` da UI; degrada limpo sem `rec.roi`. Testes: `test_render_{markdown,pdf}_*roi*`.

### O que falta

- **F6.8** Servir 1–2 modelos via Triton + TensorRT-LLM (ou vLLM) na GPU local, **ad-hoc** (fora do compose base).
- **F6.9** Gerar a **matriz de benchmark** (tamanhos × workloads): tokens/s, p50/p95, throughput.
- **F6.10** Estimador de custo: $/1M tokens self-hosted vs API externa.
- **F6.11** Mapear perfil da startup → célula da matriz → **ROI no briefing**.
- **F6.12** *(stretch do stretch)* Botão "run ao vivo" (1 modelo) para a demo.

### Caminho de menor risco (MVP, decisão já travada nos docs)

A matriz é **pré-computada uma vez** e armazenada — o "run ao vivo" nunca é caminho crítico.

**Passos.**
1. Subir o serving otimizado na GPU local (começar por **vLLM**, que é o mais simples; TensorRT-LLM/Triton se sobrar tempo).
2. `notebooks/benchmark_matrix.ipynb`: medir baseline (API externa) × otimizado (local) em 2–3 tamanhos de prompt/lote; salvar em `data/benchmark/matrix.json`.
3. `packages/benchmark/matrix.py`: carregar a matriz + mapear `perfil → célula → ROIEstimate`.
4. Preencher o nó `gpu_benchmark` (hoje stub) para anexar o `ROIEstimate` às recomendações de graduação (NIM/TensorRT/Triton).
5. Conferir a linha de ROI aparecendo no briefing (Markdown + PDF) e no cartão da UI (`ROIOut`).

**Bloqueio.** GPU local (você tem) + tempo de montar o serving. **Esforço.** ~3–6 dias conforme
quão fundo no Triton/TensorRT-LLM você for. **Fallback honesto:** se o self-host travar, medir o
lado otimizado com vLLM e/ou números de referência citados — comparação API × self-hosted
rastreável, com a limitação anotada.

---

## F. Recursos externos (degradam limpo — baixa prioridade)

- **F7.4 — Cohere Reranker.** ✅ **fechado (Cohere medido 2026-06-16; head-to-head nv-embed
  2026-06-21).** O comparativo `packages/eval/reranker_comparison.py` mede NeMo×Cohere×léxico nos
  **dois substratos**: offline (NeMo 0,823 > Cohere 0,816) e **nv-embed ao vivo** (Cohere 0,864 ≳
  NeMo 0,859, cr idêntico 0,88) — qualidade **empatada no ruído de n=7** nos dois; a decisão **NeMo
  (grátis)** fica justificada com dados. Rodar: `EMBEDDINGS_USE_NV=true INDEX_USE_QDRANT=true python -m
  packages.eval.reranker_comparison --nv --cohere`. Detalhe em [AVALIACAO.md §6](AVALIACAO.md).
- **F7.3 — Juiz LLM da RAGAS.** ✅ **import destravado (2026-06-16).** A causa era o `ragas 0.4.3`
  importar `langchain_community.chat_models.vertexai.ChatVertexAI`, caminho **removido** no
  `langchain-community 0.4.x` (o `ChatVertexAI` migrou p/ `langchain-google-vertexai`). Como o `ragas`
  só usa essa classe num `isinstance` e o juiz aqui é o **Nemotron** (nunca VertexAI), o
  `_ensure_ragas_importable` (`packages/eval/ragas.py`) registra um **stub em `sys.modules`**
  (idempotente; só age se o caminho real faltar) — sem mexer no `langchain` 1.x do projeto nem puxar
  a dep do Google. Testes: `test_ensure_ragas_importable_unblocks_lib` + `degrades_clean_offline`
  ajustado (degrada por credencial, sem rede). **Resta** o run consolidado contra os limiares (§7):
  *gated pelo LLM endpoint* (mesmo congestionamento). O proxy léxico segue cobrindo a métrica offline.

---

## G. Rótulo priorizado — eval de recomendação com granularidade de prioridade (F7.7)

> **Aberto 2026-06-22.** É a **Limitação nº2** do [AVALIACAO.md](AVALIACAO.md) tirada da gaveta: o
> teto honesto que sobrou da de-circularização (21/06). É a **única frente que avança 100% com
> teclado** — C-c (draw), D (medição GPU) e o juiz RAGAS estão todos *gated por crédito/GPU/endpoint*.
> Não muda o recommender; alinha **rótulo + métrica** ao que a regra já produz.

**Motivação.** A métrica de recomendação (F7.2b, `recommendation_metrics.py`) pontua **presença**
(TP/FP/FN por substring, micro-agregado). Isso teta a precision do recorte **maduro em 0,21**: o
§5.5/F4.8 **exige** que a regra abra o leque (gate 7/7), mas o rótulo de uma madura é estreito
(domínio + AI Enterprise) → as techs legítimas de baixa prioridade entram como FP. **Capar a regra
não é o conserto** (os 7 casos exigem o leque). O conserto é medir **prioridade**, não só presença.

**Meia-máquina já existe.** Cada `Recommendation` já sai com `prioridade` ALTA/MÉDIA/BAIXA
(`recommend_rules.py:60`, enum `Priority`); quem é chapado é o **rótulo** (`expected_nvidia_techs:
list[str]`, `dataset.py:98`) e a **métrica**. O lever é tipar o rótulo e tornar a métrica
prioridade-aware — sem tocar a seleção de techs.

**Métrica (decisão 2026-06-22): Tiered, com headline knob-free.**
- **Headline = `recall@ALTA`** — das techs marcadas ALTA no rótulo (a alavanca que importa), quantas
  a regra produziu como ALTA/MÉDIA. **Binária, sem peso nem tolerância** → não há botão a tunar
  (a lição de circularidade de 21/06).
- **Precision tolerante = diagnóstico, AO LADO da de presença (0,56), nunca no lugar dela.** Ignora
  como FP o que a **própria regra** emitiu como BAIXA (sinal da regra, independente do rótulo) — um
  "considere também" não é FP duro. A de presença segue visível: ganha-se leitura, não se apaga o
  número honesto. (Ponderada `3/2/1` e NDCG/Spearman descartadas: pesos são botões; rank de ~5 techs
  em n=7 é ruído.)

**Risco nº1 — circularidade (o que mordeu em 21/06).** A prioridade do rótulo vem do **gap binding
do perfil** (qual pilar é a restrição) + §5.5, **nunca** lida da `prioridade` que a regra emitiu.
Documentar por entrada no `notes`, igual à de-circularização. Sem isso, o lever não vale nada.

**Carga.** ~20 sintéticas in-scope + 7 reais human (BotCity é `[]`) ≈ ~25 entradas × ~4-5 techs ≈
**100-130 julgamentos (tech → prioridade)**. Bounded; o `rationale` das reais já carrega o julgamento
(Idwall "data moat forte → graduação"; Aquarela "P3 15 → domínio + AI Enterprise"), é formalizar.

**Passos (6 dias).**
1. **Schema + compat (sem mudar número).** `expected_nvidia_techs` aceita as **duas formas**:
   `"NVIDIA NIM"` (sem rank) **ou** `{tech: "NVIDIA NIM", prioridade: alta}`. Loader normaliza;
   fixtures chapadas seguem validando; métrica de presença **idêntica**. Suíte verde.
2. **Re-curadoria (pólo longo, ~Dias 2-3).** ALTA/MÉDIA/BAIXA por tech, ancorado no gap + §5.5,
   **independente da regra**, com `notes` por entrada. Reais primeiro (julgamento já escrito), depois
   as sintéticas.
3. **Métrica priority-aware + testes (~Dia 4).** Adicionar `recall@ALTA` + precision tolerante **ao
   lado** da de presença (não substituir). Testes espelhando `test_recommend_cases.py`.
4. **Rodar, medir, iterar (~Dia 5).** Recupera o maduro? `recall@ALTA` alto nos alvos? Se cheirar
   circular, ajustar **rótulo**, nunca a métrica. Write-up honesto.
5. **Buffer + docs (~Dia 6).** Fechar Limitação nº2 do `AVALIACAO.md` + checklist abaixo + commit.

**DoD.** `recall@ALTA` reportado no headline (knob-free); precision tolerante ao lado da de presença
(0,56 preservada); rótulos com prioridade ancorada no gap (notes anti-circularidade); suíte verde;
`AVALIACAO.md` Limitação nº2 fechada com o número.

---

## Sequência recomendada *(o que ainda falta, em ordem)*

1. ~~**A** (validar ao vivo)~~ ✅ **feito 2026-06-16** — coorte real, stack no ar, radar coerente.
2. ~~**C** (qualidade do radar): descrição + embeddings reais + nomes + k~~ ✅ — **resta só C-c** (★),
   que precisa de **mais evidência por empresa** (re-raspar = créditos). Opcional: re-indexar a KB em
   2048 p/ o recommender RAG ao vivo; cosmético do desempate de classe (ver §C).
3. ~~Escolher **uma** frente de profundidade~~ — **B (chat premium) entregue (2026-06-17):** busca
   semântica de texto livre + citação por empresa no `/discover` (ver §B). A outra frente de
   profundidade, **D (GPU/ROI)**, segue *gated por GPU* (4 GB local inviabiliza o self-host; endpoint
   NIM grátis congestionado p/ a medição) — engine/UI já prontos, falta só a medição real.
4. **F** por último, se sobrar tempo.

## Checklist de fechamento (DoD consolidado)

- [x] Eval com 8/9 entradas reais curadas (`label_source=human`) no headline ✅ 2026-06-15
- [x] `AVALIACAO.md` atualizado com os números finais (incl. classificação live n=32 = 0,720) ✅ 2026-06-15
- [x] Stack sobe com `run.ps1`, coorte real seedada, `/radar` + `/coorte` + detalhe AIMI navegáveis ✅ 2026-06-16
- [x] Consulta resiliente: o run sobrevive a sair/voltar da tela (F5.3+) ✅ 2026-06-16
- [x] Radar de coorte coerente ao vivo: descrição + `nv-embedqa` + nomes honestos + k default (C-a/b/d) ✅ 2026-06-16
- [x] **C-c:** causa-raiz do ★=0% **corrigida** — não era evidência (hipótese `scrape_deep_evidence`
  falsificada ao vivo), era **ancoragem do prompt** (exemplo `12/9/6/15` no `classifier.md`). Fix
  `classifier@v3` (âncoras de banda + anti-cópia); coorte re-rodada e **★ adotado (0→3:
  Semantix/Unico/Aquarela)**, Postgres reseed + rebuild ✅ 2026-06-20. **Polish 2026-06-20:** dead-end
  `scrape_deep_evidence` revertido + trava de P3 no prompt (`classifier@v4`, P3 fica baixo sem evidência
  de inferência própria); coorte re-rodada com v4 e **adotada ao vivo** (P3 0–5 em toda a coorte, ★ →
  Idwall/Neurotech/Semantix, Idwall graduou), reseed + rebuild ✅ 2026-06-20 *(draw regrediu Pareto/Unico/
  Aquarela por ruído de evidência — não P3)*
- [x] **Frente de profundidade — B (chat premium / cohort-RAG):** busca semântica de texto livre +
  citação de evidência por empresa no `/discover` (numpy em memória, offline determinístico + nv-embed
  atrás de flag), com a UI mostrando relevância + fonte citada ✅ 2026-06-17 (SSE adiado; ver §B).
- [~] **Frente de profundidade — D (ROI no briefing):** ROI numérico ponta a ponta no produto
  (matriz/engine → `gpu_benchmark` → persist → API → **UI `RoiStrip` + texto do briefing Markdown/PDF**)
  ✅ 2026-06-16. **Falta só a medição real** (`bench_nim.py`) — *gated: GPU local 4 GB + endpoint NIM
  grátis congestionado* (ver §D).
- [x] (Opcional) **Cohere reranker ao vivo** ✅ 2026-06-21 — head-to-head nos dois substratos
  (offline + nv-embed), qualidade empatada no ruído, decisão NeMo (grátis) com dados (§6 AVALIACAO)
- [ ] (Opcional) **Juiz LLM da RAGAS ao vivo** (consolidado vs limiares) — gated pelo endpoint (**F7.3**)
- [x] (Opcional) Re-indexar a KB em 2048 → recommender RAG ao vivo com citação (`INDEX_USE_QDRANT`)
  ✅ 2026-06-21 — `scripts/reindex_kb.py`; `tapi_kb` 256→2048, 75 pts, smoke de retrieve com citação ok
- [x] (Opcional) **Rótulo priorizado — eval de recomendação priority-aware (F7.7, §G)** ✅ **feito
  (2026-06-22):** rótulo tipado `{tech, prioridade}` (retrocompat, 0 mudança de número) + `recall@ALTA`
  knob-free no headline + precision tolerante ao lado da presença; prioridade ancorada no gap, **revisão
  humana confirmada** (`REVISAO-ROTULOS.md` + `gen_label_review.py`). Resultado: **recall@ALTA 1,00 em
  alvo+wrapper** (a regra surfa a alavanca onde importa, F6.13), global 0,72 ≥ 0,70; maduro 0,22/periférico
  0,00 baixos **por design gap-driven**; precision tolerante 0,56 ≈ presença (a regra não emite BAIXA →
  nada a perdoar). Limitação nº2 do `AVALIACAO.md` fechada. Commits 8681ee7→c6341d0.
- [x] (Opcional) **Lever de *recommender* — servir maduro/periférico (descoberto pela F7.7)** ✅ **feito
  (2026-06-22):** dois levers em `recommend_rules.match_techs` (aditivos, depois do gap/setor): (1)
  **maduro→AI Enterprise** se AI-native e P3≥13 (já graduou → jogada enterprise, *maturity-driven*); (2)
  **AI-enabled-chat→NeMo Guardrails** se superfície conversacional/generativa (`_has_conversational_surface`).
  Reusam as TechRules de P4 (uma fonte de verdade). **Resultado:** recall@ALTA **0,72→0,97** (maduro
  0,22→0,89, periférico 0,00→1,00) **e presença junto** (precision 0,56→0,60, recall 0,76→0,89 — as techs
  eram TP). §5.5 **7/7** intacto (teste é subconjunto), dois lados 1,00, suíte verde (testes novos
  `test_graduated_ai_native_gets_enterprise_not_alvo` + `test_ai_enabled_chat_surface_gets_guardrails`).
  Resíduo: maduro 0,89 = domínio tabular da Aquarela que o setor não pega.
- [x] (Opcional) **Suíte offline hermética contra a `.env` de dev** ✅ **feito (2026-06-21)** —
  `tests/conftest.py` com `pytest_configure` (roda **antes da coleta**, logo antes de qualquer
  fixture) pina os 11 flags de caminho-ao-vivo (`*_USE_LLM`, `EMBEDDINGS_USE_NV`, `INDEX_USE_QDRANT`,
  `RERANKER_USE_NV`, `SCRAPER_USE_NETWORK`, `RAGAS_USE_LLM`, `BRIEFING_USE_GUARDRAILS`) em `false`
  via **env** (precede o `.env` e sobrevive ao `get_settings.cache_clear()` — pinar o `setattr` da
  instância não sobreviveria). `GPU_BENCHMARK_USE_MATRIX` fica de fora (caminho local + teste que o
  liga via env). **Verificado:** `pytest` local com a `.env` real (flags ligados) caiu de **~52
  falhas → 0** (suíte verde, exit 0; só 3 skips). Os testes de rede opt-in (gated por chave/
  `TAPI_NETWORK_TESTS`) e os toggles intencionais (override no corpo do teste) seguem intactos.
