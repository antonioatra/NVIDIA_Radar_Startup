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
> ("Services: The New Software" — copiloto × autopiloto), Emergence ("The AI-Native Services
> Playbook" — data flywheel + teste "Mirage PMF") e NVIDIA ("AI Is a 5-Layer Cake"). Esses
> materiais foram **ingeridos na KB em F3.1d** (`source_type: grounding`, §10.1) e a *redação*
> dos pilares abaixo foi **reconciliada** com eles — **sem mexer na escala 0–25** nem invalidar
> os rótulos já feitos (ver changelog §7). A reconciliação **confirmou** a semântica dos 4
> pilares (cada um cita agora a fonte de grounding); nenhuma mudança semântica foi necessária.

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

> *Grounding (§10.1):* o **data flywheel** da Emergence ("cada engajamento deixa a IA melhor") e
> a **composição de dados** da Sequoia (julgamento proprietário que aprofunda a defensabilidade).

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

> *Grounding (§10.1):* o **autopiloto** da Sequoia ("vender o trabalho, não a ferramenta") e o
> "**você É a implementação**" da Emergence — a IA *entrega* o resultado, não só assiste.

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

> *Grounding (§10.1):* o **"5-layer cake"** da NVIDIA (a aplicação puxa as camadas de modelos/infra
> abaixo dela) e a **"corrida contra o modelo"** da Sequoia (wrapper sobre API crua é frágil) — a
> graduação para a stack própria é descer essas camadas. É o teste de margem "Mirage PMF" da
> Emergence em forma técnica.

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

> *Grounding (§10.1):* a **profundidade de integração** / virar *system of record* da Emergence e
> a cunha **trabalho terceirizado → insourced** da Sequoia (o gasto com mão de obra como TAM).

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

A caracterização final cruza **dois eixos** — e **não** os confunde (visão completa em
[`ALINHAMENTO-CRITERIOS-E-DECISAO.md`](ALINHAMENTO-CRITERIOS-E-DECISAO.md)):

- **Eixo qualitativo — classe (§5.1): o *papel* da IA no produto.** `AI-native` (IA é o núcleo do
  resultado) · `AI-enabled` (IA periférica sobre produto não-IA) · `non-AI` (sem IA material).
  Decidido sobretudo pela **descrição do produto** e por **Workflow Depth** (a IA *entrega* o
  resultado ou só assiste?), **não** pelo total do AIMI.
- **Eixo quantitativo — AIMI (0–100): a *maturidade/defensabilidade* dessa AI-nativeness.**

**Por que separar os eixos (coração do case).** Um *wrapper* se **posiciona** como AI-native (a IA é
o núcleo), mas tem **AIMI baixo** — sobretudo **P1** (sem dado proprietário) e **P3** (100% API
externa). Logo, *wrapper não é uma classe*: é uma **região** do plano `classe × AIMI` (`AI-native` +
AIMI baixo). É exatamente o público do §1 do brief — empresas ameaçadas pelos labs, que a NVIDIA
quer **identificar** e **ajudar a graduar** a stack.

**Mapa de decisão (plano `classe × AIMI`):**

| Região | classe | AIMI | Leitura para o Inception |
|---|---|---|---|
| Fora de escopo | `non-AI` | — | não é alvo (briefing `fora_de_escopo`, F2.13) |
| Periférico | `AI-enabled` | qualquer | baixa prioridade (IA não é o núcleo) |
| **Wrapper frágil** | `AI-native` | baixo em ~todos os pilares | risco de substituição; potencial não comprovado |
| **Alvo de graduação ★** | `AI-native` | **P1/P2 alto · P3 baixo** | **maior upside NVIDIA** → topo da fila (F6.13) |
| Maduro / defensável | `AI-native` | alto em todos | já forte; foco em comunidade/enterprise (P4) |

- **Cortes classe ↔ AIMI:** os limiares numéricos são **calibrados no eval (F6.4)**, não fixados
  arbitrariamente. Guia **provisória/ilustrativa** (a ser substituída pelo eval): `non-AI` sem sinal
  de IA no produto; `AI-enabled` quando há IA mas **Workflow Depth ≲ 8** sobre produto não-IA;
  `AI-native` quando a IA é o núcleo da descrição **e** há sinal em Workflow Depth — **independente
  do total** (um `AI-native` pode ter AIMI baixo: é o wrapper). A coerência exigida é **direcional**
  (um `non-AI` não pode ter Workflow Depth alto *por IA*), não um corte rígido no total.
- **Inception Priority (F6.13):** derivado do AIMI = **potencial AI-native × upside NVIDIA**
  (alto P1/P2 com **P3 baixo** = maior prioridade de outreach). Usa esta definição; não a redefine.
- **Explicabilidade:** cada sub-score sai com as evidências que o sustentam ("score de crédito de
  AI-nativeness") — auditável célula a célula.

---

## 7. Changelog de definição
- **v1 (F0.11, kickoff 2026-06-01):** definição inicial dos 4 pilares e escala 0–25.
- **Alinhamento classe × AIMI (2026-06-03):** §6 reescrita para separar explicitamente o eixo
  qualitativo (classe = papel da IA) do quantitativo (AIMI = maturidade), introduzindo o **plano
  `classe × AIMI`**, a **região wrapper** e a **guia provisória de cortes** (calibração final no
  eval F6.4). **Não** altera a escala 0–25 nem a semântica dos pilares (§§2–5) — só explicita como a
  rubrica vira classe/produto. Origem: [`ALINHAMENTO-CRITERIOS-E-DECISAO.md`](ALINHAMENTO-CRITERIOS-E-DECISAO.md).
- **Reconciliação §10.1 (F3.1d, 2026-06-07):** materiais ingeridos na KB (`source_type: grounding`,
  §10.1): Sequoia "Services: The New Software", Emergence "The AI-Native Services Playbook", NVIDIA
  "AI Is a 5-Layer Cake". A reconciliação **confirmou** os 4 pilares **sem mudança semântica**:
  P1↔data flywheel/composição de dados, P2↔autopiloto/"você É a implementação", P3↔"5-layer cake"/
  corrida contra o modelo/Mirage PMF, P4↔profundidade de integração/cunha de mão de obra. Único
  ajuste de **redação**: cada pilar (§§2–5) passou a citar sua fonte de grounding. **Escala 0–25 e
  semântica intactas** → rótulos do eval set (F1.12) permanecem válidos.
