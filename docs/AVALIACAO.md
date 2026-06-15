# Relatório de Avaliação — TAPI (NVIDIA Startup AI Radar)

**Tarefa:** F7.5 (consolida F7.2 · F6.4 · F7.2b · F7.2c · F7.3 · F7.4; metodologia/limitações
revisadas após a **F7.1**, com **8 empresas reais curadas** entrando no headline). **Atualizado:** 2026-06-15.

Este relatório reúne, num lugar só e **contra metas declaradas** (§7 do brief), a qualidade aferida
de cada peça do pipeline. O número final é o que os dados mostram; o alvo torna o resultado
interpretável. **Metas abaixo do alvo são reportadas como limitação honesta, não escondidas.**

## Metodologia (ler antes dos números)

- **Conjunto de avaliação (F1.12 + F7.1):** o headline tem agora **32 entradas `human`** = 24 fixtures
  sintéticas (`labeled_startups.yaml`, `synthetic: true`, cobrindo todas as regiões do plano `classe ×
  AIMI`) **+ 8 empresas reais BR curadas** (`cohort_real.yaml`, `synthetic: false`, `evidence_urls`
  rastreáveis). As reais foram raspadas/diagnosticadas pelo pipeline (F1.14) e depois **revisadas por
  humano contra a evidência pública (2026-06-15)**, promovidas de `label_source: model` → `human`
  (curadoria detalhada em `data/eval/README.md`). Logo, **o headline deixou de ser 100% sintético** — o
  gap nº1 de credibilidade. A 9ª real (Semantix) segue `label_source: model` (fora do headline;
  `load_eval_set(include_model=True)` para vê-la). O RAG usa um conjunto à parte de **7 perguntas NVIDIA**
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
| Classificação (F7.2) | macro-F1 | ≥ 0,75 | **0,875** (Nemotron-Super, 24 fixtures) · 0,314 piso offline (n=32) | ✅ fixtures · live c/ reais pendente |
| AIMI (F6.4) | Spearman vs rótulos | ≥ 0,70 | **0,815** (24 fixtures) · 0,685 (n=32, c/ reais) | ⚠️ ✅ na prosa rica |
| Recomendação (F7.2b) | evidência dos 2 lados | = 1,00 | **1,00** (invariante duro F4.5) | ✅ |
| Recomendação (F7.2b) | precision/recall de techs | ≥ 0,70 | recall **0,79** geral / **0,865** nos alvos · precision 0,37 | ✅ recall / ⚠️ precision |
| RAG (F7.3) | RAGAS faithfulness | ≥ 0,80 | **1,00** | ✅ |
| RAG (F7.3 / F7.4) | context recall | ≥ 0,70 | 0,69 (proxy léxico) → **0,74** (reranker NeMo real) | ✅ com NeMo |
| Briefing (F7.2c) | faithfulness do texto final | ≥ 0,80 | **0,870** (espinha; min 0,786) | ✅ |
| Reranker (F7.4) | qualidade (NeMo × Cohere) | decisão com dados | NeMo **0,823** > léxico 0,802; Cohere pendente | ⚠️ Cohere pendente |

## Detalhe por entregável

### 1. Classificação — classe AI-native | AI-enabled | non-AI (F7.2)

Mede a classe predita × rotulada sobre o **mesmo sinal público que a produção vê** (perfil
só-de-descrição). Reporta accuracy + macro-F1 (média não-ponderada por classe, sem deixar a
majoritária mascarar as raras) + matriz de confusão. Com a curadoria (F7.1), o conjunto passou a
**n=32** (24 fixtures + 8 reais curadas).

| Caminho | macro-F1 | accuracy | AI-native recall | n |
|---|---|---|---|---|
| Heurística offline (piso/CI) | 0,314 | 0,313 | 0,18 | 32 (c/ reais) |
| **Nemotron-Super real (produção)** | **0,875** ✅ | 0,917 | 0,933 | 24 (fixtures) |

**Leitura:** o **caminho de produção bate a meta** (0,875 ≥ 0,75) — medido ao vivo em 2026-06-11 sobre
as 24 fixtures. O piso offline caiu 0,38 → **0,314** ao incluir as 8 reais: a heurística determinística
exige Workflow Depth alto e a descrição-de-uma-linha das reais sub-prediz essa magnitude (o Super, com
reasoning, lê o *papel* da IA e recupera AI-native — recall 0,18 → 0,933 nas fixtures). ⏳ **Pendente:**
re-rodar o caminho live (`--llm`) sobre o conjunto n=32 para fixar o macro-F1 headline **com** as reais
(comando em §Reprodução; usa créditos build.nvidia.com).

### 2. Índice AIMI — correlação com os rótulos (F6.4)

**Nas 24 fixtures sintéticas (descrição rica): `Spearman(total) = 0,815` ≥ 0,70 ✅.** Incluindo as 8
reais curadas no headline (n=32): **`Spearman(total) = 0,685`** — abaixo do gate. A queda é **esperada
e honesta**: a heurística v1 pontua **só pela descrição**, e as entradas reais carregam descrição de
**uma linha** (sem funding/clientes/dado proprietário em prosa), então ela "passa fome" justo onde o
rótulo humano usou a evidência externa. Por pilar (n=32): **P3 Technical Optimization ρ=+0,67** (o que
dispara a graduação, ainda o mais forte), P1 Data Moat ρ=+0,62, P2 Workflow ρ=+0,62, **P4 Distribution
Moat ρ=+0,12** (o mais fraco — confirma que GTM/funding não cabem numa frase). **Leitura:** o número
justo da *heurística* é o das fixtures ricas (0,815); o 0,685 mede "ranquear uma empresa por 1 linha",
não a qualidade do índice na produção (que vê a evidência raspada inteira, não a descrição-resumo).
Reportado sem maquiar: a meta passa na prosa rica e falha na prosa pobre.

### 3. Recomendação — techs NVIDIA × esperadas, held-out (F7.2b)

n=28 in-scope (4 `non-AI` fora de escopo, F2.13 — a Unico saiu do non-AI com a curadoria), incluindo
as 8 reais curadas.

| Recorte | precision | recall | F1 |
|---|---|---|---|
| **alvo_graduacao** (a coorte que importa, F6.13) | 0,63 | **0,865** ✅ | 0,73 |
| wrapper (AIMI baixo) | 0,28 | 1,00 | 0,44 |
| periférico | 0,19 | 1,00 | 0,32 |
| maduro | 0,16 | 0,27 | 0,20 |
| **geral** | 0,37 | **0,79** ✅ | 0,51 |

**Leitura honesta:** **evidência dos dois lados = 1,00** (invariante duro do Guardrails F4.5) ✅. As
reais curadas **melhoraram o recall onde importa** — alvos de graduação **0,865** (era 0,78) e geral
**0,79** (era 0,69, agora ≥ 0,70) — porque os alvos reais (Hand Talk/Gupy/Idwall) têm techs de graduação
claras (NIM/TensorRT/Triton) que a regra dispara. O recall geral segue puxado pelo **maduro 0,27** (o
rótulo espera `AI Enterprise`, mas a regra só dispara isso em gap de P4, e madura tem P4 forte). A
**precision 0,37 (super-recomendação)** — a regra dispara em todo gap (~5 techs/empresa; rótulos esperam
0–4) — melhorou (era 0,23) mas segue como limitação conhecida, concentrada nas regiões de AIMI baixo.

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

1. **Headline agora inclui 8 empresas reais curadas** (não é mais 100% sintético — gap nº1 endereçado):
   revisadas por humano contra a evidência pública e promovidas a `label_source: human` (F7.1, 2026-06-15).
   **Honestidade da curadoria:** é uma curadoria *light* — verificação contra fontes públicas + correção
   dos erros do modelo (ex.: Unico `non-AI`→`AI-native/maduro`; Hand Talk/Gupy/Idwall `wrapper`→`alvo`) —
   **não** rotulagem independente do zero. Para as 3 entradas onde o rótulo humano **não** mudou o score
   do modelo (BotCity, Aquarela, Take Blip), a correlação AIMI dessas linhas conserva resíduo circular. A
   9ª real (Semantix) segue fora do headline (região pendente). Ampliar a coorte curada é o próximo ganho.
2. **Recomendação: precision 0,23 (super-recomendação) e maduro recall 0,17** — mismatch regra↔rótulo
   a reconciliar na **revisão de rótulos da F7.1** (parte é rótulo a revisar, ex.: RAPIDS pedido p/
   radiologia onde a regra prescreve Clara/MONAI).
3. **Juiz LLM da RAGAS bloqueado pelo ambiente** (conflito `ragas`/`langchain-community`) — o
   consolidado LLM-judged não rodou; vale o proxy léxico + o ganho do reranker real.
4. **Coluna Cohere do comparativo pendente** da trial key + SDK.
5. **ROI/GPU (F6.8–F6.12) não construído como medição ao vivo** — depende de serving GPU; o briefing sai
   sem linha de ROI por padrão (engine atrás de flag — ver PROXIMOS-PASSOS §D). A **camada de coorte
   (F6.5–F6.7) já foi entregue em CPU** (clustering + radar).

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
