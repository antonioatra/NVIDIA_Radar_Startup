// Cliente da API TAPI (FastAPI, F5.2) consumido pelo front. O run longo nao cabe no
// request: `POST /runs` so enfileira e devolve o `run_id`; o progresso ao vivo chega por
// SSE em `GET /runs/{id}` (canal Redis pub/sub do worker, F2.10) — ver `runStreamUrl`.
//
// A base da API vem de `NEXT_PUBLIC_API_URL` (inlinada no bundle no build); o default
// `http://localhost:8000` cobre o dev local. A auth (F5.9) entrara aqui como header.
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Modos de consulta (espelha ExecutionMode, packages/schemas/enums.py — F2.3).
export type RunMode = "single_company" | "discovery";

// Modo do HITL (HITLMode, F2.8): sync trava no single-company, auto nao bloqueia o lote.
export type HitlMode = "sync" | "auto";

// Resposta de `POST /runs` e `/resume` (RunAccepted, apps/api/schemas.py).
export interface RunAccepted {
  run_id: string;
  status: string;
}

// Evento de progresso por no (ProgressEvent, packages/agents/progress.py — contrato SSE).
export interface ProgressEvent {
  run_id: string;
  node: string;
  status: string;
  pct: number | null;
  ts: string;
  extra: Record<string, unknown>;
}

// Enfileira um run e devolve o `run_id`. O `hitl` segue o modo: single-company trava no
// interrupt (sync, F2.8/F5.10), discovery roda em lote sem bloquear a fila (auto).
export async function createRun(query: string, mode: RunMode): Promise<RunAccepted> {
  const hitl: HitlMode = mode === "single_company" ? "sync" : "auto";
  const res = await fetch(`${API_URL}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, mode, hitl }),
  });
  if (!res.ok) {
    throw new Error(`Falha ao enfileirar a consulta (HTTP ${res.status}).`);
  }
  return res.json() as Promise<RunAccepted>;
}

// URL do stream SSE do run — passada direto a `new EventSource(...)` no console (F5.3).
export function runStreamUrl(runId: string): string {
  return `${API_URL}/runs/${encodeURIComponent(runId)}`;
}

// Projecao de empresa da lista (CompanyOut, apps/api/schemas.py — F5.4): perfil achatado com o
// diagnostico AIMI mais recente. Os campos de diagnostico sao opcionais — empresa coletada mas
// ainda nao pontuada chega sem classe/AIMI. As facetas de tech (F5.11) ja vem populadas, mas o
// radar (F5.4) ainda nao as expoe como filtro.
export interface CompanyOut {
  id: number;
  nome: string;
  setor: string | null;
  pais: string;
  website: string | null;
  classificacao: string | null;
  aimi_total: number | null;
  inception_priority: number | null;
  tecnologias: string[];
  nvidia_techs: string[];
}

// Filtros do radar (F5.4): setor, classe de maturidade e AIMI minimo. Combinam em AND no
// backend; todos opcionais. As facetas de tech (F5.11) entram aqui depois.
export interface CompanyFilters {
  setor?: string;
  classificacao?: string;
  minAimi?: number;
}

// Lista as startups (perfil + AIMI) ja ordenadas por inception_priority desc (a fila de
// outreach do gerente, F6.13) no `GET /companies` (F5.2). Vazios sao omitidos da query.
export async function listCompanies(filters: CompanyFilters = {}): Promise<CompanyOut[]> {
  const params = new URLSearchParams();
  if (filters.setor?.trim()) params.set("setor", filters.setor.trim());
  if (filters.classificacao) params.set("classificacao", filters.classificacao);
  if (filters.minAimi != null && filters.minAimi > 0) {
    params.set("min_aimi", String(filters.minAimi));
  }
  const qs = params.toString();
  const res = await fetch(`${API_URL}/companies${qs ? `?${qs}` : ""}`);
  if (!res.ok) {
    throw new Error(`Falha ao carregar as startups (HTTP ${res.status}).`);
  }
  return res.json() as Promise<CompanyOut[]>;
}

// Fonte citavel de um sub-score (EvidenceOut, apps/api/schemas.py — F5.5): o link que sustenta
// o pilar. Pode vir vazia ate a persistencia do AIMI gravar essas linhas (a UI degrada).
export interface EvidenceOut {
  url: string;
  snippet: string;
  source_title: string | null;
}

// Um pilar do AIMI no detalhe (PillarOut, F5.5): sub-score 0-25 + faixa + justificativa + fontes.
// `pilar` e a chave tecnica (AIMIPillar, ex.: "data_moat"); o rotulo PT-BR e da UI.
export interface PillarOut {
  pilar: string;
  score: number;
  band: string;
  justificativa: string | null;
  evidencias: EvidenceOut[];
}

// ROI quantificado de uma recomendacao (ROIOut, F5.6/F6): opcional — vem do GPU Graduation Engine
// quando ha gap de inferencia. Convencao de sinal: delta negativo = melhora (menos custo/latencia).
// Quando ausente o cartao degrada gracioso (mostra a recomendacao sem o numero).
export interface ROIOut {
  throughput_speedup: number | null;
  latency_p95_delta_pct: number | null;
  cost_delta_pct: number | null;
  baseline: string | null;
  optimized: string | null;
  benchmark_source: string | null;
  is_live_run: boolean;
}

// Cartao de recomendacao no detalhe (RecommendationOut, §5.5/F5.6): tech + justificativas +
// evidencia dos dois lados (gap da startup / KB NVIDIA) + ROI opcional. `pilar_origem` e a chave
// tecnica (AIMIPillar); a lista ja vem ordenada por prioridade (alta->baixa), como no briefing.
export interface RecommendationOut {
  tech: string;
  prioridade: string;
  complexidade: string;
  justificativa_tecnica: string;
  justificativa_negocio: string;
  proxima_acao: string;
  pilar_origem: string | null;
  roi: ROIOut | null;
  evidencia_gap: EvidenceOut[];
  evidencia_nvidia: EvidenceOut[];
}

// Detalhe de uma startup (CompanyDetailOut, F5.5/F5.6): perfil + radar AIMI (4 pilares) com
// evidencia por pilar + cartoes de recomendacao (justificativa, evidencia dos dois lados, ROI).
// `pilares`/`recomendacoes` vem vazias quando a empresa ainda nao foi pontuada/recomendada.
export interface CompanyDetail {
  id: number;
  nome: string;
  setor: string | null;
  pais: string;
  website: string | null;
  descricao: string | null;
  ano_fundacao: number | null;
  classificacao: string | null;
  aimi_total: number | null;
  inception_priority: number | null;
  confidence: number | null;
  heuristic_version: string | null;
  pilares: PillarOut[];
  nvidia_techs: string[];
  recomendacoes: RecommendationOut[];
}

// Detalhe de uma startup pelo id (`GET /companies/{id}`, F5.2/F5.5). 404 vira mensagem propria
// (empresa inexistente) para a tela distinguir de uma falha de rede.
export async function getCompany(id: number): Promise<CompanyDetail> {
  const res = await fetch(`${API_URL}/companies/${id}`);
  if (res.status === 404) {
    throw new Error("Startup nao encontrada.");
  }
  if (!res.ok) {
    throw new Error(`Falha ao carregar a startup (HTTP ${res.status}).`);
  }
  return res.json() as Promise<CompanyDetail>;
}

// Passo (no) do grafo no trace de um run (TraceStepOut, apps/api/trace.py — F5.7). `node` e a
// chave tecnica (PIPELINE_STEPS rotula em PT-BR); `status`: done (deixou artefato no estado),
// skipped (run terminou sem passar aqui — ramo terminal ou etapa opcional sem saida) ou pending
// (run pausou/falhou antes de chegar). `summary` resume o que o no produziu (so nos done).
export interface RunTraceStep {
  node: string;
  status: "done" | "skipped" | "pending";
  summary: string | null;
}

// Rollup de tokens/custo do run (TraceUsageOut, F2.9). Ausente (null) em run offline sem LLM.
export interface RunTraceUsage {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  calls: number;
  cost_usd: number;
}

// Trace de um run para o viewer (RunTraceOut, F5.7): passos dos agentes reconstruidos do estado
// persistido (checkpoint, F2.2) + custo + erros + link Langfuse (deep-trace, quando ligado).
export interface RunTrace {
  run_id: string;
  status: string;
  prompt_version: string | null;
  steps: RunTraceStep[];
  usage: RunTraceUsage | null;
  budget_limited: boolean;
  errors: string[];
  langfuse_url: string | null;
}

// Trace de um run (`GET /runs/{id}/trace`, F5.7). 404 vira mensagem propria (run sem checkpoint)
// para a tela distinguir de uma falha de rede.
export async function getRunTrace(runId: string): Promise<RunTrace> {
  const res = await fetch(`${API_URL}/runs/${encodeURIComponent(runId)}/trace`);
  if (res.status === 404) {
    throw new Error("Run nao encontrado (sem trace registrado).");
  }
  if (!res.ok) {
    throw new Error(`Falha ao carregar o trace do run (HTTP ${res.status}).`);
  }
  return res.json() as Promise<RunTrace>;
}
