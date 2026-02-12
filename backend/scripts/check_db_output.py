
import psycopg2
import json

DB_URL = "postgres://postgres:dev_password@localhost:5432/agentx?sslmode=disable"

def check_latest_task():
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        query = """
            SELECT id, action, status, output, created_at 
            FROM tasks 
            ORDER BY created_at DESC 
            LIMIT 1
        """
        
        cursor.execute(query)
        task = cursor.fetchone()
        
        if not task:
            print("No tasks found.")
            return

        task_id, action, status, output, created_at = task
        print(f"Latest Task ID: {task_id}")
        print(f"Action: {action}")
        print(f"Status: {status}")
        print(f"Created At: {created_at}")
        
        print("\n--- Output ---")
        if output:
            print(json.dumps(output, indent=2))
            
            if "llm_usage" in output:
                print("\n✅ 'llm_usage' found in output!")
            else:
                print("\n❌ 'llm_usage' NOT found in output.")
                if "response" in output:
                    print("Response keys:", output.keys())
        else:
            print("Output is None/Empty")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_latest_task()
