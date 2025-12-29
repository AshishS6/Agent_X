"""
Redis Queue Worker for Sales Agent
Listens for tasks on Redis queue and processes them
"""

import os
import sys
import json
import time
import logging
from dotenv import load_dotenv
import redis

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.base_agent import TaskInput
from shared.db_utils import update_task_status, save_conversation_message, get_agent_by_type
from main import create_sales_agent

# Load environment variables
# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backend', '.env')
load_dotenv(env_path)

# Load local agent env if exists (overrides backend)
local_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(local_env_path):
    load_dotenv(local_env_path, override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SalesAgent.Worker")

# Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Queue name
QUEUE_NAME = "tasks:sales"


def process_task(task_data: dict):
    """Process a single task"""
    try:
        # Parse task
        task_input = TaskInput(
            task_id=task_data["taskId"],
            action=task_data["action"],
            input_data=task_data["input"],
            user_id=task_data.get("userId"),
            priority=task_data.get("priority", "medium")
        )
        
        logger.info(f"Processing task {task_input.task_id}: {task_input.action}")
        
        # Update task status to processing
        update_task_status(task_input.task_id, "processing")
        
        # Get agent info from database
        agent_info = get_agent_by_type("sales")
        if not agent_info:
            raise Exception("Sales agent not found in database")
        
        # Create and execute agent
        llm_provider = os.getenv("LLM_PROVIDER", os.getenv("DEFAULT_LLM_PROVIDER", "openai"))
        agent = create_sales_agent(llm_provider)
        
        result = agent.execute_task(task_input)
        
        # Save conversation to database
        for msg in result.conversation:
            save_conversation_message(
                agent_id=agent_info["id"],
                task_id=task_input.task_id,
                role=msg["role"],
                content=msg["content"]
            )
        
        # Update task with result
        if result.status == "completed":
            update_task_status(
                task_input.task_id,
                "completed",
                output=result.output
            )
            logger.info(f"Task {task_input.task_id} completed successfully")
        else:
            update_task_status(
                task_input.task_id,
                "failed",
                error=result.error
            )
            logger.error(f"Task {task_input.task_id} failed: {result.error}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing task: {str(e)}", exc_info=True)
        try:
            update_task_status(task_data["taskId"], "failed", error=str(e))
        except:
            pass
        raise


def listen_for_tasks():
    """Main worker loop - listen for tasks on Redis queue"""
    logger.info(f"Sales Agent Worker started, listening on {QUEUE_NAME}")
    logger.info(f"Using LLM provider: {os.getenv('DEFAULT_LLM_PROVIDER', 'openai')}")
    
    last_id = "0-0"  # Start from beginning
    
    while True:
        try:
            # Read from stream
            messages = redis_client.xread(
                {QUEUE_NAME: last_id},
                count=1,
                block=5000  # Block for 5 seconds
            )
            
            if not messages:
                continue
            
            # Process each message
            for stream_name, stream_messages in messages:
                for message_id, message_data in stream_messages:
                    try:
                        # Parse message
                        task_data = json.loads(message_data.get("data", "{}"))
                        
                        # Process task
                        process_task(task_data)
                        
                        # Update last_id for next iteration
                        last_id = message_id
                        
                    except Exception as e:
                        logger.error(f"Error processing message {message_id}: {e}")
                        last_id = message_id  # Move past failed message
                        
        except KeyboardInterrupt:
            logger.info("Worker shutting down...")
            break
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            time.sleep(5)  # Wait before retrying


if __name__ == "__main__":
    listen_for_tasks()
