# TAPI — Evoluções do Diferencial (ideias além do v1)

**Para quê este doc.** O loop **diagnosticar → prescrever** já está construído e visível no produto
(AIMI + recomendações com evidência dos dois lados + Inception Priority + briefing, rodando ponta a
ponta na UI). Este documento registra, num lugar só: **(a)** a 3ª perna que ainda falta (quantificar
o ROI) e **(b)** um conjunto de **ideias novas** para fortalecer o diferencial — cada uma com
*valor*, *encaixe na arquitetura* (o que reusa) e *esforço/risco*. É um doc de **visão de produto**,
não um plano de tasks fechado; a fonte da tese vive em [`ARQUITETURA.md`](ARQUITETURA.md) §0/§5 e a
caracterização em [`ALINHAMENTO-CRITERIOS-E-DECISAO.md`](ALINHAMENTO-CRITERIOS-E-DECISAO.md).

## Onde o TAPI já se diferencia (recap honesto)

As bases de *sourcing* do mercado (Harmonic, Specter, Tracxn, PitchBook, CB Insights) respondem
**"quem existe"** — firmographics, funding, sinais de time. Nenhuma faz **diagnóstico técnico de
maturidade + prescrição de stack com evidência + ROI**. O TAPI vive nesse vão, com três coisas que
já funcionam:

1. **AIMI** — "score de crédito de AI-nativeness": 4 pilares 0–25, cada sub-score com **evidência
   rastreável**. Diz *quão maduro* tecnicamente, não só que a empresa existe.
2. **Recomendação prescritiva** — por gap, a tech NVIDIA + justificativa técnica/negócio +
   **evidência dos dois lados** (gap da startup × citação da KB NVIDIA). Prescreve, não lista.
3. **Inception Priority** — fila de outreach (potencial × upside NVIDIA), o §1 do brief ("atrair,
   qualificar, nutrir") servido direto.

E o meta-diferencial: o TAPI **roda na stack que recomenda** (Nemotron + NeMo Retriever + NIM) —
prova viva da jornada API → stack otimizada.

---

## Bloco A — Fechar a tese: ROI na GPU (a 3ª perna) · F6.8–F6.12

**O quê.** A tese completa é *diagnosticar → prescrever → **quantificar***. Falta o número: medir na
GPU que rodar **NIM/TensorRT-LLM** bate a API externa em **tokens/s, p50/p95 e $/1M tokens**, mapear
o perfil da startup pra a célula de benchmark mais próxima e **cravar a linha de ROI no briefing**
(*"migrar atendimento de ~Xk tokens/dia de API p/ NIM self-hosted: ~Nx throughput, p95 −M%, custo
−K%"*). É o que transforma *"recomendamos NIM"* em *"recomendamos NIM, e isso economiza ~K%"*.

**Encaixe.** Pasta `packages/benchmark/` (reservada) + `notebooks/` (geração da matriz). O engine
**consome** uma matriz pré-computada (tamanhos × workloads) — não roda ao vivo por request.

**Esforço/risco.** Médio-alto, mas **fatiável e de-riscado**: o **código** (estimador de custo,
mapeamento perfil→célula, linha no briefing) é **offline-testável** com matriz placeholder + real
atrás de flag — escrevo sem GPU/rate-limit. A **medição real** precisa da GPU; fallback
**vLLM** (open-source, sem entitlement NGC) mede o lado otimizado se o NIM/Triton não subir. **É a
peça de maior valor que resta** e não esbarra no rate-limit do free tier.

---

## Bloco B — Quick wins de produto (alto valor, baixo esforço, 100% offline)

### B.1 Selos: *wrapper-risk* / *graduation-ready ★*
**O quê.** Um selo por empresa derivado da **região do plano `classe × AIMI`**: `AI-native` + AIMI
baixo (P1/P3 baixos) = **"risco de wrapper"**; `AI-native` + P1/P2 alto + **P3 baixo** =
**"graduation-ready ★"** (o alvo de maior upside). **Encaixe:** a região já é derivada (`derive_region`,
RUBRICA §6) — é só **expor** na UI/briefing. **Por que diferencia:** o case é *sobre* criticar
wrappers; nomear o risco explicitamente é on-narrative e afiado. **Esforço:** baixo (badge na UI).

### B.2 Confiança & "precisa de revisão" à mostra
**O quê.** Surfacar o `confidence` do `AIMIScore` e o `label_source` (`human` × `model`) — o gerente
vê **o que é diagnóstico de alta confiança vs. proposto pelo modelo** (pendente de revisão). **Encaixe:**
os campos já existem (`AIMIScore.confidence`, `LabeledStartup.label_source`). **Por que diferencia:**
honestidade vira *feature* — confiança calibrada é o que separa uma ferramenta de decisão de um
chute bonito. **Esforço:** baixo.

### B.3 Benchmark de pares (percentil de AIMI)
**O quê.** Dar contexto ao número: *"Aquarela: AIMI 54 — top 20% de HealthTech na coorte; P3
(otimização) no 1º quartil = gap claro"*. **Encaixe:** cálculo puro sobre a coorte acumulada (tabela
`company`); reusa o que o seed já popula. **Por que diferencia:** um score isolado informa pouco; o
**percentil** torna a priorização defensável. **Esforço:** baixo (núcleo determinístico, testável).

---

## Bloco C — Alto valor, esforço médio

### C.1 Outreach co-pilot (rascunho de abordagem) ★
**O quê.** Por empresa, gerar um **rascunho de e-mail/mensagem de outreach** ancorado no diagnóstico:
*"Olá [founder], vimos que a inferência de vocês é 100% API (Technical Optimization 6/25); o NIM
cortaria custo ~K% — a Inception cobre os créditos de GPU. Topam 20 min?"*. **Encaixe:** reusa o
conteúdo do briefing + Nemotron-Super pra redação, com a **mesma disciplina anti-alucinação** (só
afirma o que tem evidência; os dois lados sempre). **Por que diferencia:** fecha o ciclo até a
**ação** — entrega a "nutrição/atração" (§1) pronta pro gerente, não só o diagnóstico. **Esforço:**
médio (1 nó/endpoint + guardrail; espinha offline determinística como nos outros nós).

### C.2 Escada de graduação (roadmap visual API → stack)
**O quê.** Visualizar o caminho ordenado por empresa (**API hoje → NIM → TensorRT-LLM → Triton →
AI Enterprise**), marcando onde ela está e o próximo passo. **Encaixe:** o briefing já produz o
roadmap **textual** (`acao_tecnica`); é dar forma visual. **Por que diferencia:** materializa a
narrativa central do case ("graduar da API pra stack otimizada") num artefato que o founder entende
na hora. **Esforço:** médio (componente de UI + ordenação já existente).

---

## Bloco D — Visão / portfólio (v2)

### D.1 Inteligência de coorte + *whitespace* · F6.5–F6.7
Clusters **graduation-ready** por setor (cuDF/cuML) **+** análise de *whitespace*: segmentos de alto
potencial **sub-atendidos** pela NVIDIA. Dá ao gerente uma **visão de portfólio**, não consultas
avulsas. **Esforço:** alto (precisa de **volume** na coorte + clustering GPU; fallback sklearn/CPU).

### D.2 Monitoramento temporal / frescor *(fora do v1 por decisão — PLANO §"Fora de escopo")*
Re-crawl periódico detecta **mudança** (funding novo, lançamento de modelo próprio) → **re-prioriza**
automaticamente. Transforma o radar de *snapshot* em **vivo**. **Esforço:** alto (entity resolution +
detecção de mudança + agendamento).

### D.3 ROI multi-cenário
Estende a 3ª perna: ROI por **workload** (chat conversacional × batch × RAG), já que o ganho do
self-host varia com o perfil de uso. **Esforço:** médio sobre o engine de ROI (B/A).

---

## Priorização sugerida

| # | Ideia | Valor | Esforço | Offline-testável? | Quando |
|---|---|---|---|---|---|
| A | **ROI na GPU** (fecha a tese) | ★★★ | médio-alto | código sim / medição na GPU | **próximo** |
| B.1 | Selos wrapper / graduation-ready | ★★ | baixo | ✅ | quick win |
| B.2 | Confiança & needs-review à mostra | ★★ | baixo | ✅ | quick win |
| B.3 | Percentil de pares | ★★ | baixo | ✅ | quick win |
| C.1 | **Outreach co-pilot** | ★★★ | médio | ✅ (espinha) | alto valor |
| C.2 | Escada de graduação (visual) | ★★ | médio | ✅ | alto valor |
| D.1 | Coorte + whitespace | ★★ | alto | parcial | v2 |
| D.2 | Frescor temporal | ★★ | alto | — | v2 |
| D.3 | ROI multi-cenário | ★ | médio | ✅ | depois de A |

**Sequência recomendada:** **(1)** ROI na GPU (fecha o Entregável 6 e dá o "número mágico"); **(2)**
os 3 quick wins do Bloco B (selos, confiança, percentil — polimento imediato, zero infra, reforçam a
narrativa); **(3)** o **outreach co-pilot** (Bloco C.1 — o maior salto de valor: do diagnóstico à
ação). Todos exceto a *medição* do ROI rodam **offline/determinístico** (sem rate-limit, sem GPU pra
escrever e testar) — a disciplina espinha-verde do projeto.
