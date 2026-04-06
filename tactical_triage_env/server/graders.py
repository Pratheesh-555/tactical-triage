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
    assignment_score = history.get("correct_assignments", 0) / max(1, total_assignments)

    raw = 0.50 * reward_score + 0.25 * resolution_rate + 0.25 * assignment_score

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
    efficiency = 1.0 - (steps_taken / max_steps)  # fewer steps used = more efficient

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
