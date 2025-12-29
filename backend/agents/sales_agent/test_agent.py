"""
Simple test script for Sales Agent
Run this to verify agent works without full stack
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.base_agent import TaskInput
from sales_agent.main import create_sales_agent

# Load environment
load_dotenv()


def test_email_generation():
    """Test email generation capability"""
    print("🧪 Testing Sales Agent - Email Generation")
    print("=" * 50)
    
    # Check for API key
    provider = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set. Please add to .env file")
        return
    
    # Create agent
    agent = create_sales_agent(llm_provider=provider)
    print(f"✅ Created Sales Agent (using {provider})")
    
    # Create task
    task = TaskInput(
        task_id="test-001",
        action="generate_email",
        input_data={
            "recipientName": "Jane Smith",
            "companyName": "TechCorp Inc",
            "context": "Following up after our product demo last week",
            "keyPoints": "Highlight the ROI calculator and implementation timeline we discussed"
        }
    )
    
    print(f"\n📥 Input:")
    print(f"   Recipient: {task.input_data['recipientName']}")
    print(f"   Company: {task.input_data['companyName']}")
    print(f"   Context: {task.input_data['context']}")
    
    # Execute
    print(f"\n⚙️  Executing agent...")
    result = agent.execute_task(task)
    
    # Display results
    if result.status == "completed":
        print(f"\n✅ Task Completed!")
        print(f"\n📧 Generated Email:")
        print("=" * 50)
        email = result.output.get("email", {})
        print(f"Subject: {email.get('subject', 'N/A')}")
        print(f"\n{email.get('body', 'No content')}")
        print("=" * 50)
        
        print(f"\n📊 Metadata:")
        print(f"   Execution Time: {result.metadata.get('execution_time', 0):.2f}s")
        print(f"   Model: {result.metadata.get('model', 'N/A')}")
        print(f"   Conversation Steps: {len(result.conversation)}")
    else:
        print(f"\n❌ Task Failed:")
        print(f"   Error: {result.error}")


def test_lead_qualification():
    """Test lead qualification capability"""
    print("\n\n🧪 Testing Sales Agent - Lead Qualification")
    print("=" * 50)
    
    # Check for API key
    provider = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set. Please add to .env file")
        return
    
    # Create agent
    agent = create_sales_agent(llm_provider=provider)
    
    # Create task
    task = TaskInput(
        task_id="test-002",
        action="qualify_lead",
        input_data={
            "companyName": "StartupXYZ",
            "industry": "SaaS",
            "size": "50-200 employees",
            "budget": "$50k-$100k annually",
            "painPoints": "Manual data entry, lack of automation, slow reporting",
            "currentSolution": "Using spreadsheets and legacy CRM"
        }
    )
    
    print(f"\n📥 Lead Information:")
    print(f"   Company: {task.input_data['companyName']}")
    print(f"   Industry: {task.input_data['industry']}")
    print(f"   Size: {task.input_data['size']}")
    print(f"   Budget: {task.input_data['budget']}")
    
    # Execute
    print(f"\n⚙️  Qualifying lead...")
    result = agent.execute_task(task)
    
    # Display results
    if result.status == "completed":
        print(f"\n✅ Qualification Complete!")
        qualification = result.output.get("qualification", {})
        
        score = qualification.get("score", 0)
        print(f"\n📊 Lead Score: {score}/10")
        print(f"💡 Recommendation: {qualification.get('recommendation', 'N/A')}")
        print(f"\n📝 Reasoning:")
        print(qualification.get("reasoning", "No reasoning provided"))
        
        print(f"\n⏱️  Execution Time: {result.metadata.get('execution_time', 0):.2f}s")
    else:
        print(f"\n❌ Task Failed:")
        print(f"   Error: {result.error}")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🤖 Agent_X Sales Agent Test Suite")
    print("=" * 50)
    
    try:
        test_email_generation()
        test_lead_qualification()
        
        print("\n\n" + "=" * 50)
        print("✅ All tests completed!")
        print("=" * 50 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
