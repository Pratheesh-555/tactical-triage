from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field
from openenv.core.env_server.types import Action, Observation


# ── Incident ─────────────────────────────────────────────────────────────────

class Incident(BaseModel):
    incident_id: str
    incident_type: str = Field(..., description="medical | fire | crime | accident | hazmat")
    severity: int = Field(..., ge=1, le=4, description="1=low 2=med 3=high 4=critical")
    location_zone: str = Field(..., description="north | south | east | west | central")
    age_steps: int = Field(default=0)
    max_response_steps: int = Field(..., description="derived from severity at creation")
    assigned_unit: str | None = Field(default=None)
    resolved: bool = Field(default=False)
    timed_out: bool = Field(default=False)

    @classmethod
    def from_severity(
        cls,
        incident_id: str,
        incident_type: str,
        severity: int,
        location_zone: str,
    ) -> "Incident":
        max_steps = {1: 8, 2: 5, 3: 3, 4: 1}[severity]
        return cls(
            incident_id=incident_id,
            incident_type=incident_type,
            severity=severity,
            location_zone=location_zone,
            max_response_steps=max_steps,
        )


# ── Action ───────────────────────────────────────────────────────────────────

class TacticalAction(Action):
    """
    action_type:
      "assign"   → assign unit_type to incident_id
      "close"    → mark incident_id as resolved (must already be assigned)
      "escalate" → increase severity of incident_id by 1
      "wait"     → no action this step (valid, but costs opportunity)
    """
    action_type: str = Field(..., description="assign | close | escalate | wait")
    incident_id: str = Field(default="", description="Target incident ID")
    unit_type: str | None = Field(default=None, description="Required for assign action")


# ── Observation ──────────────────────────────────────────────────────────────

class TacticalObservation(Observation):
    active_incidents: list[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of serialized active (unresolved, not timed-out) incidents",
    )
    available_units: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of available units by type",
    )
    step_number: int = Field(default=0)
    episode_score: float = Field(default=0.0, description="Cumulative score this episode")
    last_action_result: str = Field(default="", description="Human-readable result of last action")
    last_action_error: str | None = Field(default=None, description="Error message if action invalid")
    task_name: str = Field(default="single_incident")
    max_steps: int = Field(default=20)
