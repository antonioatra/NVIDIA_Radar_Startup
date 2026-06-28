# Roteiro — vídeo de demonstração (NVIDIA Startup AI Radar · só o funcionamento do app)

**Autor:** Antônio Augusto Tavares Ribeiro André
**Formato:** screencast **sem narração** — só mostrar o app funcionando ponta a ponta.
Arquitetura, tese e decisões ficam para **outro vídeo**. Duração-alvo ~5 min (flexível).

> Sem voz e sem legendas explicativas. O que orienta o espectador é a **própria UI** (ela é toda
> em PT-BR). Deixe cada tela "respirar" 2–3 s para dar tempo de ler.

## Antes de gravar (checklist)

- [ ] Stack completa no ar: `.\scripts\run.ps1` (sobe api + worker + frontend + infra, migra e popula a coorte). Conferir `localhost:3000` (UI), `localhost:8080/docs` (API).
- [ ] `.env` com as chaves do caminho real (`NVIDIA_API_KEY`, `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`) — a consulta ao vivo precisa delas.
- [ ] **Empresa-alvo escolhida e testada** para a consulta ao vivo: use uma que raspa limpo (ex.: `handtalk.me` — é o caminho e2e já validado). **Rode-a uma vez antes** de gravar (aquece o cache, confirma que conclui) e só então grave a tomada ao vivo.
- [ ] **Plano B** pronto: uma startup já processada aberta em outra aba no `/radar/[id]`, caso a consulta ao vivo trave/demore.
- [ ] Coorte com algumas empresas já no `/radar` e `/coorte` (o seed já faz isso).
- [ ] Navegador limpo: tela cheia, zoom ~110%, sem barra de favoritos/extensões/notificações. Gravar em 1080p.

---

## Shot list

| Tempo | Tela (rota) | Ação na tela (o que fazer/mostrar) |
|---|---|---|
| **0:00–0:20** | **Home** `/` | Abrir a home. Deixar ler o título "NVIDIA Startup AI Radar" e o subtítulo. Passar o mouse pelos 4 cards (Consulta · Radar de startups · Descoberta · Radar de coorte) sem clicar. |
| **0:20–0:40** | `/consulta` | Clicar **"Nova consulta"**. Garantir o modo **"Empresa"** selecionado. Digitar o domínio da empresa-alvo no campo. Clicar **"Consultar"**. |
| **0:40–1:30** | `/consulta` (pipeline) | Mostrar a seção **"Pipeline"** aparecer: a barra de progresso enchendo e a **escada de nós** marcando ✓ um a um (spinner no nó ativo) — o grafo multi-agente rodando ao vivo via SSE. *Se a espera passar de ~40 s, acelere o trecho (time-lapse) ou corte.* |
| **1:30–2:05** | `/consulta` (HITL) | O run pausa e abre o painel **"Revisão humana (HITL)"**: mostrar **Classe**, **AIMI (x/100)** e **Recomendações**. Clicar **"Editar diagnóstico"** (aparecem os selects de classe/AIMI) só para mostrar; depois **"Aprovar e retomar"**. |
| **2:05–2:25** | `/consulta` (desfecho) | O stream retoma os nós restantes e conclui. Mostrar **"Desfecho"** e os dois links que surgem: **"Ver passos do run (trace) →"** e **"Exportar briefing (PDF) ↓"**. |
| **2:25–2:50** | `/runs/[id]/trace` | Clicar em **"Ver passos do run (trace)"**. Rolar mostrando os passos dos agentes (cada nó, status). Voltar. |
| **2:50–3:30** | Briefing (PDF) | Clicar em **"Exportar briefing (PDF)"** — abre o PDF. Rolar devagar: diagnóstico AIMI → recomendações com **evidência dos dois lados** (gap da startup + citação NVIDIA) → ROI, se houver. Fechar a aba do PDF. |
| **3:30–4:00** | `/radar` | Voltar e ir em **"Ver radar de startups"**. Mostrar a coorte mapeada; aplicar um **filtro** (setor / maturidade AIMI / classe); apontar a ordenação por **Inception Priority**. |
| **4:00–4:35** | `/radar/[id]` | Clicar numa startup. Mostrar o **radar AIMI (4 pilares)**, as **evidências** (links rastreáveis) e os **cartões de recomendação**. |
| **4:35–5:00** | `/coorte` | Abrir **"Radar de coorte"**: a visão de portfólio — o ecossistema agrupado por perfil e ranqueado por **prontidão de graduação**. Encerrar aqui (tela parada 2–3 s). |

**Opcional (se quiser +15 s ou trocar pelo `/coorte`):** `/descoberta` — digitar uma pergunta em PT (ex.: "healthtechs AI-native em São Paulo") e mostrar as empresas voltando como conversa.

---

## Notas de gravação

- **A estrela é o item 0:40–1:30 (pipeline ao vivo) + 1:30–2:05 (HITL).** É o que prova que o app *funciona de verdade*. Grave com folga; se a consulta ao vivo falhar, troque pelo **plano B** (abrir uma empresa já processada no `/radar/[id]`) sem interromper a gravação.
- **Sem narração:** não fale nem adicione legendas explicativas — a UI em PT-BR já rotula tudo. Se quiser, só um **título de abertura** mudo ("NVIDIA Startup AI Radar — demonstração") e um **corte final** limpo.
- **Ritmo:** o tempo morto da consulta ao vivo é o maior risco de arrastar. Acelere/corte a espera; mantenha cheio o resto.
- **Se for editar para < 5 min:** corte primeiro o `/runs/[id]/trace` (2:25–2:50) e o `/descoberta`; o núcleo é consulta → pipeline → HITL → briefing PDF → radar.
- **Plano alternativo 100% sem credencial** (se não quiser depender de chave/rede): rodar `python scripts/demo.py --case <id>` num terminal e gravar o briefing determinístico saindo — menos visual, mas reproduz o resultado sem a stack no ar.
