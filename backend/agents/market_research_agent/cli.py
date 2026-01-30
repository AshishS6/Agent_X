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
    python cli.py --input '{"action": "web_search", "query": "AI startups 2024"}'
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


def _build_simple_report(scan_data: Dict[str, Any], format_type: str) -> Dict[str, Any]:
    if format_type == "json":
        content = json.dumps(scan_data, indent=2, default=str)
        return {
            "format": "json",
            "content": content,
            "content_type": "application/json"
        }

    if format_type == "markdown":
        content = "# Market Research Report\n\n```json\n"
        content += json.dumps(scan_data, indent=2, default=str)
        content += "\n```\n"
        return {
            "format": "markdown",
            "content": content,
            "content_type": "text/markdown"
        }

    return {
        "format": format_type,
        "content": "PDF export is not supported for market research reports.",
        "content_type": "text/plain"
    }


def run_agent(action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the market research agent and return result.

    Market research handles competitor analysis, trend monitoring, and web search.
    Site scans and KYC scans are handled by the site scan agent.
    """
    # Generate task ID (or use from input)
    task_id = input_data.get("task_id") or str(uuid.uuid4())

    # Get LLM provider from environment
    llm_provider = os.getenv("LLM_PROVIDER", os.getenv("DEFAULT_LLM_PROVIDER", "openai"))
    logger.info(f"Using LLM provider: {llm_provider}")

    # Simple report download action
    if action == "download_report":
        task_id = input_data.get("task_id")
        format_type = input_data.get("format", "json").lower()
        scan_data = input_data.get("scan_data", {})

        if not task_id:
            return {
                "status": "failed",
                "error": "Missing required field: task_id",
                "output": None
            }

        if not scan_data:
            return {
                "status": "failed",
                "error": "Missing required field: scan_data",
                "output": None
            }

        if format_type not in ["pdf", "json", "markdown"]:
            return {
                "status": "failed",
                "error": f"Invalid format: {format_type}. Must be pdf, json, or markdown",
                "output": None
            }

        report_payload = _build_simple_report(scan_data, format_type)
        if format_type == "pdf":
            return {
                "status": "failed",
                "error": report_payload["content"],
                "output": None
            }

        return {
            "status": "completed",
            "output": report_payload,
            "error": None
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
  Web search:
    python cli.py --input '{"action": "web_search", "query": "AI startups 2024"}'

  Download report:
    python cli.py --input '{"action": "download_report", "task_id": "uuid", "format": "json", "scan_data": {...}}'
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
            sys.stdout.flush()
            sys.exit(1)

        # Extract action
        action = input_data.get("action")
        if not action:
            error_result = create_output(
                status="failed",
                error="Missing required field: 'action'"
            )
            print(json.dumps(error_result))
            sys.stdout.flush()
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
            sys.stdout.flush()
            sys.exit(0)

        # Execute agent
        result = run_agent(action, input_data)

        # Output result as JSON to stdout
        output_json = json.dumps(result, indent=2, default=str)
        print(output_json)
        sys.stdout.flush()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        error_result = create_output(
            status="failed",
            error=f"Internal error: {str(e)}"
        )
        print(json.dumps(error_result))
        sys.stdout.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()
