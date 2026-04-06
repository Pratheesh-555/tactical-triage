# Emergency Dispatch Triage — OpenEnv Environment
## Full Enterprise PRD · Hackathon Submission · Deadline: April 8, 2026

---

## QUICK REFERENCE FOR CLAUDE

This PRD is structured into **6 batches**. Execute one batch at a time, verify it works, then proceed.
- Batch 1 → Project scaffold + models
- Batch 2 → Server / environment logic + reward engine
- Batch 3 → Task definitions + graders (3 tasks)
- Batch 4 → FastAPI app + Dockerfile + openenv.yaml
- Batch 5 → Client + __init__.py + pyproject.toml
- Batch 6 → inference.py + README.md + validate

**NEVER skip ahead. Every batch depends on the previous.**

---

## 1. PRODUCT OVERVIEW

### 1.1 What We Are Building

An OpenEnv-compliant RL environment that simulates a 911 emergency dispatch coordination center. An AI agent acts as the dispatch coordinator — receiving incoming incidents, assessing severity, assigning the correct responder units (police, fire, ambulance, hazmat), managing limited unit availability, and handling simultaneous cascading crises.

This is a real operational problem. Every city dispatch center in the world does exactly this task, and the stakes are life-or-death. No comparable environment exists in the OpenEnv catalog today.

### 1.2 Why This Wins on Judging Criteria

| Criterion | Weight | Why We Score High |
|---|---|---|
| Real-world utility | 30% | 911 dispatch is a real operational domain with documented AI research need |
| Task & grader quality | 25% | 3 clear tasks, fully deterministic programmatic graders, hard task genuinely challenges frontier models |
| Environment design | 20% | Clean state management, rich partial rewards at every step, sensible episode boundaries |
| Code quality | 15% | Full OpenEnv spec compliance, typed Pydantic models, dual-import pattern, Dockerfile |
| Creativity & novelty | 10% | Novel in OpenEnv catalog, multi-constraint reward design, geographic zones |

### 1.3 Environment Name

```
dispatch_env
```

HF Space: `<your-username>/dispatch-env`

---

## 2. DOMAIN MODEL

### 2.1 Real-World Scenario

A dispatch center receives calls. Each call becomes an **Incident**. The dispatcher must:
1. Classify the incident type (medical, fire, crime, accident, hazmat)
2. Assess severity (1=low, 2=medium, 3=high, 4=critical)
3. Assign an appropriate responder unit (ambulance, fire_truck, police_car, hazmat_team)
4. Monitor active incidents and close resolved ones
5. Handle new incidents arriving mid-episode
6. Manage unit availability (units are busy until returned)

### 2.2 Incident Types and Valid Responder Assignments

```
INCIDENT_RESPONDER_MAP = {
    "medical":   ["ambulance"],
    "fire":      ["fire_truck", "ambulance"],
    "crime":     ["police_car"],
    "accident":  ["ambulance", "police_car", "fire_truck"],
    "hazmat":    ["hazmat_team", "fire_truck"],
}
```

A correct assignment means the unit type is in the valid list for the incident type. An incorrect assignment is penalized.

### 2.3 Severity Scale

| Level | Label | Max Response Time (steps) | Points at Risk |
|---|---|---|---|
| 1 | Low | 8 steps | 0.1 |
| 2 | Medium | 5 steps | 0.25 |
| 3 | High | 3 steps | 0.5 |
| 4 | Critical | 1 step | 1.0 |

If an incident is not assigned within its max response time, it times out and generates a penalty of `-0.3 * severity`.

### 2.4 Unit Pool (per episode)

```
UNIT_POOL = {
    "ambulance":   3,
    "fire_truck":  2,
    "police_car":  3,
    "hazmat_team": 1,
}
```

Units become available again after `unit_return_steps` (task-specific, see Task Definitions).

---

## 3. OPENENV SPEC COMPLIANCE

### 3.1 Required Interface

All three methods must be implemented exactly:

```python
reset(seed: int | None = None) -> DispatchObservation
step(action: DispatchAction) -> StepResult[DispatchObservation]
state() -> State
```

### 3.2 Typed Models (models.py)

#### DispatchAction
```python
class DispatchAction(Action):
    action_type: str          # "assign" | "close" | "escalate" | "wait"
    incident_id: str          # target incident ID (required for assign/close/escalate)
    unit_type: str | None     # required only when action_type == "assign"
```

#### Incident (internal state object, NOT an Action)
```python
class Incident(BaseModel):
    incident_id: str
    incident_type: str        # medical | fire | crime | accident | hazmat
    severity: int             # 1-4
    location_zone: str        # "north" | "south" | "east" | "west" | "central"
    age_steps: int            # how many steps this incident has been active
    max_response_steps: int   # derived from severity
    assigned_unit: str | None # None if unassigned
    resolved: bool
    timed_out: bool
```

#### DispatchObservation
```python
class DispatchObservation(Observation):
    active_incidents: list[dict]   # serialized Incident objects (unresolved, not timed out)
    available_units: dict          # {"ambulance": 2, "fire_truck": 1, ...}
    step_number: int
    episode_score: float           # cumulative score so far (partial reward signal)
    last_action_result: str        # human-readable result of last action
    last_action_error: str | None  # error message if action was invalid
    task_name: str                 # which task is running
    max_steps: int                 # episode length limit
```

### 3.3 openenv.yaml

```yaml
spec_version: 1
name: dispatch_env
type: environment
runtime: docker
app: server/app.py
port: 8000
description: >
  Emergency 911 dispatch coordination environment. An RL agent
  acts as a dispatcher — triaging incidents, assigning responder
  units, and managing cascading crises in real time.
tasks:
  - name: single_incident
    description: Easy — handle one incident at a time, slow arrival rate
  - name: multi_incident
    description: Medium — 3-5 simultaneous incidents, mixed severity
  - name: mass_casualty
    description: Hard — mass casualty event, unit scarcity, cascading escalations
```

---

## 4. FILE STRUCTURE (EXACT)

```
dispatch_env/
├── __init__.py                      ← exports DispatchEnv, DispatchAction, DispatchObservation
├── client.py                        ← EnvClient subclass
├── models.py                        ← Pydantic models (Action, Observation, Incident)
├── openenv.yaml                     ← spec_version:1, tasks list
├── pyproject.toml                   ← package metadata + openenv-core dep
├── uv.lock                          ← (generated by uv sync)
└── server/
    ├── __init__.py                  ← empty
    ├── app.py                       ← create_app(DispatchEnvironment, DispatchAction, DispatchObservation)
    ├── dispatch_environment.py      ← main environment class
    ├── scenarios.py                 ← deterministic scenario generators per task
    ├── graders.py                   ← grader functions for all 3 tasks
    ├── reward_engine.py             ← reward computation logic
    ├── requirements.txt             ← server dependencies
    └── Dockerfile                   ← FROM openenv-base, installs requirements

inference.py                         ← root level, mandatory
README.md                            ← root level
```

---

## 5. BATCH 1 — SCAFFOLD + MODELS

### 5.1 Instructions for Claude

Create all files listed. Do not skip any. Run `pip install openenv-core pydantic` in the environment first to confirm imports will work.

### 5.2 dispatch_env/__init__.py

```python
try:
    from dispatch_env.client import DispatchEnv
    from dispatch_env.models import DispatchAction, DispatchObservation, Incident
except ImportError:
    from client import DispatchEnv
    from models import DispatchAction, DispatchObservation, Incident

__all__ = ["DispatchEnv", "DispatchAction", "DispatchObservation", "Incident"]
```

### 5.3 dispatch_env/models.py

```python
from __future__ import annotations
from typing import Any
from pydantic import Field
from openenv.core.env_server.types import Action, Observation

# ── Incident model ────────────────────────────────────────────────────────────

class Incident(BaseModel):  # plain BaseModel, not Action/Observation
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
    def from_severity(cls, incident_id: str, incident_type: str, severity: int,
                      location_zone: str) -> "Incident":
        max_steps = {1: 8, 2: 5, 3: 3, 4: 1}[severity]
        return cls(
            incident_id=incident_id,
            incident_type=incident_type,
            severity=severity,
            location_zone=location_zone,
            max_response_steps=max_steps,
        )

# ── Action ────────────────────────────────────────────────────────────────────

class DispatchAction(Action):
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

# ── Observation ───────────────────────────────────────────────────────────────

class DispatchObservation(Observation):
    active_incidents: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of serialized active (unresolved, not timed-out) incidents"
    )
    available_units: dict[str, int] = Field(
        default_factory=dict,
        description="Count of available units by type"
    )
    step_number: int = Field(default=0)
    episode_score: float = Field(default=0.0, description="Cumulative score this episode")
    last_action_result: str = Field(default="", description="Human-readable result of last action")
    last_action_error: str | None = Field(default=None, description="Error message if action invalid")
    task_name: str = Field(default="single_incident")
    max_steps: int = Field(default=20)
```

> **NOTE for Claude:** Import `BaseModel` from pydantic at the top of models.py. The `Incident` class uses plain `BaseModel`. Only `DispatchAction` and `DispatchObservation` extend the openenv types.

### 5.4 dispatch_env/client.py

```python
from __future__ import annotations
from openenv.core.env_client import EnvClient

try:
    from dispatch_env.models import DispatchAction, DispatchObservation
except ImportError:
    from models import DispatchAction, DispatchObservation


class DispatchEnv(EnvClient[DispatchAction, DispatchObservation]):
    """
    Client for the Emergency Dispatch Triage environment.

    Usage (async):
        async with DispatchEnv(base_url="https://<space>.hf.space") as env:
            result = await env.reset()
            result = await env.step(DispatchAction(
                action_type="assign",
                incident_id="INC-001",
                unit_type="ambulance"
            ))

    Usage (sync):
        with DispatchEnv(base_url="http://localhost:8000").sync() as env:
            result = env.reset()
    """
    action_type = DispatchAction
    observation_type = DispatchObservation
```

### 5.5 dispatch_env/pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "dispatch_env"
version = "1.0.0"
description = "Emergency 911 Dispatch Triage — OpenEnv RL Environment"
requires-python = ">=3.10"
dependencies = [
    "openenv-core>=0.1.0",
    "pydantic>=2.0",
]

[tool.hatch.build.targets.wheel]
packages = ["dispatch_env"]
```

---

## 6. BATCH 2 — SERVER CORE + REWARD ENGINE

### 6.1 server/reward_engine.py

This is the most critical file. All reward logic lives here, isolated for testability.

```python
"""
Reward Engine for Emergency Dispatch Triage.

Design principles:
- Every step produces a non-zero signal (no sparse rewards)
- Correct assignment = positive reward proportional to severity
- Wrong unit type = negative penalty
- Timeout = negative penalty proportional to severity
- Successful close = bonus based on how quickly resolved
- Escalation handled = small positive
- Wait = small negative nudge (-0.05) to discourage passive behavior
"""

from __future__ import annotations

VALID_ASSIGNMENTS: dict[str, list[str]] = {
    "medical":   ["ambulance"],
    "fire":      ["fire_truck", "ambulance"],
    "crime":     ["police_car"],
    "accident":  ["ambulance", "police_car", "fire_truck"],
    "hazmat":    ["hazmat_team", "fire_truck"],
}

SEVERITY_ASSIGN_REWARD: dict[int, float] = {1: 0.1, 2: 0.2, 3: 0.4, 4: 0.7}
SEVERITY_TIMEOUT_PENALTY: dict[int, float] = {1: -0.1, 2: -0.2, 3: -0.4, 4: -0.8}
WRONG_UNIT_PENALTY = -0.3
CLOSE_BASE_BONUS = 0.15
ESCALATE_HANDLE_REWARD = 0.05
WAIT_NUDGE = -0.05
INVALID_ACTION_PENALTY = -0.1


def reward_assign(incident_type: str, unit_type: str, severity: int) -> tuple[float, str]:
    """Returns (reward, reason_string)."""
    if unit_type not in VALID_ASSIGNMENTS.get(incident_type, []):
        return (
            WRONG_UNIT_PENALTY,
            f"WRONG_UNIT: {unit_type} cannot handle {incident_type}"
        )
    reward = SEVERITY_ASSIGN_REWARD[severity]
    return (reward, f"CORRECT_ASSIGN: +{reward:.2f} for {unit_type} → {incident_type} sev={severity}")


def reward_close(severity: int, age_steps: int, max_response_steps: int) -> tuple[float, str]:
    """Bonus for closing. Faster = more reward."""
    speed_factor = max(0.0, 1.0 - (age_steps / (max_response_steps * 2)))
    bonus = CLOSE_BASE_BONUS + (0.1 * speed_factor * severity)
    return (round(bonus, 3), f"CLOSE_BONUS: +{bonus:.3f} (speed={speed_factor:.2f})")


def reward_timeout(severity: int) -> tuple[float, str]:
    penalty = SEVERITY_TIMEOUT_PENALTY[severity]
    return (penalty, f"TIMEOUT_PENALTY: {penalty:.2f} sev={severity}")


def reward_escalate() -> tuple[float, str]:
    return (ESCALATE_HANDLE_REWARD, f"ESCALATE_HANDLED: +{ESCALATE_HANDLE_REWARD}")


def reward_wait() -> tuple[float, str]:
    return (WAIT_NUDGE, "WAIT: opportunity cost nudge")


def reward_invalid() -> tuple[float, str]:
    return (INVALID_ACTION_PENALTY, "INVALID_ACTION: bad action format or missing fields")


def clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))
```

### 6.2 server/scenarios.py

Deterministic scenario generators. MUST use a seeded random generator so results are reproducible.

```python
"""
Scenario generators for each task.
All scenarios use seeded RNG for full reproducibility.
"""

from __future__ import annotations
import random
from typing import NamedTuple

try:
    from dispatch_env.models import Incident
except ImportError:
    from models import Incident

INCIDENT_TYPES = ["medical", "fire", "crime", "accident", "hazmat"]
ZONES = ["north", "south", "east", "west", "central"]

UNIT_POOL_DEFAULT: dict[str, int] = {
    "ambulance":   3,
    "fire_truck":  2,
    "police_car":  3,
    "hazmat_team": 1,
}


class ScenarioConfig(NamedTuple):
    task_name: str
    max_steps: int
    unit_return_steps: int        # how many steps until a dispatched unit returns
    initial_incidents: list[Incident]
    new_incident_schedule: dict[int, list[Incident]]  # step_number → list of new incidents
    unit_pool: dict[str, int]


def _make_incident(iid: str, itype: str, sev: int, zone: str) -> Incident:
    return Incident.from_severity(
        incident_id=iid,
        incident_type=itype,
        severity=sev,
        location_zone=zone,
    )


# ── Task 1: single_incident ───────────────────────────────────────────────────
def scenario_single_incident(seed: int = 42) -> ScenarioConfig:
    """
    Easy. One incident at a time. New incident only arrives after current resolved.
    No hazmat. Severity max 2. Generous response windows.
    """
    rng = random.Random(seed)
    easy_types = ["medical", "fire", "crime", "accident"]

    def rand_incident(iid: str) -> Incident:
        return _make_incident(
            iid=iid,
            itype=rng.choice(easy_types),
            sev=rng.randint(1, 2),
            zone=rng.choice(ZONES),
        )

    initial = [rand_incident("INC-001")]
    schedule = {
        4:  [rand_incident("INC-002")],
        8:  [rand_incident("INC-003")],
        12: [rand_incident("INC-004")],
    }
    return ScenarioConfig(
        task_name="single_incident",
        max_steps=20,
        unit_return_steps=4,
        initial_incidents=initial,
        new_incident_schedule=schedule,
        unit_pool=UNIT_POOL_DEFAULT.copy(),
    )


# ── Task 2: multi_incident ────────────────────────────────────────────────────
def scenario_multi_incident(seed: int = 42) -> ScenarioConfig:
    """
    Medium. 3-5 simultaneous incidents. Mixed severity 1-3.
    Units return slower. Requires prioritization.
    """
    rng = random.Random(seed)
    all_types = ["medical", "fire", "crime", "accident", "hazmat"]

    def rand_incident(iid: str, sev_max: int = 3) -> Incident:
        return _make_incident(
            iid=iid,
            itype=rng.choice(all_types),
            sev=rng.randint(1, sev_max),
            zone=rng.choice(ZONES),
        )

    initial = [
        rand_incident("INC-001"),
        rand_incident("INC-002"),
        rand_incident("INC-003"),
    ]
    schedule = {
        2:  [rand_incident("INC-004"), rand_incident("INC-005")],
        5:  [rand_incident("INC-006")],
        8:  [rand_incident("INC-007"), rand_incident("INC-008")],
        12: [rand_incident("INC-009")],
    }
    return ScenarioConfig(
        task_name="multi_incident",
        max_steps=25,
        unit_return_steps=6,
        initial_incidents=initial,
        new_incident_schedule=schedule,
        unit_pool=UNIT_POOL_DEFAULT.copy(),
    )


# ── Task 3: mass_casualty ─────────────────────────────────────────────────────
def scenario_mass_casualty(seed: int = 42) -> ScenarioConfig:
    """
    Hard. Mass casualty event. Many critical/high incidents.
    Severe unit scarcity. Cascading escalations if unhandled.
    Agent must triage ruthlessly — cannot save everyone.
    """
    rng = random.Random(seed)

    def rand_incident(iid: str, sev_min: int = 2) -> Incident:
        return _make_incident(
            iid=iid,
            itype=rng.choice(["medical", "fire", "accident", "hazmat"]),
            sev=rng.randint(sev_min, 4),
            zone=rng.choice(ZONES),
        )

    # Reduced unit pool — scarcity is the challenge
    scarce_pool = {
        "ambulance":   2,
        "fire_truck":  1,
        "police_car":  2,
        "hazmat_team": 1,
    }

    initial = [
        rand_incident("INC-001", sev_min=3),
        rand_incident("INC-002", sev_min=3),
        rand_incident("INC-003", sev_min=4),  # immediate critical
        rand_incident("INC-004", sev_min=2),
    ]
    schedule = {
        1:  [rand_incident("INC-005", 3), rand_incident("INC-006", 4)],
        2:  [rand_incident("INC-007", 3)],
        4:  [rand_incident("INC-008", 2), rand_incident("INC-009", 4)],
        6:  [rand_incident("INC-010", 3)],
        9:  [rand_incident("INC-011", 4), rand_incident("INC-012", 3)],
    }
    return ScenarioConfig(
        task_name="mass_casualty",
        max_steps=30,
        unit_return_steps=8,
        initial_incidents=initial,
        new_incident_schedule=schedule,
        unit_pool=scarce_pool,
    )


SCENARIO_REGISTRY: dict[str, callable] = {
    "single_incident": scenario_single_incident,
    "multi_incident":  scenario_multi_incident,
    "mass_casualty":   scenario_mass_casualty,
}
```

### 6.3 server/graders.py

Deterministic graders. Each returns a float in [0.0, 1.0].

```python
"""
Task graders for Emergency Dispatch Triage.
All graders are deterministic and reproducible.

Grader contract:
    grade(episode_history: dict) -> float in [0.0, 1.0]

episode_history keys:
    total_reward: float
    max_possible_reward: float
    incidents_total: int
    incidents_resolved: int
    incidents_timed_out: int
    wrong_assignments: int
    correct_assignments: int
    critical_incidents: int
    critical_resolved: int
    steps_taken: int
    max_steps: int
"""

from __future__ import annotations


def _base_score(history: dict) -> float:
    """Normalized cumulative reward."""
    total = history.get("total_reward", 0.0)
    max_r = history.get("max_possible_reward", 1.0)
    if max_r <= 0:
        return 0.0
    return max(0.0, min(1.0, total / max_r))


def grade_single_incident(history: dict) -> float:
    """
    Easy task grader.
    - 70% weight on normalized reward
    - 30% weight on correct assignment rate
    Score range: 0.0 - 1.0
    """
    reward_score = _base_score(history)

    total_assignments = history.get("correct_assignments", 0) + history.get("wrong_assignments", 0)
    if total_assignments == 0:
        assignment_score = 0.0
    else:
        assignment_score = history.get("correct_assignments", 0) / total_assignments

    return round(0.70 * reward_score + 0.30 * assignment_score, 4)


def grade_multi_incident(history: dict) -> float:
    """
    Medium task grader.
    - 50% normalized reward
    - 25% resolution rate (resolved / total)
    - 25% correct assignment rate
    Penalty applied if >40% incidents timed out.
    """
    reward_score = _base_score(history)

    total_incidents = max(1, history.get("incidents_total", 1))
    resolution_rate = history.get("incidents_resolved", 0) / total_incidents

    total_assignments = history.get("correct_assignments", 0) + history.get("wrong_assignments", 0)
    assignment_score = (
        history.get("correct_assignments", 0) / max(1, total_assignments)
    )

    raw = (0.50 * reward_score + 0.25 * resolution_rate + 0.25 * assignment_score)

    # Timeout penalty
    timeout_rate = history.get("incidents_timed_out", 0) / total_incidents
    if timeout_rate > 0.4:
        raw *= (1.0 - (timeout_rate - 0.4))

    return round(max(0.0, min(1.0, raw)), 4)


def grade_mass_casualty(history: dict) -> float:
    """
    Hard task grader.
    - 40% normalized reward
    - 30% critical incident resolution rate (critical_resolved / critical_total)
    - 20% overall resolution rate
    - 10% efficiency (steps used vs min steps needed)
    Frontier models typically score 0.35-0.55 on this task.
    """
    reward_score = _base_score(history)

    critical_total = max(1, history.get("critical_incidents", 1))
    critical_score = history.get("critical_resolved", 0) / critical_total

    total_incidents = max(1, history.get("incidents_total", 1))
    resolution_score = history.get("incidents_resolved", 0) / total_incidents

    steps_taken = history.get("steps_taken", 1)
    max_steps = max(1, history.get("max_steps", 30))
    efficiency = 1.0 - (steps_taken / max_steps)  # using fewer steps = more efficient

    raw = (
        0.40 * reward_score
        + 0.30 * critical_score
        + 0.20 * resolution_score
        + 0.10 * efficiency
    )

    return round(max(0.0, min(1.0, raw)), 4)


GRADER_REGISTRY: dict[str, callable] = {
    "single_incident": grade_single_incident,
    "multi_incident":  grade_multi_incident,
    "mass_casualty":   grade_mass_casualty,
}
```

---

## 7. BATCH 3 — MAIN ENVIRONMENT CLASS

### 7.1 server/dispatch_environment.py

This is the central class. It must implement `reset()`, `step()`, and `state()` exactly per OpenEnv spec.

```python
"""
Emergency Dispatch Triage — Main Environment Class.

Implements the OpenEnv Environment interface:
    reset(seed) → DispatchObservation
    step(action) → StepResult
    state()      → State
"""

from __future__ import annotations
import copy
from uuid import uuid4
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State, StepResult

try:
    from dispatch_env.models import DispatchAction, DispatchObservation, Incident
    from server.reward_engine import (
        reward_assign, reward_close, reward_timeout,
        reward_escalate, reward_wait, reward_invalid, clamp
    )
    from server.scenarios import SCENARIO_REGISTRY, ScenarioConfig
    from server.graders import GRADER_REGISTRY
except ImportError:
    from models import DispatchAction, DispatchObservation, Incident
    from reward_engine import (
        reward_assign, reward_close, reward_timeout,
        reward_escalate, reward_wait, reward_invalid, clamp
    )
    from scenarios import SCENARIO_REGISTRY, ScenarioConfig
    from graders import GRADER_REGISTRY

import os

DEFAULT_TASK = os.getenv("DISPATCH_TASK", "single_incident")


class DispatchEnvironment(Environment):

    def __init__(self):
        self._task_name: str = DEFAULT_TASK
        self._state: State = State(episode_id=str(uuid4()), step_count=0)
        self._incidents: dict[str, Incident] = {}
        self._available_units: dict[str, int] = {}
        self._unit_pool: dict[str, int] = {}
        self._busy_units: list[tuple[str, int]] = []  # (unit_type, return_at_step)
        self._scenario: ScenarioConfig | None = None
        self._episode_score: float = 0.0
        self._history: dict = {}
        self._seed: int = 42

    # ── reset ─────────────────────────────────────────────────────────────────

    def reset(self, seed: int | None = None, task: str | None = None) -> DispatchObservation:
        self._seed = seed if seed is not None else 42
        self._task_name = task or DEFAULT_TASK

        if self._task_name not in SCENARIO_REGISTRY:
            self._task_name = "single_incident"

        scenario_fn = SCENARIO_REGISTRY[self._task_name]
        self._scenario = scenario_fn(seed=self._seed)

        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._incidents = {}
        self._busy_units = []
        self._unit_pool = self._scenario.unit_pool.copy()
        self._available_units = self._scenario.unit_pool.copy()
        self._episode_score = 0.0

        self._history = {
            "total_reward": 0.0,
            "max_possible_reward": self._compute_max_possible_reward(),
            "incidents_total": 0,
            "incidents_resolved": 0,
            "incidents_timed_out": 0,
            "wrong_assignments": 0,
            "correct_assignments": 0,
            "critical_incidents": 0,
            "critical_resolved": 0,
            "steps_taken": 0,
            "max_steps": self._scenario.max_steps,
        }

        # Load initial incidents
        for inc in self._scenario.initial_incidents:
            self._incidents[inc.incident_id] = copy.deepcopy(inc)
            self._history["incidents_total"] += 1
            if inc.severity == 4:
                self._history["critical_incidents"] += 1

        return self._build_observation(
            last_action_result="Dispatch center online. Awaiting orders.",
            last_action_error=None,
            reward=0.0,
            done=False,
        )

    # ── step ──────────────────────────────────────────────────────────────────

    def step(self, action: DispatchAction) -> StepResult:
        step = self._state.step_count + 1
        self._state.step_count = step
        self._history["steps_taken"] = step

        # 1. Age all active incidents + check timeouts
        timeout_penalty = self._age_incidents_and_check_timeouts()

        # 2. Release units that have returned
        self._process_unit_returns(step)

        # 3. Spawn new incidents per schedule
        self._spawn_scheduled_incidents(step)

        # 4. Process the action
        reward, result_msg, error_msg = self._process_action(action)

        # 5. Combine rewards
        step_reward = clamp(reward + timeout_penalty)
        self._episode_score += step_reward
        self._history["total_reward"] = round(self._episode_score, 4)

        # 6. Check episode termination
        done = (
            step >= self._scenario.max_steps
            or self._all_incidents_terminal()
        )

        obs = self._build_observation(
            last_action_result=result_msg,
            last_action_error=error_msg,
            reward=step_reward,
            done=done,
        )

        return StepResult(observation=obs, reward=step_reward, done=done, info={
            "step": step,
            "episode_score": self._episode_score,
            "task": self._task_name,
        })

    # ── state ─────────────────────────────────────────────────────────────────

    def state(self) -> State:
        return self._state

    # ── internal helpers ──────────────────────────────────────────────────────

    def _process_action(self, action: DispatchAction) -> tuple[float, str, str | None]:
        """Returns (reward, result_message, error_message)."""
        atype = (action.action_type or "").lower().strip()

        if atype == "wait":
            r, msg = reward_wait()
            return r, msg, None

        if atype not in ("assign", "close", "escalate"):
            r, msg = reward_invalid()
            return r, "INVALID_ACTION_TYPE", msg

        iid = action.incident_id
        if not iid or iid not in self._incidents:
            r, msg = reward_invalid()
            return r, "INCIDENT_NOT_FOUND", f"Incident '{iid}' does not exist or is already closed."

        inc = self._incidents[iid]

        if inc.resolved or inc.timed_out:
            r, msg = reward_invalid()
            return r, "INCIDENT_ALREADY_TERMINAL", f"Incident {iid} is already closed."

        if atype == "assign":
            return self._handle_assign(inc, action.unit_type)

        if atype == "close":
            return self._handle_close(inc)

        if atype == "escalate":
            return self._handle_escalate(inc)

        r, msg = reward_invalid()
        return r, "UNKNOWN_ERROR", msg

    def _handle_assign(self, inc: Incident, unit_type: str | None) -> tuple[float, str, str | None]:
        if not unit_type:
            r, msg = reward_invalid()
            return r, "MISSING_UNIT_TYPE", "unit_type is required for assign action."

        if inc.assigned_unit is not None:
            r, msg = reward_invalid()
            return r, "ALREADY_ASSIGNED", f"Incident {inc.incident_id} already has unit {inc.assigned_unit}."

        if self._available_units.get(unit_type, 0) <= 0:
            r, msg = reward_invalid()
            return r, "NO_UNIT_AVAILABLE", f"No {unit_type} units available right now."

        r, msg = reward_assign(inc.incident_type, unit_type, inc.severity)

        if r < 0:
            self._history["wrong_assignments"] += 1
        else:
            self._history["correct_assignments"] += 1
            inc.assigned_unit = unit_type
            self._available_units[unit_type] -= 1
            # Schedule unit return
            return_at = self._state.step_count + self._scenario.unit_return_steps
            self._busy_units.append((unit_type, return_at))

        return r, msg, None

    def _handle_close(self, inc: Incident) -> tuple[float, str, str | None]:
        if inc.assigned_unit is None:
            r, msg = reward_invalid()
            return r, "CANNOT_CLOSE_UNASSIGNED", "Must assign a unit before closing an incident."

        r, msg = reward_close(inc.severity, inc.age_steps, inc.max_response_steps)
        inc.resolved = True
        self._history["incidents_resolved"] += 1
        if inc.severity == 4:
            self._history["critical_resolved"] += 1

        return r, msg, None

    def _handle_escalate(self, inc: Incident) -> tuple[float, str, str | None]:
        if inc.severity >= 4:
            r, msg = reward_invalid()
            return r, "ALREADY_MAX_SEVERITY", "Severity is already at maximum (4)."

        inc.severity = min(4, inc.severity + 1)
        inc.max_response_steps = {1: 8, 2: 5, 3: 3, 4: 1}[inc.severity]
        r, msg = reward_escalate()
        return r, msg, None

    def _age_incidents_and_check_timeouts(self) -> float:
        """Age all active incidents. Penalize timed-out ones."""
        total_penalty = 0.0
        for inc in self._incidents.values():
            if inc.resolved or inc.timed_out:
                continue
            inc.age_steps += 1
            if inc.age_steps > inc.max_response_steps and inc.assigned_unit is None:
                inc.timed_out = True
                p, _ = reward_timeout(inc.severity)
                total_penalty += p
                self._history["incidents_timed_out"] += 1
        return total_penalty

    def _process_unit_returns(self, current_step: int):
        remaining = []
        for unit_type, return_at in self._busy_units:
            if current_step >= return_at:
                self._available_units[unit_type] = (
                    self._available_units.get(unit_type, 0) + 1
                )
            else:
                remaining.append((unit_type, return_at))
        self._busy_units = remaining

    def _spawn_scheduled_incidents(self, step: int):
        schedule = self._scenario.new_incident_schedule
        if step in schedule:
            for inc in schedule[step]:
                fresh = copy.deepcopy(inc)
                self._incidents[fresh.incident_id] = fresh
                self._history["incidents_total"] += 1
                if fresh.severity == 4:
                    self._history["critical_incidents"] += 1

    def _all_incidents_terminal(self) -> bool:
        """Episode ends early if all incidents resolved or timed out."""
        if not self._incidents:
            return False
        return all(
            inc.resolved or inc.timed_out
            for inc in self._incidents.values()
        )

    def _build_observation(
        self,
        last_action_result: str,
        last_action_error: str | None,
        reward: float,
        done: bool,
    ) -> DispatchObservation:
        active = [
            inc.model_dump()
            for inc in self._incidents.values()
            if not inc.resolved and not inc.timed_out
        ]
        return DispatchObservation(
            active_incidents=active,
            available_units=dict(self._available_units),
            step_number=self._state.step_count,
            episode_score=round(self._episode_score, 4),
            last_action_result=last_action_result,
            last_action_error=last_action_error,
            task_name=self._task_name,
            max_steps=self._scenario.max_steps if self._scenario else 20,
            reward=reward,
            done=done,
        )

    def _compute_max_possible_reward(self) -> float:
        """
        Theoretical max if agent perfectly resolves all incidents at fastest speed.
        Used to normalize scores.
        """
        if not self._scenario:
            return 1.0
        total = 0.0
        all_incidents = list(self._scenario.initial_incidents)
        for incs in self._scenario.new_incident_schedule.values():
            all_incidents.extend(incs)
        for inc in all_incidents:
            from server.reward_engine import SEVERITY_ASSIGN_REWARD, CLOSE_BASE_BONUS
            total += SEVERITY_ASSIGN_REWARD.get(inc.severity, 0.1)
            total += CLOSE_BASE_BONUS + (0.1 * 1.0 * inc.severity)  # max speed bonus
        return max(total, 1.0)

    def get_episode_grade(self) -> float:
        """Call this at episode end to get the graded score."""
        grader = GRADER_REGISTRY.get(self._task_name, GRADER_REGISTRY["single_incident"])
        return grader(self._history)
```

---

## 8. BATCH 4 — FASTAPI APP + DOCKERFILE + OPENENV.YAML

### 8.1 server/__init__.py

```python
# empty — required for package recognition
```

### 8.2 server/app.py

```python
"""
FastAPI application entry point for Emergency Dispatch Triage environment.
Uses openenv create_app factory pattern.
"""

from __future__ import annotations
from openenv.core.env_server import create_app

try:
    from dispatch_env.models import DispatchAction, DispatchObservation
    from server.dispatch_environment import DispatchEnvironment
except ImportError:
    from models import DispatchAction, DispatchObservation
    from dispatch_environment import DispatchEnvironment

app = create_app(
    DispatchEnvironment,
    DispatchAction,
    DispatchObservation,
    env_name="dispatch_env",
)
```

### 8.3 server/requirements.txt

```
openenv-core>=0.1.0
pydantic>=2.0
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
websockets>=12.0
```

### 8.4 server/Dockerfile

```dockerfile
FROM ghcr.io/meta-pytorch/openenv-base:latest

WORKDIR /app

# Copy server dependencies first (layer caching)
COPY server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy env package (models, client)
COPY dispatch_env/ /app/dispatch_env/

# Copy server code
COPY server/ /app/server/

# Environment variables with defaults
ENV DISPATCH_TASK=single_incident
ENV PORT=8000
ENV HOST=0.0.0.0
ENV WORKERS=1

EXPOSE 8000

# Start the server
CMD uvicorn server.app:app --host $HOST --port $PORT --workers $WORKERS
```

> **NOTE for Claude:** If `ghcr.io/meta-pytorch/openenv-base:latest` is not available locally during build, fall back to:
> ```dockerfile
> FROM python:3.11-slim
> ```
> and add `pip install openenv-core` to the RUN step. The openenv-base image is preferred for HF Spaces.

### 8.5 dispatch_env/openenv.yaml

```yaml
spec_version: 1
name: dispatch_env
version: "1.0.0"
type: environment
runtime: docker
app: server/app.py
port: 8000
description: >
  Emergency 911 Dispatch Triage RL Environment. An AI agent acts as
  a dispatch coordinator — triaging incoming incidents, assigning
  limited responder units (ambulance, fire, police, hazmat), and
  managing cascading crises in real time. 3 tasks with difficulty
  ranging from single incident handling to mass casualty events.
author: "your-name"
tags:
  - openenv
  - dispatch
  - emergency
  - real-world
  - triage
tasks:
  - name: single_incident
    description: >
      Easy. One incident active at a time. Low-medium severity.
      No hazmat. Incident arrives every 4 steps. 20 step episodes.
    difficulty: easy
    max_steps: 20
  - name: multi_incident
    description: >
      Medium. 3-5 simultaneous incidents. Mixed severity 1-3.
      Requires prioritization under unit scarcity. 25 step episodes.
    difficulty: medium
    max_steps: 25
  - name: mass_casualty
    description: >
      Hard. Mass casualty event. Multiple critical incidents.
      Scarce units, cascading arrivals. Agent cannot save everyone —
      must triage ruthlessly. Frontier models score ~0.35-0.55.
    difficulty: hard
    max_steps: 30
```

---

## 9. BATCH 5 — INFERENCE SCRIPT

### 9.1 inference.py (ROOT LEVEL — MANDATORY)

This file must be at the project root, not inside dispatch_env/.
Follows the exact mandatory stdout format: [START], [STEP], [END].

```python
"""
inference.py — Emergency Dispatch Triage
=========================================
Mandatory inference script for OpenEnv hackathon submission.

Environment variables:
    API_BASE_URL    LLM endpoint (default: HF router)
    MODEL_NAME      Model identifier
    HF_TOKEN        API key
    DISPATCH_TASK   Task name (default: runs all 3)

Stdout format (mandatory):
    [START] task=<name> env=dispatch_env model=<model>
    [STEP]  step=<n> action=<str> reward=<0.00> done=<bool> error=<str|null>
    [END]   success=<bool> steps=<n> score=<0.000> rewards=<r1,r2,...>
"""

import asyncio
import json
import os
import textwrap
from typing import Optional

from openai import OpenAI

# ── Env vars ──────────────────────────────────────────────────────────────────
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
IMAGE_NAME   = os.getenv("LOCAL_IMAGE_NAME", "")
BENCHMARK    = "dispatch_env"

TASKS = ["single_incident", "multi_incident", "mass_casualty"]
MAX_STEPS_PER_TASK = {"single_incident": 20, "multi_incident": 25, "mass_casualty": 30}
SUCCESS_THRESHOLD = 0.3
TEMPERATURE = 0.2
MAX_TOKENS  = 300

# ── Logging helpers ───────────────────────────────────────────────────────────

def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]):
    err = error if error else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={err}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: list[float]):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

# ── Prompt construction ───────────────────────────────────────────────────────

SYSTEM_PROMPT = textwrap.dedent("""
You are an emergency 911 dispatch coordinator AI. Your job is to manage incoming incidents
and assign the correct responder units to save lives.

UNIT TYPES AND VALID INCIDENT ASSIGNMENTS:
- ambulance    → medical, fire (support), accident
- fire_truck   → fire, accident, hazmat (support)
- police_car   → crime, accident
- hazmat_team  → hazmat, (fire support)

ACTION FORMAT — respond with ONLY a valid JSON object, no other text:
{"action_type": "assign", "incident_id": "INC-001", "unit_type": "ambulance"}
{"action_type": "close",  "incident_id": "INC-001", "unit_type": null}
{"action_type": "wait",   "incident_id": "", "unit_type": null}

STRATEGY:
1. Always prioritize severity 4 (critical) incidents first
2. Assign the correct unit type — wrong assignments are penalized
3. Close incidents after assigning a unit (on the next step)
4. If no units available, use "wait"
5. Never leave critical incidents unassigned if a valid unit is available
""").strip()


def build_user_prompt(obs: dict, step: int, history: list[str]) -> str:
    active = obs.get("active_incidents", [])
    units  = obs.get("available_units", {})
    score  = obs.get("episode_score", 0.0)
    last   = obs.get("last_action_result", "")
    error  = obs.get("last_action_error")
    max_s  = obs.get("max_steps", 20)

    inc_lines = []
    for inc in sorted(active, key=lambda x: -x.get("severity", 0)):
        inc_lines.append(
            f"  ID={inc['incident_id']} type={inc['incident_type']} "
            f"severity={inc['severity']} zone={inc['location_zone']} "
            f"age={inc['age_steps']}/{inc['max_response_steps']} "
            f"assigned={inc.get('assigned_unit', 'NONE')}"
        )

    incidents_block = "\n".join(inc_lines) if inc_lines else "  (none active)"
    units_block = ", ".join(f"{k}:{v}" for k, v in units.items())
    history_block = "\n".join(history[-4:]) if history else "none"

    error_line = f"\nLAST ERROR: {error}" if error else ""

    return textwrap.dedent(f"""
    Step {step}/{max_s} | Cumulative score: {score:.3f}
    Last result: {last}{error_line}

    ACTIVE INCIDENTS (sorted by severity):
{incidents_block}

    AVAILABLE UNITS: {units_block}

    RECENT HISTORY:
{history_block}

    Respond with ONE JSON action object only.
    """).strip()


def get_action(client: OpenAI, obs: dict, step: int, history: list[str]) -> dict:
    """Call LLM and parse action JSON. Falls back to wait on any error."""
    prompt = build_user_prompt(obs, step, history)
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        text = (resp.choices[0].message.content or "").strip()
        # Extract JSON from response
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return {"action_type": "wait", "incident_id": "", "unit_type": None}
    except Exception as exc:
        print(f"[DEBUG] LLM call failed: {exc}", flush=True)
        return {"action_type": "wait", "incident_id": "", "unit_type": None}


def action_to_str(action: dict) -> str:
    atype = action.get("action_type", "wait")
    iid   = action.get("incident_id", "")
    unit  = action.get("unit_type") or "null"
    return f"{atype}(incident={iid},unit={unit})"


# ── Main episode runner ───────────────────────────────────────────────────────

async def run_task(env, task_name: str, client: OpenAI) -> float:
    """Run one full episode and return the graded score."""
    from dispatch_env.models import DispatchAction

    max_steps = MAX_STEPS_PER_TASK.get(task_name, 20)
    rewards: list[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset(task=task_name)
        obs = result.observation.model_dump()
        history: list[str] = []

        for step in range(1, max_steps + 1):
            if result.done:
                break

            action_dict = get_action(client, obs, step, history)
            action = DispatchAction(
                action_type=action_dict.get("action_type", "wait"),
                incident_id=action_dict.get("incident_id", ""),
                unit_type=action_dict.get("unit_type"),
            )

            result = await env.step(action)
            obs = result.observation.model_dump()
            reward = result.reward or 0.0
            done   = result.done
            error  = obs.get("last_action_error")

            rewards.append(reward)
            steps_taken = step

            action_str = action_to_str(action_dict)
            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            history.append(
                f"Step {step}: {action_str} → reward {reward:+.3f} | {obs.get('last_action_result','')}"
            )

            if done:
                break

        # Get graded score from environment
        score = getattr(env, "_env", env).get_episode_grade() if hasattr(env, "_env") else (
            obs.get("episode_score", 0.0) / max(obs.get("max_steps", 1), 1)
        )
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Episode error for {task_name}: {exc}", flush=True)

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


async def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    # Import environment client
    from dispatch_env import DispatchEnv

    all_scores: dict[str, float] = {}

    for task_name in TASKS:
        try:
            if IMAGE_NAME:
                env = await DispatchEnv.from_docker_image(IMAGE_NAME)
            else:
                # Try HF Space first, fall back to localhost
                space_url = os.getenv("DISPATCH_ENV_URL", "http://localhost:8000")
                env = DispatchEnv(base_url=space_url)

            async with env:
                score = await run_task(env, task_name, client)
                all_scores[task_name] = score

        except Exception as exc:
            print(f"[DEBUG] Failed to run task {task_name}: {exc}", flush=True)
            all_scores[task_name] = 0.0

    # Final summary
    print("\n[SUMMARY]", flush=True)
    for task, score in all_scores.items():
        print(f"  {task}: {score:.3f}", flush=True)
    avg = sum(all_scores.values()) / max(len(all_scores), 1)
    print(f"  average: {avg:.3f}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 10. BATCH 6 — README + VALIDATE

### 10.1 README.md (ROOT LEVEL)

```markdown
# Emergency Dispatch Triage — OpenEnv Environment

[![OpenEnv](https://img.shields.io/badge/OpenEnv-spec%20v1-blue)](https://github.com/meta-pytorch/OpenEnv)

An RL environment where an AI agent acts as a 911 emergency dispatch coordinator.
The agent must triage incoming incidents, assign the correct responder units (ambulance,
fire truck, police, hazmat), and manage cascading crises under real resource constraints.

## Environment Description

Real 911 dispatch centers handle thousands of simultaneous incidents daily. Operators must:
- Classify incident type and severity instantly
- Match the correct responder unit type to each incident
- Manage unit availability (units are busy until they return)
- Prioritize critical incidents before they time out

This environment simulates that exact workflow as an RL task.

## Action Space

```json
{
  "action_type": "assign | close | escalate | wait",
  "incident_id": "INC-001",
  "unit_type": "ambulance | fire_truck | police_car | hazmat_team | null"
}
```

| Action | Description |
|--------|-------------|
| assign | Assign a unit_type to an incident_id |
| close  | Mark an assigned incident as resolved |
| escalate | Increase severity of an incident by 1 |
| wait   | Take no action this step |

## Observation Space

```json
{
  "active_incidents": [...],
  "available_units": {"ambulance": 2, "fire_truck": 1, ...},
  "step_number": 5,
  "episode_score": 0.42,
  "last_action_result": "CORRECT_ASSIGN: +0.40 ...",
  "last_action_error": null,
  "task_name": "multi_incident",
  "max_steps": 25
}
```

## Tasks

| Task | Difficulty | Max Steps | Description |
|------|-----------|-----------|-------------|
| single_incident | Easy | 20 | One incident at a time, low severity, generous windows |
| multi_incident | Medium | 25 | 3-5 simultaneous incidents, mixed severity, unit scarcity |
| mass_casualty | Hard | 30 | Mass casualty event, critical incidents, ruthless triage required |

## Reward Function

- Correct assignment: `+0.1 to +0.7` (scaled by severity)
- Wrong unit type: `-0.3`
- Close resolved incident: `+0.15 to +0.55` (speed bonus)
- Incident timeout: `-0.1 to -0.8` (scaled by severity)
- Escalate handled: `+0.05`
- Wait: `-0.05`
- Invalid action: `-0.1`

## Baseline Scores

| Task | Baseline Score (Qwen2.5-72B) |
|------|------------------------------|
| single_incident | ~0.65 |
| multi_incident | ~0.45 |
| mass_casualty | ~0.32 |

## Setup

```bash
# Install
pip install openenv-core
git clone <your-repo>
cd dispatch_env

# Run server locally
uv run server
# OR
uvicorn server.app:app --host 0.0.0.0 --port 8000

# Run inference
export HF_TOKEN=your_token
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
python inference.py

# Docker
docker build -f server/Dockerfile -t dispatch-env .
docker run -p 8000:8000 dispatch-env
```

## Validate Submission

```bash
openenv validate
```

## Deploy to HF Spaces

```bash
openenv push --repo-id your-username/dispatch-env
```
```

---

## 11. CRITICAL RULES FOR CLAUDE (EXECUTION CHECKLIST)

Before considering any batch complete, Claude must verify:

### Batch 1 Checklist
- [ ] `dispatch_env/__init__.py` exports `DispatchEnv`, `DispatchAction`, `DispatchObservation`
- [ ] `models.py` has dual-import pattern (`try/except ImportError`)
- [ ] `Incident` extends `BaseModel` (NOT `Action` or `Observation`)
- [ ] `DispatchAction` extends `Action` from openenv
- [ ] `DispatchObservation` extends `Observation` from openenv
- [ ] `pyproject.toml` has `openenv-core` as dependency

### Batch 2 Checklist
- [ ] `reward_engine.py` — all 6 reward functions return `(float, str)` tuples
- [ ] `scenarios.py` — all 3 scenario functions use seeded `random.Random(seed)` NOT `random.seed()`
- [ ] `scenarios.py` — `SCENARIO_REGISTRY` dict exists with all 3 keys
- [ ] `graders.py` — all 3 graders return float in [0.0, 1.0]
- [ ] `graders.py` — `GRADER_REGISTRY` dict exists with all 3 keys

### Batch 3 Checklist
- [ ] `dispatch_environment.py` extends `Environment` from openenv
- [ ] `reset()` accepts optional `seed` and `task` params
- [ ] `step()` returns `StepResult` with `.observation`, `.reward`, `.done`
- [ ] `state()` returns `State` object
- [ ] Dual-import pattern in ALL server files
- [ ] `get_episode_grade()` method exists and calls grader

### Batch 4 Checklist
- [ ] `server/app.py` uses `create_app(DispatchEnvironment, DispatchAction, DispatchObservation)`
- [ ] `server/__init__.py` exists (even if empty)
- [ ] `Dockerfile` builds without error (`docker build -f server/Dockerfile .`)
- [ ] `openenv.yaml` has `spec_version: 1`, lists all 3 tasks

### Batch 5 Checklist
- [ ] `inference.py` is at root level (NOT inside dispatch_env/)
- [ ] All three log functions (`log_start`, `log_step`, `log_end`) match exact format
- [ ] `[START]` emitted once at episode begin
- [ ] `[STEP]` emitted per step with `reward:.2f`, `done` lowercase
- [ ] `[END]` always emitted (even on exception) with `score:.3f`
- [ ] All 3 tasks run in sequence
- [ ] Uses `OpenAI` client with `API_BASE_URL` and `HF_TOKEN`

### Batch 6 Checklist
- [ ] `openenv validate` passes (run this command explicitly)
- [ ] `docker build -f server/Dockerfile . && docker run -p 8000:8000 <image>` works
- [ ] `curl http://localhost:8000/health` returns `{"status": "healthy"}`
- [ ] `curl -X POST http://localhost:8000/reset -H 'Content-Type: application/json' -d '{}'` returns 200
- [ ] `python inference.py` runs without error and completes in < 20 minutes
- [ ] All [STEP] rewards in [-1.0, 1.0] range
- [ ] All [END] scores in [0.0, 1.0] range

---

## 12. ENVIRONMENT VARIABLES REQUIRED

```bash
# Mandatory per problem statement
API_BASE_URL=https://router.huggingface.co/v1
MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
HF_TOKEN=your_huggingface_token

# Optional
LOCAL_IMAGE_NAME=dispatch-env:latest   # if running from local docker image
DISPATCH_TASK=single_incident           # override task (default: runs all 3)
DISPATCH_ENV_URL=http://localhost:8000  # override server URL
```

---

## 13. SUBMISSION CHECKLIST (PRE-SUBMIT)

Run this exact sequence before submitting:

```bash
# 1. Validate spec
openenv validate

# 2. Build Docker
docker build -f server/Dockerfile -t dispatch-env .

# 3. Run server locally
docker run -d -p 8000:8000 --name dispatch-test dispatch-env

# 4. Health check
curl http://localhost:8000/health

# 5. Reset test
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" -d '{}'

# 6. Run inference
export HF_TOKEN=your_token
python inference.py

# 7. Deploy to HF
openenv push --repo-id your-username/dispatch-env

# 8. Run validation script
./validate-submission.sh https://your-username-dispatch-env.hf.space
```

---

## 14. CONTINUATION SUMMARY (FOR NEW CHAT)

If this PRD is used in a new chat, paste this summary:

**Project:** Emergency Dispatch Triage — OpenEnv hackathon environment
**Domain:** 911 emergency dispatch coordination
**Stack:** Python 3.11, openenv-core, FastAPI, Pydantic v2, Docker, HF Spaces
**Deadline:** April 8, 2026

**File structure:** `dispatch_env/` (models, client, openenv.yaml, pyproject.toml) + `server/` (app.py, dispatch_environment.py, scenarios.py, graders.py, reward_engine.py, Dockerfile) + `inference.py` and `README.md` at root

**3 tasks:** `single_incident` (easy/20 steps), `multi_incident` (medium/25 steps), `mass_casualty` (hard/30 steps)

**Key patterns:**
- Dual-import everywhere: `try: from dispatch_env.models import X / except ImportError: from models import X`
- `create_app(DispatchEnvironment, DispatchAction, DispatchObservation)` in app.py
- Rewards returned inside observation (openenv pattern)
- inference.py stdout: `[START]`, `[STEP]`, `[END]` exact format, score in [0,1]

**Current batch:** tell Claude which batch you're on
