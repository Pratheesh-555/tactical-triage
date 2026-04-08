---
title: Tactical Triage
emoji: 🚑
colorFrom: red
colorTo: blue
sdk: docker
app_port: 8000
pinned: false
---
# TacticalTriage ðŸš‘ðŸš“ðŸ”¥

[![OpenEnv](https://img.shields.io/badge/OpenEnv-spec%20v1-blue)](https://github.com/meta-pytorch/OpenEnv)

**TacticalTriage** is a production-grade Reinforcement Learning environment designed for the Meta Ã— Hugging Face OpenEnv Hackathon. It simulates a 911 emergency dispatch coordination center where an AI agent acts as a lead dispatcher. The agent must triage incoming incidents (medical, fire, crime, accident, hazmat), assign a limited pool of responder units (ambulance, fire_truck, police_car, hazmat_team), and manage cascading crises in real-time. This environment tests the agent's ability to prioritize high-severity events while optimizing resource allocation under extreme scarcity.

## Action Space

The agent interacts with the environment using a single `TacticalAction`.

| Action | Parameters | Description |
|---|---|---|
| `assign` | `incident_id`, `unit_type` | Assigns a unit to an active incident. Must be a valid unit type for the incident. |
| `close` | `incident_id` | Marks an incident as resolved. Requires a unit to be already assigned. |
| `escalate` | `incident_id` | Manually increases the severity of an incident (+1), shortening its timeout window. |
| `wait` | - | No action this step. Useful for waiting for units to return or new incidents to arrive. |

## Observation Space

Observations provide a snapshot of the current situation.

```json
{
  "active_incidents": [
    {
      "incident_id": "INC-001",
      "incident_type": "medical",
      "severity": 3,
      "location_zone": "north",
      "age_steps": 2,
      "max_response_steps": 3,
      "assigned_unit": null
    }
  ],
  "available_units": {
    "ambulance": 2,
    "fire_truck": 1,
    "police_car": 3,
    "hazmat_team": 1
  },
  "step_number": 5,
  "episode_score": 1.25,
  "last_action_result": "CORRECT_ASSIGN: +0.40 for ambulance -> medical sev=3",
  "task_name": "multi_incident",
  "max_steps": 25
}
```

## Tasks

| Task Name | Difficulty | Max Steps | Description |
|---|---|---|---|
| `single_incident` | Easy | 20 | One incident at a time. New incident only arrives after resolution. |
| `multi_incident` | Medium | 25 | 3-5 simultaneous incidents. Requires prioritization and resource management. |
| `mass_casualty` | Hard | 30 | Multiple critical incidents, extreme unit scarcity, and cascading arrivals. |

## Reward Function

| Event | Reward | Description |
|---|---|---|
| Correct Assignment | `+0.1 to +0.7` | Positive reward scaled by incident severity. |
| Wrong Unit Type | `-0.3` | Penalty for mismatched responder-incident types. |
| Successful Resolution | `+0.15 to +0.55` | Bonus for closing an incident, includes speed/efficiency bonus. |
| Incident Timeout | `-0.1 to -0.8` | Negative penalty scaled by severity of the missed incident. |
| Handled Escalation | `+0.05` | Tiny positive signal for dealing with high-severity growth. |
| Wait / Opportunity Cost | `-0.05` | Small nudge to encourage proactive decision making. |

## Baseline Scores (Estimated)

| Task | Baseline Score (Qwen2.5-72B) |
|---|---|
| `single_incident` | ~0.70 |
| `multi_incident` | ~0.55 |
| `mass_casualty` | ~0.45 |

## Setup & Running

### 1. Install Dependencies
```bash
pip install openenv-core pydantic fastapi uvicorn websockets openai
```

### 2. Run Locally (Dev Mode)
```bash
cd tactical_triage_env
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### 3. Run Inference
```bash
export HF_TOKEN=your_token_here
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
python inference.py
```

### 4. Run with Docker
```bash
docker build -f tactical_triage_env/server/Dockerfile -t tactical-triage .
docker run -p 8000:8000 tactical-triage
```

## Validate Submission
```bash
cd tactical_triage_env
openenv validate
```

## Deploy to Hugging Face Spaces
```bash
openenv push --repo-id your-username/tactical-triage
```

