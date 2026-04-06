from __future__ import annotations

from typing import Any, Dict

from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State
from openenv.core.env_client import EnvClient

try:
    from tactical_triage_env.models import TacticalAction, TacticalObservation
except ImportError:
    from models import TacticalAction, TacticalObservation


class TacticalTriageEnv(EnvClient[TacticalAction, TacticalObservation, State]):
    """
    Typed client for the Emergency Dispatch Triage environment.

    Usage (async):
        async with TacticalTriageEnv(base_url="https://<space>.hf.space") as env:
            result = await env.reset()
            result = await env.step(TacticalAction(
                action_type="assign",
                incident_id="INC-001",
                unit_type="ambulance"
            ))

    Usage (sync):
        with TacticalTriageEnv(base_url="http://localhost:8000").sync() as env:
            result = env.reset()
    """

    def _step_payload(self, action: TacticalAction) -> Dict[str, Any]:
        """Serialize TacticalAction to dict for the server."""
        if hasattr(action, "model_dump"):
            return action.model_dump()
        return vars(action)

    def _parse_result(self, payload: Dict[str, Any]) -> StepResult[TacticalObservation]:
        """Deserialize server response into typed StepResult."""
        obs_data = payload.get("observation", payload)
        obs = TacticalObservation(**obs_data) if obs_data else TacticalObservation()
        return StepResult(
            observation=obs,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict[str, Any]) -> State:
        """Deserialize state payload into State object."""
        return State(**payload) if payload else State()
