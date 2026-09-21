from __future__ import annotations

import argparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from impact_narrate.client import narrate
from impact_narrate.schema import Briefing, ImpactReport

app = FastAPI(title="Impact narrate", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1", "http://localhost"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/narrate", response_model=Briefing)
def narrate_route(report: ImpactReport) -> Briefing:
    return narrate(report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve POST /narrate for locked impact reports.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    import uvicorn

    uvicorn.run("impact_narrate.serve:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
