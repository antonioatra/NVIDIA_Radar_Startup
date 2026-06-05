"""Nó **evidence_validator** (F2.7): regra de N fontes + aresta condicional de retry → scraper.

Quinto nó do grafo (ARQUITETURA §3), entre o classifier (F2.6) e o nvidia_rag (F3). Antes de
gastar RAG/recomendação/benchmark sobre o diagnóstico, ele confere que o diagnóstico se apoia
em **pelo menos N fontes independentes** (corroboração — princípio nº1 §8: nada de afirmar
sobre fonte única). Se a corroboração falta e ainda há orçamento de retry, **devolve o grafo
ao scraper (F2.4)** para ampliar a coleta; se há fontes suficientes — ou o retry esgotou —
segue em frente para o RAG.

**Profundidade × largura (complementar ao classifier):** o classifier (F2.6) já trava a
evidência **por sub-score** (`PillarScore`: > 6 exige evidência — *profundidade*). Aqui o gate
é de **largura**: quantas fontes *independentes* sustentam o conjunto do diagnóstico. As duas
travas juntas realizam o princípio nº1 (§8) sem se sobreporem.

**Fonte independente = host distinto.** Duas páginas do mesmo domínio são uma fonte (auto-relato);
o site oficial + uma notícia de outro veículo são duas (corroboração real). Por isso a contagem é
por **host normalizado** (minúsculo, sem `www.`) sobre a proveniência agregada do perfil
(`all_evidence` + `source_urls`), não por URL. `MIN_SOURCES = 2` é o piso de corroboração.

**Roteamento por `Command` (decisão de design b/d):** o nó devolve um `langgraph.types.Command`
que **atualiza o estado e roteia atomicamente** — em vez de um par `nó devolve dict` +
`add_conditional_edges`. Por quê: o retry incrementa `retry_count` e a rota (scraper vs.
nvidia_rag) dependem do *mesmo* veredito; com `Command` há uma única fonte de verdade e o
contador fica **limpo** (incrementa exatamente quando re-coleta, limitado por `can_retry` ⇒
nunca passa de `max_retries`). Uma aresta condicional separada releria `can_retry` já depois do
incremento, criando ambiguidade de fronteira (a 2ª e a última tentativa ficariam
indistinguíveis). Em troca, o `evidence_validator` **não** recebe aresta estática de saída na
montagem (graph.py): as duas pontas são alcançadas pelo `goto` do nó.

**Offline é o default (igual F2.3–F2.6):** sem `profile` (espinha offline sem extração, M2/DoD)
não há o que corroborar — o nó **segue limpo** para o nvidia_rag, sem retry (re-coletar sem rede
seria loop sem ganho) e sem alucinar. Determinista/puro: a contagem de hosts é reprodutível
(ethos F2.14), sem rede/LLM/GPU.

Hooks de tasks futuras: quando o retry esgota e a evidência segue insuficiente, hoje o nó **segue
em frente com uma nota rastreável** (não trava nem alucina) — a **F2.12** intercepta esse caso
para o briefing terminal "dados insuficientes"; a **F2.13** trata a saída `non-AI` de alta
confiança. Ambas leem o veredito/erro daqui sem mudar esta regra.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal
from urllib.parse import urlsplit

from langgraph.types import Command

from packages.schemas import GraphState, RunStatus, StartupProfile

if TYPE_CHECKING:
    from collections.abc import Iterable

#: Piso de corroboração: o diagnóstico precisa de ao menos N fontes independentes (hosts
#: distintos) antes de seguir para o RAG/recomendação. 2 = "não afirmar sobre fonte única".
MIN_SOURCES = 2

#: Alvos de roteamento (espelham `graph.PIPELINE`): retry volta ao scraper (re-coleta) e o
#: caminho normal segue ao nvidia_rag. Constantes aqui evitam o ciclo de import com graph.py;
#: `tests/test_evidence_validator.py` guarda contra divergência da espinha.
RETRY_TARGET = "scraper"
CONTINUE_TARGET = "nvidia_rag"


def _host(url: str) -> str:
    """Host normalizado (minúsculo, sem `www.`) de uma URL; vazio se não der p/ parsear.

    Espelha `scraping.source_policy._host`: o `www.` não distingue fonte, então some, para que
    `site.com` e `www.site.com` contem como **uma** fonte.
    """
    raw = url if "://" in url else "//" + url
    host = (urlsplit(raw).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def evidence_sources(profile: StartupProfile) -> set[str]:
    """Hosts **independentes** que sustentam o perfil: proveniência citada + fontes agregadas.

    Une as URLs da evidência por campo (`all_evidence`, o que de fato ancora claims/sub-scores)
    com as fontes consultadas agregadas (`source_urls`), reduzidas a host normalizado. Conjunto
    ⇒ contagem de fontes *distintas* (corroboração), determinística.
    """
    urls: Iterable[object] = (
        *(ev.url for ev in profile.all_evidence),
        *profile.source_urls,
    )
    hosts = {_host(str(u)) for u in urls}
    hosts.discard("")  # URLs impossíveis de parsear não contam como fonte
    return hosts


def is_sufficient(profile: StartupProfile, *, min_sources: int = MIN_SOURCES) -> bool:
    """Regra de N fontes: o perfil se apoia em ≥ `min_sources` hosts independentes?"""
    return len(evidence_sources(profile)) >= min_sources


def evidence_validator(
    state: GraphState, *, min_sources: int = MIN_SOURCES
) -> Command[Literal["scraper", "nvidia_rag"]]:
    """F2.7 — valida a corroboração (N fontes) e roteia: retry→scraper ou segue→nvidia_rag.

    - Sem perfil (offline/extração vazia): segue limpo (nada a corroborar; o terminal de baixa
      confiança é a F2.12 — aqui não se entra em loop sem coleta nem se alucina).
    - Fontes suficientes (≥ N hosts): segue para o RAG.
    - Insuficiente e ainda com orçamento (`can_retry`): consome um retry, marca `RUNNING` e volta
      ao scraper para ampliar a coleta (F2.4 substitui os `raw_docs` no re-scrape).
    - Insuficiente e retry esgotado: **não trava nem alucina** — segue com uma nota rastreável em
      `errors` (a F2.12 fará desse caso o briefing "dados insuficientes").
    """
    profile = state.profile
    if profile is None:
        return Command(goto=CONTINUE_TARGET)

    sources = evidence_sources(profile)
    if len(sources) >= min_sources:
        return Command(goto=CONTINUE_TARGET)

    if state.can_retry:
        return Command(
            goto=RETRY_TARGET,
            update={"retry_count": state.retry_count + 1, "status": RunStatus.RUNNING},
        )

    note = (
        f"evidência insuficiente: {len(sources)} fonte(s) independente(s) < {min_sources} "
        f"exigida(s) após {state.retry_count} retry(s) de coleta"
    )
    return Command(goto=CONTINUE_TARGET, update={"errors": [*state.errors, note]})


__all__ = [
    "MIN_SOURCES",
    "RETRY_TARGET",
    "CONTINUE_TARGET",
    "evidence_sources",
    "is_sufficient",
    "evidence_validator",
]
