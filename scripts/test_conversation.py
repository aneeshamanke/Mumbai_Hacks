import sys
import os
import json

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orchestrator.worker import OrchestratorWorker

def test_conversation():
    print("Initializing OrchestratorWorker...")
    worker = OrchestratorWorker()
    
    conversation_flows = [
        # Turn 1: Multi-tool request
        {
            "run_id": "turn_1",
            "prompt": "What is the stock price of Google and what is the weather in New York?",
            "latency_ms": 0
        },
        # Turn 2: Memory request (referring to previous context)
        {
            "run_id": "turn_2",
            "prompt": "Multiply that stock price by 10.",
            "latency_ms": 0
        }
    ]
    
    for i, job in enumerate(conversation_flows):
        print(f"\n--- Turn {i+1}: {job['prompt']} ---")
        try:
            result = worker.run(job)
            print(f"Agent Answer: {result['answer']}")
        except Exception as e:
            print(f"Error running worker: {e}")

if __name__ == "__main__":
    test_conversation()
