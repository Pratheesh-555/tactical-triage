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
            f"WRONG_UNIT: {unit_type} cannot handle {incident_type}",
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
