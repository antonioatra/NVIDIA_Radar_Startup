import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// Telas do dashboard (Entregavel 5). O scaffold (F5.1) entrega a casca + tema PT-BR;
// cada tela chega na sua task (F5.3..F5.8), consumindo a API (F5.2).
const TELAS = [
  {
    id: "F5.3",
    titulo: "Consulta",
    descricao:
      "Lookup de uma empresa ou descoberta por setor/regiao, com o pipeline ao vivo (SSE).",
  },
  {
    id: "F5.4",
    titulo: "Radar de startups",
    descricao:
      "Lista filtravel por setor, AIMI, classe e tecnologia, ordenada por Inception Priority.",
  },
  {
    id: "F5.12",
    titulo: "Descoberta por chat",
    descricao:
      "Pergunte em portugues sobre a coorte (classe, AIMI, tech NVIDIA) e receba as startups.",
  },
  {
    id: "F5.5",
    titulo: "Diagnostico AIMI",
    descricao: "Detalhe da startup com o radar dos 4 pilares e evidencias com link a fonte.",
  },
  {
    id: "F5.6",
    titulo: "Recomendacoes",
    descricao:
      "Cartoes no formato do brief (tech NVIDIA, justificativas, evidencia dos dois lados) + ROI.",
  },
  {
    id: "F5.8",
    titulo: "Briefing",
    descricao: "Relatorio executivo PT-BR com export em PDF para o time do Inception.",
  },
] as const;

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center bg-background text-foreground">
      <div className="w-full max-w-5xl px-6 py-16 sm:py-24">
        <header className="flex flex-col gap-4">
          <span className="inline-flex w-fit items-center rounded-full border border-border px-3 py-1 text-xs font-medium text-muted-foreground">
            NVIDIA Inception · ferramenta interna
          </span>
          <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
            TAPI — NVIDIA Startup AI Radar
          </h1>
          <p className="max-w-2xl text-lg text-muted-foreground">
            Mapeia startups brasileiras AI-native, diagnostica a maturidade tecnica (AIMI) e
            recomenda tecnologias NVIDIA com evidencia rastreavel dos dois lados — para apoiar a
            decisao de outreach do gerente de Startups &amp; VCs.
          </p>
          <div className="mt-2 flex flex-wrap gap-3">
            <Link href="/consulta" className={cn(buttonVariants({ size: "lg" }))}>
              Nova consulta
            </Link>
            <Link
              href="/radar"
              className={cn(buttonVariants({ variant: "outline", size: "lg" }))}
            >
              Ver radar de startups
            </Link>
            <Link
              href="/descoberta"
              className={cn(buttonVariants({ variant: "outline", size: "lg" }))}
            >
              Descobrir por chat
            </Link>
          </div>
          <p className="text-sm text-muted-foreground">
            A consulta (F5.3), o radar (F5.4) e a descoberta por chat (F5.12) ja rodam; cada startup
            abre o detalhe AIMI com os 4 pilares e evidencias (F5.5).
          </p>
        </header>

        <section className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {TELAS.map((tela) => (
            <article
              key={tela.id}
              className="flex flex-col gap-2 rounded-lg border border-border bg-card p-5 text-card-foreground"
            >
              <div className="flex items-center justify-between">
                <h2 className="text-base font-semibold">{tela.titulo}</h2>
                <span className="text-xs font-mono text-muted-foreground">{tela.id}</span>
              </div>
              <p className="text-sm text-muted-foreground">{tela.descricao}</p>
            </article>
          ))}
        </section>

        <footer className="mt-12 border-t border-border pt-6 text-sm text-muted-foreground">
          Scaffold do Entregavel 5 (F5.1): Next.js (App Router) · TypeScript · Tailwind · shadcn/ui ·
          UI em PT-BR.
        </footer>
      </div>
    </main>
  );
}
