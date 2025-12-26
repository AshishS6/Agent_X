
import sys
import os
import time
import logging

# Add agents directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agents'))

from agents.sales_agent.main import create_sales_agent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


import sys
import os
import time
import logging
from unittest.mock import MagicMock

# Add agents directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agents'))

from agents.sales_agent.main import create_sales_agent
from shared.base_agent import TaskInput

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sales_tools():
    logger.info("Initializing Sales Agent...")
    try:
        agent = create_sales_agent(llm_provider='ollama')
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        return

    # Mock the LLM to avoid local inference dependency
    agent.llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Subject: Partnership Opportunity\n\nHi John,\n\nWe love what Tech Corp is doing..."
    agent.llm.invoke.return_value = mock_response

    logger.info("Testing Agent Actions...")
    
    # Test 1: Qualify Lead
    logger.info("Testing 'qualify_lead' action...")
    try:
        task = TaskInput(
            task_id="test_sf_001",
            action="qualify_lead",
            input_data={"name": "Tech Corp", "industry": "Software"}
        )
        
        # Override mock for qualification
        agent.llm.invoke.return_value.content = "This is a strong lead with high potential."
        
        result = agent.execute_task(task)
        logger.info(f"Qualify Lead Result: {result.output}")
        
        if result.output and result.output.get("action") == "qualify_lead" and "qualification" in result.output:
             logger.info("SUCCESS: Qualify Lead action verified.")
        else:
             logger.error("FAILURE: Qualify Lead output malformed.")
             
    except Exception as e:
        logger.error(f"Qualify Lead failed: {e}")

    # Test 2: Generate Email
    logger.info("\nTesting 'generate_email' action...")
    try:
        task = TaskInput(
            task_id="test_sf_002",
            action="generate_email",
            input_data={"recipientName": "John", "context": "Intro"}
        )
        
        # Override mock for email
        agent.llm.invoke.return_value.content = "Subject: Hello\n\nHi John, checking in."
        
        result = agent.execute_task(task)
        logger.info(f"Generate Email Result: {result.output}")
        
        if result.output and result.output.get("action") == "generate_email" and "email" in result.output:
             logger.info("SUCCESS: Generate Email action verified.")
        else:
             logger.error("FAILURE: Generate Email output malformed.")

    except Exception as e:
         logger.error(f"Generate Email failed: {e}")

if __name__ == "__main__":
    test_sales_tools()

