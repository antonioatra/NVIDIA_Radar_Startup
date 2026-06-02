# Rubrica AIMI — AI-Native Maturity Index (definição)

**Artefato:** F0.11. **Status:** definição estável (criada cedo).
**Escopo deste doc:** a **semântica dos 4 pilares** e a **escala 0–25** de cada um. É a
referência de rotulagem do eval set (F1.12) e o contrato semântico que o `classifier` (F2.6, v0)
e a heurística refinada (F6.1, v1) preenchem.

> **Definição × heurística (regra de ouro).** Este documento fixa **o que** cada pilar mede e
> **o que** significa cada faixa de pontos — isso **não muda** entre versões. A **heurística de
> pontuação** (como o modelo decide o número a partir das evidências) evolui: **v0** provisória
> no `classifier` (F2.6), **v1** refinada no diferencial (F6.1). Os rótulos de ground-truth do
> eval set (F1.12) dependem **só desta definição**, nunca da versão da heurística — por isso a
> escala 0–25 é imutável mesmo quando a v1 substitui a v0.

> **Grounding conceitual (§10.1).** Os 4 pilares **não são invenção arbitrária**: derivam da
> própria definição de *AI-native service vs wrapper de LLM* do case, fundamentada em Sequoia
> ("Services as Software"), Emergence ("AI-native services playbook") e NVIDIA ("AI 5-layer
> cake"). Esses materiais são ingeridos na KB em **F3.1d** e, ao serem ingeridos, a *redação*
> dos pilares abaixo é **reconciliada** com eles — **sem mexer na escala 0–25** nem invalidar os
> rótulos já feitos. Se a reconciliação mudar a semântica de um pilar, anota-se aqui (changelog).

---

## 0. Visão geral

**AIMI = soma dos 4 pilares**, cada um de **0 a 25** → score total **0–100**.

| Pilar | O que mede | Dispara recomendação NVIDIA? |
|---|---|---|
| **P1 — Data Moat** | Dados proprietários, feedback loops, ativo de dados defensável | — (mede defensabilidade, não gap de stack) |
| **P2 — Workflow Depth** | Profundidade de automação multi-passo, agentes, integrações | Sim: NeMo Guardrails, orquestração de agentes |
| **P3 — Technical Optimization** | Inferência/fine-tuning/serving próprios vs. API crua | **Sim — principal gatilho:** NIM, TensorRT-LLM, Triton, RAPIDS |
| **P4 — Distribution & Moat** | GTM claro, integração enterprise, lock-in, distribuição | Sim: AI Enterprise |

**Acoplamento arquitetural (F6.3):** **P3 baixo** é o gatilho primário das recomendações de
graduação API → stack otimizada — é o pilar que o GPU Graduation Engine (F6.3) quantifica em ROI.
O índice **alimenta** o recommender; não é decoração.

**Regra de evidência (princípio "tudo com evidência").** Todo sub-score é **exigido com
evidência** (Evidence Validator, F2.7). Sem evidência citável (URL + `fetched_at`) para sustentar
a faixa, o sub-score **não pode subir** acima da faixa "sinais públicos mínimos" (≤ 6). Score alto
sem evidência é bloqueado — não estimado por suposição.

---

## 1. Faixas genéricas da escala 0–25

Cada pilar usa a mesma escala de maturidade (a *semântica* por pilar está nas §§2–5):

| Faixa | Pontos | Significado |
|---|---|---|
| **Ausente** | 0–6 | Sem sinal, ou wrapper puro nessa dimensão. |
| **Emergente** | 7–12 | Sinais iniciais; ainda dependente / raso / não defensável. |
| **Estabelecido** | 13–18 | Capacidade real e recorrente, com evidência clara. |
| **Forte / Defensável** | 19–25 | Diferencial sustentável; difícil de replicar pelos grandes labs. |

---

## 2. P1 — Data Moat (0–25)

**Mede:** o quanto a empresa tem **dados proprietários** e **feedback loops** que melhoram o
produto com o uso — o oposto do wrapper, que não acumula nada além do prompt.

| Faixa | Sinais (evidência pública) |
|---|---|
| 0–6 | Só consome API externa; nenhum dado proprietário aparente; output não realimenta o produto. |
| 7–12 | Coleta dados de uso/clientes, mas sem loop claro de melhoria; dataset não defensável. |
| 13–18 | Dataset proprietário de domínio + sinais de feedback loop (ex.: rotulagem, fine-tuning com dado próprio). |
| 19–25 | Ativo de dados único e crescente, central ao produto, com loop de melhoria contínua difícil de replicar. |

---

## 3. P2 — Workflow Depth (0–25)

**Mede:** profundidade do **workflow** entregue — automação multi-passo, agentes, integrações —
vs. "uma caixa de texto na frente de uma API".

| Faixa | Sinais (evidência pública) |
|---|---|
| 0–6 | Chat/prompt único; sem orquestração; sem integração com sistemas do cliente. |
| 7–12 | Alguns passos encadeados ou integrações pontuais; ainda majoritariamente assistivo. |
| 13–18 | Workflow multi-passo real, agentes/ferramentas, integra-se ao processo operacional do cliente. |
| 19–25 | Automação end-to-end de um resultado de negócio; agentes com governança; substitui processo, não só assiste. |

**Gap → NVIDIA:** workflow profundo sem controle de comportamento → **NeMo Guardrails**;
orquestração de agentes em produção → stack de agentes/governança NVIDIA.

---

## 4. P3 — Technical Optimization (0–25)  ★ gatilho primário

**Mede:** o quanto a empresa **otimiza a própria stack de inferência** — serving, fine-tuning,
quantização, batching — vs. depender 100% de API externa crua. **Pilar baixo = maior upside de
graduação** e gatilho das recomendações NVIDIA (F6.3) + alvo do ROI quantificado (F6.11).

| Faixa | Sinais (evidência pública) |
|---|---|
| 0–6 | 100% API externa; sem serving próprio; sem sinais de custo/latência/governança endereçados. |
| 7–12 | Começou a sentir dor (custo/latência); experimentos pontuais de self-host ou modelo aberto. |
| 13–18 | Serving próprio de parte da carga; otimização (batching/quantização) ou fine-tuning em produção. |
| 19–25 | Stack de inferência própria madura (serving otimizado, modelos próprios), custo/latência sob controle. |

**Gap → NVIDIA (quanto menor P3, mais forte):** **NIM** (deploy otimizado), **TensorRT-LLM**
(otimização de inferência), **Triton** (serving em produção), **RAPIDS/cuDF/cuML** (pipeline de
dados em GPU). O **GPU Graduation Engine (F6.3)** mede o ROI real dessa migração.

---

## 5. P4 — Distribution & Moat (0–25)

**Mede:** **distribuição** e **defensabilidade de mercado** — GTM claro, integração enterprise,
lock-in, contratos — o que separa um AI-native service de um experimento.

| Faixa | Sinais (evidência pública) |
|---|---|
| 0–6 | Sem GTM claro; sem clientes/logos públicos; sem integração enterprise. |
| 7–12 | Tração inicial; alguns clientes; distribuição ainda dependente de canal único. |
| 13–18 | Clientes enterprise, integrações, sinais de contrato/lock-in; GTM repetível. |
| 19–25 | Distribuição defensável, lock-in real, posição de mercado difícil de deslocar. |

**Gap → NVIDIA:** escala enterprise/produção → **NVIDIA AI Enterprise**; programa/benefícios/
go-to-market → **NVIDIA Inception**.

---

## 6. Da rubrica ao produto

- **Classificação (§5.1):** a classe `AI-native | AI-enabled | non-AI` é coerente com o AIMI
  total — faixas de corte ajustadas no eval (F6.4), não fixadas arbitrariamente aqui.
- **Inception Priority (F6.13):** derivado do AIMI = **potencial AI-native × upside NVIDIA**
  (alto P1/P2 com **P3 baixo** = maior prioridade de outreach). Usa esta definição; não a redefine.
- **Explicabilidade:** cada sub-score sai com as evidências que o sustentam ("score de crédito de
  AI-nativeness") — auditável célula a célula.

---

## 7. Changelog de definição
- **v1 (F0.11, kickoff 2026-06-01):** definição inicial dos 4 pilares e escala 0–25.
- **Reconciliação §10.1 (F3.1d):** _pendente_ — registrar aqui qualquer ajuste de redação após
  ingerir Sequoia/Emergence/5-layer cake, confirmando que a escala 0–25 permaneceu intacta.
