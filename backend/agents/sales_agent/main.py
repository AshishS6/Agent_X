"""
Sales Agent Implementation
Handles lead qualification, email outreach, and meeting scheduling
"""

from typing import Dict, Any
from langchain.tools import BaseTool, tool
from shared.base_agent import BaseAgent, AgentConfig


class SalesAgent(BaseAgent):
    """
    Sales Agent - Automates sales workflows
    
    Capabilities:
    - Lead qualification
    - Personalized email generation
    - Meeting scheduling
    - CRM data analysis
    """
    
    def _register_tools(self):
        """Register sales-specific tools"""
        # For now, we'll use simple mock tools
        # In production, these would integrate with real APIs
        
        @tool
        def search_company_info(company_name: str) -> str:
            """Search for information about a company"""
            return f"Company info for {company_name}: Technology company, 50-200 employees, Series B funded"
        
        @tool
        def check_calendar(date: str) -> str:
            """Check calendar availability for a given date"""
            return f"Available time slots for {date}: 10:00 AM, 2:00 PM, 4:00 PM"
        
        self.add_tool(search_company_info)
        self.add_tool(check_calendar)
    
    def _get_system_prompt(self) -> str:
        """Sales agent system prompt"""
        return """You are a professional Sales Agent AI assistant.

Your role is to help with sales-related tasks including:
- Qualifying leads and analyzing potential customers
- Generating personalized, professional sales emails
- Scheduling meetings and managing calendar
- Providing insights on prospects

Guidelines:
- Be professional yet friendly in tone
- Personalize all communications
- Focus on value proposition
- Use data-driven insights
- Always be respectful and helpful

When generating emails:
- Use a clear subject line
- Address the recipient by name
- Highlight relevant pain points
- Include a clear call-to-action
- Keep it concise (under 200 words)

When qualifying leads:
- Research company background
- Identify key decision makers
- Assess fit with product/service
- Prioritize based on potential value

Respond with structured, actionable output."""
    
    def _run_agent_loop(self, system_prompt: str, user_prompt: str, task: Any) -> Dict[str, Any]:
        """
        Enhanced agent loop for sales tasks
        """
        # For email generation tasks, provide structured output
        if task.action == "generate_email":
            result = super()._run_agent_loop(system_prompt, user_prompt, task)
            
            # Parse email from response (simple extraction for now)
            email_content = result.get("response", "")
            
            return {
                "action": "generate_email",
                "email": {
                    "subject": self._extract_subject(email_content),
                    "body": email_content,
                    "recipient": task.input_data.get("recipientName", "Prospect"),
                },
                "metadata": {
                    "context": task.input_data.get("context", ""),
                    "tone": "professional"
                },
                "completed_at": result.get("completed_at")
            }
        
        # For lead qualification tasks
        elif task.action == "qualify_lead":
            result = super()._run_agent_loop(system_prompt, user_prompt, task)
            
            return {
                "action": "qualify_lead",
                "qualification": {
                    "score": self._extract_score(result.get("response", "")),
                    "reasoning": result.get("response", ""),
                    "recommendation": "high-priority" if "strong" in result.get("response", "").lower() else "follow-up"
                },
                "completed_at": result.get("completed_at")
            }
        
        # Default handling for other actions
        else:
            return super()._run_agent_loop(system_prompt, user_prompt, task)
    
    def _extract_subject(self, email_content: str) -> str:
        """Extract email subject from content"""
        lines = email_content.split('\n')
        for line in lines:
            if line.strip().lower().startswith('subject:'):
                return line.split(':', 1)[1].strip()
        return "Follow-up from our conversation"
    
    def _extract_score(self, response: str) -> int:
        """Extract qualification score from response (1-10)"""
        # Simple heuristic - would use more sophisticated parsing in production
        if any(word in response.lower() for word in ['excellent', 'strong', 'perfect']):
            return 9
        elif any(word in response.lower() for word in ['good', 'qualified', 'promising']):
            return 7
        elif any(word in response.lower() for word in ['moderate', 'potential']):
            return 5
        else:
            return 3


# Create default sales agent instance
def create_sales_agent(llm_provider: str = "openai") -> SalesAgent:
    """Factory function to create sales agent. LLM provider/model via router (env: LLM_*)."""
    import os
    model = os.getenv("LLM_LOCAL_MODEL") or os.getenv("LLM_CLOUD_MODEL") or ""

    config = AgentConfig(
        agent_type="sales",
        name="Sales Agent",
        description="Automates lead qualification, email outreach, and meeting scheduling",
        llm_provider=llm_provider,
        model=model,
        temperature=0.7,
        tools=["search_company_info", "check_calendar"]
    )
    return SalesAgent(config)
