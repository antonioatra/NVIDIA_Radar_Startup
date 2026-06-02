# TAPI — Plano de Execução (mestre)

Plano de tasks dividido por fase/entregável. Cada fase tem um documento próprio em `docs/tasks/`.
IDs de task são estáveis (ex.: `F2.3`) e referenciados em commits.

## Fases e dependências

```
F0 ─┬─> F1 ──> F2 ──┐
    │                ├─> F4 ─┬─> F5 ──┐
    └─> F3 ──────────┘       └─> F6 ──┴─> F7
```
> O grafo acima é só visual; a fonte de verdade das dependências é a coluna "Depende de"
> abaixo (cada task-doc repete a sua no cabeçalho). Note que **F4 depende de F2 *e* F3**.

| Fase | Documento | Entregável do brief | Depende de |
|---|---|---|---|
| **F0** Fundação | [tasks/00-fundacao.md](tasks/00-fundacao.md) | (base p/ todos) | — |
| **F1** Scraping | [tasks/01-scraping.md](tasks/01-scraping.md) | Entregável 1 | F0 |
| **F2** Multi-agente | [tasks/02-multiagente.md](tasks/02-multiagente.md) | Entregável 2 | F0, F1 |
| **F3** RAG NVIDIA | [tasks/03-rag.md](tasks/03-rag.md) | Entregável 3 | F0 |
| **F4** Recomendação | [tasks/04-recomendacao.md](tasks/04-recomendacao.md) | Entregável 4 | F2, F3 |
| **F5** Frontend | [tasks/05-frontend.md](tasks/05-frontend.md) | Entregável 5 | F2, F4 |
| **F6** Diferencial | [tasks/06-diferencial.md](tasks/06-diferencial.md) | Entregável 6 | F4 |
| **F7** Validação | [tasks/07-validacao.md](tasks/07-validacao.md) | (transversal / qualidade) | F3, F4, F6 |

> **Eval set (transversal):** o conjunto rotulado de ~20–30 startups é **criado cedo em F1.12**
> (rótulos de classificação + AIMI esperado). F6.4 e F7.1/F7.2 apenas **consomem/consolidam**
> esse conjunto — não o criam. Isso remove a dependência circular (F6 precisava do eval set
> que antes só nascia em F7).

> **Rubrica AIMI (transversal):** a **definição** dos 4 pilares e da escala 0–25 é um artefato
> **criado cedo em F0.11** (`docs/RUBRICA-AIMI.md`), antes do eval set (F1.12) rotular "AIMI
> esperado". Separa-se **definição** (fixa, cedo) da **heurística de pontuação** (v0 em F2.6,
> refinada p/ v1 em F6.1) — assim os rótulos de ground-truth não dependem da versão do modelo.
> O grounding conceitual (materiais §10.1) chega em F3.1d e é **reconciliado** com o doc sem
> mudar a escala. Remove o risco de rotular AIMI antes de existir qualquer rubrica.

> **ROI na UI (F5.6 × F6):** F5 depende de F2/F4, mas o **número de ROI** vem do F6 (paralelo).
> F5.6 trata ROI como **opcional** e degrada graciosamente — mostra a recomendação sem ROI até a
> matriz de benchmark (F6.9–F6.11) existir, e exibe o número quando disponível. Não é dependência
> bloqueante de F5 sobre F6.

> **Modos de execução (esclarecimento):** o grafo LangGraph roda **por empresa** (1 consulta →
> 1 `StartupProfile`). A **coorte** (clustering F6.5–F6.7) e o **eval set** (F1.12) precisam de
> volume: quem popula a tabela `company` é o **cohort builder em lote (F1.14)** — crawl dos
> diretórios §9 (F1.6) → fila de empresas → grafo rodado em lote. F6.5+ consomem a tabela
> acumulada, não a saída de um run único. Há dois modos de consulta: *single-company lookup* e
> *discovery por setor/região* (contrato em F2.3).

> **Transporte de progresso (worker → SSE):** o worker RQ **publica** eventos de progresso num
> canal **Redis pub/sub por `run_id`**; o endpoint SSE da API (F5.2/F5.3) **assina** esse canal e
> repassa ao front. Há um contrato de evento (nó atual · status · %). Detalhe em **F2.10** — fecha
> o vão entre o run assíncrono e o acompanhamento ao vivo do F5.3.

> **HITL acionável pelo produto:** o interrupt do grafo (F2.8) só vale no modo `sync` se houver
> superfície para o humano agir — **endpoint `POST /runs/{id}/resume` (F5.2)** + **tela de revisão/
> aprovação (F5.10)**. Sem isso o interrupt fica inalcançável pela UI. Em lote, `hitl=auto` (F1.14)
> não usa essa superfície (não bloqueia a fila).

> **Fora de escopo explícito (v1):** frescor/re-crawl periódico das empresas (detecção de mudança)
> e entity resolution avançada ficam para depois — a v1 coleta **sob demanda**. Registrado aqui
> para não ser confundido com lacuna não vista.

## Marcos (milestones)
- **M1** — Pipeline coleta + persiste 1 startup com proveniência (fim F1).
- **M2** — Grafo LangGraph end-to-end gera briefing rascunho (fim F2).
- **M3** — RAG NVIDIA responde com citações + RAGAS rodando (fim F3).
- **M4** — Recomendação estruturada (§5.5) a partir do AIMI (fim F4).
- **M5** — Dashboard navegável + export PDF (fim F5).
- **M6** — Diferencial: AIMI + clustering de coorte + ROI real na GPU (fim F6).
- **M7** — Eval consolidado + comparativo NeMo vs Cohere (fim F7).

## Definition of Done (global, por task)
- [ ] Código + teste mínimo + entrada/saída tipada (Pydantic onde aplicável).
- [ ] Toda afirmação/score tem evidência rastreável (URL + `fetched_at`).
- [ ] Trace visível no Langfuse (quando envolve agente/LLM).
- [ ] Commit incremental referenciando o ID da task (§11 do brief).

## Regra do reranker (decisão travada)
- **Durante todo o build e os testes:** NeMo Retriever Reranking NIM (grátis, on-narrative).
- **Cohere Rerank:** entra **só na F7 (validação final)** como benchmark comparativo. Ver
  `docs/COBERTURA-TECNOLOGIAS.md`.
- **Atenção:** o brief **nomeia a Cohere** no §5.3. O comparativo NeMo×Cohere (F7.4) é, portanto,
  item de **destaque** no relatório de avaliação (F7.5) — a escolha do NeMo precisa aparecer
  justificada por dados (qualidade × custo × latência), não por omissão.
