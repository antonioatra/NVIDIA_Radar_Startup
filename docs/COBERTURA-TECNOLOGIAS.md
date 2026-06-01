# Cobertura de Tecnologias — verificação

Verifica que **todas** as tecnologias citadas no brief estão endereçadas, e destaca o
**dogfooding**: onde o próprio TAPI *usa* tecnologia NVIDIA (não só recomenda).

## §5.1 Agentes (LangGraph)
| Agente do brief | Nó no grafo | Fase |
|---|---|---|
| Search Planner | `search_planner` | F2 |
| Scraper | `scraper` (map paralelo) | F1/F2 |
| Extractor | `extractor` | F1/F2 |
| Startup Classifier | `classifier` (+ AIMI) | F2/F6 |
| Evidence Validator | `evidence_validator` | F2 |
| NVIDIA RAG | `nvidia_rag` | F3 |
| Recommendation | `recommender` | F4 |
| Briefing | `briefing` | F4 |

## §5.2 Scraping — todas usadas
| Tech | Uso no TAPI | Fase |
|---|---|---|
| Playwright | sites dinâmicos (JS) | F1 |
| BeautifulSoup | parsing HTML simples | F1 |
| Scrapy | crawl em escala dos diretórios §9 | F1 |
| Firecrawl | extração limpa p/ RAG | F1 |
| trafilatura | texto principal de blogs/notícias | F1 |

## §5.3 RAG — todas usadas
| Tech | Uso no TAPI | Fase |
|---|---|---|
| Qdrant | vector DB (dense + sparse) | F3 |
| PostgreSQL | dados estruturados + checkpointer LangGraph | F0/F3 |
| BM25 | busca lexical (sparse no Qdrant) | F3 |
| **Cohere Rerank** | **validação final (F7)**; NeMo no build | F7 |

## §5.4 Base de conhecimento NVIDIA — recomendada vs. usada (dogfooding)
| Tech NVIDIA | Na base de conhecimento (recomendável) | **Usada pelo TAPI (dogfooding)** | Onde |
|---|---|---|---|
| NVIDIA Inception | ✅ | contexto/consumidor | F4 (briefing) |
| **NIM** | ✅ | ✅ serving Nemotron + NeMo Retriever | F0/F2/F3/F6 |
| **NeMo** | ✅ | ✅ NeMo Retriever (embed/rerank) | F3 |
| **NeMo Guardrails** | ✅ | ✅ rails no Briefing Agent | F4 |
| **Triton Inference Server** | ✅ | ✅ serving dos modelos do benchmark | F6 |
| **TensorRT-LLM** | ✅ | ✅ otimização no GPU Graduation Engine | F6 |
| **RAPIDS** | ✅ | ✅ pipeline de coorte | F6 |
| **cuDF** | ✅ | ✅ normalização/dedup da coorte | F6 |
| **cuML** | ✅ | ✅ clustering setorial | F6 |
| **CUDA** | ✅ | ✅ base de toda execução em GPU | F6 |
| **Riva (voz/ASR)** | ✅ | ✅ ASR p/ transcrever os vídeos do §10.1 → KB | F3 |
| Omniverse (3D) | ✅ | recomendável (domínio) | — |
| Isaac (robotics) | ✅ | recomendável (domínio) | — |
| Clara (saúde) | ✅ | recomendável (domínio) | — |
| Morpheus (cyber) | ✅ | recomendável (domínio) | — |
| AI Enterprise | ✅ | recomendável (domínio) | — |

> **MONAI** (citado no §5.5 como alvo de recomendação em saúde, junto de Clara/AI Enterprise)
> entra na **base de conhecimento** (F3.1c) para ser recuperável pelo RAG. Não é dogfooded
> (o TAPI não faz imagem médica) — vive na KB como recomendável de domínio.

> **Modelos generativos (cérebro):** NVIDIA **Nemotron** (Nano/Super) via `build.nvidia.com`
> e self-hosted na GPU — usado em todos os nós que chamam LLM. Reforça a narrativa anti-wrapper:
> o TAPI roda na stack que prescreve.

**Conclusão:** as 5 domain-specific restantes (Omniverse/Isaac/Clara+MONAI/Morpheus/AI Enterprise)
vivem na base de conhecimento como recomendáveis (honesto — o TAPI não faz 3D/robótica/saúde).
Toda a **stack de inferência e dados** (NIM, NeMo, Guardrails, Triton, TensorRT-LLM,
RAPIDS/cuDF/cuML, CUDA, Nemotron) **+ Riva (ASR)** é **dogfooded** pelo próprio TAPI.
