#!/usr/bin/env python3
"""
CLI wrapper for Blog Agent

This CLI tool is called by the Go backend to execute blog generation tasks.
It follows the standard CLI contract:
- Input: --input '{"action": "...", ...}' (JSON string argument)
- Output: JSON object on stdout
- Logs: Write to stderr (not stdout)
- Exit Code: 0 = success, non-zero = failure

Usage:
    python cli.py --input '{"action": "generate_outline", "brand": "OPEN", "topic": "AI in Marketing", "target_audience": "SME", "intent": "education"}'
    python cli.py --input '{"action": "generate_post_from_outline", "brand": "OPEN", "outline": {...}, "tone": "professional", "length": "medium"}'
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
logger = logging.getLogger("BlogAgent.CLI")

# Load environment variables
from dotenv import load_dotenv

# Try multiple .env locations
env_paths = [
    os.path.join(os.path.dirname(__file__), '.env'),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backend', '.env'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'go-backend', '.env'),
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
    """Execute the blog agent and return result"""
    from main import create_blog_agent
    from shared.base_agent import TaskInput
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Create task input
    task_input = TaskInput(
        task_id=task_id,
        action=action,
        input_data=input_data,
        priority=input_data.get("priority", "medium")
    )
    
    # Get LLM provider from environment
    llm_provider = os.getenv("LLM_PROVIDER", os.getenv("DEFAULT_LLM_PROVIDER", "openai"))
    logger.info(f"Using LLM provider: {llm_provider}")
    
    # Create and execute agent
    agent = create_blog_agent(llm_provider)
    result = agent.execute_task(task_input)
    
    return {
        "status": result.status,
        "output": result.output,
        "error": result.error,
        "metadata": result.metadata
    }


def main():
    parser = argparse.ArgumentParser(
        description="Blog Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate outline:
    python cli.py --input '{"action": "generate_outline", "brand": "OPEN", "topic": "AI in Marketing", "target_audience": "SME", "intent": "education"}'
  
  Generate post from outline:
    python cli.py --input '{"action": "generate_post_from_outline", "brand": "OPEN", "outline": {"title": "...", "outline": [...]}, "tone": "professional", "length": "medium"}'
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
        
        # Validate action
        valid_actions = ["generate_outline", "generate_post_from_outline"]
        if action not in valid_actions:
            error_result = create_output(
                status="failed",
                error=f"Invalid action: '{action}'. Must be one of: {', '.join(valid_actions)}"
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
        output_json = json.dumps(result, indent=2, default=str)
        print(output_json)
        sys.stdout.flush()
        
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
        sys.stdout.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()
