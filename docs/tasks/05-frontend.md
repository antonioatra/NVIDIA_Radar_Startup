# F5 — Interface Web (Entregável 5)

**Objetivo:** dashboard para consulta, visualização de empresas/recomendações e export de briefing.
**Dependências:** F2, F4. **Marco:** M5.

## Tasks
- [ ] **F5.1** Setup Next.js (App Router) + TypeScript + Tailwind + shadcn/ui. **UI em PT-BR** (F0.13).
- [ ] **F5.2** API FastAPI: endpoints `POST /runs`, `GET /runs/{id}`, `GET /companies`,
      `/briefings/{id}` **+ `POST /runs/{id}/resume`** (retoma o grafo após o HITL — F2.8). O SSE
      de `GET /runs/{id}` lê o canal Redis pub/sub publicado pelo worker (F2.10). `GET /companies`
      aceita os filtros de tecnologia da F5.11 (`tech`, `nvidia_tech`); o chat da F5.12 (stretch)
      adiciona `POST /companies/chat` (SSE).
- [ ] **F5.3** Tela de consulta (**dois modos**: single-company lookup e discovery por setor/região,
      F2.3) + acompanhamento **ao vivo** do pipeline via **SSE**.
- [ ] **F5.4** Lista/busca de startups (filtros por setor, AIMI, classificação) **+ ordenação por
      `inception_priority` (F6.13)** — a fila de outreach do gerente.
- [ ] **F5.5** Detalhe da startup: **radar AIMI** (4 pilares) + evidências com link à fonte.
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
