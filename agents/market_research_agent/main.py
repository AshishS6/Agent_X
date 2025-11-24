"""
Market Research Agent Implementation
Handles market research, competitor analysis, and compliance monitoring
Using free tools: DuckDuckGo Search and BeautifulSoup
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from langchain.tools import tool
from duckduckgo_search import DDGS

from shared.base_agent import BaseAgent, AgentConfig


class MarketResearchAgent(BaseAgent):
    """
    Market Research Agent - Comprehensive intelligence gathering
    
    Capabilities:
    - Multi-source web research (via DuckDuckGo)
    - Competitor analysis and monitoring
    - Trend tracking
    - Compliance and risk monitoring
    - Web crawling for specific content
    - Automated report generation
    """
    
    def _register_tools(self):
        """Register market research-specific tools"""
        
        @tool
        def search_web(query: str, max_results: int = 5) -> str:
            """
            Search the web for information using DuckDuckGo (Free).
            
            Args:
                query: Search query
                max_results: Number of results to return (default: 5)
            
            Returns:
                Search results with titles, snippets, and links
            """
            try:
                results = []
                with DDGS() as ddgs:
                    # Use text search
                    search_results = list(ddgs.text(query, max_results=max_results))
                    
                    for i, r in enumerate(search_results):
                        results.append(f"{i+1}. {r['title']}\n   Source: {r['href']}\n   Snippet: {r['body']}\n")
                
                if not results:
                    return f"No results found for query: {query}"
                
                return "\n".join(results)
            except Exception as e:
                return f"Error performing search: {str(e)}"

        @tool
        def monitor_url(url: str, keywords: str = "") -> str:
            """
            Crawl a specific URL and extract text content.
            
            Args:
                url: URL to monitor/crawl
                keywords: Comma-separated keywords to look for (optional)
            
            Returns:
                Extracted text content and keyword matches
            """
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text
                text = soup.get_text()
                
                # Clean text (remove extra whitespace)
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                clean_text = '\n'.join(chunk for chunk in chunks if chunk)
                
                # Check for keywords if provided
                keyword_matches = []
                if keywords:
                    keyword_list = [k.strip().lower() for k in keywords.split(',')]
                    text_lower = clean_text.lower()
                    for k in keyword_list:
                        if k in text_lower:
                            keyword_matches.append(k)
                
                summary = clean_text[:1000] + "..." if len(clean_text) > 1000 else clean_text
                
                result = f"Crawled {url}\n\nStatus: Success\nContent Length: {len(clean_text)} chars\n"
                if keywords:
                    result += f"Keywords Found: {', '.join(keyword_matches) if keyword_matches else 'None'}\n"
                result += f"\nContent Summary:\n{summary}"
                
                return result
                
            except Exception as e:
                return f"Error crawling URL {url}: {str(e)}"

        @tool
        def analyze_competitor(company_name: str) -> str:
            """
            Analyze a competitor by searching for key information.
            
            Args:
                company_name: Name of the competitor
            
            Returns:
                Competitor intelligence summary
            """
            # Use the search tool logic internally
            try:
                queries = [
                    f"{company_name} company overview products",
                    f"{company_name} pricing model",
                    f"{company_name} recent news 2024",
                    f"{company_name} competitors"
                ]
                
                combined_results = []
                with DDGS() as ddgs:
                    for q in queries:
                        results = list(ddgs.text(q, max_results=2))
                        for r in results:
                            combined_results.append(f"- {r['title']}: {r['body']} ({r['href']})")
                
                return f"Raw Research Data for {company_name}:\n\n" + "\n".join(combined_results)
            except Exception as e:
                return f"Error analyzing competitor: {str(e)}"

        @tool
        def track_trends(topic: str) -> str:
            """
            Track trends for a specific topic.
            
            Args:
                topic: Topic to track
            
            Returns:
                Trend analysis data
            """
            try:
                queries = [
                    f"{topic} trends 2024 2025",
                    f"future of {topic}",
                    f"{topic} market growth statistics"
                ]
                
                combined_results = []
                with DDGS() as ddgs:
                    for q in queries:
                        results = list(ddgs.text(q, max_results=3))
                        for r in results:
                            combined_results.append(f"- {r['title']}: {r['body']} ({r['href']})")
                
                return f"Trend Research Data for {topic}:\n\n" + "\n".join(combined_results)
            except Exception as e:
                return f"Error tracking trends: {str(e)}"

        @tool
        def compliance_check(topic: str, industry: str = "general") -> str:
            """
            Check for compliance and regulatory updates.
            
            Args:
                topic: Specific compliance topic
                industry: Industry sector
            
            Returns:
                Regulatory information
            """
            try:
                queries = [
                    f"{topic} regulations {industry} 2024",
                    f"{topic} compliance requirements",
                    f"{topic} legal risks {industry}"
                ]
                
                combined_results = []
                with DDGS() as ddgs:
                    for q in queries:
                        results = list(ddgs.text(q, max_results=3))
                        for r in results:
                            combined_results.append(f"- {r['title']}: {r['body']} ({r['href']})")
                
                return f"Compliance Research Data for {topic} ({industry}):\n\n" + "\n".join(combined_results)
            except Exception as e:
                return f"Error checking compliance: {str(e)}"

        @tool
        def generate_report(research_data: str, report_type: str = "summary") -> str:
            """
            Generate a structured research report.
            
            Args:
                research_data: Summary of research findings
                report_type: Type of report
            
            Returns:
                Formatted report confirmation
            """
            # In a real system, this might generate a PDF or save to a DB
            return f"Report generated successfully.\nType: {report_type}\nLength: {len(research_data)} chars\n\n(This content would be formatted into a PDF/Doc in production)"

        # Register all tools
        self.add_tool(search_web)
        self.add_tool(monitor_url)
        self.add_tool(analyze_competitor)
        self.add_tool(track_trends)
        self.add_tool(compliance_check)
        self.add_tool(generate_report)
    
    def _get_system_prompt(self) -> str:
        """Market research agent system prompt"""
        return """You are a professional Market Research AI agent.

Your role is to help with comprehensive market intelligence, competitor analysis, and compliance monitoring.
You have access to real-time web search (DuckDuckGo) and web crawling tools.

Guidelines:
- ALWAYS cite sources (URLs) for your information.
- When asked to research a topic, use the `search_web` tool to find recent information.
- When asked to monitor a specific site, use `monitor_url`.
- For competitor analysis, use `analyze_competitor` or manual search.
- Provide data-driven insights.
- If you find conflicting information, note it.
- Be objective and professional.

When generating the final response:
- Structure it clearly with headings.
- Include a "Key Findings" section.
- Include a "Sources" section.
- If it's a compliance check, highlight risks clearly.
"""
    
    def _run_agent_loop(self, system_prompt: str, user_prompt: str, task: Any) -> Dict[str, Any]:
        """
        Agent loop for market research tasks
        """
        # We can add custom logic here if needed, but the base ReAct loop 
        # (which calls LLM -> Tools -> LLM) should handle most cases if we use LangChain's agent.
        # However, the base_agent.py implementation seems to be a simple LLM call 
        # without an automatic tool loop in `_run_agent_loop`.
        
        # NOTE: The base_agent.py `_run_agent_loop` implementation shown in context 
        # only does a single LLM call. To make tools work, we need to use 
        # LangChain's AgentExecutor or implement a loop.
        
        # Let's override to use a proper agent executor if possible, 
        # or just manually call tools if the base class doesn't support it.
        # Given the base class structure, let's try to use the tools in the prompt 
        # or rely on the LLM to ask for tool usage if we were using function calling.
        
        # Since the base class `_run_agent_loop` is simple, let's enhance it here 
        # to support basic tool usage via ReAct or similar, 
        # OR just rely on the LLM to do the work if it has the context.
        
        # BUT: The `BaseAgent` initializes `self.tools`.
        # If we want real tool execution, we should use `create_react_agent` or similar.
        
        # Let's try to use LangChain's create_react_agent if available, 
        # or implement a simple loop.
        
        from langchain.agents import AgentExecutor, create_react_agent
        from langchain import hub
        
        # Pull the react prompt
        # prompt = hub.pull("hwchase17/react") 
        # We'll define a simple one to avoid pulling
        from langchain.prompts import PromptTemplate
        
        template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)
        
        # Construct the ReAct agent
        agent = create_react_agent(self.llm, self.tools, prompt)
        
        # Create an agent executor by passing in the agent and tools
        agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)
        
        # Execute
        try:
            # Combine system prompt and user prompt for the input
            full_input = f"{system_prompt}\n\nTask: {user_prompt}"
            
            result = agent_executor.invoke({"input": full_input})
            response_text = result["output"]
            
        except Exception as e:
            # Fallback to simple generation if agent fails
            self.logger.error(f"Agent execution failed: {e}")
            response_text = f"Error executing agent: {str(e)}"

        return {
            "response": response_text,
            "action": task.action,
            "completed_at": "now" # In real code use datetime
        }


# Create default market research agent instance
def create_market_research_agent(llm_provider: str = "openai") -> MarketResearchAgent:
    """Factory function to create market research agent"""
    # Determine model based on provider
    if llm_provider == "openai":
        model = "gpt-4-turbo-preview"
    elif llm_provider == "anthropic":
        model = "claude-3-sonnet-20240229"
    elif llm_provider == "ollama":
        model = os.getenv("LLM_MODEL", "deepseek-r1:7b")
    else:
        model = "gpt-3.5-turbo"  # Fallback

    config = AgentConfig(
        agent_type="market_research",
        name="Market Research Agent",
        description="Comprehensive market intelligence, competitor analysis, and compliance monitoring",
        llm_provider=llm_provider,
        model=model,
        temperature=0.5,
        tools=[
            "search_web",
            "monitor_url",
            "analyze_competitor",
            "track_trends",
            "compliance_check",
            "generate_report"
        ]
    )
    return MarketResearchAgent(config)
