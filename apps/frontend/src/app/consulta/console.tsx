"use client";

// Console de consulta (F5.3): dois modos (lookup de uma empresa / descoberta por setor) e
// acompanhamento ao vivo do pipeline via SSE. Enfileira em `POST /runs`, abre um EventSource
// no `GET /runs/{id}` e desenha a espinha do grafo conforme os nos terminam (F2.10).

import { useEffect, useRef, useState } from "react";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  briefingUrl,
  createRun,
  type ProgressEvent,
  type RunMode,
  runStreamUrl,
} from "@/lib/api";
import { END_NODE, hasBriefing, PIPELINE_STEPS, statusLabel } from "@/lib/pipeline";

type Phase = "idle" | "starting" | "streaming" | "done" | "error";

const MODES: ReadonlyArray<{ mode: RunMode; titulo: string; placeholder: string }> = [
  {
    mode: "single_company",
    titulo: "Empresa",
    placeholder: "Nome ou dominio da empresa (ex.: minha-startup.ai)",
  },
  {
    mode: "discovery",
    titulo: "Descoberta",
    placeholder: "Setor / regiao (ex.: healthtech em Sao Paulo)",
  },
];

// Estados terminais do run que pausam (nao concluiram) — guiam a nota de desfecho.
const PAUSED = "awaiting_review";

export function ConsultaConsole() {
  const [mode, setMode] = useState<RunMode>("single_company");
  const [query, setQuery] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [runId, setRunId] = useState<string | null>(null);
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [terminal, setTerminal] = useState<ProgressEvent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  // Fecha o stream ao desmontar — o EventSource reconecta sozinho se nao for fechado.
  useEffect(() => () => esRef.current?.close(), []);

  const busy = phase === "starting" || phase === "streaming";

  async function start(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q || busy) return;

    esRef.current?.close();
    setEvents([]);
    setTerminal(null);
    setError(null);
    setRunId(null);
    setPhase("starting");

    try {
      const accepted = await createRun(q, mode);
      setRunId(accepted.run_id);
      setPhase("streaming");

      const es = new EventSource(runStreamUrl(accepted.run_id));
      esRef.current = es;
      es.onmessage = (msg) => {
        const event = JSON.parse(msg.data) as ProgressEvent;
        if (event.node === END_NODE) {
          setTerminal(event);
          setPhase("done");
          es.close();
          return;
        }
        setEvents((prev) => [...prev, event]);
      };
      es.onerror = () => {
        // O browser reconecta enquanto readyState != CLOSED; so e erro se ele desistiu
        // antes do evento terminal (queda de rede / API fora).
        if (es.readyState === EventSource.CLOSED) {
          es.close();
          setPhase("error");
          setError("Conexao de progresso encerrada antes do fim da consulta.");
        }
      };
    } catch (err) {
      setPhase("error");
      setError(err instanceof Error ? err.message : "Erro ao iniciar a consulta.");
    }
  }

  const seen = new Set(events.map((ev) => ev.node));
  const pct = terminal?.pct ?? events.at(-1)?.pct ?? 0;
  // Primeiro no ainda nao visto = o que esta rodando agora (so durante o streaming).
  const activeIndex = PIPELINE_STEPS.findIndex((s) => !seen.has(s.node));
  const activeFinal = terminal?.status ?? null;

  return (
    <div className="flex flex-col gap-8">
      <form onSubmit={start} className="flex flex-col gap-4">
        <div className="inline-flex w-fit gap-1 rounded-lg border border-border p-1">
          {MODES.map((m) => (
            <Button
              key={m.mode}
              type="button"
              size="sm"
              variant={mode === m.mode ? "default" : "ghost"}
              onClick={() => setMode(m.mode)}
              disabled={busy}
            >
              {m.titulo}
            </Button>
          ))}
        </div>

        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={MODES.find((m) => m.mode === mode)?.placeholder}
            disabled={busy}
            className="h-9 flex-1 rounded-lg border border-border bg-background px-3 text-sm text-foreground outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:opacity-50"
          />
          <Button type="submit" size="lg" disabled={busy || query.trim() === ""}>
            {busy ? "Consultando..." : "Consultar"}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          {mode === "single_company"
            ? "Diagnostica uma empresa e pausa para revisao (HITL sync, F2.8)."
            : "Descobre empresas por setor/regiao em lote, sem bloquear a fila (HITL auto)."}
        </p>
      </form>

      {phase !== "idle" && (
        <section className="flex flex-col gap-4 rounded-lg border border-border bg-card p-5 text-card-foreground">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-base font-semibold">Pipeline</h2>
            {runId && (
              <span className="font-mono text-xs text-muted-foreground">run {runId}</span>
            )}
          </div>

          <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all duration-300"
              style={{ width: `${pct}%` }}
            />
          </div>

          <ol className="flex flex-col gap-2">
            {PIPELINE_STEPS.map((step, i) => {
              const done = seen.has(step.node);
              const active = !done && i === activeIndex && phase === "streaming";
              return (
                <li key={step.node} className="flex items-center gap-3 text-sm">
                  <StepMarker done={done} active={active} />
                  <span
                    className={cn(
                      done
                        ? "text-foreground"
                        : active
                          ? "font-medium text-foreground"
                          : "text-muted-foreground",
                    )}
                  >
                    {step.label}
                  </span>
                </li>
              );
            })}
          </ol>

          {activeFinal && (
            <div className="rounded-md border border-border bg-background px-3 py-2 text-sm">
              <span className="font-medium">Desfecho:</span> {statusLabel(activeFinal)}
              {activeFinal === PAUSED && (
                <p className="mt-1 text-xs text-muted-foreground">
                  O run pausou para revisao humana — a tela de aprovacao (F5.10) habilita a
                  retomada.
                </p>
              )}
            </div>
          )}

          {/* Acoes ao concluir: trace dos agentes (F5.7) + export do briefing em PDF (F5.8). */}
          {phase === "done" && runId && (
            <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
              <Link
                href={`/runs/${encodeURIComponent(runId)}/trace`}
                className="text-sm text-primary hover:underline"
              >
                Ver passos do run (trace) →
              </Link>
              {/* So oferece o PDF quando o run chegou ao briefing (F5.8): completou ou caiu
                  num ramo terminal que salta ao briefing — nao em pausa HITL nem falha. */}
              {hasBriefing(activeFinal) && (
                <a
                  href={briefingUrl(runId, "pdf")}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline"
                >
                  Exportar briefing (PDF) ↓
                </a>
              )}
            </div>
          )}

          {phase === "error" && error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
        </section>
      )}
    </div>
  );
}

// Marcador de etapa: check (concluida), spinner (em execucao) ou anel vazio (pendente).
function StepMarker({ done, active }: { done: boolean; active: boolean }) {
  if (done) {
    return (
      <span className="flex size-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
        ✓
      </span>
    );
  }
  if (active) {
    return (
      <span className="size-4 animate-spin rounded-full border-2 border-muted border-t-foreground" />
    );
  }
  return <span className="size-4 rounded-full border-2 border-muted" />;
}
