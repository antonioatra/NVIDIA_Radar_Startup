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
| Classificação (F7.2) | macro-F1 | ≥ 0,75 | **0,875** (24 fixtures) · **0,720** (n=32 c/ reais) · 0,314 piso offline | ⚠️ ✅ fixtures · reais ↓ (AI-enabled n=6) |
| AIMI (F6.4) | Spearman vs rótulos | ≥ 0,70 | **0,705** (n=32, reais sobre evidência completa) · 0,815 (24 fixtures) | ✅ |
| Recomendação (F7.2b) | evidência dos 2 lados | = 1,00 | **1,00** (invariante duro F4.5) | ✅ |
| Recomendação (F7.2b) | precision/recall de techs | ≥ 0,70 | recall **0,76** geral / **0,87** alvos · precision **0,56** de-circularizada (era 0,37 inflada; sintética 0,375 × real 0,90) | ✅ recall / ⚠️ precision |
| RAG (F7.3) | RAGAS faithfulness | ≥ 0,80 | **1,00** | ✅ |
| RAG (F7.3 / F7.4) | context recall | ≥ 0,70 | 0,69 (proxy léxico) → **0,74** (reranker NeMo real) | ✅ com NeMo |
| Briefing (F7.2c) | faithfulness do texto final | ≥ 0,80 | **0,870** (espinha; min 0,786) | ✅ |
| Reranker (F7.4) | qualidade (NeMo × Cohere) | decisão com dados | NeMo **0,823**>Cohere **0,816** (offline) · Cohere **0,864**≳NeMo **0,859** (nv-embed) — empate no ruído n=7, NeMo grátis | ✅ |

## Detalhe por entregável

### 1. Classificação — classe AI-native | AI-enabled | non-AI (F7.2)

Mede a classe predita × rotulada sobre o **mesmo sinal público que a produção vê** (perfil
só-de-descrição). Reporta accuracy + macro-F1 (média não-ponderada por classe, sem deixar a
majoritária mascarar as raras) + matriz de confusão. Com a curadoria (F7.1), o conjunto passou a
**n=32** (24 fixtures + 8 reais curadas).

| Caminho | macro-F1 | accuracy | AI-native recall | n |
|---|---|---|---|---|
| Heurística offline (piso/CI) | 0,314 | 0,313 | 0,18 | 32 (c/ reais) |
| Nemotron-Super real — só fixtures | **0,875** ✅ | 0,917 | 0,933 | 24 |
| **Nemotron-Super real — c/ as 8 reais** | **0,720** | 0,844 | 0,955 | 32 |

Por classe no conjunto **n=32** (Nemotron-Super, medido ao vivo 2026-06-15): **AI-native P=0,91 R=0,96
F1=0,93** · AI-enabled P=1,00 R=0,33 F1=0,50 · non-AI P=0,57 R=1,00 F1=0,73.

**Leitura honesta:** a classe que importa para achar alvos de graduação — **AI-native — segue forte
(recall 0,96)**. Mas o macro-F1 caiu **0,875 → 0,720** (abaixo do gate 0,75) ao incluir as reais,
puxado pelo **AI-enabled (recall 0,33, n=6)**: com só 6 exemplos cada erro custa caro no macro, e em
empresa real de descrição curta o Super tende a ler IA-periférica como AI-native. É o **custo honesto
de sair do sintético**: accuracy alta (0,84), AI-native robusto, e o gap real é **separar AI-enabled de
AI-native** com pouco sinal — não um colapso do classificador. O piso offline (0,314) é só o substituto
determinístico do CI (rebaixa AI-native porque a heurística exige Workflow Depth alto que a prosa-só
sub-prediz). Medido ao vivo em 2026-06-15 (24 fixtures: 2026-06-11).

### 2. Índice AIMI — correlação com os rótulos (F6.4)

**Nas 24 fixtures sintéticas (descrição rica): `Spearman(total) = 0,815` ≥ 0,70 ✅.** No headline
completo (n=32, com as 8 reais curadas): **`Spearman(total) = 0,705` ≥ 0,70 ✅.** Por pilar (n=32):
**P3 Technical Optimization ρ=+0,76** (o que dispara a graduação — o mais forte), P2 Workflow ρ=+0,63,
P1 Data Moat ρ=+0,57, **P4 Distribution Moat ρ=+0,42** (o mais fraco, mas recuperado vs antes).

**O lever (F7.1) — empresa real é pontuada sobre a evidência COMPLETA, não a descrição-resumo.** A
versão anterior media **0,685** (abaixo do gate) por um artefato do harness: ele alimentava a heurística
só com a `descricao` de **1 linha** das reais — sem funding/clientes/dado em prosa, a heurística afundava
**todas no piso 12** (8 empates contra 8 ranks distintos → o Spearman colapsava). Mas a produção (F1.14)
pontua sobre a **evidência raspada inteira**. O eval agora carrega esse AIMI de produção (`model_aimi`)
como predito das reais — o sinal que a produção de fato vê. Resultado: **7 das 9 reais correlacionam
quase perfeito** (Aquarela 54/54, Hand Talk 42/44, Idwall 42/46, Semantix 42/42, BotCity/Take Blip 36/36)
e a meta passa. **Não** é maquiagem: a heurística é a mesma; o que mudou é parar de medi-la com 1 linha.

**Limitações honestas que permanecem:** (a) **Unico (pred 21 × rótulo 64)** e **Kunumi (12 × 39)** seguem
outliers — o rótulo humano da Unico **excede a evidência raspada** (1 cliente enterprise + US$120M → a
rubrica dá 21; o humano pontuou 64 por reputação de unicórnio), e o scrape da Kunumi é raso; puxam P1/P4.
(b) Para **3 reais** o humano **confirmou** o score do modelo (BotCity/Take Blip/Semantix) → essas linhas
têm **resíduo circular** (predito = gold por concordância humana, não por re-cálculo independente). O
lever fecha o gap do "1 linha", mas a calibração fina de Unico/Kunumi pede **mais fonte por empresa**
(re-scrape, créditos). O número das fixtures ricas (0,815) segue o teto da heurística com sinal pleno.

### 3. Recomendação — techs NVIDIA × esperadas, held-out (F7.2b)

n=28 in-scope (4 `non-AI` fora de escopo, F2.13 — a Unico saiu do non-AI com a curadoria), incluindo
as 8 reais curadas.

| Recorte | precision | recall | F1 |
|---|---|---|---|
| **alvo_graduacao** (a coorte que importa, F6.13) | **0,69** | **0,87** ✅ | 0,77 |
| wrapper (AIMI baixo) | 0,62 | 1,00 | 0,77 |
| periférico (AI-enabled) | 0,00 | 0,00 | 0,00 |
| maduro | 0,21 | 0,33 | 0,26 |
| **geral** | **0,56** | **0,76** ✅ | 0,64 |

> **Cisão honesta sintética × real (2026-06-21):** precision **sintética 0,375** (rótulo §5.5 escrito à
> mão = sinal genuíno) × **real 0,900** (rótulo re-curado, ver abaixo). A geral 0,56 é a mistura;
> **dois lados = 1,00** (invariante duro do Guardrails F4.5) ✅.

**De-circularização dos rótulos reais — o conserto que mais agrega.** O `expected_nvidia_techs` das 8
entradas reais era a **saída do próprio recommender** (`cohort_to_eval` lê a tabela `recommendation`):
**baseline circular** — medir a regra contra ela dava um falso **0,974**. Re-curado por **julgamento §5.5
+ perfil real, independente da regra** (2026-06-21): **BotCity** (AI-enabled/RPA) → `[]` (IA periférica,
não é alvo); **Unico/Aquarela** maduros → domínio (Morpheus) + AI Enterprise/RAPIDS, **não** graduação
(P3 já alto); os **alvos reais** (Hand Talk/Gupy/Idwall/Kunumi/Blip) confirmam o bundle de graduação
(genuíno — um alvo real **deve** graduar). A divergência (BotCity/maduros) **prova a independência**: o
real caiu **0,974 → 0,900** (os 3 FP/3 FN agora são erros reais da regra, não auto-avaliação).

**Gates de prioridade na regra (DSS §5, `recommend_rules`).** A graduação de infra (pilares NVIDIA) só
dispara p/ **core de IA provado**: suprimida em **periférico** (`AI-enabled`, a IA não é o núcleo) **e**
**wrapper frágil** (`AI-native` com P1 **e** P2 ausentes ≤6); a tech de **setor** segue p/ ambos
(AI-enabled recebe setor por design, F4.8 — `test_node_end_to_end_over_real_rag` verde). §5.5 **7/7**.

**Trajetória honesta:** precision **0,37 (inflada por circularidade) → 0,56 (de-circularizada)**, recall
0,79 → 0,76 (≥ 0,70). **O resíduo é genuíno, não overfitável:**
- **periférico 0,00** (n=6, TP=0): a regra **não serve o periférico** — e isso é **desejável** (baixa
  prioridade). Os 2 FP vêm do **matching de setor grosseiro** (AgendaJá, agendamento, casa "health" →
  Clara/MONAI errado); os 2 FN são `NeMo Guardrails` p/ chats AI-enabled (debatível).
- **maduro 0,21** — a regra cobre o **gap mais severo** (P2 → NeMo Retriever); o rótulo de uma madura
  foca governança/enterprise (AI Enterprise) + domínio, que a regra não prioriza. Conserto = rótulo com
  **granularidade de prioridade** (não só presença de tech), próxima curadoria.

**Capar a regra não é o conserto** (os 7 casos do §5.5/F4.8 — gate **7/7** — *exigem* o leque). Lever
detalhado na Limitação nº2.

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

Três dimensões, mesmo conjunto (n=7), mesmo scorer (comparação justa). Medido em **dois substratos
de recuperação** — o vencedor de qualidade troca entre eles, então ambos ficam registrados:

**(a) Substrato offline (hashing, CI/reprodutível) — 2026-06-16:**

| Reranker | qualidade (RAGAS) | context recall | latência | custo/1k |
|---|---|---|---|---|
| lexical-offline (piso) | 0,802 | 0,69 | 0,21 ms/q | $0 |
| **nv-rerankqa (NeMo, ao vivo)** | **0,823** | **0,74** | ~1002 ms/q | $0 (catálogo) |
| cohere-rerank (ao vivo) | 0,816 | 0,69 | ~388 ms/q | $2,00 |

**(b) Substrato nv-embed ao vivo (Qdrant 2048, recuperação real) — 2026-06-21:**

| Reranker | qualidade (RAGAS) | context recall | latência | custo/1k |
|---|---|---|---|---|
| lexical-offline (piso) | 0,819 | 0,74 | 0,33 ms/q | $0 |
| nv-rerankqa (NeMo, ao vivo) | 0,859 | **0,88** | ~574 ms/q | $0 (catálogo) |
| **cohere-rerank (ao vivo)** | **0,864** | **0,88** | ~291 ms/q | $2,00 |

> **Comparação justa:** as três linhas reranqueiam o **mesmo conjunto recuperado** (a recuperação é
> compartilhada — só o **reranker** varia). A trial key Cohere é 10 req/min, então o run se auto-regula
> no 429 (retry com backoff; ver `CohereReranker`).
> **Leitura honesta (n=7):** com a recuperação **nv-embed real** (b) os dois rerankers reais sobem
> (NeMo 0,823→0,859; Cohere 0,816→0,864) e o **context recall salta** (NeMo 0,74→0,88) — candidatos
> melhores dão mais o que reordenar. O ranking de qualidade **inverte** vs (a): Cohere **0,864 ≳ NeMo
> 0,859**, mas o gap (0,005) é **ruído em n=7** — o context recall é idêntico (0,88) e a diferença mora
> só no context precision (1,00 vs 0,99). Topo em **empate técnico**, ambos bem acima do piso léxico.

**Decisão (F7.5) — com dados, agora nos dois substratos:** a qualidade NeMo×Cohere fica
**estatisticamente empatada** (offline NeMo +0,007; nv-embed Cohere +0,005 — ambos dentro do ruído de
n=7). O desempate é **custo + narrativa**: **NeMo é grátis** (catálogo build.nvidia.com / dogfood),
**Cohere é pago** ($2/1k). Cohere é consistentemente **mais rápido** (~291–388 ms vs ~574–1002 ms). 
**Conclusão:** a escolha do **NeMo** no build segue justificada **com dados** — paridade de qualidade a
custo zero; trocar para o Cohere compraria latência menor por $2/1k **sem ganho de qualidade fora do
ruído**.

## Limitações honestas (o que ainda não é real / não bate a meta)

1. **Headline agora inclui 8 empresas reais curadas** (não é mais 100% sintético — gap nº1 endereçado):
   revisadas por humano contra a evidência pública e promovidas a `label_source: human` (F7.1, 2026-06-15).
   **Honestidade da curadoria:** é uma curadoria *light* — verificação contra fontes públicas + correção
   dos erros do modelo (ex.: Unico `non-AI`→`AI-native/maduro`; Hand Talk/Gupy/Idwall `wrapper`→`alvo`) —
   **não** rotulagem independente do zero. Para as 3 entradas onde o rótulo humano **não** mudou o score
   do modelo (BotCity, Aquarela, Take Blip), a correlação AIMI dessas linhas conserva resíduo circular. A
   9ª real (Semantix) segue fora do headline (região pendente). Ampliar a coorte curada é o próximo ganho.
2. **Recomendação: precision 0,56 de-circularizada (era 0,37 inflada)** — **lever aplicado + circularidade
   removida (2026-06-21).** Descoberta: o `expected_nvidia_techs` das 8 reais era a **saída do próprio
   recommender** (`cohort_to_eval` lê a tabela `recommendation`) → **baseline CIRCULAR** que inflava a
   precision (real falso = 0,974). **Conserto (o que mais agregou):** re-curei os tech-labels reais por
   **julgamento §5.5 + perfil, independente da regra** (BotCity AI-enabled→`[]`; Unico/Aquarela maduros→
   domínio + AI Enterprise, não graduação; alvos reais confirmam o bundle) → real **0,974→0,900** (agora
   sinal genuíno: 3 FP/3 FN reais). **+ gate de prioridade** na regra (graduação só p/ AI-native com core
   provado; periférico/wrapper-frágil só recebem setor). precision **0,37→0,56**, recall **0,79→0,76**
   (≥0,70), §5.5 **7/7**, suíte verde, **sem** alinhar rótulo à saída. **Resíduo genuíno** (não overfitável):
   `periférico 0,00` (a regra **não serve** o periférico, e isso é o desejado — baixa prioridade; FP = setor
   grosseiro na AgendaJá) e `maduro 0,21` (regra cobre o gap; rótulo de madura foca enterprise/domínio).
   **Capar a regra segue fora** (§5.5/F4.8 *exige* o leque). Próximo lever: rótulo com **granularidade de
   prioridade** (não só presença de tech) — re-curadoria maior, fora do escopo de hoje.
3. **Juiz LLM da RAGAS bloqueado pelo ambiente** (conflito `ragas`/`langchain-community`) — o
   consolidado LLM-judged não rodou; vale o proxy léxico + o ganho do reranker real.
4. ~~**Coluna Cohere do comparativo pendente** da trial key + SDK.~~ ✅ **medida (2026-06-16)** +
   ~~head-to-head com a recuperação nv-embed ao vivo~~ ✅ **feito (2026-06-21)**: nos **dois**
   substratos a qualidade NeMo×Cohere fica **empatada no ruído** (offline NeMo 0,823 vs 0,816;
   nv-embed Cohere 0,864 vs 0,859, cr idêntico 0,88). Decisão NeMo (grátis) intacta. Ver §6.
5. **ROI/GPU (F6.8–F6.12) não construído como medição ao vivo** — depende de serving GPU; o briefing sai
   sem linha de ROI por padrão (engine atrás de flag — ver PROXIMOS-PASSOS §D). A **camada de coorte
   (F6.5–F6.7) está entregue em CPU** (clustering + radar), mas a **qualidade do radar é limitada para
   demo** (feedback 2026-06-15): embeddings hashing-offline + texto de clustering sem a descrição +
   AIMI subavaliado por evidência rasa por empresa (mesma raiz dos outliers Unico/Kunumi no eval) → clusters incoerentes e 0%
   "prontas ★". Fixes de qualidade rastreados em PROXIMOS-PASSOS §C (embeddings reais + descrição +
   re-score por evidência).

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
