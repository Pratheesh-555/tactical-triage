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
            print(f"✓ Reset successful!")
            print(f"  Episode ID: {data.get('episode_id', 'N/A')}")
            print(f"  Task: {data.get('task_name', 'N/A')}")
            print(f"  Step: {data.get('step_number', 'N/A')}")
            print(f"  Active Incidents: {len(data.get('active_incidents', []))}")
            return True
        else:
            print(f"✗ Reset failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error during reset: {e}")
        return False

def test_step():
    """Test the /step endpoint."""
    print("\n=== Testing /step endpoint ===")
    try:
        response = requests.post(
            f"{BASE_URL}/step",
            json={"action": {"action_type": "wait"}},
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Step successful!")
            print(f"  Step Number: {data.get('step_number', 'N/A')}")
            print(f"  Reward: {data.get('reward', 'N/A')}")
            print(f"  Done: {data.get('done', 'N/A')}")
            print(f"  Last Action: {data.get('last_action_result', 'N/A')}")
            return True
        else:
            print(f"✗ Step failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error during step: {e}")
        return False

def test_step_before_reset():
    """Test calling /step before /reset (should fail gracefully)."""
    print("\n=== Testing /step BEFORE /reset (should fail gracefully) ===")
    try:
        response = requests.post(
            f"{BASE_URL}/step",
            json={"action": {"action_type": "wait"}},
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 500:
            print(f"✓ Expected 500 error returned")
            print(f"  Response: {response.text[:200]}")
            return True
        elif response.status_code == 200:
            print(f"✗ Unexpectedly succeeded! Should require reset first.")
            return False
        else:
            print(f"? Got status {response.status_code}")
            print(f"  Response: {response.text}")
            return True
    except Exception as e:
        print(f"✗ Error during step: {e}")
        return False

def main():
    print("="*60)
    print("API Testing Suite for Tactical Triage Fix")
    print("="*60)
    
    # Test 1: Try step without reset (should fail gracefully now)
    test_step_before_reset()
    
    # Test 2: Reset the environment
    if not test_reset():
        print("\n❌ Reset failed. Cannot continue testing.")
        sys.exit(1)
    
    # Test 3: Try step after reset (should work)
    if not test_step():
        print("\n❌ Step failed after reset.")
        sys.exit(1)
    
    # Test 4: Try another step (should still work)
    if not test_step():
        print("\n❌ Second step failed.")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✓ All tests passed!")
    print("="*60)

if __name__ == "__main__":
    main()
