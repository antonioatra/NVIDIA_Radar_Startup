# Relatório de Avaliação — TAPI (NVIDIA Startup AI Radar)

**Tarefa:** F7.5 (consolida F7.2 · F6.4 · F7.2b · F7.2c · F7.3 · F7.4; metodologia/limitações
revisadas após a **F7.1**). **Atualizado:** 2026-06-13.

Este relatório reúne, num lugar só e **contra metas declaradas** (§7 do brief), a qualidade aferida
de cada peça do pipeline. O número final é o que os dados mostram; o alvo torna o resultado
interpretável. **Metas abaixo do alvo são reportadas como limitação honesta, não escondidas.**

## Metodologia (ler antes dos números)

- **Conjunto de avaliação (F1.12):** 24 fixtures rotuladas (`data/eval/labeled_startups.yaml`) —
  classe (§5.1) + AIMI esperado (4 pilares 0–25) + techs NVIDIA esperadas, cobrindo todas as regiões
  do plano `classe × AIMI`. **São 100% sintéticas** (`synthetic: true`): é "modelo real sobre dados de
  fixture". A **F7.1** acrescenta ao lado a **metade real automática** — coorte BR raspada ao vivo e
  auto-rotulada pelo pipeline (`packages/eval/cohort_to_eval.py` → `data/eval/cohort_real.yaml`,
  `synthetic: false`, `evidence_urls` reais). Mas como o rótulo é a **saída do próprio modelo**
  (**baseline circular**), essas entradas saem com `label_source: model` e ficam **fora do headline**
  (`load_eval_set(include_model=True)` para incluí-las; promover a ground-truth é revisão humana). Logo,
  **todos os números abaixo são human-reviewed** (as 24 fixtures); o auto-rotulado real é reportado à
  parte (ver §Limitações). O RAG usa um conjunto à parte de **7 perguntas NVIDIA**
  (`data/eval/rag/questions.yaml`).
- **Espinha verde / real atrás de flag:** cada peça que precisa de rede/LLM/GPU tem um **substituto
  offline determinístico como _default_** (roda no CI, reprodutível), com o **backend real plugável**.
  Onde o LLM **muda o resultado** (classificação, briefing), medimos o **real ao vivo**; onde **não
  muda por design** (seleção de techs do recommender), explicamos o porquê e ficamos no determinístico.
- **Cada métrica é reprodutível** por um comando (ver §Reprodução). Os caminhos `--llm`/`--nv`/`--cohere`
  fazem rede e gastam créditos; os defaults são offline.

## Resumo executivo (cada métrica × meta §7)

| Entregável | Métrica | Meta §7 | Resultado | Veredito |
|---|---|---|---|---|
| Classificação (F7.2) | macro-F1 | ≥ 0,75 | **0,875** (Nemotron-Super real) · 0,38 piso offline | ✅ |
| AIMI (F6.4) | Spearman vs rótulos | ≥ 0,70 | **0,815** | ✅ |
| Recomendação (F7.2b) | evidência dos 2 lados | = 1,00 | **1,00** (invariante duro F4.5) | ✅ |
| Recomendação (F7.2b) | precision/recall de techs | ≥ 0,70 | recall **0,69** geral / **0,78** nos alvos · precision 0,23 | ⚠️ parcial |
| RAG (F7.3) | RAGAS faithfulness | ≥ 0,80 | **1,00** | ✅ |
| RAG (F7.3 / F7.4) | context recall | ≥ 0,70 | 0,69 (proxy léxico) → **0,74** (reranker NeMo real) | ✅ com NeMo |
| Briefing (F7.2c) | faithfulness do texto final | ≥ 0,80 | **0,870** (espinha; min 0,786) | ✅ |
| Reranker (F7.4) | qualidade (NeMo × Cohere) | decisão com dados | NeMo **0,823** > léxico 0,802; Cohere pendente | ⚠️ Cohere pendente |

## Detalhe por entregável

### 1. Classificação — classe AI-native | AI-enabled | non-AI (F7.2)

Mede a classe predita × rotulada (n=24), sobre o **mesmo sinal público que a produção vê** (perfil
só-de-descrição). Reporta accuracy + macro-F1 (média não-ponderada por classe, sem deixar a
majoritária mascarar as raras) + matriz de confusão.

| Caminho | macro-F1 | accuracy | AI-native recall |
|---|---|---|---|
| Heurística offline (piso/CI) | 0,38 | 0,375 | 0,20 |
| **Nemotron-Super real (produção)** | **0,875** ✅ | 0,917 | 0,933 |

**Leitura:** o **caminho de produção bate a meta** (0,875 ≥ 0,75). O 0,38 é só o substituto
determinístico, que rebaixa AI-native porque a heurística exige Workflow Depth alto e a prosa-só
sub-prediz essa magnitude; o Super, com reasoning, lê o *papel* da IA na descrição e recupera
AI-native (recall 0,20 → 0,933). Medido ao vivo (2026-06-11).

### 2. Índice AIMI — correlação com os rótulos (F6.4)

`Spearman(total) = 0,815` ≥ 0,70 ✅ — a heurística v1, sobre a descrição-só, **ranqueia** as startups
como o rótulo (sub-prediz a magnitude, preserva a ordem, que é o que o índice precisa). Por pilar:
**P3 Technical Optimization ρ=+0,76** (o que dispara a graduação, recuperado bem); **P4 Distribution
Moat ρ=+0,18** (o mais fraco — funding/clientes enterprise não vivem numa fixture em prosa; o total
ainda passa porque P4 é 1 de 4).

### 3. Recomendação — techs NVIDIA × esperadas, held-out (F7.2b)

n=20 in-scope (4 `non-AI` fora de escopo, F2.13), 97 recomendações.

| Recorte | precision | recall | F1 |
|---|---|---|---|
| **alvo_graduacao** (a coorte que importa, F6.13) | 0,53 | **0,78** ✅ | 0,63 |
| periférico / wrapper (AIMI baixo) | ~0,06 | 1,00 | ~0,11 |
| maduro | 0,08 | 0,17 | 0,11 |
| **geral** | 0,23 | 0,69 | 0,34 |

**Leitura honesta:** **evidência dos dois lados = 1,00** nas 97 recomendações (invariante duro do
Guardrails F4.5) ✅. O **recall onde importa bate a meta** (alvos de graduação 0,78 ≥ 0,70: a graduação
NIM/TensorRT/Triton **sempre** sai). O recall geral (0,69) é puxado pelo **maduro 0,17** (o rótulo
espera `AI Enterprise`, mas a regra só dispara isso em gap de P4, e madura tem P4 forte). A **precision
baixa (0,23) é super-recomendação** (a regra dispara em todo gap, ~5 techs/empresa; os rótulos esperam
0–4), concentrada nas regiões de AIMI baixo. Ambos são **mismatch regra↔rótulo a reconciliar na F7.1**.

### 4. RAG — RAGAS sobre as perguntas NVIDIA (F7.3)

Consolidado contra os limiares §7 (n=7, proxy lexical determinístico):

| Métrica | valor | meta |
|---|---|---|
| faithfulness | **1,00** ✅ | ≥ 0,80 |
| context recall | 0,69 (léxico) → **0,74** com reranker NeMo real (F7.4) | ≥ 0,70 |
| answer relevancy | 0,54 | (sem meta §7) |
| context precision | 0,98 | (sem meta §7) |

**Leitura:** faithfulness 1,0 porque a resposta avaliada é extrativa (fiel por construção — piso do
CI). O **context recall 0,69** do proxy léxico fica a 0,01 da meta; com o **reranker NeMo real** (F7.4)
sobe a **0,74 ≥ 0,70** — a recuperação certa vem de **reordenar melhor**. O **juiz LLM consolidado**
(lib `ragas` + Nemotron) está **bloqueado pelo ambiente** (conflito de versão `ragas`/
`langchain-community`, adiado no dev-env): o backend `RagasJudge` fica reservado e o CLI degrada limpo
para o proxy. Reproduzível por `--llm --gate` quando a dep for reconciliada.

### 5. Briefing — faithfulness do texto final (F7.2c)

Fidelidade dos **4 campos que o briefing gera** (resumo + 3 eixos do §2) às suas **fontes aterradas**
(diagnóstico + recomendações + fatos do programa Inception + framework de decisão). n=20 in-scope.

| Recorte | faithfulness |
|---|---|
| **média (gate)** | **0,870** ✅ (≥ 0,80; min 0,786) |
| resumo_executivo | 0,967 |
| acao_comercial | 1,000 |
| acao_tecnica | 0,817 |
| acao_comunitaria | 0,800 |

**Leitura:** a espinha determinista só **reafirma** as fontes → fiel por construção (anti-alucinação,
o piso do CI). O valor que importa ao vivo é o do `--llm` (o Super reescreve os 4 campos e pode
derivar) — provado nos testes: injetar uma afirmação sem fonte **derruba** a faithfulness; um refino
fiel a preserva. Juiz LLM sobre o briefing fica reservado (mesmo backend da F7.3).

### 6. Reranker — NeMo Retriever × Cohere Rerank (F7.4)

Três dimensões, mesmo conjunto (n=7), mesmo scorer (comparação justa):

| Reranker | qualidade (RAGAS) | context recall | latência | custo/1k |
|---|---|---|---|---|
| lexical-offline (piso) | 0,802 | 0,69 | 0,21 ms/q | $0 |
| **nv-rerankqa (NeMo, ao vivo)** | **0,823** | **0,74** | ~1002 ms/q | $0 (catálogo) |
| cohere-rerank | — | — | — | indisponível (sem trial key + SDK) |

**Decisão (parcial):** o **NeMo real supera o piso léxico** em qualidade e cruza o gate de recall
(0,74 ≥ 0,70); o custo é **latência** (~1 s/consulta, ida-volta ao NIM do catálogo). O backend Cohere
está **ligado e testado** (`CohereReranker`, modelo multilíngue), mas a coluna fica **pendente da
Cohere trial key + SDK `cohere`** — sem número falso. A decisão NeMo×Cohere final entra aqui quando a
key estiver disponível (`--cohere`).

## Limitações honestas (o que ainda não é real / não bate a meta)

1. **Headline ainda sobre as 24 fixtures sintéticas** — toda métrica acima é "modelo real sobre dados
   de fixture". A **F7.1** já entrega a **metade real automática** (coorte BR raspada ao vivo e
   auto-rotulada, `cohort_real.yaml`), mas o rótulo é do próprio modelo (**baseline circular**) → fica
   fora do headline por padrão. O gap nº 1 que **resta** é a **revisão humana** que promove essas
   entradas reais a ground-truth (`label_source: model → human`).
2. **Recomendação: precision 0,23 (super-recomendação) e maduro recall 0,17** — mismatch regra↔rótulo
   a reconciliar na **revisão de rótulos da F7.1** (parte é rótulo a revisar, ex.: RAPIDS pedido p/
   radiologia onde a regra prescreve Clara/MONAI).
3. **Juiz LLM da RAGAS bloqueado pelo ambiente** (conflito `ragas`/`langchain-community`) — o
   consolidado LLM-judged não rodou; vale o proxy léxico + o ganho do reranker real.
4. **Coluna Cohere do comparativo pendente** da trial key + SDK.
5. **ROI/GPU (F6.8–F6.12) e a camada de coorte (F6.5–F6.7) não construídos** — dependem do cohort
   builder (F1.14) e de serving GPU; o briefing sai sem linha de ROI.

## Reprodução

Defaults offline (CI); flags fazem rede/créditos.

```bash
python -m packages.eval.classification_metrics [--llm]      # classe (F7.2)
python -m packages.eval.aimi_correlation                    # AIMI Spearman (F6.4)
python -m packages.eval.recommendation_metrics              # techs precision/recall (F7.2b)
python -m packages.eval.briefing_faithfulness [--llm]       # faithfulness do briefing (F7.2c)
python -m packages.eval.ragas [--gate] [--llm]              # RAGAS consolidado (F7.3)
python -m packages.eval.reranker_comparison [--nv] [--cohere]  # NeMo × Cohere (F7.4)
```

Baseline RAGAS versionado: `data/eval/rag/baseline.json` (regravado/conferido por `ragas --check`).
