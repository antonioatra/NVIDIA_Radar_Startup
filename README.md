# TAPI — NVIDIA Startup AI Radar

Plataforma multi-agente que mapeia startups brasileiras AI-native, diagnostica maturidade
técnica e prescreve a stack NVIDIA adequada, com evidência rastreável e ROI quantificado.

## Documentação
- **Arquitetura:** [ARQUITETURA.md](ARQUITETURA.md)
- **Plano de execução:** [docs/PLANO.md](docs/PLANO.md)
- **Cobertura de tecnologias:** [docs/COBERTURA-TECNOLOGIAS.md](docs/COBERTURA-TECNOLOGIAS.md)

## Stack
LangGraph · NVIDIA Nemotron (build.nvidia.com / NIM self-hosted) · NeMo Retriever (embed+rerank) ·
NeMo Guardrails · Qdrant · PostgreSQL · Redis · RAPIDS/cuDF/cuML · Triton · TensorRT-LLM ·
FastAPI · Next.js · Langfuse · RAGAS.

## Estrutura
```
apps/        api (FastAPI) · worker (LangGraph) · frontend (Next.js)
packages/    schemas · agents · scraping · rag · scoring · benchmark · eval
data/        knowledge_base (fontes NVIDIA) · seeds (fontes de startups) · eval (set rotulado)
docs/        plano + tasks por fase + cobertura
notebooks/   geração da matriz de benchmark (GPU)
```

## Subir o ambiente
```bash
cp .env.example .env   # preencher chaves (NVIDIA_API_KEY, TAVILY_API_KEY, ...)
docker compose up -d
```

## Princípio
Tudo com evidência rastreável. O TAPI roda na stack que recomenda (dogfooding NVIDIA).
