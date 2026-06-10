# F5 — Interface Web (Entregável 5)

**Objetivo:** dashboard para consulta, visualização de empresas/recomendações e export de briefing.
**Dependências:** F2, F4. **Marco:** M5.

## Tasks
- [x] **F5.1** Setup Next.js (App Router) + TypeScript + Tailwind + shadcn/ui. **UI em PT-BR** (F0.13).
      → `apps/frontend/`: scaffold via `create-next-app` (decisão já travada no README do app) —
      **Next.js 16 (App Router) + TypeScript + Tailwind v4 + shadcn/ui**, `src/`-dir e alias `@/*`.
      `shadcn init` gravou `components.json` (baseColor neutral), `src/lib/utils.ts` (`cn`) e
      `src/components/ui/button.tsx`; os design tokens (oklch, dark via classe `.dark`) foram para o
      `globals.css`. **PT-BR (F0.13):** `<html lang="pt-BR">` + metadata e home page em português — a
      casca lista as telas do entregável como roadmap (consulta/F5.3, radar/F5.4, diagnóstico
      AIMI/F5.5, recomendações/F5.6, briefing/F5.8), com os botões shadcn **desabilitados** até a API
      (F5.2) e as telas (F5.3+) existirem (sem antecipar fase futura). Corrigi a fiação de fontes que o
      `shadcn init` deixou inconsistente (liguei `--font-sans`/`--font-mono` do `@theme` às fontes Geist
      do layout) e fixei `turbopack.root` no `next.config.ts` — havia múltiplos `package-lock.json` na
      árvore (home do usuário + raiz) e o Next inferia o workspace root errado. **Gate verde** (o
      `npm run build` é o gate da fase, equivalente ao pytest do backend): `npm run lint` e
      `npm run build` limpos (build estático, 0 erros de TypeScript); ruff/pytest do backend seguem
      verdes (nenhum Python tocado). `node_modules`/`.next` git-ignored; `package-lock.json` commitado
      para builds reprodutíveis. **Nota Next 16:** versão pós-cutoff com breaking changes — o
      `create-next-app` deixou um `apps/frontend/AGENTS.md`/`CLAUDE.md` apontando para os docs
      empacotados em `node_modules/next/dist/docs/` (consultar antes de mexer no app).
- [x] **F5.2** API FastAPI: endpoints `POST /runs`, `GET /runs/{id}`, `GET /companies`,
      `/briefings/{id}` **+ `POST /runs/{id}/resume`** (retoma o grafo após o HITL — F2.8). O SSE
      de `GET /runs/{id}` lê o canal Redis pub/sub publicado pelo worker (F2.10). `GET /companies`
      aceita os filtros de tecnologia da F5.11 (`tech`, `nvidia_tech`); o chat da F5.12 (stretch)
      adiciona `POST /companies/chat` (SSE).
      → `apps/api/` (`main.py` rotas, `deps.py` DI, `companies.py` query, `schemas.py` DTOs): os 5
      endpoints sobre o worker (F2.10) e a persistência (F0.6/F4.7). **`POST /runs`** só
      **enfileira** (`enqueue_run`) e responde `run_id` (202, `status=pending`) — run longo não cabe
      no request. **`GET /runs/{id}`** é **SSE** (`text/event-stream`, frames `data: <json>`):
      assina o canal Redis pub/sub do run (`subscribe_progress`, F2.10) e repassa cada
      `ProgressEvent`. **`POST /runs/{id}/resume`** fecha o laço do HITL sync (F2.8): enfileira o
      **novo driver de retomada** que esta task entregou — `resume_pipeline` (em `progress.py`,
      irmão do `stream_pipeline`: `Command(resume=<decisão>)` na thread persistida, emite só os nós
      restantes + terminal) e `resume_graph_job`/`enqueue_resume` (worker, `job_id="{run_id}:resume"`
      distinto do job original). Refatorei o `stream_pipeline` extraindo o núcleo `_drive`/`_publish`
      compartilhado (sem mudar o comportamento — `test_progress` segue verde). **`GET /companies`**
      projeta `Company` + o `Score` (AIMI/classe/`inception_priority`) do run mais recente + techs
      recomendadas (`Recommendation`), com os filtros setor/AIMI/classe (F5.4) e as **duas facetas de
      tech** (F5.11 — a que a startup usa e a NVIDIA recomendada; match por substring, a normalização
      de vocabulário fica na F5.11), ordenado por `inception_priority` (fila de outreach, F6.13).
      **`GET /briefings/{id}`** serve o relatório (F4.4) do estado persistido (checkpoint, F2.2) em
      **JSON | Markdown | PDF** (reusa `render_markdown`/`render_pdf` da F4.6 — base do export F5.8),
      404 sem briefing. Recursos vivos (fila/Redis/sessão/leitor de briefing) entram por
      **dependência** sobrescrevível, então a `tests/test_api.py` exercita tudo **offline** (SQLite em
      memória, fila/SSE/loader stubados — sem broker/Postgres/worker). **Auth deferida à F5.9** (gancho
      de dependência documentado, não implementado aqui). **Gate verde:** `ruff` limpo e `pytest`
      (608 passed, 4 skipped). `requirements-ci.txt` ganhou `fastapi`+`httpx` (test client), no padrão
      do `reportlab`/`pypdf` da F4.6.
- [x] **F5.3** Tela de consulta (**dois modos**: single-company lookup e discovery por setor/região,
      F2.3) + acompanhamento **ao vivo** do pipeline via **SSE**.
      → `apps/frontend/src/app/consulta/`: casca **server** (`page.tsx`, metadata + cabeçalho PT-BR)
      sobre o **console client** (`console.tsx`, `"use client"`). O formulário tem os **dois modos**
      como segmented control (`single_company` / `discovery` → `ExecutionMode`, F2.3) e deriva o
      `hitl` do modo (single→`sync`, discovery→`auto`, F2.8). Fluxo: `createRun` (`POST /runs`) →
      `run_id` → **`EventSource`** no `GET /runs/{id}` (F5.2); consome cada `ProgressEvent`
      (status=running, o nó que acabou) e fecha o stream no **terminal** `END_NODE`, lendo o desfecho
      real (`completed`/`awaiting_review`/…). A espinha do grafo é espelhada em `src/lib/pipeline.ts`
      (ordem/nomes de `PIPELINE`, F2.1) com rótulos PT-BR + `statusLabel` (`RunStatus`); a UI desenha
      a **barra por `pct`** e marca cada etapa (check/spinner/anel) pelos nós já vistos. O
      `awaiting_review` **degrada gracioso** (nota apontando F5.10, sem antecipar a tela de
      aprovação). Cliente da API isolado em `src/lib/api.ts` com base por **`NEXT_PUBLIC_API_URL`**
      (default `http://localhost:8000`; **auth F5.9 deferida** — entra como header aqui). A **home**
      passou a habilitar "Nova consulta" (`<Link href="/consulta">` via `buttonVariants`); "Ver radar
      de startups" segue desabilitado (F5.4). **Gate verde** (o gate da fase): `npm run lint` e
      `npm run build` limpos (TypeScript 0 erros, `/consulta` prerenderizada estática); nenhum Python
      tocado, então `ruff`/`pytest` do backend seguem verdes. **Nota Next 16:** consultei
      `node_modules/next/dist/docs/` (App Router, server×client, params Promise) antes de escrever —
      ícones via CSS (sem depender de nomes do `lucide-react`, que mudam entre versões).
- [x] **F5.4** Lista/busca de startups (filtros por setor, AIMI, classificação) **+ ordenação por
      `inception_priority` (F6.13)** — a fila de outreach do gerente.
      → `apps/frontend/src/app/radar/`: casca **server** (`page.tsx`, metadata + cabeçalho PT-BR)
      sobre o **board client** (`board.tsx`, `"use client"`) que consome o `GET /companies` (F5.2).
      Os **três filtros** da task — `setor` (input texto), `classificacao` (segmented AI-native/
      AI-enabled/non-AI, espelha `Classification` §5.1) e `min_aimi` (range 0–100) — combinam em AND
      no backend; a lista **já vem ordenada por `inception_priority` desc** (a API ordena, F6.13), a
      UI só numera as linhas. Cada empresa mostra nome + badge de classe (AI-native em destaque) +
      AIMI + Inception Priority, com `—` quando ainda não pontuada (campos de diagnóstico opcionais).
      Cliente da API ganhou `listCompanies(filters)` + o tipo `CompanyOut` em `src/lib/api.ts`
      (monta a query com `URLSearchParams`, omite vazios). O board **rebusca com debounce de 300ms**
      ao mudar qualquer filtro (sem martelar a API a cada tecla do setor) e degrada com estados
      `loading`/`error`/vazio. **Sem antecipar fase futura:** as facetas de tech (F5.11) e o detalhe
      AIMI clicável (F5.5) ficam fora — nota na UI apontando a F5.5. A **home** habilitou "Ver radar
      de startups" (`<Link href="/radar">` via `buttonVariants`, removido o `<Button disabled>`).
      **Gate verde** (o gate da fase): `npm run lint` e `npm run build` limpos (TypeScript 0 erros,
      `/radar` prerenderizada estática); nenhum Python tocado, então `ruff`/`pytest` do backend
      seguem verdes. **Nota Next 16:** o lint novo do React 19 (`react-hooks/set-state-in-effect`)
      barra `setState` síncrono no corpo do effect — o `setPhase("loading")` foi para dentro do
      callback do timer (o estado inicial já é `loading`, então o primeiro load não pisca).
- [x] **F5.5** Detalhe da startup: **radar AIMI** (4 pilares) + evidências com link à fonte.
      → **Backend** (`apps/api/`): nova rota **`GET /companies/{id}`** + a função `get_company_detail`
      (`companies.py`) e os DTOs `CompanyDetailOut`/`PillarOut`/`EvidenceOut` (`schemas.py`). O
      detalhe achata a `Company` (§2) com o `Score` **mais recente** e devolve o **breakdown** do
      AIMI: os 4 sub-scores na ordem canônica (RUBRICA §1) com a **faixa** derivada (reusa
      `band_for`, sem duplicar), a justificativa (`just_*`) e as **fontes citáveis por pilar** —
      as linhas `evidence` com `entity_type='score'`/`field=<pilar>`, agrupadas por pilar. `404`
      quando a empresa não existe; empresa coletada mas **não pontuada** sai com `pilares=[]` e o
      diagnóstico nulo (mesma degradação graciosa da lista F5.4). **Nota de honestidade:** a
      persistência do AIMI ainda não grava evidência de score (não há `persist_score` — a tabela
      `Score` é escrita só em teste hoje; F6.2/persistência futura); a rota já **superfície** o
      `field=<pilar>` corretamente, então os links aparecem assim que essa escrita existir — até
      lá o pilar mostra o sub-score sem link, sem quebrar. **Frontend** (`apps/frontend/`): rota
      **`/radar/[id]`** — casca **server** (`page.tsx`, metadata; `params` é **Promise** no Next 16,
      resolvido com `await`) sobre a **view client** (`detail.tsx`) que busca `getCompany(id)`
      (`lib/api.ts`, com os tipos `CompanyDetail`/`PillarOut`/`EvidenceOut`; `404` vira mensagem
      própria). A tela desenha um **radar SVG dos 4 pilares** (0–25/eixo) **sem dependência de
      chart** — eixos topo/direita/baixo/esquerda, anéis-guia e polígono via `currentColor` + os
      tokens oklch do tema (mesma disciplina de "sem dep frágil" da F5.3) — e, ao lado, um card por
      pilar com barra do sub-score, faixa, justificativa e as **evidências como `<a>`** (`target=
      _blank` + `rel=noopener`, link à fonte). Os rótulos PT-BR dos pilares espelham o texto do
      briefing (`packages/agents/briefing.py`). A **lista F5.4** (`board.tsx`) agora tem cada linha
      como **`<Link href="/radar/{id}">`** (hover/focus visíveis), removida a nota "habilita na
      F5.5". **Sem antecipar fase futura:** os cartões de recomendação+ROI (F5.6) e o filtro por
      tech (F5.11) ficam fora; só os chips de techs NVIDIA recomendadas aparecem (já vêm do detalhe).
      **Gate verde:** `npm run lint` e `npm run build` limpos (TypeScript 0 erros; `/radar/[id]`
      server-rendered on demand) e, como desta vez **tocou Python** (`apps/api`), o backend também:
      `ruff` limpo e `pytest` **610 passed, 4 skipped** (1 deselecionado = o smoke de rede
      `test_smoke_real`, que exige endpoint externo). `tests/test_api.py` ganhou 3 testes do detalhe
      (pilares+evidência, empresa sem score, `404`) e o `_seed` passou a semear evidência de score.
- [x] **F5.6** Cartões de recomendação (§5.5) + número de ROI. **ROI é opcional:** vem do F6, que
      roda em paralelo a esta fase — a UI degrada graciosamente (mostra a recomendação sem o ROI
      enquanto a matriz/benchmark do F6 não existir; exibe o número quando disponível).
      → **Backend** (`apps/api/`): o detalhe `GET /companies/{id}` (F5.5) ganhou os **cartões**.
      Novos DTOs em `schemas.py` — `RecommendationOut` (tech, prioridade/complexidade, as duas
      justificativas, próxima ação, `pilar_origem`, evidência dos dois lados e `roi`) e `ROIOut`
      (projeção do `ROIEstimate`/F0.5: throughput/p95/custo, baseline→otimizado, fonte e
      `is_live_run`) — e o campo `recomendacoes` no `CompanyDetailOut`. Em `companies.py`,
      `_recommendation_cards` projeta as linhas `recommendation` (F4.3/F4.7) **ordenadas por
      prioridade** (alta→baixa, igual ao briefing/F4.4), carrega a **evidência dos dois lados** via
      o helper generalizado `_evidence_by_field` (antes `_score_evidence` — agora serve score E
      recomendação, `field='gap'`/`'nvidia'`) e desserializa o `roi` JSON com
      `ROIOut.model_validate` (`None` → cartão sem número). O `nvidia_techs` agora **deriva** dos
      cartões (removida a query redundante). **Honestidade:** os cartões saem de **todas** as
      recomendações da empresa (como já era o `nvidia_techs`); filtrar pelo run do score vigente
      fica para quando houver multiplicidade de runs por empresa. **Frontend** (`apps/frontend/`):
      `lib/api.ts` ganhou os tipos `RecommendationOut`/`ROIOut` + `recomendacoes` no
      `CompanyDetail`; `radar/[id]/detail.tsx` trocou os **chips placeholder** (a nota "chegam na
      F5.6") por uma seção **"Recomendações NVIDIA"** com um `RecommendationCard` por item — header
      (tech + badge de prioridade, alta em destaque + complexidade), pilar de origem, as duas
      justificativas e a próxima ação, a faixa **`RoiStrip`** (throughput `Nx`, custo/p95 com sinal
      explícito = melhora, baseline→otimizado, selo matriz×ao-vivo) que **só aparece com `roi`** e
      omite cada número ausente, e duas colunas de **evidência** (gap × NVIDIA) com link à fonte
      (`target=_blank`+`rel=noopener`; "sem fonte registrada ainda" quando vazia). Rótulos PT-BR
      reusam o `PILLAR_LABELS` da F5.5; sem dependência de chart/UI nova (mesma disciplina das
      F5.3–F5.5). **Sem antecipar fase futura:** filtro por tech (F5.11) e export do briefing (F5.8)
      ficam fora. **Gate verde:** backend `ruff` limpo e `pytest` verde (suíte completa exit 0;
      `test_api.py` **18 passed**, +2 testes novos — cartão completo com ROI/evidência dos 2 lados e
      ordenação por prioridade com ROI ausente degradando); frontend `npm run lint` e `npm run
      build` limpos (TypeScript 0 erros, `/radar/[id]` server-rendered). **Nota Next 16:** só edição
      de client component existente (reuso de `useState`/`useEffect`/`cn`), sem API nova do Next.
- [x] **F5.7** Trace viewer: passos dos agentes (consome Langfuse/estado do grafo).
      → **Backend** (`apps/api/`): novo `GET /runs/{id}/trace` que **reconstrói o trace do estado
      persistido** do run (checkpoint, F2.2) — fonte offline-reproduzível, sem depender do Langfuse no
      ar. `apps/api/trace.py` (puro/testável) projeta o `GraphState` em `RunTraceOut`: a espinha de
      nós (`PIPELINE`, F2.1) vira passos cujo `status` deriva da **presença do artefato** de cada nó
      no estado — `done` (deixou artefato), `skipped` (run terminou sem passar aqui: ramo terminal
      F2.12/F2.13, ou etapa opcional sem saída, ex.: `gpu_benchmark` sem ROI) ou `pending` (pausou/
      falhou antes de chegar) — com `summary` factual nos `done` (ex.: "12 documentos coletados",
      "AI-native · AIMI 62/100", "5 trechos da KB NVIDIA"). `evidence_validator` herda o `aimi` (roda
      colado ao classifier, sem campo próprio) e `human_review` só conclui no `completed` (nos ramos
      terminais o grafo salta direto ao briefing). Soma o rollup de custo (`trace['usage']`, F2.9), a
      nota de orçamento (F2.11) e os `errors` rastreáveis; o `langfuse_url` (deep-trace, F0.8) entra
      como link opcional — **honestidade:** sem `trace_id` persistido não há deep-link por run, então
      expomos o **host** do Langfuse (só quando as chaves estão setadas, F0.3) e mantemos o
      passo-a-passo no estado do grafo. DTOs novos em `schemas.py`
      (`RunTraceOut`/`TraceStepOut`/`TraceUsageOut`), loader `get_trace_loader` (espelha o de briefing
      — devolve o `GraphState` inteiro) e `get_langfuse_url` em `deps.py`. **Frontend**
      (`apps/frontend/`): rota nova `/runs/[id]/trace` (casca server + `RunTraceView` client, mesmo
      padrão Next 16 do detalhe F5.5) que consome o endpoint e desenha a **timeline dos passos** —
      reusa os rótulos PT-BR da espinha (`PIPELINE_STEPS`, F5.3) e o `statusLabel`; marcador por
      status (✓ concluído · – pulado · anel pendente), resumo por passo, faixa de custo
      (tokens/chamadas/custo) que **só aparece com `usage`** (run offline esconde), selo de orçamento
      atingido, botão "Abrir no Langfuse" quando há `langfuse_url` e lista de erros rastreáveis. O
      console da consulta (F5.3) ganhou o link **"Ver passos do run (trace)"** ao terminar (run_id em
      mãos). **Sem antecipar fase futura:** sem trace_id por run (deep-link fica para quando o estado
      carimbar o id) e sem consumir a API do Langfuse direto. **Gate verde:** backend `ruff` limpo e
      `pytest` verde (suíte completa **618 passed, 4 skipped**; 2 deselected = os smokes de rede
      `test_smoke_real`/`test_search_real`, que exigem endpoint externo — hoje 504); `tests/test_api.py`
      +7 testes (done/skipped/pending, ramo terminal, custo/orçamento/Langfuse, endpoint + 404).
      Frontend `npm run lint` e `npm run build` limpos (TypeScript 0 erros, `/runs/[id]/trace`
      server-rendered como o `/radar/[id]`).
- [x] **F5.8** Export do briefing em PDF.
      → **Frontend** (`apps/frontend/`): superfície de export sobre o `GET /briefings/{id}` que a
      F5.2 já entrega em JSON|Markdown|PDF (renderizadores deterministas da F4.6) — esta task **não
      tocou backend**. `lib/api.ts` ganhou `briefingUrl(runId, format)` (+ tipo `BriefingFormat`):
      **monta a URL** do relatório em vez de fazer `fetch`, porque o PDF sai com
      `Content-Disposition: inline` e a auth (F5.9) entrará como query/header aqui. O **console da
      consulta** (`consulta/console.tsx`, F5.3) ganhou, ao concluir, o link **"Exportar briefing
      (PDF)"** ao lado do "Ver passos do run (trace)" (F5.7) — agrupei os dois numa linha de ações.
      Abre o PDF em nova aba (`target=_blank` + `rel=noopener noreferrer`, mesma disciplina dos links
      de evidência da F5.5/F5.6); cross-origin ignora `download`, então o relatório inline é o
      caminho honesto (o gerente salva de lá). **Só oferece o PDF quando há briefing:** novo helper
      `hasBriefing(status)` em `pipeline.ts` (junto do `STATUS_LABELS`) libera o link só nos
      desfechos que chegaram ao nó `briefing` — `completed` e os ramos terminais que saltam direto a
      ele (`insufficient_data` F2.12 / `out_of_scope` F2.13) — e o esconde em `awaiting_review`
      (pausa ANTES do briefing, F2.8/F5.10) e `failed`, evitando um link que daria 404. O status
      terminal vem **sempre** no evento `END_NODE` (F2.10), então o gate é confiável mesmo se algum
      evento intermediário se perder. **Sem antecipar fase futura:** export só do PDF (o helper já
      aceita md/json para reuso), sem página dedicada de briefing nem auth (F5.9). **Gate verde** (o
      gate da fase): `npm run lint` e `npm run build` limpos (TypeScript 0 erros, `/consulta` segue
      prerenderizada estática — o link é client, não muda a rota); nenhum Python tocado, então
      `ruff`/`pytest` do backend seguem verdes. **Nota Next 16:** só edição de client component
      existente; link externo (cross-origin para a API) é `<a>` puro, não `next/link` (igual aos
      links de evidência da F5.5) — `AGENTS.md`/`node_modules/next/dist/docs/` consultados.
- [x] **F5.9** **Auth leve (gate interno):** a ferramenta é interna do gerente de Startups & VCs
      da NVIDIA Brasil — não é público. Proteger a API e a UI com autenticação simples
      (API key/bearer token via env, ou login único), aplicada como dependência nos endpoints
      do F5.2. Não expor `POST /runs` nem dados de empresas sem credencial. Mantém-se leve
      (sem IdP/OAuth completo) — proporcional a uma ferramenta interna de demo, mas fecha o
      buraco de "endpoint aberto" coerente com a governança/LGPD do projeto (F1.13).
      → **Backend** (`apps/api/`): o gate vive em `deps.py` como `require_auth` (+ o provider
      `get_auth_token`, que lê `TAPI_API_TOKEN` da config F0.3). `main.py` move os **endpoints de
      negócio** para um `APIRouter(dependencies=[Depends(require_auth)])` — todos atrás do gate de
      uma vez (DRY) — e deixa **só `/health` aberto** (liveness; passou a devolver `auth_required`
      p/ o front decidir se pede login). **Open-by-default (chave da espinha verde):** sem
      `TAPI_API_TOKEN` o gate fica **aberto** (dev/offline reproduzível, todos os testes existentes
      seguem sem credencial); com token, exige-o. Aceita o token por `Authorization: Bearer`,
      `X-API-Key` **ou** `?token=` na query — este último porque o **SSE** (`EventSource`) e o
      **PDF** (`<a>`) do front (F5.2/F5.8) navegam sem poder setar header. **Honestidade:** token na
      URL pode vazar em log — trade-off assumido de ferramenta interna (não é OAuth); comparação em
      tempo constante (`secrets.compare_digest`), `401` + `WWW-Authenticate: Bearer`. **Frontend**
      (`apps/frontend/`): `lib/auth.ts` guarda o token compartilhado no `localStorage` (digitado em
      runtime — **não** vai pro bundle, nada de `NEXT_PUBLIC_*` com segredo) e expõe `authHeaders`
      (fetch) / `appendToken` (SSE+PDF). `lib/api.ts` ganhou o wrapper `req` que injeta o header e,
      no **401**, limpa a sessão e dispara `tapi:unauthorized` (volta a UI pro login), além de
      `fetchHealth`/`pingAuth`. O novo `components/auth-gate.tsx` (client, envolve os `children`
      server no `layout.tsx` — padrão de provider do App Router) sonda o `/health` no boot: API sem
      gate → abre direto; com gate e sem token → **tela de login** (valida o token via `pingAuth`
      antes de liberar); ouve o `tapi:unauthorized` p/ reexigir login. **Sem antecipar fase futura:**
      gate por token único compartilhado (não há multiusuário/IdP — fora do escopo "leve"); a tela
      HITL (F5.10) e o filtro por tech (F5.11) seguem nas suas tasks. **Gate verde:** backend `ruff`
      limpo e `pytest` **628 passed, 4 skipped** (`test_api.py` +9 testes de auth — health
      aberto/`auth_required`, gate aberto×fechado, bearer/X-API-Key/query token aceitos, sem/errada
      credencial = 401; o fixture `client` força o modo aberto p/ os testes existentes serem
      determinísticos); frontend `npm run lint` e `npm run build` limpos (TypeScript 0 erros, rotas
      preservadas). **Nota Next 16:** o `react-hooks/set-state-in-effect` (React 19) barrou o
      `setState` síncrono do probe no effect — movido p/ o callback async da Promise (`resolveGate`),
      com o "checking" do retry no event handler; `node_modules/next/dist/docs/` (server×client,
      provider no layout) consultado antes de escrever.
- [ ] **F5.10** **Tela de revisão/aprovação HITL (modo `sync`):** quando o grafo pausa no interrupt
      (F2.8), a UI mostra a classificação/AIMI/recomendação para o gerente **aprovar, editar ou
      rejeitar** e então chama `POST /runs/{id}/resume` (F5.2) com a decisão. Sem essa tela o
      interrupt fica inalcançável pela UI. Só no *single-company lookup* (`hitl=sync`); em lote o
      `hitl=auto` (F1.14) não usa esta superfície.
- [ ] **F5.11** **Filtro por tecnologia (estende a lista F5.4):** duas facetas novas no
      `GET /companies` (F5.2) e na UI — (a) **tech que a startup usa**, derivada de
      `StartupProfile.tecnologias` (F2.5) + sinais AI-native (F1.11); (b) **tech NVIDIA
      recomendada**, derivada do `Recommendation` (F4.3) — ex.: filtrar "candidatas a Riva/NIM/
      RAPIDS". Tags normalizadas (vocabulário controlado) para o filtro ser determinístico e sem
      LLM. Soma-se aos filtros já existentes (setor/AIMI/classificação) e à ordenação por
      `inception_priority`. **MVP.**
- [ ] **F5.12** *(stretch)* **Chat de descoberta da coorte (linguagem natural → empresas):** caixa
      de busca conversacional (ex.: "startups de saúde com Workflow alto e Technical Optimization
      baixo") que devolve **cards de empresa fundamentados + citações**, com streaming via SSE
      (reusa o canal do F5.3). Consome o **cohort-RAG (F3.10)** no backend; **não inventa empresa**
      (NeMo Guardrails, princípio nº1 da ARQUITETURA §8 — nada sem fonte). É a camada premium de
      descoberta **por cima** do filtro estruturado (F5.11), não o substitui.

## Tecnologias
Next.js · React · TypeScript · Tailwind/shadcn · FastAPI · SSE · auth (API key/bearer).

## DoD
- [x] Fluxo completo navegável: consulta → progresso (F5.3) → empresa (F5.4/F5.5) → recomendação
      (F5.6) → export PDF (F5.8), atrás do gate interno (F5.9). *(Filtro por tech F5.11 e HITL
      F5.10 seguem abertos.)*
- [x] API e UI exigem credencial; endpoints não respondem sem auth (F5.9). *(Gate por token único
      compartilhado via `TAPI_API_TOKEN`; aberto quando não configurado — dev/offline.)*
- [ ] Lista filtrável por tecnologia (tech da startup + tech NVIDIA recomendada), além de
      setor/AIMI/classificação (F5.11, MVP).
- [ ] *(stretch)* Chat de descoberta responde em linguagem natural com cards de empresa citados
      e nunca retorna empresa sem evidência (F5.12).
- [ ] No modo `sync`, o run pausa no HITL e só segue após aprovação na UI via `resume` (F5.10).
