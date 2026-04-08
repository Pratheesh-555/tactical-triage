"""
TacticalTriage — Mandatory Inference Script.
Coordinates RL environment with an LLM agent and logs trajectory.
"""

import os
import json
import time
import sys
import traceback
from typing import List, Optional

from pydantic import ValidationError

# Adding tactical_triage_env to path if not installed
sys.path.append(os.path.abspath("tactical_triage_env"))

try:
    from tactical_triage_env import TacticalTriageEnv, TacticalAction
except ImportError:
    # Try local import if package structure is different locally
    from client import TacticalTriageEnv
    from models import TacticalAction

# --- Configuration ---
from openai import OpenAI
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

# Optional - if you use from_docker_image():
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
ENV_URL = os.getenv("DISPATCH_ENV_URL", "http://localhost:8000")

# --- Logging Helpers ---
def log_start(task: str, model: str):
    print(f"[START] task={task} env=tactical_triage_env model={model}")

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]):
    done_str = "true" if done else "false"
    error_str = f'"{error}"' if error else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_str} error={error_str}")

def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    success_str = "true" if success else "false"
    rewards_str = ",".join([f"{r:.2f}" for r in rewards])
    print(f"[END] success={success_str} steps={steps} score={score:.3f} rewards={rewards_str}")

# --- LLM Logic ---
SYSTEM_PROMPT = """You are an Emergency Dispatch AI. Your goal is to triage and assign units.
Units:
- ambulance: medical, accident (priority: high)
- fire_truck: fire, accident, hazmat (priority: critical)
- police_car: crime, accident (priority: high)
- hazmat_team: hazmat (priority: critical)

Strategy:
1. Always prioritize Critical (4) and High (3) severity incidents.
2. An incident must be assigned a valid unit type before it can be closed.
3. Once assigned, use the "close" action to resolve it in the next step.
4. "escalate" only if an incident is not already at severity 4 and you lack units now.

Response Format (JSON only):
{"action_type": "assign", "incident_id": "INC-001", "unit_type": "ambulance"}
{"action_type": "close", "incident_id": "INC-001"}
{"action_type": "wait"}
"""

def get_action_from_llm(client: OpenAI, obs_json: dict) -> TacticalAction:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Observations:\n{json.dumps(obs_json, indent=2)}"}
            ],
            temperature=0.2,
            max_tokens=256
        )
        content = response.choices[0].message.content.strip()
        # Extract JSON if returned within markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        data = json.loads(content)
        return TacticalAction(**data)
    except Exception as e:
        # Fallback to wait action on any LLM or parse failure
        return TacticalAction(action_type="wait")

def action_to_str(action: TacticalAction) -> str:
    # Format: assign(incident=INC-001,unit=ambulance)
    # Format: close(incident=INC-001,unit=null)
    # Format: wait(incident=,unit=null)
    a_type = action.action_type or "wait"
    i_id = action.incident_id or ""
    u_type = action.unit_type or "null"
    return f"{a_type}(incident={i_id},unit={u_type})"

# --- Episode Runner ---
async def run_episode(task_name: str):
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    env = TacticalTriageEnv(base_url=ENV_URL)
    
    rewards = []
    steps = 0
    score = 0.0
    success = False
    
    log_start(task_name, MODEL_NAME)
    
    try:
        async with env:
            # Task name passed as a keyword argument in kwargs
            # openenv reset expects (seed, episode_id, **kwargs)
            reset_result = await env.reset(task=task_name)
            obs = reset_result.observation
            
            while True:
                # Prepare data for LLM
                obs_dict = obs.model_dump()
                action = get_action_from_llm(client, obs_dict)
                
                step_result = await env.step(action)
                obs = step_result.observation
                
                rewards.append(step_result.reward or 0.0)
                steps += 1
                
                log_step(
                    step=steps,
                    action=action_to_str(action),
                    reward=step_result.reward or 0.0,
                    done=step_result.done,
                    error=obs.last_action_error
                )
                
                if step_result.done:
                    break
            
            # Final scoring
            # Optional: score = await env.get_episode_grade() if implemented in client
            # For now, use cumulative score or server's internal state if reachable
            # We can use the episode_score from the last observation
            score = obs.episode_score / max(1, steps) 
            score = max(0.0, min(1.0, score)) # Clamp to [0,1]
            success = score >= 0.3
            
    except Exception as e:
        # In case of environment error, ensure [END] is still logged
        print(f"Error during episode: {traceback.format_exc()}", file=sys.stderr)
    finally:
        log_end(success, steps, score, rewards)

# --- Main ---
import asyncio

async def main():
    tasks = ["single_incident", "multi_incident", "mass_casualty"]
    # Check if a specific task was requested via environment variable
    requested_task = os.getenv("DISPATCH_TASK")
    if requested_task in tasks:
        tasks = [requested_task]
        
    for task in tasks:
        await run_episode(task)

if __name__ == "__main__":
    if os.getenv("MOCK_RUN") == "1":
        print("inference.py imports OK")
    else:
        asyncio.run(main())
