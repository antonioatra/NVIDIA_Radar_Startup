# Próximos passos para fechar o TAPI

> **Estado em 2026-06-14.** O núcleo testável dos 7 entregáveis está feito (suíte ~747 passed,
> 4 skipped; métricas batendo as metas do §7 — ver [AVALIACAO.md](AVALIACAO.md)). Tudo que resta
> abaixo é **stretch gated por recurso** (volume de coorte, GPU, dependência ou chave externa),
> **não** código de base faltando. Este documento detalha cada frente: estado real no código, o
> que falta, os passos concretos, o bloqueio (se houver) e o esforço.

## Visão geral

| # | Frente | Estado | Bloqueio real | Esforço | Prioridade |
|---|---|---|---|---|---|
| A | **Validar a stack + chat ao vivo** | UI pronta, dados via seed | Nenhum (só rodar) | ~1–2 h | **Alta** |
| B | **Chat "premium" (F3.10/F5.12)** | MVP determinístico entregue | Volume de coorte | ~2–3 dias | Média |
| C | **Clustering de coorte (F6.5–F6.7)** | Não iniciado | Coorte em volume | ~2–3 dias | Média |
| D | **GPU Graduation Engine (F6.8–F6.12)** | Stub + contrato prontos | GPU local (**não pago**, ver §D) | ~3–6 dias | Média/Baixa |
| E | **Eval set real → ground-truth (F7.1)** | Auto-rotulado, fora do headline | Curadoria humana | ~1 dia | Média |
| F | **Recursos externos (F7.3, F7.4)** | Degradam limpo | Chave / dep | ~1–2 h cada | Baixa |

**Caminho mínimo para "fechar e demonstrar":** A → E → (B *ou* D, escolher um para mostrar
profundidade). **Caminho completo:** A → B → C → D → E → F.

---

## A. Validar a stack e o chat ao vivo  *(prioridade 1 — barato, destrava a demo)*

**Estado.** A UI do chat está pronta (`apps/frontend/src/app/descoberta/`), o endpoint
`GET /discover` existe (`apps/api/main.py`), `tsc`+`eslint` verdes. **Mas o chat e o radar só
mostram empresas se o banco estiver populado.** O `scripts/run.ps1` chama `scripts/seed_postgres.py`,
que copia de `data/cohort.db` (gitignored) para o Postgres. Sem `cohort.db`, a stack sobe vazia.

**O que falta.** Rodar a coorte uma vez (gera `cohort.db`), subir a stack e conferir o fluxo.

**Passos.**
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

---

## B. Chat "premium" — cohort-RAG semântico (F3.10/F5.12 stretch)

**Estado (honesto).** O `/discover` entregue é o **MVP determinístico**: parser de palavra-chave
(`packages/agents/discovery.py`) traduz PT-BR → filtros (tech NVIDIA / classe / piso de AIMI) →
`list_companies` ordenado por Inception Priority. É offline, reproduzível e sem alucinação; a UI
casa com ele. **Não** cobre: setor/região livre, busca semântica, **citação de evidência por
empresa** no chat, nem **streaming SSE**.

**O que falta (a versão dos docs).** Índice de busca sobre a tabela `company` acumulada, distinto
da KB NVIDIA mas reusando a mesma stack de RAG:
- Coleção Qdrant separada para perfis/evidências da coorte (reusa `nv-embedqa` da F3.3, híbrida F3.5, reranker F3.6).
- Nó Nemotron que extrai filtros estruturados **+** faz busca semântica → empresas com **citação à fonte**.
- NeMo Guardrails: nunca retornar empresa sem evidência (princípio nº1 da ARQUITETURA §8).
- UI: streaming via SSE (reusa o canal do `/runs/{id}` do console F5.3) + cards com a citação.

**Passos.**
1. `packages/rag/cohort_index.py`: indexar `company` + `evidence` numa coleção Qdrant nova (reusar o embedder e o cliente já existentes, só trocar a coleção).
2. `packages/agents/cohort_rag.py`: `parse_query` (já existe) **+** retrieval semântico → merge → rerank → empresas com `evidence_url`.
3. Estender `GET /discover` (ou novo `/discover/rag`) para devolver as citações por empresa; ligar Guardrails no caminho de resposta.
4. UI: trocar o `fetch` único por `EventSource` (padrão do `console.tsx`) e renderizar a citação no `CompanyCard`.

**Bloqueio.** Precisa da coorte **em volume** (frente A gera ~10 empresas; o RAG semântico só
brilha com dezenas+). Sem volume, o MVP determinístico é honestamente melhor. **Esforço.** ~2–3 dias.
**Decisão sugerida:** manter o MVP como entrega e documentar o premium como evolução — **ou** fazer
o premium se houver tempo e a coorte crescer. Não marcar o DoD de citações enquanto não houver fonte por empresa.

---

## C. Clustering de coorte (F6.5–F6.7)

**Estado.** Não iniciado. O `packages/benchmark/` está vazio; não há módulo de coorte/cuML.

**O que falta.**
- **F6.5** cuDF: normalização/dedup da tabela `company` na GPU.
- **F6.6** Embeddings de setor/perfil (reusa `nv-embedqa`) → cuML (KMeans + UMAP) → clusters.
- **F6.7** Radar/ranking do ecossistema BR: clusters "graduation-ready" para o Inception.

**Passos.**
1. `packages/scoring/cohort_cluster.py`: carregar a coorte, embeddar perfis, KMeans + UMAP.
2. **Fallback travado:** se cuML/UMAP der problema, cair para scikit-learn em CPU (o radar continua, anota-se a limitação).
3. Expor um endpoint `GET /cohort/clusters` + uma aba de radar visual na UI (scatter 2D por cluster, cor por classe).

**Bloqueio.** Coorte em volume (mesma dependência da frente A/B). **Esforço.** ~2–3 dias
(MVP cuDF dedup + ranking simples; clustering visual é o stretch dentro do stretch).

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
| RAPIDS / cuDF / cuML | **Grátis (OSS)** | Frente C |
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

**O que você precisa fazer (passos):**
1. `python scripts/bench_nim.py --tier medium` (mede o Nemotron-Nano-8B hospedado; opcional `--tier large --model ...super-49b...`).
2. Ajustar o lado **baseline** da célula no `matrix.json` para o preço/latência da API externa que a startup-alvo usa hoje (o número de comparação).
3. Rodar um run com `GPU_BENCHMARK_USE_MATRIX=true` → o ROI aparece no cartão da UI (`/radar/[id]`).
4. *(Opcional)* Adicionar a linha de ROI numérica no **texto** do briefing (a UI já mostra; o briefing hoje só narra o ROI qualitativamente).

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

## E. Eval set real → ground-truth (F7.1)

**Estado.** `data/eval/cohort_real.yaml` (9 entradas, untracked) é gerado pela ponte
`packages/eval/cohort_to_eval.py` a partir da coorte. **Porém** é auto-rotulado pelo **próprio
modelo** (`label_source=model`) → baseline circular → fica **fora do headline** por padrão (o
headline segue nas 24 fixtures `human`). Ver `data/eval/README.md`.

**O que falta.** Curadoria humana para promover `model → human`: revisar classe/AIMI/techs
esperadas de cada empresa contra a fonte e corrigir o que o modelo errou (a memória nota casos
discutíveis: maioria cai em região "wrapper" por extração só-de-descrição; Unico classificada non-AI).

**Passos.**
1. Rodar a coorte (frente A) e gerar o YAML.
2. Revisar manualmente as ~9 entradas (1 dia): conferir classe, AIMI e `expected_nvidia_techs`.
3. Marcar `label_source=human` nas revisadas e versionar o YAML curado.
4. Rodar as métricas incluindo as reais no headline (`load_eval_set(include_model=...)`) e atualizar `AVALIACAO.md`.

**Bloqueio.** Trabalho humano de curadoria. **Esforço.** ~1 dia. **Resultado.** Métricas headline
deixam de ser 100% sintéticas — o gap nº1 de credibilidade do eval.

---

## F. Recursos externos (degradam limpo — baixa prioridade)

- **F7.4 — Cohere Reranker.** O comparativo `packages/eval/reranker_comparison.py` já liga o
  `CohereReranker` (`packages/rag/rerank.py`), mas falta a **trial key** + o SDK para gerar o número
  Cohere. NeMo já foi medido ao vivo (0,823). **Passo:** obter trial key, `pip install cohere`,
  rodar `python -m packages.eval.reranker_comparison --cohere`. **Esforço.** ~1 h.
- **F7.3 — Juiz LLM da RAGAS.** A lib `ragas` quebra no import (conflito `langchain-community`
  removido — ver memória de ambiente). O proxy léxico roda; o juiz ao vivo está reservado e degrada
  limpo. **Passo:** resolver o conflito de dependência num venv isolado **ou** documentar como
  limitação conhecida. **Esforço.** ~1–2 h (ou aceitar a limitação).

---

## Sequência recomendada

1. **A** (validar ao vivo) — destrava a demo, baratíssimo, gera screenshots.
2. **E** (curar o eval) — maior ganho de credibilidade por hora investida.
3. Escolher **uma** frente de profundidade para mostrar no case:
   - **D** (GPU/ROI) se quiser o diferencial "stack viva + ROI medido" — **não é pago**, é montar na GPU.
   - **B** (chat premium) se quiser a narrativa "descoberta conversacional com citações".
4. **C** e **F** por último, se sobrar tempo.

## Checklist de fechamento (DoD consolidado)

- [ ] Stack sobe com `run.ps1`, coorte seedada, `/radar` + `/descoberta` + detalhe AIMI navegáveis (A)
- [ ] Eval com ao menos as ~9 entradas reais curadas (`label_source=human`) no headline (E)
- [ ] **Uma** das duas frentes de profundidade entregue: ROI no briefing (D) **ou** chat com citações (B)
- [ ] `AVALIACAO.md` atualizado com os números finais
- [ ] (Opcional) Cohere e juiz RAGAS ao vivo, ou ambos documentados como limitação (F)
