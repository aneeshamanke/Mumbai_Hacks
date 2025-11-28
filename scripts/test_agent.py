import sys
import os
import json

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orchestrator.worker import OrchestratorWorker

def test_agent():
    print("Initializing OrchestratorWorker...")
    worker = OrchestratorWorker()
    
    # Mock job
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is the stock price of Apple?"
    job = {
        "run_id": "test_run_001",
        "prompt": prompt,
        "latency_ms": 0
    }
    
    print(f"Running job: {job}")
    try:
        result = worker.run(job)
        print("\n--- Result ---")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error running worker: {e}")

if __name__ == "__main__":
    test_agent()
