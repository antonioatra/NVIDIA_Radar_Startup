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
- [ ] **F5.6** Cartões de recomendação (§5.5) + número de ROI. **ROI é opcional:** vem do F6, que
      roda em paralelo a esta fase — a UI degrada graciosamente (mostra a recomendação sem o ROI
      enquanto a matriz/benchmark do F6 não existir; exibe o número quando disponível).
- [ ] **F5.7** Trace viewer: passos dos agentes (consome Langfuse/estado do grafo).
- [ ] **F5.8** Export do briefing em PDF.
- [ ] **F5.9** **Auth leve (gate interno):** a ferramenta é interna do gerente de Startups & VCs
      da NVIDIA Brasil — não é público. Proteger a API e a UI com autenticação simples
      (API key/bearer token via env, ou login único), aplicada como dependência nos endpoints
      do F5.2. Não expor `POST /runs` nem dados de empresas sem credencial. Mantém-se leve
      (sem IdP/OAuth completo) — proporcional a uma ferramenta interna de demo, mas fecha o
      buraco de "endpoint aberto" coerente com a governança/LGPD do projeto (F1.13).
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
- [ ] Fluxo completo navegável: consulta → progresso → empresa → recomendação → export PDF.
- [ ] API e UI exigem credencial; endpoints não respondem sem auth (F5.9).
- [ ] Lista filtrável por tecnologia (tech da startup + tech NVIDIA recomendada), além de
      setor/AIMI/classificação (F5.11, MVP).
- [ ] *(stretch)* Chat de descoberta responde em linguagem natural com cards de empresa citados
      e nunca retorna empresa sem evidência (F5.12).
- [ ] No modo `sync`, o run pausa no HITL e só segue após aprovação na UI via `resume` (F5.10).
