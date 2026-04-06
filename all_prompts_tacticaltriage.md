# TacticalTriage — All Claude Prompts
## OpenEnv Hackathon Build Guide · April 2026

> **How to use this file:**
> Copy one prompt at a time into Claude. Wait for confirmation. Verify the checklist. Then move to the next.
> Never send two prompts at once. Never skip a prompt.

---

# PROMPT 01 — Project Initialization & Environment Setup

You are going to build **TacticalTriage** — a production-grade OpenEnv RL environment simulating a 911 emergency dispatch coordination center, built for the Meta × Hugging Face OpenEnv Hackathon (deadline: April 8, 2026).

Before writing a single line of code, do the following in order. Do not skip any step. Confirm each step is done before moving to the next.

## STEP 1 — Verify Python version

```bash
python --version
```

Must be 3.10, 3.11, or 3.12.

## STEP 2 — Install all required tools

```bash
pip install openenv-core pydantic fastapi uvicorn websockets huggingface_hub openai
pip install uv
huggingface-cli --version
docker --version
openenv --version
```

## STEP 3 — Create the project folder structure EXACTLY as below

```bash
mkdir -p tactical_triage/tactical_triage_env/server

cd tactical_triage

touch inference.py README.md

touch tactical_triage_env/__init__.py
touch tactical_triage_env/client.py
touch tactical_triage_env/models.py
touch tactical_triage_env/openenv.yaml
touch tactical_triage_env/pyproject.toml

touch tactical_triage_env/server/__init__.py
touch tactical_triage_env/server/app.py
touch tactical_triage_env/server/tactical_environment.py
touch tactical_triage_env/server/scenarios.py
touch tactical_triage_env/server/graders.py
touch tactical_triage_env/server/reward_engine.py
touch tactical_triage_env/server/requirements.txt
touch tactical_triage_env/server/Dockerfile
```

## STEP 4 — Verify the structure

```bash
find tactical_triage -type f | sort
```

Expected output:
```
tactical_triage/README.md
tactical_triage/inference.py
tactical_triage/tactical_triage_env/__init__.py
tactical_triage/tactical_triage_env/client.py
tactical_triage/tactical_triage_env/models.py
tactical_triage/tactical_triage_env/openenv.yaml
tactical_triage/tactical_triage_env/pyproject.toml
tactical_triage/tactical_triage_env/server/Dockerfile
tactical_triage/tactical_triage_env/server/__init__.py
tactical_triage/tactical_triage_env/server/app.py
tactical_triage/tactical_triage_env/server/graders.py
tactical_triage/tactical_triage_env/server/requirements.txt
tactical_triage/tactical_triage_env/server/reward_engine.py
tactical_triage/tactical_triage_env/server/scenarios.py
tactical_triage/tactical_triage_env/server/tactical_environment.py
```

## STEP 5 — Initialize git

```bash
cd tactical_triage
git init
git add .
git commit -m "chore: initial scaffold — TacticalTriage OpenEnv environment"
```

## STEP 6 — Confirm HF CLI login

```bash
huggingface-cli whoami
```

## STEP 7 — Confirm Docker is running

```bash
docker info
```

## DONE — Report back with all 6 confirmations. Say "Setup complete — ready for Batch 1" and stop. Do not write any code yet.

---

# PROMPT 02 — Batch 1: Models + Client + Package Config

Setup is confirmed. Now execute Batch 1.

Write the complete, production-ready code for these 4 files. No placeholders. No TODOs. Every file must be fully working.

**Files to write in this batch:**
1. `tactical_triage_env/models.py`
2. `tactical_triage_env/client.py`
3. `tactical_triage_env/__init__.py`
4. `tactical_triage_env/pyproject.toml`

**Critical rules:**
- `Incident` must extend `pydantic.BaseModel` — NOT Action or Observation
- `TacticalAction` must extend `Action` from `openenv.core.env_server.types`
- `TacticalObservation` must extend `Observation` from `openenv.core.env_server.types`
- Every file that imports from the package must use the dual-import pattern:
```python
try:
    from tactical_triage_env.models import TacticalAction, TacticalObservation
except ImportError:
    from models import TacticalAction, TacticalObservation
```
- `TacticalObservation` must include these fields: `active_incidents`, `available_units`, `step_number`, `episode_score`, `last_action_result`, `last_action_error`, `task_name`, `max_steps`
- `TacticalAction` must include: `action_type` (assign/close/escalate/wait), `incident_id`, `unit_type`
- `Incident` must include a `from_severity()` classmethod that derives `max_response_steps` from severity

After writing all 4 files, run:
```bash
cd tactical_triage
python -c "from tactical_triage_env.models import TacticalAction, TacticalObservation, Incident; print('models OK')"
python -c "from tactical_triage_env.client import TacticalTriageEnv; print('client OK')"
python -c "from tactical_triage_env import TacticalTriageEnv, TacticalAction, TacticalObservation; print('__init__ OK')"
```

All 3 must print OK. Fix any errors before confirming.

**Checklist before confirming:**
- [ ] `models.py` — dual-import pattern present
- [ ] `Incident` has `from_severity()` classmethod
- [ ] `TacticalAction` fields: `action_type`, `incident_id`, `unit_type`
- [ ] `TacticalObservation` has all 8 required fields
- [ ] `client.py` — `TacticalTriageEnv` extends `EnvClient`
- [ ] `__init__.py` — exports all 3 public symbols
- [ ] `pyproject.toml` — `openenv-core` listed as dependency
- [ ] All 3 import tests pass

Say "Batch 1 complete" and list every file written with line counts.

---

# PROMPT 03 — Batch 2: Reward Engine + Scenarios + Graders

Batch 1 is confirmed complete. Now execute Batch 2.

Write the complete code for these 3 files:
1. `tactical_triage_env/server/reward_engine.py`
2. `tactical_triage_env/server/scenarios.py`
3. `tactical_triage_env/server/graders.py`

**Rules for reward_engine.py:**
- All 6 reward functions must return `tuple[float, str]` — (reward_value, reason_string)
- Functions: `reward_assign`, `reward_close`, `reward_timeout`, `reward_escalate`, `reward_wait`, `reward_invalid`
- `reward_assign` must check `VALID_ASSIGNMENTS` dict and return negative if wrong unit type
- Include `clamp(value, lo=-1.0, hi=1.0)` utility function
- VALID_ASSIGNMENTS: `medical→[ambulance]`, `fire→[fire_truck, ambulance]`, `crime→[police_car]`, `accident→[ambulance, police_car, fire_truck]`, `hazmat→[hazmat_team, fire_truck]`

**Rules for scenarios.py:**
- All 3 scenario functions: `scenario_single_incident`, `scenario_multi_incident`, `scenario_mass_casualty`
- EVERY scenario must use `random.Random(seed)` — NOT `random.seed()` — for full reproducibility
- `ScenarioConfig` must be a `NamedTuple` with fields: `task_name`, `max_steps`, `unit_return_steps`, `initial_incidents`, `new_incident_schedule`, `unit_pool`
- `new_incident_schedule` is `dict[int, list[Incident]]` — step number maps to list of new incidents
- mass_casualty must have a scarce unit pool (fewer units than other tasks)
- `SCENARIO_REGISTRY` dict must exist: `{"single_incident": fn, "multi_incident": fn, "mass_casualty": fn}`

**Rules for graders.py:**
- All 3 graders: `grade_single_incident`, `grade_multi_incident`, `grade_mass_casualty`
- Every grader takes `history: dict` and returns `float` in `[0.0, 1.0]`
- history keys used: `total_reward`, `max_possible_reward`, `incidents_total`, `incidents_resolved`, `incidents_timed_out`, `wrong_assignments`, `correct_assignments`, `critical_incidents`, `critical_resolved`, `steps_taken`, `max_steps`
- `grade_mass_casualty` must weight critical incident resolution heavily (30%+)
- `GRADER_REGISTRY` dict must exist
- All returned values must be clamped to [0.0, 1.0] and rounded to 4 decimal places

After writing, run these tests:
```bash
cd tactical_triage
python -c "
from tactical_triage_env.server.reward_engine import reward_assign, reward_close, reward_timeout, reward_wait, reward_invalid, clamp
r, msg = reward_assign('medical', 'ambulance', 3)
assert r > 0, f'correct assign should be positive, got {r}'
r2, msg2 = reward_assign('medical', 'police_car', 3)
assert r2 < 0, f'wrong assign should be negative, got {r2}'
print('reward_engine OK')
"

python -c "
from tactical_triage_env.server.scenarios import SCENARIO_REGISTRY
for name, fn in SCENARIO_REGISTRY.items():
    s1 = fn(seed=42)
    s2 = fn(seed=42)
    assert s1.initial_incidents[0].incident_id == s2.initial_incidents[0].incident_id, f'{name} not reproducible'
    print(f'{name}: {len(s1.initial_incidents)} initial incidents, max_steps={s1.max_steps}')
print('scenarios OK — all reproducible')
"

python -c "
from tactical_triage_env.server.graders import GRADER_REGISTRY
dummy = {'total_reward': 2.0, 'max_possible_reward': 5.0, 'incidents_total': 5, 'incidents_resolved': 3, 'incidents_timed_out': 1, 'wrong_assignments': 1, 'correct_assignments': 4, 'critical_incidents': 2, 'critical_resolved': 1, 'steps_taken': 20, 'max_steps': 25}
for name, fn in GRADER_REGISTRY.items():
    score = fn(dummy)
    assert 0.0 <= score <= 1.0, f'{name} returned {score} outside [0,1]'
    print(f'{name}: {score:.4f}')
print('graders OK')
"
```

All tests must pass. Fix any failures before confirming.

**Checklist before confirming:**
- [ ] All reward functions return `(float, str)` tuples
- [ ] `clamp()` function exists
- [ ] All scenarios use `random.Random(seed)` not `random.seed()`
- [ ] `ScenarioConfig` is a NamedTuple
- [ ] `SCENARIO_REGISTRY` has all 3 keys
- [ ] `GRADER_REGISTRY` has all 3 keys
- [ ] All graders return float in [0.0, 1.0]
- [ ] All 3 test blocks pass without errors

Say "Batch 2 complete" and list every file written with line counts.

---

# PROMPT 04 — Batch 3: Main Environment Class

Batch 2 is confirmed complete. Now execute Batch 3.

Write the complete code for:
1. `tactical_triage_env/server/tactical_environment.py`

This is the most critical file. It must be complete, production-ready, with zero TODOs.

**The class `TacticalEnvironment` must:**
- Extend `Environment` from `openenv.core.env_server.interfaces`
- Implement `reset(seed=None, task=None) → TacticalObservation`
- Implement `step(action: TacticalAction) → StepResult`
- Implement `state() → State`
- Implement `get_episode_grade() → float` (calls the correct grader)

**reset() must:**
- Accept optional `seed: int` and `task: str` parameters
- Load the correct scenario from `SCENARIO_REGISTRY`
- Deep copy all incidents from scenario (never mutate scenario objects)
- Initialize `_history` dict with all required keys
- Initialize `_available_units` from scenario unit_pool
- Initialize `_busy_units` as empty list
- Return a clean `TacticalObservation`
- Use `State(episode_id=str(uuid4()), step_count=0)` for fresh state

**step() must do these in order every step:**
1. Increment `step_count`
2. Age all active incidents + collect timeout penalties
3. Release units whose return step has been reached
4. Spawn new incidents from schedule if any due this step
5. Process the agent's action (assign/close/escalate/wait)
6. Combine all rewards with `clamp()`
7. Accumulate into `episode_score` and `_history["total_reward"]`
8. Check done condition: `step >= max_steps OR all incidents terminal`
9. Return `StepResult(observation=obs, reward=step_reward, done=done, info={...})`

**Episode termination:**
- `step >= scenario.max_steps` OR
- All incidents are either `resolved=True` or `timed_out=True`

**Unit management:**
- When a unit is assigned: decrement `_available_units[unit_type]`
- Append `(unit_type, current_step + unit_return_steps)` to `_busy_units`
- Each step: check `_busy_units` — if `return_at <= current_step`, increment `_available_units[unit_type]` and remove from list

**History tracking — update these keys as events happen:**
- `total_reward` — running sum
- `incidents_total` — increment when new incident spawned
- `incidents_resolved` — increment on successful close
- `incidents_timed_out` — increment when incident times out
- `correct_assignments` — increment on valid assignment
- `wrong_assignments` — increment on wrong unit type
- `critical_incidents` — increment when severity=4 incident spawns
- `critical_resolved` — increment when severity=4 incident closed
- `steps_taken` — update each step

**Dual-import pattern required in this file:**
```python
try:
    from tactical_triage_env.models import TacticalAction, TacticalObservation, Incident
    from server.reward_engine import ...
    from server.scenarios import ...
    from server.graders import ...
except ImportError:
    from models import TacticalAction, TacticalObservation, Incident
    from reward_engine import ...
    from scenarios import ...
    from graders import ...
```

After writing, run this full integration test:
```bash
cd tactical_triage
python -c "
import sys
sys.path.insert(0, 'tactical_triage_env')
from tactical_triage_env.server.tactical_environment import TacticalEnvironment
from tactical_triage_env.models import TacticalAction

env = TacticalEnvironment()

# Test all 3 tasks
for task in ['single_incident', 'multi_incident', 'mass_casualty']:
    obs = env.reset(seed=42, task=task)
    assert obs.task_name == task, f'task name mismatch: {obs.task_name}'
    assert len(obs.active_incidents) > 0, f'no incidents on reset for {task}'
    assert obs.step_number == 0

    # Run a few steps
    for i in range(3):
        if obs.active_incidents:
            inc = obs.active_incidents[0]
            action = TacticalAction(
                action_type='assign',
                incident_id=inc['incident_id'],
                unit_type=list(obs.available_units.keys())[0]
            )
        else:
            action = TacticalAction(action_type='wait', incident_id='', unit_type=None)
        result = env.step(action)
        obs = result.observation
        assert -1.0 <= result.reward <= 1.0, f'reward out of range: {result.reward}'

    grade = env.get_episode_grade()
    assert 0.0 <= grade <= 1.0, f'grade out of range: {grade}'
    print(f'{task}: steps={obs.step_number}, score={obs.episode_score:.3f}, grade={grade:.4f} OK')

print('TacticalEnvironment integration test PASSED')
"
```

All tasks must pass. Fix any failures before confirming.

**Checklist before confirming:**
- [ ] `TacticalEnvironment` extends `Environment`
- [ ] `reset()` deep copies all incidents
- [ ] `reset()` initializes all `_history` keys
- [ ] `step()` processes in the correct 9-step order
- [ ] Timeout detection happens BEFORE action processing
- [ ] Unit return happens BEFORE action processing
- [ ] Incident spawning happens BEFORE action processing
- [ ] `done` condition checks both max_steps AND all-terminal
- [ ] `get_episode_grade()` exists and calls grader
- [ ] Dual-import pattern present
- [ ] Integration test passes for all 3 tasks

Say "Batch 3 complete" and list file written with line count.

---

# PROMPT 05 — Batch 4: FastAPI App + Dockerfile + openenv.yaml

Batch 3 is confirmed complete. Now execute Batch 4.

Write the complete code for these 4 files:
1. `tactical_triage_env/server/app.py`
2. `tactical_triage_env/server/requirements.txt`
3. `tactical_triage_env/server/Dockerfile`
4. `tactical_triage_env/openenv.yaml`

**Rules for app.py:**
- Use `create_app` from `openenv.core.env_server`
- Pattern: `app = create_app(TacticalEnvironment, TacticalAction, TacticalObservation, env_name="tactical_triage_env")`
- Dual-import pattern required
- Nothing else — keep it minimal

**Rules for requirements.txt:**
```
openenv-core>=0.1.0
pydantic>=2.0
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
websockets>=12.0
```

**Rules for Dockerfile:**
- Start with `FROM ghcr.io/meta-pytorch/openenv-base:latest`
- If that image is unavailable during build, fall back to `FROM python:3.11-slim` and add `RUN pip install openenv-core`
- `WORKDIR /app`
- Copy `server/requirements.txt` first (layer caching)
- `RUN pip install --no-cache-dir -r /app/requirements.txt`
- Copy `tactical_triage_env/` to `/app/tactical_triage_env/`
- Copy `server/` to `/app/server/`
- ENV defaults: `TACTICAL_TASK=single_incident`, `PORT=8000`, `HOST=0.0.0.0`, `WORKERS=1`
- `EXPOSE 8000`
- CMD: `uvicorn server.app:app --host $HOST --port $PORT --workers $WORKERS`

**Rules for openenv.yaml:**
- `spec_version: 1`
- `name: tactical_triage_env`
- `type: environment`
- `runtime: docker`
- `app: server/app.py`
- `port: 8000`
- Must list all 3 tasks with `name`, `description`, `difficulty`, `max_steps`

After writing, run these tests:
```bash
cd tactical_triage

# Test 1: Import app
python -c "
import sys
sys.path.insert(0, 'tactical_triage_env')
from tactical_triage_env.server.app import app
print('app import OK')
"

# Test 2: Docker build
docker build -f tactical_triage_env/server/Dockerfile -t tactical-triage:test .
echo "Docker build exit code: $?"

# Test 3: Run container + health check
docker run -d --name tt-test -p 8001:8000 tactical-triage:test
sleep 5
curl -s http://localhost:8001/health
echo ""
curl -s -X POST http://localhost:8001/reset \
  -H "Content-Type: application/json" -d '{}'
echo ""

# Test 4: openenv validate
cd tactical_triage_env
openenv validate
cd ..

# Cleanup
docker stop tt-test && docker rm tt-test
```

All 4 tests must pass. Fix any failures before confirming.

**Checklist before confirming:**
- [ ] `app.py` uses `create_app` factory pattern
- [ ] `requirements.txt` has all 5 dependencies
- [ ] `Dockerfile` builds without error
- [ ] Container starts and `/health` returns `{"status": "healthy"}`
- [ ] `/reset` returns 200 with observation JSON
- [ ] `openenv validate` passes
- [ ] `openenv.yaml` has `spec_version: 1` and all 3 tasks listed

Say "Batch 4 complete" and show the output of `openenv validate`.

---

# PROMPT 06 — Batch 5: Inference Script

Batch 4 is confirmed complete. Now execute Batch 5.

Write the complete code for:
1. `inference.py` — at project root, NOT inside tactical_triage_env/

This is the mandatory hackathon inference script. It must follow the exact stdout format specification.

**Mandatory stdout format — no deviations allowed:**
```
[START] task=<task_name> env=tactical_triage_env model=<model_name>
[STEP] step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
[END] success=<true|false> steps=<n> score=<0.000> rewards=<r1,r2,...,rn>
```

**Rules:**
- `reward` in `[STEP]` formatted to exactly 2 decimal places
- `done` and `success` are lowercase: `true` or `false`
- `error` is the raw `last_action_error` string, or `null`
- `score` in `[END]` formatted to exactly 3 decimal places
- `rewards` in `[END]` is comma-separated, each to 2 decimal places
- `[END]` must ALWAYS be emitted — even if an exception occurs — use try/finally
- One `[START]` per task episode
- One `[STEP]` per step, immediately after `env.step()` returns
- Runs all 3 tasks in sequence: `single_incident`, `multi_incident`, `mass_casualty`

**Environment variables to read:**
```python
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
IMAGE_NAME   = os.getenv("LOCAL_IMAGE_NAME", "")
```

**LLM interaction rules:**
- Use `OpenAI` client (not any other client)
- System prompt must explain: unit types, valid assignments, action JSON format, prioritization strategy
- User prompt must show: active incidents sorted by severity DESC, available units, step number, last result, last error, recent history
- Agent responds with a single JSON object — parse it safely, fall back to `wait` on any parse error
- Temperature: 0.2 (low — we want deterministic dispatch decisions)

**Score calculation:**
- Call `env.get_episode_grade()` if accessible through the client
- Fallback: `episode_score / max_steps` clamped to [0.0, 1.0]
- `success = score >= 0.3`

**Action string format for [STEP] log:**
```
assign(incident=INC-001,unit=ambulance)
close(incident=INC-001,unit=null)
wait(incident=,unit=null)
```

After writing, run this validation:
```bash
cd tactical_triage

# Test 1: Script exists at root
ls -la inference.py

# Test 2: Syntax check
python -m py_compile inference.py && echo "syntax OK"

# Test 3: Dry run with mock (no real API needed)
MOCK_RUN=1 python -c "
import inference
print('inference.py imports OK')
"

# Test 4: Check stdout format with a short run (requires server running)
# Start server in background first:
docker run -d --name tt-inf -p 8000:8000 tactical-triage:test
sleep 5
export HF_TOKEN=test_token_placeholder
export API_BASE_URL=http://localhost:8000
python inference.py 2>&1 | head -20
docker stop tt-inf && docker rm tt-inf
```

**Checklist before confirming:**
- [ ] `inference.py` is at root level
- [ ] All 3 env vars read correctly
- [ ] `log_start`, `log_step`, `log_end` match exact format
- [ ] `[END]` inside `finally` block
- [ ] All 3 tasks run in sequence
- [ ] Score clamped to [0.0, 1.0]
- [ ] Action fallback to `wait` on LLM/parse error
- [ ] Uses `OpenAI` client

Say "Batch 5 complete" and show the first 10 lines of `inference.py`.

---

# PROMPT 07 — Batch 6: README + Final Validation

Batch 5 is confirmed complete. Now execute Batch 6 — the final batch.

Write the complete `README.md` at project root, then run the full pre-submission validation sequence.

**README.md must include (in order):**
1. Project title + badge: `[![OpenEnv](https://img.shields.io/badge/OpenEnv-spec%20v1-blue)](https://github.com/meta-pytorch/OpenEnv)`
2. One paragraph description — what it is, why it matters
3. Action space table
4. Observation space JSON example
5. Tasks table (name, difficulty, max_steps, description)
6. Reward function table (all 6 reward types with values)
7. Baseline scores table (estimated scores per task)
8. Setup instructions (install, run locally, run inference, docker, deploy)
9. Validate submission section
10. Deploy to HF Spaces section

**After writing README.md, run the complete validation sequence:**

```bash
cd tactical_triage

echo "=== 1. openenv validate ==="
cd tactical_triage_env && openenv validate && cd ..

echo "=== 2. Docker build ==="
docker build -f tactical_triage_env/server/Dockerfile -t tactical-triage:final .

echo "=== 3. Start container ==="
docker run -d --name tt-final -p 8000:8000 tactical-triage:final
sleep 8

echo "=== 4. Health check ==="
curl -s http://localhost:8000/health

echo "=== 5. Reset test ==="
curl -s -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" -d '{}'

echo "=== 6. Step test ==="
curl -s -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action_type": "wait", "incident_id": "", "unit_type": null}'

echo "=== 7. State test ==="
curl -s http://localhost:8000/state

echo "=== 8. Inference syntax ==="
python -m py_compile inference.py && echo "inference.py syntax OK"

echo "=== 9. File structure check ==="
find . -type f | grep -v __pycache__ | grep -v .git | sort

echo "=== 10. Cleanup ==="
docker stop tt-final && docker rm tt-final

echo "=== ALL CHECKS DONE ==="
```

Every check must pass with no errors. For any failure, fix it and re-run that specific check.

**Final checklist — ALL must be true before submitting:**
- [ ] `openenv validate` passes
- [ ] `docker build` succeeds
- [ ] `/health` returns `{"status": "healthy"}`
- [ ] `/reset` returns 200 with `active_incidents` in response
- [ ] `/step` returns 200 with `reward` in response
- [ ] `/state` returns 200
- [ ] `inference.py` syntax clean
- [ ] All 15 files exist at correct paths
- [ ] README.md has all 10 required sections

Say "Batch 6 complete — TacticalTriage is ready to deploy" and show the output of all 9 checks.

---

# PROMPT 08 — Deploy to Hugging Face Spaces

All 6 batches confirmed complete. Now deploy.

Run the following in order:

```bash
cd tactical_triage

# Step 1: Login to HF (if not already)
huggingface-cli whoami

# Step 2: Push to HF Spaces
cd tactical_triage_env
openenv push --repo-id YOUR_HF_USERNAME/tactical-triage

# Step 3: Wait for build (check HF Spaces dashboard)
# Go to: https://huggingface.co/spaces/YOUR_HF_USERNAME/tactical-triage
# Wait until status shows "Running" (not "Building")

# Step 4: Health check on live space
curl -s https://YOUR_HF_USERNAME-tactical-triage.hf.space/health

# Step 5: Live reset test
curl -s -X POST https://YOUR_HF_USERNAME-tactical-triage.hf.space/reset \
  -H "Content-Type: application/json" -d '{}'

# Step 6: Run validation script against live space
chmod +x validate-submission.sh
./validate-submission.sh https://YOUR_HF_USERNAME-tactical-triage.hf.space .

# Step 7: Run inference against live space
export HF_TOKEN=your_actual_token
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export DISPATCH_ENV_URL=https://YOUR_HF_USERNAME-tactical-triage.hf.space
python inference.py
```

Replace `YOUR_HF_USERNAME` with your actual Hugging Face username everywhere.

**All 7 steps must succeed.** If the Space fails to build, check the build logs on HF dashboard and fix any Docker/import errors.

After all steps pass, report:
1. Live space URL
2. Output of `/health` check
3. First 5 lines of `inference.py` output
4. Validation script result (PASSED or FAILED with reason)

Say "TacticalTriage deployed and live at: <url>"

---

# PROMPT 09 — Fix & Troubleshoot (use only if something breaks)

Something failed. Here is how to diagnose and fix it.

## If `openenv validate` fails:
```bash
cd tactical_triage_env
openenv validate --verbose
```
Read the error carefully. Common fixes:
- Missing `spec_version: 1` in openenv.yaml → add it
- Wrong `app:` path → must be `server/app.py`
- Missing task fields → each task needs `name` and `description`

## If Docker build fails:
```bash
docker build -f tactical_triage_env/server/Dockerfile -t tactical-triage:debug . 2>&1 | tail -30
```
Common fixes:
- `ghcr.io/meta-pytorch/openenv-base` not available → change to `python:3.11-slim` and add `RUN pip install openenv-core`
- Import error → check dual-import pattern in all server files
- Missing file → check all COPY paths in Dockerfile

## If `/reset` returns 500:
```bash
docker run --name tt-debug -p 8000:8000 tactical-triage:debug
# In another terminal:
curl -s -X POST http://localhost:8000/reset -H "Content-Type: application/json" -d '{}'
docker logs tt-debug
```
Read the stack trace in docker logs.

## If inference.py fails:
```bash
python -m py_compile inference.py
python -c "import inference" 2>&1
```
Common fixes:
- Import path issues → ensure `tactical_triage_env` is in sys.path
- JSON parse error → add try/except around `json.loads`
- API connection error → check `API_BASE_URL` and `HF_TOKEN`

## If HF Space won't start:
- Check Space logs on HF dashboard (Settings → Logs)
- Common issue: Dockerfile path wrong → must be `server/Dockerfile`
- Common issue: Port mismatch → Space must expose port 7860, remap to 8000 internally

## After fixing any issue:
Re-run only the specific check that failed, then continue.

---

# PROMPT 10 — New Chat Continuation Summary

**Use this prompt to resume in a new chat after hitting the 20-message limit.**

---

I am building **TacticalTriage** — a production-grade OpenEnv RL environment for the Meta × Hugging Face OpenEnv Hackathon (deadline: April 8, 2026).

**What it is:** 911 emergency dispatch coordination environment. Agent triages incidents, assigns responder units (ambulance, fire_truck, police_car, hazmat_team), manages unit scarcity, handles cascading crises.

**Tech stack:** Python 3.11, openenv-core, FastAPI, Pydantic v2, Docker, HF Spaces

**Project structure:**
```
tactical_triage/
├── inference.py
├── README.md
└── tactical_triage_env/
    ├── __init__.py       ← exports TacticalTriageEnv, TacticalAction, TacticalObservation
    ├── client.py         ← EnvClient subclass
    ├── models.py         ← Pydantic models with dual-import pattern
    ├── openenv.yaml      ← spec_version:1, 3 tasks
    ├── pyproject.toml
    └── server/
        ├── app.py        ← create_app(TacticalEnvironment, TacticalAction, TacticalObservation)
        ├── tactical_environment.py  ← main env class
        ├── scenarios.py  ← 3 deterministic scenarios (seeded RNG)
        ├── graders.py    ← 3 graders returning float in [0,1]
        ├── reward_engine.py  ← 6 reward functions returning (float, str)
        ├── requirements.txt
        └── Dockerfile
```

**3 tasks:**
- `single_incident` — easy, 20 steps, 1 incident at a time
- `multi_incident` — medium, 25 steps, 3-5 simultaneous
- `mass_casualty` — hard, 30 steps, critical scarcity, ruthless triage

**Key patterns:**
- Dual-import: `try: from tactical_triage_env.models import X / except ImportError: from models import X`
- `create_app(TacticalEnvironment, TacticalAction, TacticalObservation)` in app.py
- Rewards returned inside observation (openenv pattern)
- inference.py stdout: `[START]` / `[STEP]` / `[END]` exact format
- Score clamped to [0.0, 1.0]

**Current status:** [TELL CLAUDE WHICH BATCH YOU ARE ON AND WHAT THE LAST ERROR WAS IF ANY]

Please continue from where we left off. The full PRD with all code specs is in the file `emergency_dispatch_triage_PRD.md` — refer to it for all implementation details.
