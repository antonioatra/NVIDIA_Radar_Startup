# F6 — Diferencial: TAPI Maturity Index + GPU Graduation Engine (Entregável 6)

**Objetivo:** loop único *diagnosticar → prescrever → quantificar*. **Dependências:** F4. **Marco:** M6.

## 6.1 AI-Native Maturity Index (AIMI)
- [ ] **F6.1** Rubrica AIMI v1: 4 pilares × 0–25 (Data Moat · Workflow Depth · Technical
      Optimization · Distribution), regras de pontuação por evidência.
- [ ] **F6.2** Cálculo do score no `classifier`; cada sub-score com evidência citada (explicável).
- [ ] **F6.3** Acoplamento: Technical Optimization baixo **dispara** recomendações NVIDIA no F4.
- [ ] **F6.4** Eval do índice: correlação com rótulos do eval set (F7).

## 6.2 Camada de coorte (RAPIDS/cuML)
- [ ] **F6.5** **cuDF**: normalização/dedup da coorte coletada (GPU).
- [ ] **F6.6** Embeddings de setor/perfil → **cuML** (KMeans + UMAP) → clusters.
- [ ] **F6.7** Radar/ranking do ecossistema BR: clusters "graduation-ready" p/ Inception.

## 6.3 GPU Graduation Engine
- [ ] **F6.8** Servir modelos de benchmark via **Triton + TensorRT-LLM** na GPU local.
- [ ] **F6.9** Gerar **matriz de benchmark** (tamanhos × workloads): tokens/s, p50/p95, throughput.
- [ ] **F6.10** Estimador de custo: $/1M tokens self-hosted (NIM) vs API externa.
- [ ] **F6.11** Mapear perfil da startup → célula da matriz → **ROI** no briefing.
- [ ] **F6.12** Botão "run ao vivo" (1 modelo, ex. Nemotron-Nano) p/ demo.

## Tecnologias
RAPIDS · cuDF · cuML · CUDA · Triton · TensorRT-LLM · NIM (self-hosted).

## DoD
- [ ] Briefing inclui linha de ROI quantificado (ex.: "~Nx throughput, p95 −M%, custo −K%").
- [ ] Radar de coorte exibe clusters e ranking de prontidão.
