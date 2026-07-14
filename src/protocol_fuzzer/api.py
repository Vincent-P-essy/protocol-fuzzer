"""Local HTTP surface for launching campaigns and reading crash buckets."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .engine import run_campaign
from .models import CampaignConfig, Protocol
from .regression import replay_all, to_regression_cases
from .reporting import result_to_dict
from .resources import web_dir


class CampaignRequest(BaseModel):
    protocol: Protocol
    iterations: int = Field(default=500, ge=1, le=50_000)
    seed: int = Field(default=1337, ge=0, le=2**63)
    max_input_bytes: int = Field(default=512, ge=1, le=65_536)
    semantic_corpus: bool = True


def create_app() -> FastAPI:
    app = FastAPI(
        title="Protocol Fuzzer",
        version="0.2.0",
        description="Coverage-guided, grammar-based protocol fuzzer with crash triage.",
    )

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/protocols")
    def protocols() -> dict[str, Any]:
        return {"protocols": [p.value for p in Protocol]}

    @app.post("/campaign")
    def campaign(request: CampaignRequest) -> dict[str, Any]:
        config = CampaignConfig(
            protocol=request.protocol,
            iterations=request.iterations,
            seed=request.seed,
            max_input_bytes=request.max_input_bytes,
            semantic_corpus=request.semantic_corpus,
        )
        result, _crashes = run_campaign(config)
        cases = to_regression_cases(result)
        return {
            "result": result_to_dict(result),
            "regressions_reproduced": all(replay_all(cases).values()),
        }

    directory = web_dir()
    if directory.exists():
        app.mount("/", StaticFiles(directory=str(directory), html=True), name="web")

    return app
