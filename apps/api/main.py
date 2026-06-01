"""TAPI API (FastAPI) — F5.2.

Endpoints (a implementar): POST /runs, GET /runs/{id} (SSE de progresso),
GET /companies, GET /briefings/{id}. Dispara o grafo via worker (Redis/RQ).
"""

from fastapi import FastAPI

app = FastAPI(title="TAPI API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
