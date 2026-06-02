# F6 — Diferencial: TAPI Maturity Index + GPU Graduation Engine (Entregável 6)

**Objetivo:** loop único *diagnosticar → prescrever → quantificar*. **Dependências:** F4. **Marco:** M6.

> **Sobre os IDs.** A numeração não é contígua: **F6.13** vive aqui (§6.1) por pertencer ao
> AIMI, mas tem número alto porque foi acrescentada depois das tasks de GPU (F6.5–F6.12). Os IDs
> são **estáveis e referenciados** em outros docs (ARQUITETURA §5.1, F0.5, F5.4) e em commits —
> por isso **não** são renumerados. Leia por seção (6.1 AIMI · 6.2 coorte · 6.3 GPU), não por número.

## 6.1 AI-Native Maturity Index (AIMI)
- [ ] **F6.1** Rubrica AIMI **v1** (refina a v0 provisória de F2.6): 4 pilares × 0–25 (Data Moat ·
      Workflow Depth · Technical Optimization · Distribution), regras de pontuação por evidência.
      Mantém o contrato `AIMIScore` (F0.5) estável; só melhora a heurística de pontuação.
      Rubrica **fundamentada (grounding)** nos materiais de AI-native services do §10.1 (F3.1d) —
      os 4 pilares derivam dessa definição, não são invenção arbitrária.
- [ ] **F6.2** Cálculo do score no `classifier`; cada sub-score com evidência citada (explicável).
- [ ] **F6.3** Acoplamento: Technical Optimization baixo **dispara** recomendações NVIDIA no F4.
- [ ] **F6.4** Eval do índice: correlação do AIMI com os rótulos do **eval set de F1.12**
      (consome o conjunto já criado; F7.2 consolida a métrica).
- [ ] **F6.13** **Inception Priority (fila de outreach):** score 0–100 por empresa = **potencial
      AI-native × upside NVIDIA**, derivado do AIMI (alto potencial em Data Moat/Workflow +
      **Technical Optimization baixo** = maior upside de graduação → maior prioridade). Serve
      diretamente o §1 ("atrair, qualificar e nutrir"): dá ao gerente uma **fila priorizada** de
      empresas, não só o diagnóstico. Sem GPU (puro AIMI). Preenche `AIMIScore.inception_priority`
      (F0.5), exibido na lista da UI (F5.4) e no briefing. Explicável: cada score com os fatores
      que o compõem. **Complementa** o radar de coorte (F6.7): F6.7 ranqueia *clusters*, F6.13
      ranqueia *empresas*.

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
