# Alinhamento — Critérios de Caracterização & Apoio à Decisão

**Status:** referência canônica (apresentação + implementação). **Escopo:** consolida, num só
lugar, **(I)** como o TAPI *caracteriza* uma startup e **(II)** os *métodos e sistemas de apoio à
decisão* construídos sobre essa caracterização. É a fonte de verdade narrativa; os detalhes
operacionais vivem em [`ARQUITETURA.md`](../ARQUITETURA.md), [`RUBRICA-AIMI.md`](RUBRICA-AIMI.md)
e nas tasks ([F4](tasks/04-recomendacao.md), [F6](tasks/06-diferencial.md)).

> **Por que este doc existe.** O brief faz duas perguntas implícitas: *como você descreve/qualifica
> uma startup?* (caracterização) e *como isso vira decisão para o gerente do Inception?* (apoio à
> decisão). Este documento fixa as respostas e a ponte com o vocabulário do brief (§1, §2, §5.1,
> §5.5, §6), para que apresentação e código contem a **mesma** história.

---

## Parte I — Critérios de caracterização das startups

### 1. As três camadas (do bruto ao sintético)

A caracterização não é um único rótulo: são **três camadas encaixadas**, cada uma alimentando a
seguinte. Todas com **proveniência** (URL + `fetched_at`).

| Camada | Artefato (schema) | O que é | Origem no brief |
|---|---|---|---|
| **1. Perfil** | `StartupProfile` | a "ficha" estruturada da empresa | §2 (empresa, produto, setor, clientes, funding, founders, tecnologias) |
| **2. Classe** | `Classification` | *papel* da IA no produto (qualitativo) | §5.1 / §6 ("Diagnóstico de maturidade AI-native") |
| **3. AIMI** | `AIMIScore` | *maturidade/defensabilidade* (quantitativo, 0–100) | diferencial (Entregável 6), fundamentado no §10.1 |

### 2. Camada 1 — Perfil estruturado (`StartupProfile`)

Cobre **todas** as dimensões do §2, cada campo carregando a evidência que o sustenta (`Claim`/
`Evidence`). É a matéria-prima dos dois eixos de diagnóstico:

| Campo do perfil | Alimenta principalmente |
|---|---|
| `tecnologias` (stack, providers, serving) | **P3 — Technical Optimization** (gatilho NVIDIA) |
| `clientes` (enterprise?) | **P4 — Distribution & Moat**, **P1 — Data Moat** |
| `produtos` / `descricao` | **classe** + **P2 — Workflow Depth** |
| `funding` | prontidão de coorte (F6.7), sinal de P4 |
| `founders` | contexto (só info profissional pública — LGPD) |

### 3. Camada 2 — Classe: o *papel* da IA (eixo qualitativo)

Três classes (§5.1), decididas **sobretudo pela descrição do produto e por Workflow Depth** — *a
IA entrega o resultado ou só assiste?* — **não** pelo total do AIMI:

- **`AI-native`** — a IA é o **núcleo** do produto/moat.
- **`AI-enabled`** — a IA é **periférica** sobre um produto não-IA.
- **`non-AI`** — sem uso material de IA → fora do alvo Inception (briefing `fora_de_escopo`, F2.13).

### 4. Camada 3 — AIMI: a *maturidade* (eixo quantitativo)

Índice **0–100** = soma de **4 pilares de 0–25**. Definição imutável em
[`RUBRICA-AIMI.md`](RUBRICA-AIMI.md); aqui, o resumo:

| Pilar | Mede | Dispara tech NVIDIA |
|---|---|---|
| **P1 — Data Moat** | dados proprietários, feedback loops | — (mede defensabilidade) |
| **P2 — Workflow Depth** | automação multi-passo, agentes, integração | NeMo Guardrails, agentes |
| **P3 — Technical Optimization** ★ | inferência/serving próprios vs. API crua | **NIM, TensorRT-LLM, Triton, RAPIDS** |
| **P4 — Distribution & Moat** | GTM, enterprise, lock-in | AI Enterprise |

Cada pilar usa a mesma escala: **Ausente** (0–6) · **Emergente** (7–12) · **Estabelecido**
(13–18) · **Forte/Defensável** (19–25).

### 5. O plano `classe × AIMI` — onde mora o *wrapper* e o *alvo de graduação*

Esta é a ideia central que amarra o case. Cruzar os dois eixos revela que **"wrapper" não é uma
classe** — é uma **região** do plano: empresa que se posiciona como `AI-native` (a IA é o núcleo)
mas tem **AIMI baixo**, sobretudo **P1** (sem dado proprietário) e **P3** (100% API externa). É
exatamente quem o §1 do brief descreve como ameaçada pelos grandes labs.

| Região | classe | AIMI | Leitura para o Inception |
|---|---|---|---|
| Fora de escopo | `non-AI` | — | não é alvo (`fora_de_escopo`, F2.13) |
| Periférico | `AI-enabled` | qualquer | baixa prioridade (IA não é o núcleo) |
| **Wrapper frágil** | `AI-native` | baixo em ~todos os pilares | risco de substituição; potencial ainda não comprovado |
| **Alvo de graduação ★** | `AI-native` | **P1/P2 alto · P3 baixo** | **maior upside NVIDIA** → topo da fila (Inception Priority, F6.13) |
| Maduro / defensável | `AI-native` | alto em todos | já forte; foco em comunidade/enterprise (P4) |

> **A virada do produto:** o radar não premia só quem já é maduro. Ele identifica o **AI-native com
> moat real (P1/P2) mas stack imatura (P3 baixo)** — a startup com mais a ganhar graduando para a
> stack NVIDIA. É aí que diagnóstico e recomendação se encontram.

### 6. Princípios travados da caracterização

- **Tudo com evidência (invariante de código).** Sub-score > 6 sem evidência citável é **rejeitado**
  pelo validator (`PillarScore`); não é estimado por suposição.
- **Critérios não arbitrários (grounding §10.1).** Os 4 pilares derivam da definição *AI-native vs
  wrapper* (Sequoia "Services as Software", Emergence "AI-native services playbook", NVIDIA
  "5-layer cake"), ingerida na KB em F3.1d.
- **Definição estável × heurística evolutiva.** A régua (pilares + escala 0–25) é fixa; só o *como
  pontuar* evolui (`heuristic_version` v0 F2.6 → v1 F6.1). Os rótulos do eval set (F1.12) dependem
  só da definição — nunca da versão do modelo.
- **Explicável célula a célula** ("score de crédito de AI-nativeness"): cada sub-score sai com as
  evidências que o sustentam.

---

## Parte II — Métodos e sistemas para apoio à decisão

### 7. O TAPI como Sistema de Apoio à Decisão (DSS)

O usuário final é o **gerente de Startups & VCs / NVIDIA Inception** (§1). A decisão que ele toma é:
*quem atrair, qualificar e nutrir — e o que oferecer a cada um.* O TAPI estrutura isso em **três
níveis de decisão**, cada um com seu método e seu artefato:

| Nível | Pergunta de decisão | Método | Sistema/artefato | Tasks |
|---|---|---|---|---|
| **1. Por empresa** | *O que ofereço a esta startup?* | gap (AIMI) × tech NVIDIA (RAG) → recomendação + ROI | **Briefing executivo** (3 eixos §2) | F4 · F6.3/F6.11 |
| **2. Priorização** | *Quem abordo primeiro?* | Inception Priority 0–100 (potencial × upside) | **fila priorizada** + filtro por tech (UI) | F6.13 · F5.4/F5.11 |
| **3. Portfólio** | *Onde está o ecossistema?* | clustering de coorte (cuML) | **radar** de clusters graduation-ready | F6.5–F6.7 |

### 8. Nível 1 — decisão por empresa: *diagnosticar → prescrever → quantificar*

O método central. Três passos encadeados:

1. **Diagnosticar** (F2/F6.1): o pilar fraco do AIMI — sobretudo **P3 (Technical Optimization)** —
   é o **gatilho** (F6.3). Pilar baixo = maior gap = maior upside de graduação.
2. **Prescrever** (F4.2): o recommender cruza o **gap** (lado startup) com a **citação da KB NVIDIA**
   recuperada pelo RAG dirigido pelos gaps (F3.7). Mapa base de regras gap→tech vem dos exemplos do
   §5.5 (F4.1).
3. **Quantificar** (F6.11): o **GPU Graduation Engine** anexa o **ROI** real (throughput, p95,
   custo $/1M tokens) mapeando o perfil para a célula da matriz de benchmark pré-computada.

A saída é o `Recommendation` — formato **§5.5**, ver §10 abaixo — e o **Briefing executivo**
(`BriefingStatus.normal`), em **PT-BR** (F0.13), com próximas-ações nos **três eixos do §2**:
**comercial · técnica · comunitária** (onboarding, créditos, comunidade, eventos, GTM do Inception).

> Variantes de borda do briefing: **`dados_insuficientes`** (F2.12, evidência insuficiente após
> retry — não alucina) e **`fora_de_escopo`** (F2.13, `non-AI` de alta confiança — explica por que
> não é alvo, sem forçar recomendação).

### 9. Nível 2 — priorização: Inception Priority (fila de outreach)

Score **0–100 por empresa** (F6.13) derivado do AIMI = **potencial AI-native × upside NVIDIA**:
alto **P1/P2** (moat e workflow reais) com **P3 baixo** (stack imatura) = topo da fila — é a região
"alvo de graduação" do §5. Serve direto o §1 ("atrair, qualificar e nutrir"): entrega ao gerente uma
**fila priorizada**, não só diagnósticos avulsos. Sem GPU (puro AIMI). Explicável: cada score sai
com os fatores que o compõem. Exibido na lista da UI (F5.4) e ordenável; **complementa** o ranking
de *clusters* do nível 3 (ranqueia *empresas*).

### 10. Nível 3 — portfólio: radar de coorte

Visão de mercado, não consultas avulsas. O cohort builder em lote (F1.14) popula a tabela `company`;
`cuDF` normaliza/deduplica (F6.5); embeddings de setor/perfil (reusa `nv-embedqa`) → `cuML`
(KMeans + UMAP) clusteriza (F6.6); o **radar** ranqueia clusters "graduation-ready" para o Inception
(F6.7). Dá ao gerente uma **leitura de portfólio do ecossistema BR**.

### 11. Aderência ao §5.5 do brief (contrato `Recommendation`)

A saída do motor de recomendação entrega **exatamente** o que o §5.5 pede — e vai além em dois
pontos:

| §5.5 pede | Campo `Recommendation` | Extra do TAPI |
|---|---|---|
| Tecnologias NVIDIA | `tech` | — |
| Justificativa técnica | `justificativa_tecnica` | — |
| Justificativa de negócio | `justificativa_negocio` | — |
| Nível de prioridade | `prioridade` | — |
| Complexidade de implementação | `complexidade` | — |
| Próxima ação | `proxima_acao` | — |
| Evidências usadas | `evidencia_gap` + `evidencia_nvidia` | **evidência dos DOIS lados** |
| — | `roi` (`ROIEstimate`) | **ROI quantificado** (gap de inferência) |
| — | `pilar_origem` | rastreabilidade gap → tech |

### 12. Garantias de confiabilidade da decisão

O que faz a decisão ser **defensável** (e não um chute de LLM):

- **Evidência dos dois lados (invariante de schema + Guardrails F4.5).** Nenhuma recomendação sem
  `evidencia_gap` **E** `evidencia_nvidia` — o validator do `Recommendation` rejeita; o NeMo
  Guardrails reforça no briefing. Bloqueia recomendação alucinada por construção.
- **RAG com citações + reranking** (Entregável 3): a justificativa NVIDIA vem de trecho recuperado e
  citável, avaliado com RAGAS (faithfulness ≥ 0,80).
- **Estado terminal honesto:** sem evidência suficiente, o sistema emite `dados_insuficientes` —
  não inventa.
- **Fallbacks de de-risking (F6):** matriz de ROI sempre pré-computada; vLLM se NIM/Triton não
  subir; clustering em CPU (scikit-learn) se cuML falhar. A narrativa do apoio à decisão se mantém
  mesmo se o caminho GPU travar.

---

## Mapa de rastreabilidade (brief ↔ artefato ↔ task)

| Brief | Caracterização / Decisão | Artefato | Task |
|---|---|---|---|
| §2 dados públicos | Perfil estruturado | `StartupProfile` | F2.5 |
| §5.1 / §6 classe | Classe (papel da IA) | `Classification` | F2.6 |
| §10.1 AI-native | AIMI (maturidade) | `AIMIScore` (4 pilares) | F2.6 / F6.1 |
| §1 atrair/qualificar | Priorização de outreach | `inception_priority` | F6.13 |
| §5.5 recomendação | Decisão por empresa | `Recommendation` | F4.2–F4.3 |
| §5.3 RAG+rerank | Evidência NVIDIA citável | `evidencia_nvidia` | F3.7 |
| §2 briefing | Artefato de decisão | Briefing (3 eixos) | F4.4 |
| Entregável 6 | ROI + portfólio | `ROIEstimate` + radar | F6.5–F6.11 |
