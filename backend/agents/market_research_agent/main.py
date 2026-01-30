"""
Market Research Agent Implementation
Handles market research, competitor analysis, and compliance monitoring
Using free tools: DuckDuckGo Search and BeautifulSoup
"""

# Path setup to allow running from any directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import requests
import asyncio
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from langchain.tools import tool
from duckduckgo_search import DDGS

from shared.base_agent import BaseAgent, AgentConfig


def ensure_event_loop() -> None:
    """Ensure an asyncio event loop exists for libraries that expect one."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)


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
        try:
            self.logger.info("Registering market research tools...")
            
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
                    ensure_event_loop()
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

            # Add logging to monitor_url
            # We need to inject logging into the inner function or wrap it
            # Since we are inside _register_tools, we can use self.logger
            
            # Let's redefine monitor_url with logging
            @tool
            def monitor_url(url: str, keywords: str = "", max_pages: int = 0, depth: int = 1, respect_robots_txt: bool = True, delay: float = 1.0) -> str:
                """
                Crawl a URL with advanced options.
                
                CRITICAL: You must return the raw JSON string output from this tool EXACTLY as is. 
                DO NOT summarize. DO NOT reformat. DO NOT wrap in markdown.
                Just return the JSON string.
                
                Args:
                    url: Base URL to monitor
                    keywords: Comma-separated keywords
                    max_pages: Max pages (0 for unlimited)
                    depth: Crawl depth
                    respect_robots_txt: Respect robots.txt
                    delay: Request delay
                
                Returns:
                    str: Raw JSON report
                """
                self.logger.info(f"Starting crawl for URL: {url} (Depth: {depth}, Max: {max_pages})")
                try:
                    import time
                    from urllib.parse import urljoin, urlparse
                    from urllib.robotparser import RobotFileParser
                    import re
                    
                    headers = {
                        'User-Agent': 'Agent_X_MarketResearchBot/1.0'
                    }
                    
                    # 1. Check robots.txt
                    if respect_robots_txt:
                        parsed_url = urlparse(url)
                        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
                        rp = RobotFileParser()
                        try:
                            self.logger.info(f"Checking robots.txt at {robots_url}")
                            rp.set_url(robots_url)
                            rp.read()
                            if not rp.can_fetch(headers['User-Agent'], url):
                                return json.dumps({
                                    "error": "Crawling forbidden by robots.txt",
                                    "url": url
                                }, indent=2)
                        except Exception as e:
                            self.logger.warning(f"Could not check robots.txt: {e}. Proceeding with caution.")

                    # Helper to crawl a single page
                    def crawl_page(page_url):
                        try:
                            self.logger.info(f"Crawling page: {page_url}")
                            time.sleep(delay) # Polite delay
                            resp = requests.get(page_url, headers=headers, timeout=10)
                            if resp.status_code != 200: 
                                self.logger.warning(f"Failed to fetch {page_url}: Status {resp.status_code}")
                                return None
                            
                            soup = BeautifulSoup(resp.content, 'html.parser')
                            
                            # Clean
                            for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe", "svg"]):
                                element.decompose()
                                
                            text = soup.get_text(separator='\n', strip=True)
                            lines = (line.strip() for line in text.splitlines())
                            clean_text = '\n'.join(line for line in lines if line)
                            
                            # Find keywords WITH CONTEXT
                            keyword_matches = []  # List of {keyword, context, position}
                            if keywords:
                                keyword_list = [k.strip().lower() for k in keywords.split(',')]
                                
                                # Split text into sentences for context extraction
                                import re
                                sentences = re.split(r'(?<=[.!?])\s+', clean_text)
                                
                                for i, sentence in enumerate(sentences):
                                    sentence_lower = sentence.lower()
                                    for keyword in keyword_list:
                                        if keyword in sentence_lower:
                                            # Get context: current sentence + prev/next if available
                                            context_sentences = []
                                            if i > 0:
                                                context_sentences.append(sentences[i-1])
                                            context_sentences.append(sentence)
                                            if i < len(sentences) - 1:
                                                context_sentences.append(sentences[i+1])
                                            
                                            context = ' '.join(context_sentences)
                                            
                                            # Highlight the keyword in context (for JSON, we'll use **bold**)
                                            highlighted_context = re.sub(
                                                f'({re.escape(keyword)})',
                                                r'**\1**',
                                                context,
                                                flags=re.IGNORECASE
                                            )
                                            
                                            keyword_matches.append({
                                                'keyword': keyword,
                                                'context': highlighted_context,
                                                'sentence_index': i
                                            })
                            
                            # Extract links for recursion
                            links = []
                            for a_tag in soup.find_all('a', href=True):
                                href = a_tag['href']
                                full_url = urljoin(page_url, href)
                                # Only follow internal links or same domain
                                if urlparse(full_url).netloc == urlparse(url).netloc:
                                    links.append(full_url)

                            return {
                                "url": page_url,
                                "title": soup.title.string if soup.title else "No Title",
                                "text": clean_text,
                                "keyword_matches": keyword_matches,  # NEW: Detailed matches
                                "links": links,
                                "length": len(clean_text)
                            }
                        except Exception as e:
                            self.logger.error(f"Error crawling page {page_url}: {e}")
                            return None

                    # BFS Crawl
                    visited = set()
                    queue = [(url, 1)] # (url, current_depth)
                    results = []
                    
                    # If max_pages is 0 or negative, treat as unlimited (bounded by depth)
                    while queue and (max_pages <= 0 or len(results) < max_pages):
                        current_url, current_depth = queue.pop(0)
                        
                        if current_url in visited:
                            continue
                        
                        visited.add(current_url)
                        
                        # Check robots.txt for this specific URL if needed (simplified here to just base check above for now, 
                        # but ideally should check every URL if strict)
                        
                        page_data = crawl_page(current_url)
                        if page_data:
                            # Add to results (exclude links to keep JSON smaller)
                            result_entry = {k: v for k, v in page_data.items() if k != 'links'}
                            results.append(result_entry)
                            
                            # Add children to queue if depth allows
                            if current_depth < depth:
                                for link in page_data['links']:
                                    if link not in visited:
                                        queue.append((link, current_depth + 1))
                    
                    # Aggregate Report
                    total_keyword_matches = sum(len(r.get('keyword_matches', [])) for r in results)
                    
                    report = {
                        "base_url": url,
                        "pages_crawled": len(results),
                        "total_keyword_matches": total_keyword_matches,
                        "pages": []
                    }
                    
                    for res in results:
                        keyword_matches_data = res.get('keyword_matches', [])
                        
                        page_summary = {
                            "url": res['url'],
                            "title": res['title'],
                            "keyword_matches": keyword_matches_data,  # NEW: Full match details
                            "content_snippet": res['text'][:500] + "..." if len(res['text']) > 500 else res['text']
                        }
                        report["pages"].append(page_summary)

                    return json.dumps(report, indent=2)

                except Exception as e:
                    self.logger.error(f"Error crawling URL {url}: {str(e)}")
                    return json.dumps({"error": str(e)})

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
                    ensure_event_loop()
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
                    ensure_event_loop()
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
                    ensure_event_loop()
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
            def generate_report(research_data: str, report_type: str = "summary", format: str = "markdown") -> str:
                """
                Generate a structured research report from crawled data or research findings.
                
                Args:
                    research_data: JSON string or text summary of research findings
                    report_type: Type of report (summary, detailed, executive)
                    format: Output format (markdown, json, text)
                
                Returns:
                    Formatted report
                """
                try:
                    # Try to parse as JSON first
                    try:
                        data = json.loads(research_data)
                        is_json = True
                    except:
                        data = research_data
                        is_json = False
                    
                    if format == "markdown":
                        report = f"# Research Report\n\n"
                        report += f"**Report Type:** {report_type}\n\n"
                        
                        if is_json and isinstance(data, dict):
                            # Handle JSON from monitor_url
                            if "base_url" in data:
                                report += f"## Web Crawl Analysis\n\n"
                                report += f"**Target URL:** {data.get('base_url', 'N/A')}\n\n"
                                report += f"**Pages Crawled:** {data.get('pages_crawled', 0)}\n\n"
                                report += f"**Total Keyword Matches:** {data.get('total_keyword_matches', 0)}\n\n"
                                
                                if data.get('pages'):
                                    report += f"### Page Details\n\n"
                                    for i, page in enumerate(data['pages'], 1):
                                        report += f"#### {i}. {page.get('title', 'Untitled')}\n\n"
                                        report += f"**URL:** {page.get('url', 'N/A')}\n\n"
                                        
                                        # Display keyword matches with context
                                        keyword_matches = page.get('keyword_matches', [])
                                        if keyword_matches:
                                            report += f"**Keyword Matches Found:** {len(keyword_matches)}\n\n"
                                            for match in keyword_matches:
                                                keyword = match.get('keyword', 'N/A')
                                                context = match.get('context', 'No context available')
                                                report += f"- **Keyword:** `{keyword}`\n"
                                                report += f"  **Context:** {context}\n\n"
                                        else:
                                            report += "**Keyword Matches:** None\n\n"
                                        
                                        report += f"**Content Preview:**\n\n{page.get('content_snippet', 'No content')}\n\n"
                                        report += "---\n\n"
                            else:
                                # Generic JSON formatting
                                report += f"## Data Summary\n\n```json\n{json.dumps(data, indent=2)}\n```\n\n"
                        else:
                            # Plain text data
                            report += f"## Findings\n\n{data}\n\n"
                        
                        from datetime import datetime
                        report += f"\n---\n\n*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
                        return report
                    
                    elif format == "json":
                        if is_json:
                            return json.dumps(data, indent=2)
                        else:
                            return json.dumps({"content": data, "type": report_type}, indent=2)
                    
                    else:  # text format
                        if is_json and isinstance(data, dict):
                            return f"Report Type: {report_type}\n\n" + json.dumps(data, indent=2)
                        else:
                            return f"Report Type: {report_type}\n\n{data}"
                
                except Exception as e:
                    self.logger.error(f"Error generating report: {str(e)}")
                    return f"Error generating report: {str(e)}"

            # Register all tools
            self.logger.info("Adding tools to agent...")
            self.add_tool(search_web)
            self.add_tool(monitor_url)
            self.add_tool(analyze_competitor)
            self.add_tool(track_trends)
            self.add_tool(compliance_check)
            self.add_tool(generate_report)
            self.logger.info(f"Tools registered: {[t.name for t in self.tools]}")
            
        except Exception as e:
            self.logger.error(f"Error registering tools: {str(e)}", exc_info=True)
            raise

    def _run_agent_loop(self, system_prompt: str, user_prompt: str, task: Any) -> Dict[str, Any]:
        """
        Agent loop for market research tasks
        """
        # Customize prompt based on action
        if hasattr(task, 'action'):
            if task.action == 'web_crawler':
                # DIRECT TOOL EXECUTION
                inputs = task.input_data if hasattr(task, 'input_data') else {}
                url = inputs.get('topic', '')
                filters = inputs.get('filters', {})
                keywords = filters.get('industry', '') if filters else ''
                max_pages = inputs.get('max_pages', 5)
                depth = inputs.get('crawl_depth', 1)
                
                tool = next((t for t in self.tools if t.name == "monitor_url"), None)
                if tool:
                    self.logger.info(f"Directly executing tool: {tool.name}")
                    try:
                        result = tool.invoke({
                            "url": url, 
                            "keywords": keywords, 
                            "max_pages": max_pages, 
                            "depth": depth
                        })
                        return {
                            "response": result,
                            "action": task.action,
                            "completed_at": "now"
                        }
                    except Exception as e:
                        self.logger.error(f"Direct tool execution failed: {e}")

        # ... (Existing ReAct Agent Logic for other tasks) ... 

        # Optimize prompt for other tasks
        if hasattr(task, 'action'):
             # (Existing prompt setup logic can remain or move here if needed)
             pass 

        # Custom output parser for robust handling
        from langchain.agents.output_parsers import ReActSingleInputOutputParser
        from langchain.schema import AgentAction, AgentFinish, OutputParserException
        from langchain.agents import AgentExecutor, create_react_agent
        import re

        class RobustReActOutputParser(ReActSingleInputOutputParser):
            """Parser that tries to recover from common LLM formatting errors"""
            
            def parse(self, text: str):
                try:
                    # Clean up text - sometimes models put markdown blocks around everything
                    cleaned_text = text.strip()
                    if cleaned_text.startswith("```") and cleaned_text.endswith("```"):
                        # Remove first and last line
                        lines = cleaned_text.splitlines()
                        if len(lines) >= 2:
                            cleaned_text = "\n".join(lines[1:-1])
                    
                    # Try standard parsing first
                    return super().parse(cleaned_text)
                except Exception as e:
                    # Fallback recovery logic
                    
                    # Check if we have an Action and Action Input but formatting is slightly off
                    # e.g. "Action: tool_name\nAction Input: {json}" (missing Thought)
                    
                    action_match = re.search(r'Action:\s*([^\n]+)', text, re.IGNORECASE)
                    input_match = re.search(r'Action Input:\s*(.+)', text, re.IGNORECASE | re.DOTALL)
                    
                    if action_match and input_match:
                        action = action_match.group(1).strip()
                        action_input = input_match.group(1).strip()
                        
                        # Clean up action input if it has extra text at the end
                        # This is tricky without a clear delimiter, but let's try to parse JSON
                        # or take the first line if it looks like a simple string
                        
                        # Try to find a JSON block in the input
                        json_match = re.search(r'(\{.*\})', action_input, re.DOTALL)
                        if json_match:
                            action_input = json_match.group(1)
                        
                        return AgentAction(tool=action, tool_input=action_input, log=text)
                    
                    # Check if it's a Final Answer but malformed
                    final_answer_match = re.search(r'Final Answer:\s*(.+)', text, re.IGNORECASE | re.DOTALL)
                    if final_answer_match:
                        return AgentFinish(return_values={"output": final_answer_match.group(1).strip()}, log=text)
                        
                    # If we really can't parse it, but it looks like a final response (no Action keyword), treat as Final Answer
                    if "Action:" not in text:
                        return AgentFinish(return_values={"output": text}, log=text)
                        
                    raise OutputParserException(f"Could not parse LLM output: {text}")

        from langchain.prompts import PromptTemplate
        
        # Basic ReAct Prompt Template
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
        
        # Construct the ReAct agent with custom parser
        agent = create_react_agent(self.llm, self.tools, prompt, output_parser=RobustReActOutputParser())
        
        # Custom error handler that provides clear feedback to the LLM
        def handle_parsing_error(error) -> str:
            """Provide clear feedback when the LLM generates malformed output"""
            return f"formatting_error: {str(error)}. Please follow the format: Action: <tool_name> [newline] Action Input: <input>"
        
        # Create an agent executor with improved error handling
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=handle_parsing_error,
            max_iterations=10,  # Prevent infinite loops
            max_execution_time=300,  # 5 minute timeout
            return_intermediate_steps=True
        )
        
        # Execute
        try:
            # Combine system prompt and user prompt for the input
            full_input = f"{system_prompt}\n\nTask: {user_prompt}"
            
            result = agent_executor.invoke({"input": full_input})
            response_text = result.get("output", "")
            
            # Check if the result indicates a failure
            if not response_text or "Error executing agent" in response_text or "max iterations" in str(result).lower():
                self.logger.error(f"Agent failed to complete task properly. Result: {result}")
                # Don't raise immediately, try to return what we have
                if not response_text:
                     response_text = "Task executed but no final summary was generated."
            
        except Exception as e:
            # Agent execution failed - this will be caught by base class and returned as failed status
            self.logger.error(f"Agent execution failed: {e}", exc_info=True)
            raise  # Re-raise to let base class handle it properly

        return {
            "response": response_text,
            "action": task.action,
            "completed_at": "now" # In real code use datetime
        }
    
    def _get_system_prompt(self) -> str:
        """Market research agent system prompt"""
        return """CRITICAL INSTRUCTION:
    When using `monitor_url`, you MUST return the raw JSON output from the tool exactly as is.
    DO NOT summarize. DO NOT reformat. DO NOT wrap in markdown (no ```json blocks).
    Just return the JSON string. The frontend needs RAW JSON to render the dashboard.
    
    You are an advanced Market Research AI Agent.
    Your goal is to gather deep market intelligence, analyze competitors, and track industry trends.
    
    Guidelines:
    - ALWAYS cite sources (URLs) for your information.
    - When asked to monitor a specific site, use `monitor_url` and return the JSON.
    - Site scans are handled by the Site Scan agent, not this agent.
    - For OTHER tasks (competitor analysis, trends):
      - Structure it clearly with headings.
      - Include a "Key Findings" section.
      - Include a "Sources" section.
    """


# Create default market research agent instance
def create_market_research_agent(llm_provider: str = "openai") -> MarketResearchAgent:
    """Factory function to create market research agent. LLM provider/model via router (env: LLM_*)."""
    model = os.getenv("LLM_LOCAL_MODEL") or os.getenv("LLM_CLOUD_MODEL") or ""

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
