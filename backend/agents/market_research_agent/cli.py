#!/usr/bin/env python3
"""
CLI wrapper for Market Research Agent

This CLI tool is called by the Go backend to execute market research tasks.
It follows the standard CLI contract:
- Input: --input '{"action": "...", ...}' (JSON string argument)
- Output: JSON object on stdout
- Logs: Write to stderr (not stdout)
- Exit Code: 0 = success, non-zero = failure

Usage:
    python cli.py --input '{"action": "site_scan", "url": "https://example.com"}'
"""

import sys
import os
import json
import argparse
import logging
import uuid
from typing import Dict, Any

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging to stderr (stdout is reserved for JSON output)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("MarketResearchAgent.CLI")

# Load environment variables
from dotenv import load_dotenv

# Try multiple .env locations
env_paths = [
    os.path.join(os.path.dirname(__file__), '.env'),  # agents/market_research_agent/.env
    os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'),  # agents/.env
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backend', '.env'),  # backend/.env
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'go-backend', '.env'),  # go-backend/.env
]

for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info(f"Loaded environment from: {env_path}")
        break


def create_output(status: str, output: Dict = None, error: str = None, metadata: Dict = None) -> Dict[str, Any]:
    """Create standardized output structure"""
    result = {
        "status": status,
        "output": output,
        "error": error,
        "metadata": metadata or {}
    }
    return result


def run_agent(action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the market research agent and return result
    
    Uses V2 modular engine for site scans (includes tech_stack, seo_analysis)
    Falls back to V1 agent for other actions
    """
    import uuid
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Get LLM provider from environment
    llm_provider = os.getenv("LLM_PROVIDER", os.getenv("DEFAULT_LLM_PROVIDER", "openai"))
    logger.info(f"Using LLM provider: {llm_provider}")
    
    # Site scans use V2 modular engine (includes tech_stack & seo_analysis)
    if action in ["comprehensive_site_scan", "site_scan"]:
        from scan_engine import ModularScanEngine
        
        # Extract URL from input (frontend sends it as 'topic' or 'url')
        url = input_data.get("topic", "") or input_data.get("url", "")
        business_name = input_data.get("business_name", "")
        
        logger.info(f"Using V2 modular engine for site scan: {url}")
        
        v2_engine = ModularScanEngine(logger=logger)
        v2_output = v2_engine.comprehensive_site_scan(url, business_name)
        
        # Parse the V2 output
        v2_data = json.loads(v2_output)
        
        # Return in format expected by Go backend
        return {
            "status": "completed",
            "output": {
                "action": action,
                "response": v2_output  # JSON string with comprehensive_site_scan
            },
            "error": None,
            "metadata": {
                "engine": "v2",
                "url": url
            }
        }
    
    # Other actions use V1 agent
    from main import create_market_research_agent
    from shared.base_agent import TaskInput
    
    task_input = TaskInput(
        task_id=task_id,
        action=action,
        input_data=input_data,
        priority=input_data.get("priority", "medium")
    )
    
    agent = create_market_research_agent(llm_provider)
    result = agent.execute_task(task_input)
    
    return {
        "status": result.status,
        "output": result.output,
        "error": result.error,
        "metadata": result.metadata
    }


def main():
    parser = argparse.ArgumentParser(
        description="Market Research Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Site scan:
    python cli.py --input '{"action": "site_scan", "url": "https://example.com"}'
  
  Comprehensive scan:
    python cli.py --input '{"action": "comprehensive_site_scan", "url": "https://example.com", "business_name": "Example Inc"}'
  
  Web search:
    python cli.py --input '{"action": "web_search", "query": "AI startups 2024"}'
"""
    )
    parser.add_argument(
        "--input", 
        required=True, 
        help="JSON input string with action and parameters"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate input without executing"
    )
    
    args = parser.parse_args()
    
    try:
        # Parse input JSON
        try:
            input_data = json.loads(args.input)
        except json.JSONDecodeError as e:
            error_result = create_output(
                status="failed",
                error=f"Invalid JSON input: {str(e)}"
            )
            print(json.dumps(error_result))
            sys.exit(1)
        
        # Extract action
        action = input_data.get("action")
        if not action:
            error_result = create_output(
                status="failed",
                error="Missing required field: 'action'"
            )
            print(json.dumps(error_result))
            sys.exit(1)
        
        logger.info(f"Received action: {action}")
        logger.info(f"Input data: {json.dumps(input_data, indent=2)}")
        
        # Dry run - just validate
        if args.dry_run:
            result = create_output(
                status="completed",
                output={"dry_run": True, "action": action, "input": input_data}
            )
            print(json.dumps(result, indent=2))
            sys.exit(0)
        
        # Execute agent
        result = run_agent(action, input_data)
        
        # Output result as JSON to stdout
        print(json.dumps(result, indent=2, default=str))
        
        # Exit with appropriate code
        if result.get("status") == "failed":
            sys.exit(1)
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"CLI execution failed: {e}", exc_info=True)
        error_result = create_output(
            status="failed",
            error=str(e)
        )
        print(json.dumps(error_result))
        sys.exit(1)


if __name__ == "__main__":
    main()
