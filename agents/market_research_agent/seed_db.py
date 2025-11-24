"""
Seed database with Market Research Agent
"""

import os
import sys
import uuid
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_utils import get_db_connection, get_agent_by_type
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backend', '.env')
load_dotenv(env_path)

def seed_agent():
    """Seed the market research agent"""
    
    # Check if agent already exists
    existing = get_agent_by_type("market_research")
    if existing:
        print(f"Market Research Agent already exists: {existing['id']}")
        return

    print("Creating Market Research Agent...")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        agent_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO agents (id, type, name, description, status, config, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        config = {
            "model": "gpt-4-turbo-preview",
            "tools": ["search_web", "monitor_url", "analyze_competitor", "track_trends", "compliance_check", "generate_report"]
        }
        
        cursor.execute(query, (
            agent_id,
            "market_research",
            "Market Research Agent",
            "Comprehensive market intelligence, competitor analysis, and compliance monitoring",
            "active",
            json.dumps(config),
            datetime.now(),
            datetime.now()
        ))
        
        print(f"Successfully created Market Research Agent: {agent_id}")

if __name__ == "__main__":
    seed_agent()
