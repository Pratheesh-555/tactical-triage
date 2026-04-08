"""Test script to validate the API fix."""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_reset():
    """Test the /reset endpoint."""
    print("\n=== Testing /reset endpoint ===")
    try:
        response = requests.post(
            f"{BASE_URL}/reset",
            json={"task": "single_incident"},
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            obs = data.get("observation", {})
            print(f"âœ“ Reset successful!")
            episode_id = obs.get('episode_id', 'N/A')
            print(f"  Episode ID: {episode_id}")
            print(f"  Task: {obs.get('task_name', 'N/A')}")
            print(f"  Step: {obs.get('step_number', 'N/A')}")
            print(f"  Active Incidents: {len(obs.get('active_incidents', []))}")
            return episode_id
        else:
            print(f"âœ— Reset failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print(f"âœ— Error during reset: {e}")
        return None

def test_step(episode_id=None):
    """Test the /step endpoint."""
    print("\n=== Testing /step endpoint ===")
    try:
        headers = {}
        if episode_id:
            headers["X-Episode-Id"] = episode_id
            
        response = requests.post(
            f"{BASE_URL}/step",
            json={"action": {"action_type": "wait"}},
            headers=headers,
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            obs = data.get("observation", {})
            print(f"âœ“ Step successful!")
            print(f"  Step Number: {obs.get('step_number', 'N/A')}")
            print(f"  Reward: {data.get('reward', 'N/A')}")
            print(f"  Done: {data.get('done', 'N/A')}")
            print(f"  Last Action: {obs.get('last_action_result', 'N/A')}")
            return True
        else:
            print(f"âœ— Step failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"âœ— Error during step: {e}")
        return False

def test_step_before_reset():
    """Test calling /step before /reset (should fail gracefully)."""
    print("\n=== Testing /step BEFORE /reset (should fail gracefully) ===")
    try:
        response = requests.post(
            f"{BASE_URL}/step",
            json={"action": {"action_type": "wait"}},
            headers={"X-Episode-Id": "invalid-id"},
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 500:
            print(f"âœ“ Expected 500 error returned")
            print(f"  Response: {response.text[:200]}")
            return True
        elif response.status_code == 200:
            print(f"âœ— Unexpectedly succeeded! Should require reset first.")
            return False
        else:
            print(f"? Got status {response.status_code}")
            print(f"  Response: {response.text}")
            return True
    except Exception as e:
        print(f"âœ— Error during step: {e}")
        return False

def main():
    print("="*60)
    print("API Testing Suite for Tactical Triage Fix")
    print("="*60)
    
    # Test 1: Try step without reset (should fail gracefully now)
    test_step_before_reset()
    
    # Test 2: Reset the environment
    episode_id = test_reset()
    if not episode_id:
        print("\nâŒ Reset failed. Cannot continue testing.")
        sys.exit(1)
    
    # Test 3: Try step after reset (should work)
    if not test_step(episode_id):
        print("\nâŒ Step failed after reset.")
        sys.exit(1)
    
    # Test 4: Try another step (should still work)
    if not test_step(episode_id):
        print("\nâŒ Second step failed.")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("âœ“ All tests passed!")
    print("="*60)

if __name__ == "__main__":
    main()
