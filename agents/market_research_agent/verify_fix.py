
import os
import sys
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from market_research_agent.main import create_market_research_agent
from shared.base_agent import TaskInput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyFix")

def test_agent_formatting():
    """Test if the agent can handle a tool call without formatting errors"""
    
    print("Initializing Market Research Agent...")
    try:
        agent = create_market_research_agent(llm_provider="ollama") 
        # Using ollama as it was the one causing issues usually
        
        task_input = TaskInput(
            task_id="test_verify_001",
            action="web_crawler",
            input_data={
                "topic": "https://example.com",
                "max_pages": 1,
                "crawl_depth": 1,
                "filters": {"industry": "testing"}
            }
        )
        
        print(f"Executing task with provider: {agent.config.llm_provider}")
        result = agent.execute_task(task_input)
        
        print("\nResult Status:", result.status)
        if result.status == "completed":
            print("Output length:", len(str(result.output)))
            print("SUCCESS: Agent executed without formatting crashes.")
        else:
            print("FAILURE: Agent failed.")
            print("Error:", result.error)
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent_formatting()
