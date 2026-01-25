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
import base64
import asyncio
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
    
    # Generate task ID (or use from input)
    task_id = input_data.get("task_id") or str(uuid.uuid4())
    
    # Get LLM provider from environment
    llm_provider = os.getenv("LLM_PROVIDER", os.getenv("DEFAULT_LLM_PROVIDER", "openai"))
    logger.info(f"Using LLM provider: {llm_provider}")
    
    # Report download action
    if action == "download_report":
        from reports.json_builder import JSONBuilder
        from reports.markdown_builder import MarkdownBuilder
        from reports import get_pdf_builder
        
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
        
        try:
            logger.info(f"Generating {format_type} report for task {task_id}")
            
            if format_type == "pdf":
                PDFBuilder = get_pdf_builder()
                builder = PDFBuilder()
                pdf_bytes = builder.build(scan_data, task_id)
                # Encode as base64 for JSON transport
                pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                return {
                    "status": "completed",
                    "output": {
                        "format": "pdf",
                        "content": pdf_base64,
                        "content_type": "application/pdf"
                    },
                    "error": None
                }
            
            elif format_type == "json":
                builder = JSONBuilder()
                json_content = builder.build(scan_data, task_id)
                return {
                    "status": "completed",
                    "output": {
                        "format": "json",
                        "content": json_content,
                        "content_type": "application/json"
                    },
                    "error": None
                }
            
            elif format_type == "markdown":
                builder = MarkdownBuilder()
                md_content = builder.build(scan_data, task_id)
                return {
                    "status": "completed",
                    "output": {
                        "format": "markdown",
                        "content": md_content,
                        "content_type": "text/markdown"
                    },
                    "error": None
                }
        
        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": f"Report generation failed: {str(e)}",
                "output": None
            }
    
    # KYC Site Scan - uses KYC Decision Engine
    if action == "kyc_site_scan":
        logger.info(f"Processing KYC site scan action (Task ID: {task_id})")
        
        # Add kyc_site_scan to path - try multiple possible locations
        agents_dir = os.path.dirname(os.path.dirname(__file__))
        kyc_path = os.path.join(agents_dir, "kyc_site_scan")
        
        # Also try absolute path resolution
        current_file = os.path.abspath(__file__)
        agents_abs_dir = os.path.dirname(os.path.dirname(current_file))
        kyc_abs_path = os.path.join(agents_abs_dir, "kyc_site_scan")
        
        paths_to_add = [kyc_path, kyc_abs_path]
        for path in paths_to_add:
            if os.path.exists(path) and path not in sys.path:
                sys.path.insert(0, path)
                logger.info(f"Added KYC path to sys.path: {path}")
        
        try:
            # Try importing KYC modules
            logger.info("Attempting to import KYC engine...")
            from kyc_site_scan.kyc_engine import KYCDecisionEngine
            from kyc_site_scan.models.input_schema import MerchantKYCInput
            logger.info("Successfully imported KYC engine")
            
            # Extract KYC input fields
            website_url = input_data.get("url", "") or input_data.get("website_url", "") or input_data.get("topic", "")
            merchant_legal_name = input_data.get("merchant_legal_name", "")
            registered_address = input_data.get("registered_address", "")
            declared_business_type = input_data.get("declared_business_type", "E-commerce")
            declared_products_services = input_data.get("declared_products_services", [])
            merchant_display_name = input_data.get("merchant_display_name", "")
            
            logger.info(f"Extracted KYC input - URL: {website_url}, Merchant: {merchant_legal_name}")
            
            if not website_url:
                return create_output(
                    status="failed",
                    error="Missing required field: website_url"
                )
            
            if not merchant_legal_name:
                return create_output(
                    status="failed",
                    error="Missing required field: merchant_legal_name"
                )
            
            if not registered_address:
                return create_output(
                    status="failed",
                    error="Missing required field: registered_address"
                )
            
            # Ensure products/services is a list
            if not declared_products_services or len(declared_products_services) == 0:
                declared_products_services = ["Products/Services"]
            
            # Build KYC input
            logger.info("Building MerchantKYCInput...")
            kyc_input = MerchantKYCInput(
                merchant_legal_name=merchant_legal_name,
                registered_address=registered_address,
                declared_business_type=declared_business_type,
                declared_products_services=declared_products_services,
                website_url=website_url,
                merchant_display_name=merchant_display_name or merchant_legal_name.split()[0] if merchant_legal_name else "Merchant"
            )
            
            logger.info(f"Running KYC scan for: {website_url} (Task ID: {task_id})")
            
            # Run KYC scan (async)
            engine = KYCDecisionEngine(logger=logger)
            logger.info("Starting KYC engine process...")
            kyc_result = asyncio.run(engine.process(kyc_input))
            logger.info(f"KYC scan completed. Decision: {kyc_result.decision.value if hasattr(kyc_result.decision, 'value') else kyc_result.decision}")
            
            # Convert Pydantic model to dict for JSON serialization
            kyc_output = kyc_result.model_dump(mode='json')
            
            # Return in format expected by Go backend
            result = {
                "status": "completed",
                "output": {
                    "action": action,
                    "response": json.dumps(kyc_output, default=str)  # JSON string with KYC decision output
                },
                "error": None,
                "metadata": {
                    "engine": "kyc_v2.2",
                    "url": website_url,
                    "decision": kyc_result.decision.value if hasattr(kyc_result.decision, 'value') else str(kyc_result.decision)
                }
            }
            logger.info("KYC scan result prepared successfully")
            return result
        except ImportError as e:
            logger.error(f"Failed to import KYC engine: {e}", exc_info=True)
            return create_output(
                status="failed",
                error=f"KYC engine not available: {str(e)}"
            )
        except Exception as e:
            logger.error(f"KYC scan failed: {e}", exc_info=True)
            return create_output(
                status="failed",
                error=f"KYC scan failed: {str(e)}"
            )
    
    # Site scans use V2 modular engine (includes tech_stack & seo_analysis)
    if action in ["comprehensive_site_scan", "site_scan"]:
        from scan_engine import ModularScanEngine
        
        # Extract URL from input (frontend sends it as 'topic' or 'url')
        url = input_data.get("topic", "") or input_data.get("url", "")
        business_name = input_data.get("business_name", "")
        
        logger.info(f"Using V2 modular engine for site scan: {url} (Task ID: {task_id})")
        
        v2_engine = ModularScanEngine(logger=logger)
        # Pass task_id for snapshot tracking
        v2_output = v2_engine.comprehensive_site_scan(url, business_name, task_id=task_id)
        
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
  
  Download report:
    python cli.py --input '{"action": "download_report", "task_id": "uuid", "format": "pdf", "scan_data": {...}}'
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
        
        # CRITICAL: Flush stdout before os._exit() to ensure output is captured
        # os._exit() bypasses Python cleanup, including stdout buffering
        sys.stdout.flush()
        
        # Force immediate exit to prevent hanging
        # Use os._exit() instead of sys.exit() to bypass Python cleanup that might delay exit
        # This ensures the process exits immediately after completing the scan
        exit_code = 1 if result.get("status") == "failed" else 0
        os._exit(exit_code)
        
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
