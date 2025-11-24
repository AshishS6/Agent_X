"""
Test Market Research Agent
Sends a task to the Redis queue and waits for the result
"""

import os
import sys
import json
import time
import uuid
import redis
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backend', '.env')
load_dotenv(env_path)

# Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

QUEUE_NAME = "tasks:market_research"

def test_agent():
    """Test the agent"""
    print(f"Testing Market Research Agent on {QUEUE_NAME}...")
    
    # Create task
    task_id = str(uuid.uuid4())
    task = {
        "taskId": task_id,
        "action": "market_analysis",
        "input": {
            "topic": "AI in Legal Tech",
            "depth": "standard"
        },
        "userId": "test-user",
        "priority": "high"
    }
    
    # Push to queue
    print(f"Sending task {task_id}...")
    redis_client.xadd(QUEUE_NAME, {"data": json.dumps(task)})
    
    print("Task sent! Check the worker logs for processing.")
    print("You can also check the dashboard for task status.")

if __name__ == "__main__":
    test_agent()
