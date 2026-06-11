# Imagem Python compartilhada pela API (F5.2) e pelo worker RQ (F2.10) — F0.2.
#
# Contexto de build = **raiz do repo** (os apps importam `packages.*`; o empacotamento é
# flat, sem `[project]` no pyproject — ver pyproject.toml). Por isso o compose aponta
# `context: .` / `dockerfile: apps/Dockerfile`. As duas imagens são idênticas; só o
# `command` difere (a API roda uvicorn; o worker, `rq worker tapi`) — definido no compose.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependências primeiro (camada cacheável): requirements muda menos que o código.
# psycopg[binary] já traz o driver, mas algumas libs do requirements compilam extensões
# C/C++ no slim (ex.: `annoy`, via nemoguardrails) — daí o build-essential. Mantido na
# imagem (ambiente de build, não produção enxuta); o apt cache é limpo.
COPY requirements.txt ./
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install -r requirements.txt

# Código: os pacotes flat + os dois apps Python. `apps` vira namespace package (PEP 420);
# com WORKDIR /app na raiz do path, `import packages...`/`apps.api...` resolvem.
COPY packages ./packages
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker

# Default: API (o serviço `worker` sobrescreve o command no compose).
# Obs.: scraping JS-pesado (Playwright, F1.3) precisa de uma camada extra de browser
# (`playwright install --with-deps chromium`); fora desta imagem base de propósito —
# os caminhos Tavily/Firecrawl/trafilatura (HTTP) rodam sem ela.
EXPOSE 8080
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
