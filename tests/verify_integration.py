import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_flow():
    # 1. Check health
    print("Checking API health...")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        print(f"Health: {resp.status_code} - {resp.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return

    # 2. Submit a bug
    print("\nSubmitting a bug...")
    bug_data = {
        "title": "System crash on login",
        "body": "The system crashes immediately when a user tries to log in with valid credentials.",
        "priority": "critical"
    }
    resp = requests.post(f"{BASE_URL}/predict", json=bug_data)
    print(f"Predict Status: {resp.status_code}")
    if resp.status_code == 200:
        prediction = resp.json()
        print(f"Bug ID: {prediction['bug_id']}")
        print(f"Auto-Assigned: {prediction['is_auto_assigned']}")
        print(f"Top Developer: {prediction['predictions'][0]['developer']}")

    # 3. Check Bug History
    print("\nChecking Bug History...")
    resp = requests.get(f"{BASE_URL}/bugs")
    print(f"Bugs: {len(resp.json())} found")
    
    # 4. Check Stats
    print("\nChecking Dashboard Stats...")
    resp = requests.get(f"{BASE_URL}/stats")
    print(f"Stats: {resp.json()}")

if __name__ == "__main__":
    test_flow()
