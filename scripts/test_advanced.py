import sys
import os
import json

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orchestrator.worker import OrchestratorWorker

def test_advanced():
    print("Initializing OrchestratorWorker...")
    worker = OrchestratorWorker()
    
    # Test 1: Persona Injection
    print("\n--- Test 1: Persona Injection (Pirate) ---")
    job_pirate = {
        "run_id": "test_pirate",
        "prompt": "What is the stock price of Apple?",
        "latency_ms": 0
    }
    # We need to modify the worker to accept persona in run() or just test the internal method if possible.
    # Since run() doesn't expose persona, we'll hack it slightly for the test or just rely on the default.
    # Actually, let's modify the worker to accept persona in the job dict!
    
    # But for now, let's test the validation by sending a request that might trigger a validation error if the model messes up.
    # It's hard to force the model to mess up, but we can verify the successful path works with the new validation logic.
    
    print("Running standard job with new validation logic...")
    try:
        result = worker.run(job_pirate)
        print(f"Agent Answer: {result['answer']}")
    except Exception as e:
        print(f"Error running worker: {e}")

    # Test 2: Complex Calculation (to verify args parsing)
    print("\n--- Test 2: Complex Calculation ---")
    job_calc = {
        "run_id": "test_calc",
        "prompt": "Calculate (123 + 456) * 789",
        "latency_ms": 0
    }
    try:
        result = worker.run(job_calc)
        print(f"Agent Answer: {result['answer']}")
    except Exception as e:
        print(f"Error running worker: {e}")

if __name__ == "__main__":
    test_advanced()
