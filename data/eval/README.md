# `data/eval/` — Eval set rotulado (F1.12)

Ground-truth de **classificação** (§5.1) + **AIMI esperado** (4 pilares × 0–25) por
startup. Criado **cedo** (F1.12) porque é consumido por:

- **F6.4** — correlação do AIMI do modelo com os rótulos (Spearman ≥ 0,70, meta F7);
- **F7.1/F7.2** — métricas de classificação (macro-F1 ≥ 0,75) e consolidação;
- **F7.2b** — eval da recomendação: `expected_nvidia_techs` por empresa.

F7 **consolida/expande** este conjunto — não cria do zero.

## Como os rótulos são feitos
Por **revisão humana** sobre a definição de pilares/escala de
[`docs/RUBRICA-AIMI.md`](../../docs/RUBRICA-AIMI.md) (F0.11). O ground-truth depende **só
da definição** (escala 0–25 imutável), nunca da heurística de pontuação (v0 F2.6 / v1
F6.1) — trocar a heurística não invalida os rótulos. Cada entrada carrega a **região do
plano `classe × AIMI`** (RUBRICA §6): `fora_escopo` · `periferico` · `wrapper` ·
`alvo_graduacao` ★ · `maduro`.

## `synthetic: true` vs entradas reais
As 24 entradas de `labeled_startups.yaml` são **fixtures-semente sintéticas**
(`synthetic: true`): empresas fictícias ancoradas na rubrica, que cobrem todas as
regiões do mapa de decisão e **destravam F6.4/F7 desde já**. Não são empresas reais e
**não** trazem `evidence_urls`.

Entradas **reais** (`synthetic: false`) — **exigem** `evidence_urls` rastreáveis; o loader
recusa entrada real sem fonte.

## `cohort_real.yaml` — expansão real automática (F7.1)
A metade real da F7.1 é **automática**: o cohort builder (F1.14) parte das candidatas curadas
(`data/seeds/cohort_candidates.yaml` — empresas BR de IA reais), o pipeline **resolve e raspa
ao vivo** (Tavily+Firecrawl) e diagnostica (Nemotron-Super), e `packages/eval/cohort_to_eval.py`
materializa as entradas em `data/eval/cohort_real.yaml` (`synthetic: false`, `evidence_urls`
reais). Reproduzível por:

```
python -m packages.agents.cohort --seed --db sqlite:///data/cohort.db   # + flags de rede/LLM
python -m packages.eval.cohort_to_eval --db sqlite:///data/cohort.db
```

**Honestidade — `label_source`.** O rótulo (classe/AIMI/techs) dessas entradas é a **saída do
próprio modelo**, então medir o modelo contra ele é um **baseline circular**. Por isso elas
carregam `label_source: model` e `load_eval_set()` as mantém **fora do headline** por padrão
(`include_model=True` para incluí-las); o `AVALIACAO.md` reporta o baseline auto-rotulado em
**linha separada**, nunca fundido nos números human-reviewed. Promover uma entrada a ground-truth
exige **revisão humana** (virar `label_source: human`). O sourcing/evidência é real; o rótulo é
proposto. (Por que curada e não por crawl: o crawl-discovery Scrapy rende **0 ao vivo** —
robots/JS/bloqueio; a coleta por-empresa via Tavily/Firecrawl é robusta. Ver
`data/seeds/cohort_candidates.yaml`.)

## Esquema (validado em `packages/eval/dataset.py`)
`id` · `nome` · `setor` · `descricao` · `classificacao` (`AI-native|AI-enabled|non-AI`) ·
`region` · `aimi {data_moat, workflow_depth, technical_optimization, distribution_moat}`
(0–25 cada) · `expected_nvidia_techs[]` (F7.2b) · `rationale` · `evidence_urls[]` ·
`synthetic` · `label_source` (`human|model`) · `notes`.

O loader valida **coerência direcional** da anotação (ex.: `non-AI` não tem Workflow
Depth alto por IA; `alvo_graduacao` tem P3 ≤ 8 com P1 ou P2 ≥ 13) — sanidade da
rotulagem, **não** o corte de decisão calibrado (esse é F6.4).
