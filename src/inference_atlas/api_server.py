"""Optional FastAPI server for InferenceAtlas endpoints.

This server is intentionally lightweight. It currently exposes:
- POST /api/v1/ai/copilot
"""

from __future__ import annotations

import os

from inference_atlas.api_models import CopilotTurnRequest, CopilotTurnResponse
from inference_atlas.api_service import run_copilot_turn


def create_app():
    """Create FastAPI app lazily so base package has no hard FastAPI dependency."""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "FastAPI is not installed. Install with: "
            "pip install 'fastapi>=0.110,<1.0' 'uvicorn>=0.30,<1.0'"
        ) from exc

    app = FastAPI(title="InferenceAtlas API", version="0.1.1")

    origins_raw = os.getenv("INFERENCE_ATLAS_CORS_ORIGINS", "*")
    allow_origins = [origin.strip() for origin in origins_raw.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/ai/copilot", response_model=CopilotTurnResponse)
    def copilot_turn(payload: CopilotTurnRequest) -> CopilotTurnResponse:
        try:
            return run_copilot_turn(payload)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app
