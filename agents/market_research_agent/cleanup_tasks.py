import os
import sys
from dotenv import load_dotenv
import psycopg2

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_utils import get_db_connection

# Load env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backend', '.env')
load_dotenv(env_path)

def cleanup_stuck_tasks():
    print("Cleaning up stuck tasks...")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Find stuck tasks
            cursor.execute("SELECT id FROM tasks WHERE status = 'processing'")
            stuck_tasks = cursor.fetchall()
            
            if not stuck_tasks:
                print("No stuck tasks found.")
                return

            print(f"Found {len(stuck_tasks)} stuck tasks. Marking as failed...")
            
            for (task_id,) in stuck_tasks:
                cursor.execute("""
                    UPDATE tasks 
                    SET status = 'failed', 
                        error = 'Task cancelled by cleanup script',
                        completed_at = NOW()
                    WHERE id = %s
                """, (task_id,))
                print(f" - Task {task_id} marked as failed.")
                
            conn.commit()
        print("Cleanup complete.")
    except Exception as e:
        print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    cleanup_stuck_tasks()
