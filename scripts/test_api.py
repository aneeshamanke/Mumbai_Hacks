import requests
import time
import subprocess
import sys
import os

def test_api():
    print("Starting API server...")
    # Start the API server in the background
    process = subprocess.Popen(
        [sys.executable, "api_gateway/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Wait for server to start
        print("Waiting for server to start...")
        time.sleep(5)
        
        url = "http://127.0.0.1:8000/prompts"
        payload = {
            "prompt": "What is the latest cricket news?",
            "user_id": "test_user"
        }
        
        print(f"Sending request to {url}...")
        response = requests.post(url, json=payload)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("\n--- Response ---")
            print(f"Run ID: {data['run_id']}")
            print(f"Answer: {data['provisional_answer'][:200]}...") # Truncate for brevity
            print(f"Evidence Count: {len(data['evidence'])}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        print("\nStopping API server...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_api()
