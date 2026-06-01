# TAPI — Plano de Execução (mestre)

Plano de tasks dividido por fase/entregável. Cada fase tem um documento próprio em `docs/tasks/`.
IDs de task são estáveis (ex.: `F2.3`) e referenciados em commits.

## Fases e dependências

```
F0 Fundação ──┬──> F1 Scraping ──> F2 Multi-agente ──┐
              └──> F3 RAG ───────> F4 Recomendação ──┼──> F5 Frontend ──┐
                                   F4 ──> F6 Diferencial ───────────────┴──> F7 Validação
```

| Fase | Documento | Entregável do brief |
|---|---|---|
| **F0** Fundação | [tasks/00-fundacao.md](tasks/00-fundacao.md) | (base p/ todos) |
| **F1** Scraping | [tasks/01-scraping.md](tasks/01-scraping.md) | Entregável 1 |
| **F2** Multi-agente | [tasks/02-multiagente.md](tasks/02-multiagente.md) | Entregável 2 |
| **F3** RAG NVIDIA | [tasks/03-rag.md](tasks/03-rag.md) | Entregável 3 |
| **F4** Recomendação | [tasks/04-recomendacao.md](tasks/04-recomendacao.md) | Entregável 4 |
| **F5** Frontend | [tasks/05-frontend.md](tasks/05-frontend.md) | Entregável 5 |
| **F6** Diferencial | [tasks/06-diferencial.md](tasks/06-diferencial.md) | Entregável 6 |
| **F7** Validação | [tasks/07-validacao.md](tasks/07-validacao.md) | (transversal / qualidade) |

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
