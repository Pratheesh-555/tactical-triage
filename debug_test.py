"""Quick debug script to test environment connection"""
import asyncio
import json
import sys
from tactical_triage_env.client import TacticalTriageEnv
from tactical_triage_env.models import TacticalAction

async def test_env():
    try:
        env = TacticalTriageEnv(base_url="http://localhost:8000")
        print("[OK] Client created")

        async with env:
            print("[OK] Connected to environment")

            # Test reset
            result = await env.reset(task="single_incident")
            obs = result.observation
            print(f"[OK] Reset successful - Step: {obs.step_number}")
            print(f"     Active incidents: {len(obs.active_incidents)}")
            print(f"     Available units: {obs.available_units}")

            # Test step
            if obs.active_incidents:
                inc = obs.active_incidents[0]
                action = TacticalAction(
                    action_type="assign",
                    incident_id=inc["incident_id"],
                    unit_type="ambulance"
                )
                print(f"\n[ACTION] Testing action: assign ambulance to {inc['incident_id']}")
                result = await env.step(action)
                obs = result.observation
                print(f"[OK] Step successful!")
                print(f"     Reward: {result.reward}")
                print(f"     Step: {obs.step_number}")
                print(f"     Last Action: {obs.last_action_result}")
                if obs.last_action_error:
                    print(f"     Error: {obs.last_action_error}")
                
                # Test close action
                action2 = TacticalAction(
                    action_type="close",
                    incident_id=inc["incident_id"]
                )
                print(f"\n[ACTION] Testing close action for {inc['incident_id']}")
                result2 = await env.step(action2)
                obs2 = result2.observation
                print(f"[OK] Close action successful!")
                print(f"     Reward: {result2.reward}")
                print(f"     Step: {obs2.step_number}")
                print(f"     Active incidents remaining: {len(obs2.active_incidents)}")

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_env())
