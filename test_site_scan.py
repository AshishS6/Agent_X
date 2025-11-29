
import sys
import time
import logging
from agents.market_research_agent.main import create_market_research_agent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_scan():
    agent = create_market_research_agent(llm_provider='ollama')
    scan_tool = next(t for t in agent.tools if t.name == 'comprehensive_site_scan')
    
    url = "https://juspay.io/in"
    logger.info(f"Starting scan for {url}...")
    
    start_time = time.time()
    try:
        result = scan_tool.func(url)
        duration = time.time() - start_time
        logger.info(f"Scan completed in {duration:.2f} seconds")
        print(result[:500] + "...") # Print first 500 chars
    except Exception as e:
        logger.error(f"Scan failed: {e}")

if __name__ == "__main__":
    test_scan()
