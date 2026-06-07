# NVIDIA NeMo

NVIDIA NeMo é a plataforma end-to-end para construir, customizar e operar modelos de IA
generativa em produção. Cobre o ciclo completo: curadoria de dados, treinamento e
fine-tuning, recuperação (RAG), guardrails e avaliação.

## Componentes relevantes
- **NeMo Retriever**: microsserviços de **embedding** (ex.: nv-embedqa, multilíngue) e
  **reranking** (nv-rerankqa) — a espinha do RAG de qualidade com busca semântica e
  reordenação. É o que o TAPI usa para embeddings e reranking da base NVIDIA.
- **NeMo Customizer**: fine-tuning e técnicas como LoRA/PEFT para adaptar modelos ao domínio
  proprietário da startup (dado próprio vira moat de produto).
- **NeMo Guardrails**: trilhos de segurança/escopo para apps de LLM (item próprio na KB).
- **NeMo Evaluator**: avaliação sistemática de qualidade de modelos e pipelines de RAG —
  governança de IA exigida quando a startup precisa medir, não só rodar, seus agentes.
- **NeMo Curator**: curadoria e deduplicação de grandes corpora de treino.

## Quando recomendar
Indicado para startups que precisam ir além de prompt em API crua: customizar modelos com
dado próprio, montar RAG robusto, ou estabelecer governança/avaliação de agentes. Endereça
gaps de **Workflow Depth** (orquestração, RAG) e **Data Moat** (fine-tuning sobre dado
proprietário) no AIMI.
