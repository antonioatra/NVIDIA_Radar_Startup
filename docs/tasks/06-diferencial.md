# F6 — Diferencial: TAPI Maturity Index + GPU Graduation Engine (Entregável 6)

**Objetivo:** loop único *diagnosticar → prescrever → quantificar*. **Dependências:** F4. **Marco:** M6.

> **Sobre os IDs.** A numeração não é contígua: **F6.13** vive aqui (§6.1) por pertencer ao
> AIMI, mas tem número alto porque foi acrescentada depois das tasks de GPU (F6.5–F6.12). Os IDs
> são **estáveis e referenciados** em outros docs (ARQUITETURA §5.1, F0.5, F5.4) e em commits —
> por isso **não** são renumerados. Leia por seção (6.1 AIMI · 6.2 coorte · 6.3 GPU), não por número.

## 6.1 AI-Native Maturity Index (AIMI)
- [x] **F6.1** Rubrica AIMI **v1** (refina a v0 provisória de F2.6): 4 pilares × 0–25 (Data Moat ·
      Workflow Depth · Technical Optimization · Distribution), regras de pontuação por evidência.
      Mantém o contrato `AIMIScore` (F0.5) estável; só melhora a heurística de pontuação.
      Rubrica **fundamentada (grounding)** nos materiais de AI-native services do §10.1 (F3.1d) —
      os 4 pilares derivam dessa definição, não são invenção arbitrária.
      → `packages\agents\classifier.py`: a heurística (`heuristic_score`) passa de **v0 → v1**
      (carimba `heuristic_version="v1"`; `parse_score` do caminho Super idem). O que muda **só na
      heurística** (RUBRICA e contrato `AIMIScore` intactos): além da *breadth* de sinais (base
      0→3·1→9·2→12·3+→15), cada **sinal forte** do pilar soma profundidade (+2) e a faixa
      **"Forte/Defensável" (19–25)** deixa de ser proibida — mas só com **corroboração**: sinal
      forte **e** ≥2 fontes independentes (`MIN_SOURCES_FOR_STRONG`); sem isso o teto é
      "Estabelecido" (18, `ESTABLISHED_CEILING`). Subconjuntos `*_STRONG` por pilar (ex.: P3 =
      serving/fine-tuning/Triton/TensorRT/NIM — não "gpu"/"cuda" genéricos). A trava §0 (sub-score
      >6 exige evidência) e o gatilho de graduação (P3 100% API → ≤6) seguem; calibração dos cortes
      fica para o eval F6.4. **Gate verde:** `ruff` limpo e `pytest` **646 passed, 4 skipped** (o
      teste do teto v0 virou dois da v1 — Forte com corroboração ×, Estabelecido sem ela; nada
      downstream regrediu, pois wrapper P3 ≤6 e classe se preservam).
- [x] **F6.2** Cálculo do score no `classifier`; cada sub-score com evidência citada (explicável).
      → `packages\agents\classifier.py`: `_band_score` passa a devolver `(score, breakdown)` — o
      **mesmo** cálculo que gera o número, agora em texto auditável (base por *breadth* + `+N`
      profundidade dos sinais fortes + `+N` tração/contexto `= score`, e qual **teto** o limitou:
      "Estabelecido (sem corroboração)", "faixa Forte liberada (corroboração: X forte × Y fontes)"
      ou "sem evidência" RUBRICA §0). `_justify` ganha o parâmetro `breakdown` e anexa
      `Cálculo: …` à `justificativa` de cada pilar — o sub-score deixa de ser caixa-preta (lê-se
      *quais* sinais pesaram **e** *como* viraram o score). Alimenta direto o radar da UI
      (F5.4/F5.5) e os **fatores** exigidos pelo Inception Priority (F6.13). **Sem mudar o contrato
      `AIMIScore`/`PillarScore`** (princípio travado na F6.1): a explicabilidade vive no campo
      `justificativa` que já existe e já é exibido. Contrato/RUBRICA intactos; só a heurística
      ganhou rastro. **Gate verde:** `ruff` limpo e `pytest` **650 passed, 4 skipped** (4 testes
      novos: cada sub-score traz "Cálculo: … = N", e o breakdown explica os 3 tetos — Estabelecido,
      Forte e graduação por API).
- [x] **F6.3** Acoplamento: Technical Optimization baixo **dispara** recomendações NVIDIA no F4.
      → `packages\agents\nvidia_rag.py`: a seleção de gaps (`gap_pillars`, fonte única do RAG/F3.7
      **e** das regras/F4.1 — consistência gap↔evidência) passa a **priorizar P3**. Novo
      `_gap_sort_key`: quando Technical Optimization é gap (score ≤ `GAP_CEILING`), ele encabeça a
      lista e **sobrevive ao corte `MAX_GAPS`** — antes, por severidade pura, um P3 gap podia ser
      descartado se outros 3 pilares pontuassem mais baixo, e a graduação **não disparava**. Agora
      P3 baixo sempre aciona NIM/TensorRT-LLM/Triton (o maior upside NVIDIA, `ALINHAMENTO §8` /
      `RUBRICA §4`) e lidera a prescrição; P3 **não**-gap (score alto) não recebe prioridade (vale
      só severidade/nome — startup com stack forte não é alvo de graduação). Efeito de borda
      desejado no briefing (F4.4): `gap_pillars(aimi)[0]` vira P3 sempre que P3 é gap, reforçando o
      ramo "alvo de graduação" do eixo comercial. **Sem mudar contrato nem `GAP_CEILING`/`MAX_GAPS`**
      — só a ordem/garantia de seleção. **Gate verde:** `ruff` limpo e `pytest` **652 passed, 4
      skipped** (2 testes novos: P3 gap lidera e sobrevive ao corte mesmo não sendo o mais severo —
      no nível de query/F3.7 e de regra/F4.1; os 7 casos §5.5 e a ordenação por severidade seguem).
- [x] **F6.4** Eval do índice: correlação do AIMI com os rótulos do **eval set de F1.12**
      (consome o conjunto já criado; F7.2 consolida a métrica).
      → `packages\eval\aimi_correlation.py` (+ `tests\test_aimi_correlation.py`): harness que mede
      o quanto a **heurística v1** (F6.1) recupera o AIMI **rotulado** a partir do **mesmo sinal
      que a produção vê do lado público** — a descrição. Para cada entrada do eval set monta um
      `StartupProfile` **só-de-descrição** (descrição+setor como `Claim`, espelhando o `extractor`
      F2.5), roda `heuristic_score` e correlaciona o total predito × rotulado por **Spearman**
      (rank-based: o ground-truth segue a RUBRICA, não a heurística, então a descrição-só
      **sub-prediz a magnitude** mas preserva a **ordem** — que é o que "o índice ranqueia como o
      rótulo?" exige). Spearman em **Python puro** (sem numpy/scipy — fora do `requirements-ci.txt`),
      empates pela média, espinha verde offline como o §5.5 (F4.8). **Resultado:**
      `Spearman(total)=0.815` ≥ gate **0,70** do §7 (que a F7.2 consolida); por pilar, P3 Technical
      Optimization (o que dispara a graduação, F6.3) é recuperado bem (ρ=+0.76), e o relatório é
      **honesto sobre o limite**: Distribution Moat é o pilar mais fraco (ρ=+0.18) porque seus
      sinais (funding/clientes enterprise) não vivem numa fixture em prosa — o total ainda passa
      porque P4 é 1 de 4. CLI `python -m packages.eval.aimi_correlation` (exit 1 abaixo do gate).
      **Gate verde:** `ruff` limpo e `pytest` **663 passed, 4 skipped** (11 testes novos: Spearman
      puro — identidade/inversa, valor conhecido 0,6, monotônica não-linear, empates/constante,
      validação — + correlação ≥ gate, P3 recuperado, P4 o mais fraco, per-entry rastreável,
      heurística v1 determinista, CLI exit 0).
- [x] **F6.13** **Inception Priority (fila de outreach):** score 0–100 por empresa = **potencial
      AI-native × upside NVIDIA**, derivado do AIMI (alto potencial em Data Moat/Workflow +
      **Technical Optimization baixo** = maior upside de graduação → maior prioridade). Serve
      diretamente o §1 ("atrair, qualificar e nutrir"): dá ao gerente uma **fila priorizada** de
      empresas, não só o diagnóstico. Sem GPU (puro AIMI). Preenche `AIMIScore.inception_priority`
      (F0.5), exibido na lista da UI (F5.4) e no briefing. Explicável: cada score com os fatores
      que o compõem. **Complementa** o radar de coorte (F6.7): F6.7 ranqueia *clusters*, F6.13
      ranqueia *empresas*.
      → `packages\agents\inception.py` (+ `tests\test_inception.py`): função pura
      `inception_priority(aimi) → (score 0–100, fatores)` — `100 × peso(classe) × potencial ×
      upside`, com **potencial** `=(P1+P2)/50` (moat + workflow reais) e **upside** `=(25−P3)/25`
      (P3 baixo = stack imatura = maior upside de graduação, RUBRICA §4). **Multiplicativo de
      propósito** (o "×" do §9): exige os **dois** lados — quem já internalizou a inferência (P3
      alto) cai por upside menor; wrapper sem moat (P1/P2 baixo) cai por potencial menor. O **peso
      da classe** (§5.1: `AI-native` 1.0 · `AI-enabled` 0.5 · `non-AI` 0.0) realiza a região "alvo
      de graduação ★" (ALINHAMENTO §5): `AI-native` + P1/P2 alto + P3 baixo → topo da fila. Puro/
      determinista (sem rede/LLM/GPU). **Wiring:** o `classifier` carimba o campo nos **dois**
      caminhos (heurística v1 **e** parse do Super — deriva do AIMI, não do que o modelo alegar);
      o `briefing` (F4.4) preenche `Briefing.inception_priority` e **exibe os fatores** no Markdown
      e no PDF (paridade), na mesma linha do diagnóstico — score nunca caixa-preta (§9). **Sem
      mudar contrato:** só preenche o campo `inception_priority` que já existia em `AIMIScore`/
      `Briefing`/`Score`(DB); a API (`GET /companies`, ordena por ele desc) e a UI (lista F5.4 +
      detalhe) já o liam — agora vem com valor real, não `None`. (A *persistência* do `Score` no
      banco — mapear `aimi → Score` — segue como lacuna à parte; o campo flui por contrato.)
      **Gate verde:** `ruff` limpo e `pytest` **671 passed, 4 skipped** (8 testes novos: limites
      [0,100], alvo-de-graduação > já-otimizado [upside] e > wrapper [potencial], ordem por classe
      native>enabled>non-AI=0, fatores explicáveis, carimbo na heurística e no parse, e o briefing
      exibindo o score + a linha no Markdown).

## 6.2 Camada de coorte (RAPIDS/cuML)
- [ ] **F6.5** **cuDF**: normalização/dedup da **coorte acumulada** (tabela `company` populada
      pelo cohort builder F1.14), na GPU.
- [ ] **F6.6** Embeddings de setor/perfil (**reusa `nv-embedqa`**, o mesmo do RAG — sem 2º
      embedder) → **cuML** (KMeans + UMAP) → clusters.
- [ ] **F6.7** Radar/ranking do ecossistema BR: clusters "graduation-ready" p/ Inception.

## 6.3 GPU Graduation Engine
- [ ] **F6.8** Servir modelos de benchmark via **Triton + TensorRT-LLM** na GPU local.
      **Fora do `docker-compose.yml` base** (que é o ambiente de build com NIM hospedado): o
      serving de benchmark sobe ad-hoc/notebook na GPU. Documentar o comando de subida aqui.
- [ ] **F6.9** Gerar **matriz de benchmark** (tamanhos × workloads): tokens/s, p50/p95, throughput.
- [ ] **F6.10** Estimador de custo: $/1M tokens self-hosted (NIM) vs API externa.
- [ ] **F6.11** Mapear perfil da startup → célula da matriz → **ROI** no briefing.
- [ ] **F6.12** Botão "run ao vivo" (1 modelo, ex. Nemotron-Nano) p/ demo.

## Prioridade (MVP vs. stretch) — esta é a fase de maior risco de entrega
F6 acumula GPU self-host (NIM/Triton/TensorRT-LLM), RAPIDS/cuML e ROI. Para garantir uma
entrega defensável mesmo se o self-host travar, o escopo é fatiado:

| Camada | **MVP (must-have)** | **Stretch (se sobrar tempo/GPU)** |
|---|---|---|
| AIMI (6.1) | F6.1–F6.4 **+ F6.13** (Inception Priority) — núcleo do diferencial, sem GPU | — |
| Coorte (6.2) | F6.5 dedup (cuDF) + ranking simples | F6.6/F6.7 clustering KMeans+UMAP + radar visual |
| GPU Engine (6.3) | F6.9–F6.11 **matriz pré-computada** → ROI no briefing | F6.8 Triton/TRT-LLM completo + F6.12 botão "run ao vivo" |

**Fallbacks de de-risking (decisões travadas):**
- **ROI:** a matriz de benchmark é **sempre pré-computada uma vez** e armazenada; o "run ao vivo"
  (F6.12) é demo opcional, nunca caminho crítico por request.
- **Self-host:** se NIM/Triton local não subir a tempo, medir o lado "otimizado" com **vLLM** na GPU
  e/ou números de referência citados; manter a comparação API × self-hosted honesta e rastreável.
- **Clustering:** se cuML/UMAP der problema, cair para KMeans em CPU (scikit-learn) — o radar
  continua, só sem aceleração GPU (anota-se a limitação).

## Tecnologias
RAPIDS · cuDF · cuML · CUDA · Triton · TensorRT-LLM · NIM (self-hosted) · vLLM (fallback) ·
scikit-learn (fallback de clustering).

## DoD
- [ ] **MVP:** AIMI v1 calculado + Inception Priority (F6.13) por empresa + ROI no briefing a
      partir da matriz pré-computada.
- [ ] Briefing inclui linha de ROI quantificado (ex.: "~Nx throughput, p95 −M%, custo −K%").
- [ ] Lista de empresas ordenável por Inception Priority (fila de outreach do gerente).
- [ ] Radar de coorte exibe clusters e ranking de prontidão (stretch: aceleração GPU).
