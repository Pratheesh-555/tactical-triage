"""
Emergency Dispatch Triage — Main Environment Class.

Implements the OpenEnv Environment interface:
    reset(seed, **kwargs) → TacticalObservation
    step(action)         → TacticalObservation
    state (property)     → State
"""

from __future__ import annotations

import copy
import os
from typing import Any, Optional
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from tactical_triage_env.models import TacticalAction, TacticalObservation, Incident
    from tactical_triage_env.server.reward_engine import (
        reward_assign, reward_close, reward_timeout,
        reward_escalate, reward_wait, reward_invalid, clamp,
        SEVERITY_ASSIGN_REWARD, CLOSE_BASE_BONUS,
    )
    from tactical_triage_env.server.scenarios import SCENARIO_REGISTRY, ScenarioConfig
    from tactical_triage_env.server.graders import GRADER_REGISTRY
except ImportError:
    from models import TacticalAction, TacticalObservation, Incident
    from reward_engine import (
        reward_assign, reward_close, reward_timeout,
        reward_escalate, reward_wait, reward_invalid, clamp,
        SEVERITY_ASSIGN_REWARD, CLOSE_BASE_BONUS,
    )
    from scenarios import SCENARIO_REGISTRY, ScenarioConfig
    from graders import GRADER_REGISTRY


class TacticalEnvironment(Environment[TacticalAction, TacticalObservation, State]):

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self) -> None:
        super().__init__()
        self._task_name: str = DEFAULT_TASK
        self._state: State = State(episode_id=str(uuid4()), step_count=0)
        self._incidents: dict[str, Incident] = {}
        self._available_units: dict[str, int] = {}
        self._unit_pool: dict[str, int] = {}
        self._busy_units: list[tuple[str, int]] = []  # (unit_type, return_at_step)
        self._scenario: Optional[ScenarioConfig] = None
        self._episode_score: float = 0.0
        self._history: dict[str, Any] = {}
        self._seed: int = 42

    # ── reset ─────────────────────────────────────────────────────────────────

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> TacticalObservation:
        self._reset_rubric()
        self._seed = seed if seed is not None else 42
        self._task_name = kwargs.get("task", DEFAULT_TASK)

        if self._task_name not in SCENARIO_REGISTRY:
            self._task_name = "single_incident"

        scenario_fn = SCENARIO_REGISTRY[self._task_name]
        self._scenario = scenario_fn(seed=self._seed)

        eid = episode_id or str(uuid4())
        self._state = State(episode_id=eid, step_count=0)
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

        # Load initial incidents — deep copy so scenario is never mutated
        for inc in self._scenario.initial_incidents:
            fresh = copy.deepcopy(inc)
            self._incidents[fresh.incident_id] = fresh
            self._history["incidents_total"] += 1
            if fresh.severity == 4:
                self._history["critical_incidents"] += 1

        return self._build_observation(
            last_action_result="Dispatch center online. Awaiting orders.",
            last_action_error=None,
        )

    # ── step ──────────────────────────────────────────────────────────────────

    def step(
        self,
        action: TacticalAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> TacticalObservation:
        # Ensure reset() was called before step()
        if self._scenario is None:
            raise RuntimeError(
                "Environment must be reset() before calling step(). "
                "Call reset() to initialize a scenario first."
            )
        
        step = self._state.step_count + 1
        self._state.step_count = step
        self._history["steps_taken"] = step

        # 1. Age all active incidents + collect timeout penalties
        timeout_penalty = self._age_incidents_and_check_timeouts()

        # 2. Release units whose return step has been reached
        self._process_unit_returns(step)

        # 3. Spawn new incidents from schedule if any due this step
        self._spawn_scheduled_incidents(step)

        # 4. Process the agent's action
        reward, result_msg, error_msg = self._process_action(action)

        # 5. Combine all rewards + clamp
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
        )
        obs.reward = step_reward
        obs.done = done

        return self._apply_transform(obs)

    # ── state (property) ──────────────────────────────────────────────────────

    @property
    def state(self) -> State:
        return self._state

    # ── grading ───────────────────────────────────────────────────────────────

    def get_episode_grade(self) -> float:
        """Call at episode end to obtain the graded score [0.0, 1.0]."""
        grader = GRADER_REGISTRY.get(self._task_name, GRADER_REGISTRY["single_incident"])
        return grader(self._history)

    # ── internal: action dispatch ─────────────────────────────────────────────

    def _process_action(
        self, action: TacticalAction
    ) -> tuple[float, str, str | None]:
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

        # atype == "escalate"
        return self._handle_escalate(inc)

    def _handle_assign(
        self, inc: Incident, unit_type: str | None
    ) -> tuple[float, str, str | None]:
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

    # ── internal: per-step lifecycle ──────────────────────────────────────────

    def _age_incidents_and_check_timeouts(self) -> float:
        """Age all active incidents. Penalise timed-out ones. Returns total penalty."""
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

    def _process_unit_returns(self, current_step: int) -> None:
        remaining = []
        for unit_type, return_at in self._busy_units:
            if current_step >= return_at:
                self._available_units[unit_type] = (
                    self._available_units.get(unit_type, 0) + 1
                )
            else:
                remaining.append((unit_type, return_at))
        self._busy_units = remaining

    def _spawn_scheduled_incidents(self, step: int) -> None:
        if self._scenario is None:
            return
        schedule = self._scenario.new_incident_schedule
        if step not in schedule:
            return
        for inc in schedule[step]:
            fresh = copy.deepcopy(inc)
            self._incidents[fresh.incident_id] = fresh
            self._history["incidents_total"] += 1
            if fresh.severity == 4:
                self._history["critical_incidents"] += 1

    def _all_incidents_terminal(self) -> bool:
        """Episode ends early when all incidents are resolved or timed out."""
        if not self._incidents:
            return False
        return all(inc.resolved or inc.timed_out for inc in self._incidents.values())

    # ── internal: observation builder ─────────────────────────────────────────

    def _build_observation(
        self,
        last_action_result: str,
        last_action_error: str | None,
    ) -> TacticalObservation:
        active = [
            inc.model_dump()
            for inc in self._incidents.values()
            if not inc.resolved and not inc.timed_out
        ]
        return TacticalObservation(
            active_incidents=active,
            available_units=dict(self._available_units),
            step_number=self._state.step_count,
            episode_score=round(self._episode_score, 4),
            last_action_result=last_action_result,
            last_action_error=last_action_error,
            task_name=self._task_name,
            max_steps=self._scenario.max_steps if self._scenario else 20,
        )

    def _compute_max_possible_reward(self) -> float:
        """Theoretical max if agent perfectly resolves all incidents at fastest speed."""
        if not self._scenario:
            return 1.0
        total = 0.0
        all_incidents = list(self._scenario.initial_incidents)
        for incs in self._scenario.new_incident_schedule.values():
            all_incidents.extend(incs)
        for inc in all_incidents:
            total += SEVERITY_ASSIGN_REWARD.get(inc.severity, 0.1)
            total += CLOSE_BASE_BONUS + (0.1 * 1.0 * inc.severity)  # max speed bonus
        return max(total, 1.0)
