import redis
import json
import uuid
import time
import os
from dotenv import load_dotenv

load_dotenv("backend/.env")

redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)

task_id = str(uuid.uuid4())
stream_key = "tasks:market_research"

task_payload = {
    "taskId": task_id,
    "action": "site_scan",
    "input": {
        "topic": "https://www.opencapital.co.in/",
        "filters": {"business_name": "Open Capital"}
    },
    "userId": "test_user_001",
    "priority": "high"
}

print(f"Pushing task {task_id} to {stream_key}...")
redis_client.xadd(stream_key, {"data": json.dumps(task_payload)})
print("Task pushed. Check worker output.")
