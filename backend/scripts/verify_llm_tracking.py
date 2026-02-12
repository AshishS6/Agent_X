
import requests
import time
import json
import uuid
import sys
import psycopg2

BASE_URL = "http://localhost:3001/api"
DB_URL = "postgres://postgres:dev_password@localhost:5432/agentx?sslmode=disable"

def get_db_connection():
    return psycopg2.connect(DB_URL)

def create_task(agent_id, action, input_data):
    url = f"{BASE_URL}/agents/{agent_id}/execute"
    payload = {
        "action": action,
        "input": input_data,
        "priority": "medium"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["data"]["id"]
    except Exception as e:
        print(f"Failed to create task for {agent_id}: {e}")
        if hasattr(e, 'response') and e.response:
             print(e.response.text)
        return None

def wait_for_task(task_id):
    print(f"Waiting for task {task_id}...")
    for _ in range(60):  # Wait up to 60 seconds
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT status, output FROM tasks WHERE id = %s", (task_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                status, output = row
                if status in ["completed", "failed"]:
                    return status, output
            
            time.sleep(1)
        except Exception as e:
            print(f"Error checking task: {e}")
            time.sleep(1)
    return "timeout", None

def verify_output(agent_name, output):
    if not output:
        print(f"❌ {agent_name}: No output")
        return False
        
    print(f"--- {agent_name} Output Metadata ---")
    # Output might be a dict or a string depending on how psycopg2 returns it
    if isinstance(output, str): # Should be dict if using Json adapter but let's be safe
         pass 

    if "llm_usage" in output:
        usage = output["llm_usage"]
        print(f"✅ {agent_name}: LLM Usage Found!")
        print(json.dumps(usage, indent=2))
        return True
    else:
        print(f"❌ {agent_name}: LLM Usage NOT Found")
        print("Keys:", output.keys())
        return False

def main():
    print("Starting Verification...")
    
    # 1. Sales Agent
    print("\n--- Testing Sales Agent ---")
    sales_task_id = create_task(
        "sales", 
        "generate_email", 
        {"recipientName": "Alice", "context": "Meeting follow-up"}
    )
    if sales_task_id:
        status, output = wait_for_task(sales_task_id)
        print(f"Sales Task Status: {status}")
        verify_output("Sales Agent", output)

    # 2. Blog Agent
    print("\n--- Testing Blog Agent ---")
    blog_task_id = create_task(
        "blog",
        "generate_outline",
        {
            "brand": "OPEN",
            "topic": "API Banking 101",
            "target_audience": "SME",
            "intent": "education"
        }
    )
    if blog_task_id:
        status, output = wait_for_task(blog_task_id)
        print(f"Blog Task Status: {status}")
        verify_output("Blog Agent", output)

    # 3. Market Research Agent
    print("\n--- Testing Market Research Agent ---")
    mr_task_id = create_task(
        "market_research",
        "web_search",
        {"query": "Python 3.14 release date"}
    )
    if mr_task_id:
        status, output = wait_for_task(mr_task_id)
        print(f"Market Research Task Status: {status}")
        verify_output("Market Research Agent", output)

if __name__ == "__main__":
    main()
