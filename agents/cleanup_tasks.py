import os
import sys
import logging
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv

# Add parent directory to path for imports if needed, though we'll use direct db connection here
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend', '.env')
load_dotenv(env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TaskCleanup")

def get_db_connection():
    """Get database connection"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(db_url)

def cleanup_stuck_tasks():
    """Mark tasks as failed if they have been processing for too long"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Define threshold (1 hour ago)
        threshold_time = datetime.now() - timedelta(hours=1)
        
        logger.info(f"Cleaning up tasks stuck in 'processing' since before {threshold_time}")
        
        # Find and update stuck tasks
        query = """
            UPDATE tasks 
            SET status = 'failed', 
                error = 'Task timed out (stuck in processing)',
                completed_at = NOW()
            WHERE status = 'processing' 
            AND (started_at < %s OR (started_at IS NULL AND created_at < %s))
            RETURNING id, action
        """
        
        cursor.execute(query, (threshold_time, threshold_time))
        updated_rows = cursor.fetchall()
        
        conn.commit()
        
        if updated_rows:
            logger.info(f"Successfully marked {len(updated_rows)} stuck tasks as failed:")
            for task_id, action in updated_rows:
                logger.info(f" - Task {task_id} ({action})")
        else:
            logger.info("No stuck tasks found.")
            
    except Exception as e:
        logger.error(f"Error cleaning up tasks: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    cleanup_stuck_tasks()
