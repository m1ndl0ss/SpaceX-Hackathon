from __future__ import annotations

import argparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from impact_models.infer import ArtifactError, infer
from impact_models.warehouse import warehouse_flags
from impact_models.schema import ImpactReport, Treatment

app = FastAPI(title="Impact models", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1", "http://localhost", "http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:8080", "http://localhost:8080"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "warehouse": warehouse_flags()}


@app.post("/infer", response_model=ImpactReport)
def infer_route(treatment: Treatment) -> ImpactReport:
    try:
        return infer(treatment)
    except ArtifactError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve POST /infer for Benelux impact heads.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    import uvicorn

    uvicorn.run("impact_models.serve:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
