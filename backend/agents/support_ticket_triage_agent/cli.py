#!/usr/bin/env python3
"""
CLI wrapper for Support Ticket Triage Agent

Contract:
- Input: --input '{"action": "...", "task_id": "...", ...}' (JSON string)
- Output: JSON object on stdout
- Logs: stderr
- Exit code: 0 success, non-zero failure
"""

import sys
import os
import json
import argparse
import logging
import uuid
from typing import Dict, Any, Optional

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging to stderr (stdout reserved for JSON)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("SupportTicketTriage.CLI")

from dotenv import load_dotenv

env_paths = [
    os.path.join(os.path.dirname(__file__), ".env"),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend", ".env"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "go-backend", ".env"),
]
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info(f"Loaded environment from: {env_path}")
        break


def create_output(
    status: str,
    output: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {"status": status, "output": output, "error": error, "metadata": metadata or {}}


def run_agent(action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    from main import create_support_ticket_triage_agent
    from shared.base_agent import TaskInput

    task_id = input_data.get("task_id") or str(uuid.uuid4())

    task_input = TaskInput(
        task_id=task_id,
        action=action,
        input_data=input_data,
        priority=input_data.get("priority", "medium"),
    )

    llm_provider = os.getenv("LLM_PROVIDER", os.getenv("DEFAULT_LLM_PROVIDER", "openai"))
    logger.info(f"Using LLM provider: {llm_provider}")

    agent = create_support_ticket_triage_agent(llm_provider)
    result = agent.execute_task(task_input)

    return {
        "status": result.status,
        "output": result.output,
        "error": result.error,
        "metadata": result.metadata,
    }


def main():
    parser = argparse.ArgumentParser(description="Support Ticket Triage Agent CLI")
    parser.add_argument("--input", required=True, help="JSON input string with action and parameters")
    parser.add_argument("--dry-run", action="store_true", help="Validate input without executing")
    args = parser.parse_args()

    try:
        try:
            input_data = json.loads(args.input)
        except json.JSONDecodeError as e:
            print(json.dumps(create_output(status="failed", error=f"Invalid JSON input: {str(e)}")))
            sys.exit(1)

        action = input_data.get("action")
        if not action:
            print(json.dumps(create_output(status="failed", error="Missing required field: 'action'")))
            sys.exit(1)

        logger.info(f"Received action: {action}")

        if args.dry_run:
            print(json.dumps(create_output(status="completed", output={"dry_run": True, "action": action, "input": input_data}), indent=2))
            sys.exit(0)

        if action != "triage_ticket":
            print(json.dumps(create_output(status="failed", error=f"Unsupported action: {action}")))
            sys.exit(1)

        # Execute agent
        result = run_agent(action, input_data)
        print(json.dumps(result, indent=2, default=str))
        if result.get("status") == "failed":
            sys.exit(1)
        sys.exit(0)

    except Exception as e:
        logger.error(f"CLI execution failed: {e}", exc_info=True)
        print(json.dumps(create_output(status="failed", error=str(e))))
        sys.exit(1)


if __name__ == "__main__":
    main()

