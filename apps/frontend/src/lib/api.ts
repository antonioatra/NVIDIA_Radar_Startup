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
