"""
FastAPI application entry point for Emergency Dispatch Triage environment.
Uses openenv create_app factory pattern.
"""

from __future__ import annotations

import os

import uvicorn
from openenv.core.env_server import create_app

try:
    from tactical_triage_env.models import TacticalAction, TacticalObservation
    from server.tactical_environment import TacticalEnvironment
except ImportError:
    from models import TacticalAction, TacticalObservation
    from tactical_environment import TacticalEnvironment

app = create_app(
    TacticalEnvironment,
    TacticalAction,
    TacticalObservation,
    env_name="tactical_triage_env",
)

@app.get("/")
def read_root():
    return {"status": "ok", "environment": "tactical_triage_env"}

@app.get("/reset")
def read_reset():
    return {"status": "ok", "message": "Use POST to reset the environment"}



def main() -> None:
    uvicorn.run(
        "server.app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        workers=int(os.getenv("WORKERS", "1")),
    )


if __name__ == "__main__":
    main()
