"""
Scenario generators for each task.
All scenarios use seeded RNG for full reproducibility.
"""

from __future__ import annotations

import random
from typing import NamedTuple

try:
    from tactical_triage_env.models import Incident
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
    unit_return_steps: int          # how many steps until a dispatched unit returns
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
    schedule: dict[int, list[Incident]] = {
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
    schedule: dict[int, list[Incident]] = {
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
    schedule: dict[int, list[Incident]] = {
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
