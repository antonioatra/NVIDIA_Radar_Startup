# Revisão de rótulos do eval set (F1.12 / F7.1 / F7.7)

> Gerado por `scripts/gen_label_review.py` em 2026-06-22. **Objetivo:** você (revisor humano) confere CADA rótulo e marca concordo/ajustar. Até esta revisão, `label_source: human` é **aspiracional** para as reais — completá-la torna a proveniência honesta.
>
> **Prioridade das techs (F7.7):** 🔴 ALTA = a alavanca NVIDIA da empresa (entra no `recall@ALTA`) · 🟡 MÉDIA = complemento · ⚪ BAIXA = leque que o §5.5 emite por completude. Ancorada no **gap do perfil**, não na saída da regra (anti-circularidade).

## A. Empresas REAIS (headline) — 9 entradas

Estas afirmam empresas reais; é aqui que a revisão importa.

### Gupy · `alvo_graduacao` · AI-native

- **Setor / país:** HRTech (Recursos Humanos) (BR) — origem do rótulo: ✅ human
- **AIMI:** P1 data_moat **14** · P2 workflow **9** · P3 tech_opt **6** · P4 distrib **15** (total 44)
- **Techs (prioridade):** 🔴 NVIDIA NIM · 🔴 TensorRT-LLM · 🟡 NVIDIA Triton Inference Server · ⚪ NeMo Retriever (RAG) · ⚪ NeMo (customização + Curator)
- **Por quê (rationale):** Revisão humana (F7.1): ML/deep learning para recrutamento é o núcleo => AI-native. Vasto banco proprietário de descrições de vagas + feedback de sucesso = data moat estabelecido (P1 13+). Tem otimização pontual (modelo próprio de validação documental), mas o serving do core roda em cloud externa => P3 baixo = upside de graduação => alvo de graduação.
- **Evidência:** https://tech-career.gupy.io/ · https://www.gupy.io/inteligencia-artificial · https://startup.google.com/intl/pt-BR_ALL/alumni/stories/gupy/
- **Notas:** Revisado por humano (2026-06-15) vs evidência (gupy.io, Google for Startups). data_moat 12->14 => wrapper vira alvo. Ressalva - já tem otimização pontual (modelo próprio de imagem, -98,7% custo). Prioridade (F7.7, 2026-06-22) gap-anchored — alvo => ALTA = graduação (NIM/TensorRT, gap P3); Triton MÉDIA; NeMo Retriever/customização BAIXA (leque, P1 já estabelecido dm14).
- **Sua revisão:** ☐ concordo  ☐ ajustar → _______________________

### Hand Talk · `alvo_graduacao` · AI-native

- **Setor / país:** Tecnologia de Acessibilidade (BR) — origem do rótulo: ✅ human
- **AIMI:** P1 data_moat **14** · P2 workflow **9** · P3 tech_opt **6** · P4 distrib **15** (total 44)
- **Techs (prioridade):** 🔴 NVIDIA NIM · 🔴 TensorRT-LLM · 🟡 NVIDIA Triton Inference Server · 🟡 NVIDIA Riva (ASR/TTS) · ⚪ NeMo (customização + Curator)
- **Por quê (rationale):** Revisão humana (F7.1): a IA traduz texto/áudio para Libras entendendo contexto e gramática própria; corpus proprietário de Libras + comunidade surda no loop = data moat estabelecido (P1 13+). Serving via API externa (sem stack própria) mantém P3 baixo = upside de graduação. Ampla distribuição (app + plugin web).
- **Evidência:** https://impacto.google/historias/handtalk · https://aiotbrasil.com.br/noticias/hand-talk-lanca-tecnologia-de-reconhecimento-de-sinais-com-ia
- **Notas:** Revisado por humano (2026-06-15) vs evidência pública (handtalk.me, AIoT Brasil); promovido model->human. data_moat 12->14 (corpus Libras + experts no loop) => wrapper vira alvo de graduação. Prioridade (F7.7, 2026-06-22) ancorada no gap, não na regra; ALTA = graduação de inferência (NIM/TensorRT-LLM, gap P3); Riva MÉDIA (áudio é core do produto, não a alavanca de graduação); NeMo BAIXA (P1 já estabelecido).
- **Sua revisão:** ☐ concordo  ☐ ajustar → _______________________

### Idwall · `alvo_graduacao` · AI-native

- **Setor / país:** Validação de Identidade e Prevenção de Fraudes (BR) — origem do rótulo: ✅ human
- **AIMI:** P1 data_moat **16** · P2 workflow **9** · P3 tech_opt **6** · P4 distrib **15** (total 46)
- **Techs (prioridade):** 🔴 NVIDIA NIM · 🔴 TensorRT-LLM · 🟡 NVIDIA Triton Inference Server · 🟡 NVIDIA Morpheus · ⚪ NeMo (customização + Curator)
- **Por quê (rationale):** Revisão humana (F7.1): algoritmos confidenciais próprios + biometria treinada em faces brasileiras + lab interno de fraude realimentando a plataforma = data moat forte com feedback loop (P1 16). Infra em cloud externa (Google) sem serving próprio => P3 baixo = upside de graduação => alvo de graduação. Clientes enterprise (bancos) e aquisição pela Serasa sustentam P4.
- **Evidência:** https://idwall.co/pt-BR/ai-based · https://blog.idwall.co/ia-contra-fraudes-como-a-tecnologia-da-idwall-atua-na-pratica/ · https://startups.com.br/negocios/serasa-compra-idwall-de-solucoes-antifraude-por-r-450m/
- **Notas:** Revisado por humano (2026-06-15) vs evidência (blog.idwall.co, Brazil Journal, Startups). data_moat 12->16 (moat de documentos BR + lab de fraude com feedback) => wrapper vira alvo de graduação. Prioridade (F7.7, 2026-06-22) gap-anchored — alvo => ALTA = graduação (NIM/TensorRT, gap P3); Triton + Morpheus (domínio fraude) MÉDIA; NeMo customização BAIXA (P1 já forte dm16).
- **Sua revisão:** ☐ concordo  ☐ ajustar → _______________________

### Aquarela Analytics · `maduro` · AI-native

- **Setor / país:** Tecnologia/Inteligência Artificial (BR) — origem do rótulo: ✅ human
- **AIMI:** P1 data_moat **12** · P2 workflow **9** · P3 tech_opt **15** · P4 distrib **18** (total 54)
- **Techs (prioridade):** 🔴 NVIDIA RAPIDS · 🔴 NVIDIA AI Enterprise · 🟡 cuDF · 🟡 cuML
- **Por quê (rationale):** Revisão humana (F7.1): desenvolve algoritmos-base próprios (raro no Brasil) e roda a plataforma Vorteris self-hosted (10+ anos de P&D) => stack de inferência própria madura (P3 15 => maduro). A IA é o núcleo (AI-native). Clientes enterprise diversos e prêmio CNI de inovação sustentam P4.
- **Evidência:** https://aquare.la/ · https://aquare.la/vorteris/ · https://aquare.la/en/about/
- **Notas:** Revisado por humano (2026-06-15) vs evidência (aquare.la/vorteris); rótulo do pipeline (maduro, P3=15) confirmado — algoritmos-base próprios sustentam o P3 alto. Prioridade (F7.7, 2026-06-22) ancorada no gap, não na regra; já graduou (P3 alto), então ALTA = domínio-core (RAPIDS, analytics tabular) + AI Enterprise (governança/enterprise, tese de maduro); cuDF/cuML MÉDIA (componentes sob RAPIDS).
- **Sua revisão:** ☐ concordo  ☐ ajustar → _______________________

### Unico · `maduro` · AI-native

- **Setor / país:** Identidade Digital (IDtech) (BR) — origem do rótulo: ✅ human
- **AIMI:** P1 data_moat **18** · P2 workflow **13** · P3 tech_opt **15** · P4 distrib **18** (total 64)
- **Techs (prioridade):** 🔴 NVIDIA AI Enterprise · 🔴 NVIDIA Morpheus
- **Por quê (rationale):** Revisão humana (F7.1) — CORREÇÃO: biometria facial = visão computacional no núcleo do produto, logo AI-native (o rótulo non-AI do pipeline foi erro de extração só-de-descrição). Base de faces+CPF de ~90% da população BR = data moat forte (P1); algoritmos próprios + detecção de deepfake em tempo real a 170M+ usuários = stack de inferência madura (P3 estabelecido => maduro); bancos e grandes varejistas = distribuição defensável (P4).
- **Evidência:** https://timesbrasil.com.br/empresas-e-negocios/tecnologia-e-inovacao/biometria-facial-virou-tecnologia-padrao-do-mercado-diz-head-da-unico/ · https://www.biometricupdate.com/companies/unico · https://www.biometricupdate.com/202108/brazilian-startup-unico-raises-120m-for-face-biometrics-powered-authentication
- **Notas:** Revisado por humano (2026-06-15) vs evidência (Times Brasil, Biometric Update). CORREÇÃO grave do pipeline - non-AI/fora_escopo vira AI-native/maduro (biometria facial é IA no núcleo). Prioridade (F7.7, 2026-06-22) gap-anchored — maduro (já graduou, P3=15) => ALTA = AI Enterprise (governança) + Morpheus (fraude/deepfake é o domínio-core do produto).
- **Sua revisão:** ☐ concordo  ☐ ajustar → _______________________

### BotCity · `periferico` · AI-enabled

- **Setor / país:** Utilidades (BR) — origem do rótulo: ✅ human
- **AIMI:** P1 data_moat **6** · P2 workflow **9** · P3 tech_opt **6** · P4 distrib **15** (total 36)
- **Techs (prioridade):** _(nenhuma — fora do escopo de prescrição: periférico/non-AI ou wrapper frágil)_
- **Por quê (rationale):** Revisão humana (F7.1): o núcleo é RPA (automação por regras em Python); a IA é combinada perifericamente (automação inteligente/agêntica), não o núcleo do produto => AI-enabled. Orquestração enterprise sustenta a distribuição (P4).
- **Evidência:** https://botcity.dev/industry/utilities · https://blog.botcity.dev/pt-br/2023/11/15/automacao-inteligente/
- **Notas:** Revisado por humano (2026-06-15) vs evidência (botcity.dev); rótulo do pipeline (AI-enabled/periférico) confirmado sem alteração.
- **Sua revisão:** ☐ concordo  ☐ ajustar → _______________________

### Kunumi · `wrapper` · AI-native

- **Setor / país:** Inteligência Artificial / Deep Tech (BR) — origem do rótulo: ✅ human
- **AIMI:** P1 data_moat **9** · P2 workflow **9** · P3 tech_opt **6** · P4 distrib **15** (total 39)
- **Techs (prioridade):** 🔴 NeMo (customização + Curator) · ⚪ NVIDIA NIM · ⚪ TensorRT-LLM · ⚪ NVIDIA Triton Inference Server
- **Por quê (rationale):** Revisão humana (F7.1): spin-off da UFMG, deep learning/ML/NLP com plataforma auto-ML própria — IA é o núcleo (AI-native confirmado). O 6/6/6/6 do pipeline subavaliou (extração de descrição genérica). Sem dado único público claramente defensável (P1 emergente) e serving em cloud (P3 baixo); adquirida pelo Bradesco em 2023 = validação/distribuição (P4).
- **Evidência:** https://www.kunumi.com/br · https://fundepar.com.br/kunumi-e-vendida-ao-grupo-bradesco-e-consolida-caso-de-sucesso-por-meio-de-parceria-entre-a-spin-off-e-a-ufmg/
- **Notas:** Revisado por humano (2026-06-15) vs evidência (Projeto Draft, Fundepar/Bradesco). Re-score do flat 6/6/6/6 subavaliado; classe AI-native confirmada (você sinalizou). Permanece wrapper (P3 baixo). Prioridade (F7.7, 2026-06-22) gap-anchored — wrapper => ALTA = NeMo customização (provar core/P1=9 emergente); graduação (NIM/TensorRT/Triton) BAIXA = prematura sem core provado.
- **Sua revisão:** ☐ concordo  ☐ ajustar → _______________________

### Semantix · `wrapper` · AI-native

- **Setor / país:** Inteligência Artificial e Dados (BR) — origem do rótulo: ⚠️ model (pendente, fora do headline)
- **AIMI:** P1 data_moat **12** · P2 workflow **9** · P3 tech_opt **6** · P4 distrib **15** (total 42)
- **Techs (prioridade):** · NVIDIA NIM · · TensorRT-LLM · · NeMo Retriever (RAG) · · NeMo (customização + Curator)
- **Por quê (rationale):** Proprietária em transformação de dados e fundações de dados modernas, mas sem evidência explícita de dados exclusivos ou loops de feedback. Orquestração multi-passo via plataforma e automação de pipelines (Cloudbees), mas sem detalhes de agentes ou orquestração complexa. Arquitetura proprietária, mas dependência de serviços externos (AWS, Databricks) sem evidência de fine-tuning ou self-host. Presença global via Nasdaq, liderança em deep tech no LATAM e soluções enterprise, com alta defensabilidade.
- **Evidência:** https://semantix.ai/ · https://semantix.ai/sobre-nos
- **Notas:** PENDENTE de revisão (fora do headline). Evidência (Exame) mostra LLM próprio "Lloro" + suíte de governança própria (Safetix) => o rótulo wrapper/P3=6 do pipeline está SUBavaliado (provável maduro). Promoção a human aguarda decisão humana sobre a região.
- **Sua revisão:** ☐ concordo  ☐ ajustar → _______________________

### Take Blip · `wrapper` · AI-native

- **Setor / país:** Tecnologia de Conversação e AI (BR) — origem do rótulo: ✅ human
- **AIMI:** P1 data_moat **6** · P2 workflow **9** · P3 tech_opt **6** · P4 distrib **15** (total 36)
- **Techs (prioridade):** 🔴 NeMo (customização + Curator) · 🟡 NeMo Retriever (RAG) · ⚪ NVIDIA NIM · ⚪ TensorRT-LLM · ⚪ NVIDIA Triton Inference Server
- **Por quê (rationale):** Revisão humana (F7.1): plataforma conversacional que orquestra NLP de TERCEIROS (IBM Watson, Microsoft LUIS, Google Dialogflow) e cujo dado é do cliente — sem moat próprio (P1 baixo) e sem stack própria (P3 baixo). Wrapper legítimo, apesar do posicionamento AI-native. Forte distribuição enterprise (P4).
- **Evidência:** https://www.capterra.com.br/software/200367/blip · https://www.blip.ai/en · https://learn.take.net/courses/criando-chatbots-com-a-plataforma-blip
- **Notas:** Revisado por humano (2026-06-15) vs evidência (learn.take.net, blip.ai); rótulo do pipeline (wrapper) confirmado — é um caso de wrapper verdadeiro (orquestra NLP de terceiros). Prioridade (F7.7, 2026-06-22) ancorada no gap, não na regra; ALTA = NeMo customização (construir moat próprio, gap P1=6 "prove o core"); NeMo Retriever MÉDIA (orquestração/P2); graduação (NIM/TensorRT/Triton) BAIXA = prematura sem core provado.
- **Sua revisão:** ☐ concordo  ☐ ajustar → _______________________

## B. Fixtures sintéticas (andaime de medição, NÃO empresas reais) — 24

Ancoradas na `RUBRICA-AIMI.md` para dar *span* à métrica (cobrir todas as regiões × classes). Não há empresa real por trás — revise se a prioridade bate com a região/AIMI.

| id | região | classe | AIMI (P1/P2/P3/P4) | techs (prioridade) |
|---|---|---|---|---|
| `eval-alvo-01` | alvo_graduacao | AI-native | 20/17/6/12 | 🔴 NVIDIA NIM · 🔴 TensorRT-LLM · 🟡 Triton · ⚪ RAPIDS |
| `eval-alvo-02` | alvo_graduacao | AI-native | 18/18/5/13 | 🔴 NVIDIA NIM · 🔴 TensorRT-LLM · 🟡 Triton · ⚪ NeMo Guardrails |
| `eval-alvo-03` | alvo_graduacao | AI-native | 21/14/7/10 | 🔴 NVIDIA NIM · 🔴 TensorRT-LLM · 🟡 Triton · ⚪ RAPIDS |
| `eval-alvo-04` | alvo_graduacao | AI-native | 17/16/8/14 | 🔴 NVIDIA NIM · 🔴 TensorRT-LLM · 🟡 NVIDIA Riva (ASR) · 🟡 Triton · ⚪ NeMo Guardrails |
| `eval-alvo-05` | alvo_graduacao | AI-native | 16/19/6/15 | 🔴 NVIDIA NIM · 🔴 TensorRT-LLM · 🟡 Triton · ⚪ RAPIDS |
| `eval-alvo-06` | alvo_graduacao | AI-native | 22/14/5/11 | 🔴 NVIDIA NIM · 🔴 TensorRT-LLM · 🟡 Triton |
| `eval-noai-01` | fora_escopo | non-AI | 4/3/1/9 | _(nenhuma — fora do escopo de prescrição: periférico/non-AI ou wrapper frágil)_ |
| `eval-noai-02` | fora_escopo | non-AI | 5/2/0/8 | _(nenhuma — fora do escopo de prescrição: periférico/non-AI ou wrapper frágil)_ |
| `eval-noai-03` | fora_escopo | non-AI | 3/4/2/7 | _(nenhuma — fora do escopo de prescrição: periférico/non-AI ou wrapper frágil)_ |
| `eval-noai-04` | fora_escopo | non-AI | 6/2/1/10 | _(nenhuma — fora do escopo de prescrição: periférico/non-AI ou wrapper frágil)_ |
| `eval-maduro-01` | maduro | AI-native | 20/18/19/20 | 🔴 NVIDIA AI Enterprise |
| `eval-maduro-02` | maduro | AI-native | 18/17/21/18 | 🔴 NVIDIA AI Enterprise |
| `eval-maduro-03` | maduro | AI-native | 23/16/18/22 | 🔴 NVIDIA AI Enterprise |
| `eval-maduro-04` | maduro | AI-native | 17/21/16/19 | 🔴 NVIDIA AI Enterprise · 🟡 NeMo Guardrails |
| `eval-maduro-05` | maduro | AI-native | 24/17/20/17 | 🔴 NVIDIA AI Enterprise |
| `eval-enabled-01` | periferico | AI-enabled | 7/6/5/16 | _(nenhuma — fora do escopo de prescrição: periférico/non-AI ou wrapper frágil)_ |
| `eval-enabled-02` | periferico | AI-enabled | 8/5/4/15 | _(nenhuma — fora do escopo de prescrição: periférico/non-AI ou wrapper frágil)_ |
| `eval-enabled-03` | periferico | AI-enabled | 6/7/4/13 | 🔴 NeMo Guardrails |
| `eval-enabled-04` | periferico | AI-enabled | 7/5/5/12 | _(nenhuma — fora do escopo de prescrição: periférico/non-AI ou wrapper frágil)_ |
| `eval-enabled-05` | periferico | AI-enabled | 6/6/4/11 | 🔴 NeMo Guardrails |
| `eval-wrapper-01` | wrapper | AI-native | 3/5/3/6 | _(nenhuma — fora do escopo de prescrição: periférico/non-AI ou wrapper frágil)_ |
| `eval-wrapper-02` | wrapper | AI-native | 4/6/4/7 | _(nenhuma — fora do escopo de prescrição: periférico/non-AI ou wrapper frágil)_ |
| `eval-wrapper-03` | wrapper | AI-native | 2/4/3/5 | _(nenhuma — fora do escopo de prescrição: periférico/non-AI ou wrapper frágil)_ |
| `eval-wrapper-04` | wrapper | AI-native | 5/8/6/8 | 🔴 NeMo Guardrails |
