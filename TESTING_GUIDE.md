# Tactical Triage Environment - Testing Guide with curl

## Project Overview
**Tactical Triage** is an emergency 911 dispatch RL environment where an AI agent acts as a dispatch coordinator. The agent must:
- Triage incoming emergency incidents
- Assign limited responder units (ambulance, fire_truck, police_car, hazmat_team)
- Manage cascading crises in real time
- Maximize rewards by making correct, timely decisions

## Testing with curl Commands

### 1. Reset the Environment

**Command:**
```bash
curl -X POST http://127.0.0.1:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task":"single_incident", "seed": 42}'
```

**Expected Output:**
```json
{
  "observation": {
    "active_incidents": [
      {
        "incident_id": "INC-001",
        "incident_type": "medical",
        "severity": 1,
        "location_zone": "east",
        "age_steps": 0,
        "max_response_steps": 8,
        "assigned_unit": null,
        "resolved": false,
        "timed_out": false
      }
    ],
    "available_units": {
      "ambulance": 3,
      "fire_truck": 2,
      "police_car": 3,
      "hazmat_team": 1
    },
    "step_number": 0,
    "episode_score": 0.0,
    "last_action_result": "Dispatch center online. Awaiting orders.",
    "last_action_error": null,
    "task_name": "single_incident",
    "max_steps": 20
  },
  "reward": null,
  "done": false
}
```

**What This Means:**
- **active_incidents**: One medical emergency (severity 1 = low) in the east zone
- **available_units**: You have 3 ambulances, 2 fire trucks, 3 police cars, 1 hazmat team
- **step_number**: Episode starts at step 0
- **max_response_steps**: 8 - You have 8 steps to respond before timeout penalty
- **episode_score**: Starting score is 0.0
- **max_steps**: Episode will end at step 20

---

### 2. Wait Action (Do Nothing)

**Command:**
```bash
curl -X POST http://127.0.0.1:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "wait"}}'
```

**Expected Output:**
```json
{
  "observation": {
    "active_incidents": [
      {
        "incident_id": "INC-001",
        "incident_type": "medical",
        "severity": 1,
        "location_zone": "east",
        "age_steps": 1,
        "max_response_steps": 8,
        "assigned_unit": null,
        "resolved": false,
        "timed_out": false
      }
    ],
    "available_units": {
      "ambulance": 3,
      "fire_truck": 2,
      "police_car": 3,
      "hazmat_team": 1
    },
    "step_number": 1,
    "episode_score": 0.01,
    "last_action_result": "WAIT: +0.01 (no action taken)",
    "last_action_error": null,
    "task_name": "single_incident",
    "max_steps": 20
  },
  "reward": 0.01,
  "done": false
}
```

**What Changed:**
- **reward**: +0.01 (small reward for waiting, but not optimal)
- **step_number**: Increased to 1
- **age_steps**: Incident aged from 0 to 1
- **episode_score**: Cumulative score is now 0.01

---

### 3. Assign Unit to Incident (Correct Match)

**Command:**
```bash
curl -X POST http://127.0.0.1:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "assign", "incident_id": "INC-001", "unit_type": "ambulance"}}'
```

**Expected Output:**
```json
{
  "observation": {
    "active_incidents": [
      {
        "incident_id": "INC-001",
        "incident_type": "medical",
        "severity": 1,
        "location_zone": "east",
        "age_steps": 2,
        "max_response_steps": 8,
        "assigned_unit": "ambulance",
        "resolved": false,
        "timed_out": false
      }
    ],
    "available_units": {
      "ambulance": 2,
      "fire_truck": 2,
      "police_car": 3,
      "hazmat_team": 1
    },
    "step_number": 2,
    "episode_score": 0.11,
    "last_action_result": "CORRECT_ASSIGN: +0.10 for ambulance → medical sev=1",
    "last_action_error": null,
    "task_name": "single_incident",
    "max_steps": 20
  },
  "reward": 0.1,
  "done": false
}
```

**What Changed:**
- **reward**: +0.10 (Good! Ambulance is correct for medical incident)
- **assigned_unit**: Now shows "ambulance"
- **available_units**: Ambulances reduced from 3 to 2 (one is now busy)
- **episode_score**: 0.01 + 0.10 = 0.11
- **last_action_result**: Confirms correct assignment with reward breakdown

---

### 4. Assign Wrong Unit (Penalty)

**Command:**
```bash
# Reset first to test wrong assignment
curl -X POST http://127.0.0.1:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"seed": 42}'

# Try assigning fire truck to medical incident
curl -X POST http://127.0.0.1:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "assign", "incident_id": "INC-001", "unit_type": "fire_truck"}}'
```

**Expected Output:**
```json
{
  "observation": {
    "active_incidents": [
      {
        "incident_id": "INC-001",
        "incident_type": "medical",
        "severity": 1,
        "location_zone": "east",
        "age_steps": 1,
        "max_response_steps": 8,
        "assigned_unit": null,
        "resolved": false,
        "timed_out": false
      }
    ],
    "available_units": {
      "ambulance": 3,
      "fire_truck": 2,
      "police_car": 3,
      "hazmat_team": 1
    },
    "step_number": 1,
    "episode_score": -0.15,
    "last_action_result": "WRONG_ASSIGN: -0.15 for fire_truck → medical sev=1",
    "last_action_error": null,
    "task_name": "single_incident",
    "max_steps": 20
  },
  "reward": -0.15,
  "done": false
}
```

**What Changed:**
- **reward**: -0.15 (Penalty! Fire truck is wrong for medical incident)
- **assigned_unit**: Still null (wrong assignment doesn't stick)
- **episode_score**: -0.15 (negative score)
- **last_action_result**: Shows the penalty

---

### 5. Close an Incident (After Assignment)

**Command:**
```bash
# First assign correctly
curl -X POST http://127.0.0.1:8000/reset -H "Content-Type: application/json" -d '{"seed": 42}'

curl -X POST http://127.0.0.1:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "assign", "incident_id": "INC-001", "unit_type": "ambulance"}}'

# Now close it
curl -X POST http://127.0.0.1:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "close", "incident_id": "INC-001"}}'
```

**Expected Output:**
```json
{
  "observation": {
    "active_incidents": [],
    "available_units": {
      "ambulance": 2,
      "fire_truck": 2,
      "police_car": 3,
      "hazmat_team": 1
    },
    "step_number": 2,
    "episode_score": 0.347,
    "last_action_result": "RESOLVED: +0.237 (base=0.15 + speed_bonus=0.087 for sev=1)",
    "last_action_error": null,
    "task_name": "single_incident",
    "max_steps": 20
  },
  "reward": 0.237,
  "done": false
}
```

**What Changed:**
- **reward**: +0.237 (Big reward! Quick resolution gets speed bonus)
- **active_incidents**: Now empty (incident resolved)
- **episode_score**: 0.10 + 0.237 = 0.347
- **Speed bonus**: Faster resolution = higher reward

---

### 6. Escalate Incident Severity

**Command:**
```bash
curl -X POST http://127.0.0.1:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "escalate", "incident_id": "INC-001"}}'
```

**Expected Output:**
```json
{
  "observation": {
    "active_incidents": [
      {
        "incident_id": "INC-001",
        "incident_type": "medical",
        "severity": 2,
        "location_zone": "east",
        "age_steps": 1,
        "max_response_steps": 5,
        "assigned_unit": null,
        "resolved": false,
        "timed_out": false
      }
    ],
    "available_units": {
      "ambulance": 3,
      "fire_truck": 2,
      "police_car": 3,
      "hazmat_team": 1
    },
    "step_number": 1,
    "episode_score": 0.0,
    "last_action_result": "ESCALATED: severity 1→2",
    "last_action_error": null,
    "task_name": "single_incident",
    "max_steps": 20
  },
  "reward": 0.0,
  "done": false
}
```

**What Changed:**
- **severity**: Increased from 1 to 2
- **max_response_steps**: Reduced from 8 to 5 (higher severity = less time)
- **reward**: 0.0 (neutral action)

---

### 7. Invalid Action - No Unit Available

**Command:**
```bash
curl -X POST http://127.0.0.1:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "assign", "incident_id": "INC-001", "unit_type": "helicopter"}}'
```

**Expected Output:**
```json
{
  "observation": {
    "active_incidents": [...],
    "available_units": {
      "ambulance": 3,
      "fire_truck": 2,
      "police_car": 3,
      "hazmat_team": 1
    },
    "step_number": 1,
    "episode_score": -0.2,
    "last_action_result": "NO_UNIT_AVAILABLE",
    "last_action_error": "No helicopter units available right now.",
    "task_name": "single_incident",
    "max_steps": 20
  },
  "reward": -0.2,
  "done": false
}
```

**What Changed:**
- **reward**: -0.2 (Penalty for invalid action)
- **last_action_error**: Explains what went wrong

---

### 8. Timeout Scenario (Let Incident Age Too Long)

**Command:**
```bash
# Wait 9 times (incident times out after 8 steps for severity 1)
for i in {1..9}; do
  curl -X POST http://127.0.0.1:8000/step \
    -H "Content-Type: application/json" \
    -d '{"action": {"action_type": "wait"}}'
done
```

**Expected Output (after 9th wait):**
```json
{
  "observation": {
    "active_incidents": [
      {
        "incident_id": "INC-001",
        "incident_type": "medical",
        "severity": 1,
        "location_zone": "east",
        "age_steps": 9,
        "max_response_steps": 8,
        "assigned_unit": null,
        "resolved": false,
        "timed_out": true
      }
    ],
    "available_units": {...},
    "step_number": 9,
    "episode_score": -0.21,
    "last_action_result": "WAIT: +0.01 (no action taken)",
    "last_action_error": null,
    "task_name": "single_incident",
    "max_steps": 20
  },
  "reward": -0.29,
  "done": false
}
```

**What Changed:**
- **timed_out**: true (incident failed)
- **reward**: Large negative penalty (~-0.3) for timeout
- **age_steps** > **max_response_steps**: Missed deadline

---

## Reward Structure Summary

| Action | Reward Range | Notes |
|--------|--------------|-------|
| Correct Assignment | +0.05 to +0.40 | Higher for critical incidents |
| Wrong Assignment | -0.10 to -0.40 | Bigger penalty for critical |
| Close Incident | +0.15 to +0.50 | Speed bonus for fast resolution |
| Timeout Penalty | -0.30 to -1.00 | Severe for critical incidents |
| Wait | +0.01 | Very small reward |
| Invalid Action | -0.20 | Fixed penalty |
| Escalate | 0.00 | Neutral |

## Incident Type to Unit Mapping

| Incident Type | Correct Unit | Wrong Units |
|---------------|--------------|-------------|
| medical | ambulance | fire_truck, police_car, hazmat_team |
| fire | fire_truck | ambulance, police_car, hazmat_team |
| crime | police_car | ambulance, fire_truck, hazmat_team |
| accident | ambulance | fire_truck, police_car, hazmat_team |
| hazmat | hazmat_team | ambulance, fire_truck, police_car |

## Episode Termination

The episode ends when:
1. **Max steps reached**: step_number >= max_steps (20 for single_incident)
2. **All incidents resolved/timed out**: No active incidents remaining

When done=true, the episode is complete.

---

## Testing Different Tasks

### Easy Task: single_incident
```bash
curl -X POST http://127.0.0.1:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task":"single_incident"}'
```
- 1 incident at a time
- Severity 1-2 (low-medium)
- New incident every 4 steps
- 20 steps total

### Medium Task: multi_incident
```bash
curl -X POST http://127.0.0.1:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task":"multi_incident"}'
```
- 3-5 simultaneous incidents
- Severity 1-3
- Requires prioritization
- 25 steps total

### Hard Task: mass_casualty
```bash
curl -X POST http://127.0.0.1:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task":"mass_casualty"}'
```
- Multiple critical incidents
- Severity 3-4 (high-critical)
- Scarce units
- Cannot save everyone
- 30 steps total

---

## Quick Test Script

Save this as `test_tactical.sh`:
```bash
#!/bin/bash

echo "=== Test 1: Reset ==="
curl -X POST http://127.0.0.1:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task":"single_incident", "seed": 42}' | jq '.observation | {step: .step_number, incidents: .active_incidents | length, score: .episode_score}'

echo -e "\n=== Test 2: Assign Ambulance ==="
curl -X POST http://127.0.0.1:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "assign", "incident_id": "INC-001", "unit_type": "ambulance"}}' | jq '{step: .observation.step_number, reward: .reward, action: .observation.last_action_result}'

echo -e "\n=== Test 3: Close Incident ==="
curl -X POST http://127.0.0.1:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "close", "incident_id": "INC-001"}}' | jq '{step: .observation.step_number, reward: .reward, score: .observation.episode_score, done: .done}'
```

Run with: `bash test_tactical.sh`
