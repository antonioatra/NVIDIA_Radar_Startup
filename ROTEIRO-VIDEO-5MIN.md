# Roteiro — vídeo de 5 minutos (TAPI · NVIDIA Startup AI Radar)

**Autor:** Antônio Augusto Tavares Ribeiro André
**Duração-alvo:** 5:00 · **Ritmo:** ~130–150 palavras/min · narração total ≈ 680 palavras.

## Antes de gravar (checklist de tela)

- [x] **Demo principal = stack completa** (`.\scripts\run.ps1`, frontend em `localhost:3000`). Subir a stack e processar uma empresa **antes** de gravar — não rodar `run.ps1` ao vivo. Manter `python scripts/demo.py --case <id>` engatilhado num terminal só como **rede de segurança** caso a UI engasgue.
- [ ] Frontend aberto em `localhost:3000` (radar AIMI + lista da coorte), uma empresa já processada para abrir o detalhe.
- [ ] Aba com o **trace ao vivo** (SSE) ou Langfuse (`localhost:3001`) pronta.
- [ ] `docs/ARQUITETURA.md` aberto no diagrama do §2.1 (o grafo) para o segmento de arquitetura.
- [ ] Terminal limpo com o `python scripts/demo.py --case <id>` já digitado (fallback).
- [ ] Silenciar notificações; gravar em 1080p.

---

## Segmentos

| Tempo | Tela (o que MOSTRAR) | Narração (o que FALAR) |
|---|---|---|
| **0:00–0:30** Hook | Slide-título: "TAPI — NVIDIA Startup AI Radar" + seu nome. | "Oi, eu sou o Antônio. O case da NVIDIA Inception critica startups que são meros *wrappers* de LLM — e tem razão. Mas olhando o mercado de *sourcing* — Harmonic, Specter, Tracxn, PitchBook — todos param em *firmographics* e *funding*: quem captou, de quem, quando. **Ninguém diagnostica a maturidade técnica de IA de uma startup, prescreve a stack certa com evidência, e quantifica o ROI.** Esse espaço em branco é onde o TAPI vive." |
| **0:30–1:10** A tese | Slide com 3 verbos: **Mapeia · Diagnostica · Prescreve**. Ao lado, "roda na stack que recomenda". | "O TAPI é uma plataforma **multi-agente** que faz três coisas sobre startups brasileiras de IA: **mapeia** dados públicos, **diagnostica** a maturidade com um índice próprio — o **AIMI** —, e **prescreve** a stack NVIDIA adequada, com **evidência rastreável dos dois lados** e ROI da graduação de API externa para GPU própria. E ele não é wrapper: o valor está na orquestração, no dataset coletado e no RAG. Aliás, ele **roda na própria stack que recomenda** — Nemotron, NeMo Retriever, NIM. Dogfooding da jornada que prescreve." |
| **1:10–2:20** Arquitetura | `docs/ARQUITETURA.md` §2.1 — o diagrama do grafo. Passar o cursor pelos nós conforme cita. | "Por baixo, é um **grafo LangGraph de 10 nós** sobre um estado compartilhado. Uma consulta entra: o **planner** monta o plano de busca; o **scraper** coleta em paralelo, com proveniência e gate de ToS; o **extractor** destila um perfil estruturado; o **classifier** atribui a classe — AI-native, AI-enabled ou non-AI — e pontua os **4 pilares do AIMI**. Aí vem a parte que me importa: o **evidence_validator**, único nó que desvia o fluxo — sem corroboração suficiente, ele **volta a coletar** ou corta para um briefing honesto de 'dados insuficientes'. **Nunca inventa.** O **RAG híbrido** — Qdrant denso mais BM25, rerank NeMo — traz a evidência do lado NVIDIA; o **recommender** cruza os gaps da startup com essa evidência e **exige evidência dos dois lados** em toda recomendação. O LLM só refina redação — diagnóstico e prescrição vêm da regra, ancorados em fonte." |
| **2:20–3:55** DEMO | **Frontend `localhost:3000`:** (1) radar AIMI da coorte; (2) abrir uma empresa → detalhe com os 4 pilares e evidências; (3) trace do pipeline ao vivo; (4) briefing com recomendações citadas + export PDF. | "Na prática: aqui está a **coorte** de startups reais, plotadas no plano **classe × AIMI**. Abro uma empresa — cada sub-score acima do limiar **exige uma evidência citada**, com URL e data. Olha o **trace do pipeline ao vivo**: o grafo rodando nó a nó. E o **briefing executivo**: para cada gap de maturidade, uma recomendação NVIDIA, com a citação da base de conhecimento de um lado e o sinal da própria startup do outro. Exporta em PDF para o gerente do programa. *(Plano B, se offline: 'rodo o mesmo briefing pela espinha determinista, sobre um caso rotulado do eval set — o caminho que o CI mede'.)*" |
| **3:55–4:40** Resultados + diferencial | Slide/tabela da **§9.2** (números honestos). Depois, mini-clipe da coorte (clustering) + nota do GPU Graduation Engine. | "E mede de verdade, contra metas declaradas: classificação macro-F1 **0,875** nas fixtures; AIMI Spearman acima do gate; **evidência dos dois lados 1,00** — invariante duro; **recall@ALTA 0,97** nas techs que mais importam; RAG faithfulness **1,00**; briefing **0,87**. Quando inclui as reais, o macro-F1 cai para 0,72 — e eu **reporto isso como limitação honesta**, é o custo de sair do sintético. O diferencial vai além do single-company: **clustering de coorte** para ler o portfólio inteiro e um **GPU Graduation Engine** que estima o ROI de servir o modelo na própria GPU." |
| **4:40–5:00** Fechamento | Volta ao slide-título + 3 bullets: "evidência sempre · espinha verde · dogfooding". | "Resumindo: tudo com **evidência rastreável**, **anti-alucinação** por design, e uma **espinha verde** — cada peça que precisa de rede, LLM ou GPU tem um substituto offline determinístico que roda no CI, com o backend real plugável por flag. Um produto de **apoio à decisão** para o Inception, que roda na stack que recomenda. Obrigado." |

---

## Dicas de gravação

- **Maior risco = o segmento de demo (2:20–3:55).** Grave-o separado e com folga; se a stack real falhar, use o plano B offline sem hesitar — a narração já cobre os dois.
- **Não leia número que você não vai mostrar.** Alinhe README ↔ ARQUITETURA §9.2 antes (ver pendência) para não citar dois valores de AIMI/recall.
- Se passar de 5 min, corte do segmento de **arquitetura** (1:10–2:20): mantenha planner → classifier → evidence_validator → recommender e fale o resto por cima do diagrama.
- Frase de ouro para repetir se sobrar tempo: **"diagnóstico técnico + prescrição com evidência + ROI — o que nenhum sourcing faz."**
