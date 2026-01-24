"""
Base Agent Framework for Agent_X
Provides core functionality for all AI agents

This module uses the LLM Router for all LLM calls.
All LLM provider selection and usage tracking is handled centrally.
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
from datetime import datetime

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import BaseTool
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

# Import LLM Router
from llm.router import LLMRouter, Intent, get_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class AgentConfig(BaseModel):
    """Configuration for an agent"""
    agent_type: str
    name: str
    description: str
    llm_provider: str = "openai"  # legacy; router uses LLM_MODE / LLM_PRIORITY
    model: str = ""  # optional preference; router uses LLM_LOCAL_MODEL / LLM_CLOUD_MODEL when empty
    temperature: float = 0.7
    max_tokens: int = 2000
    tools: List[str] = Field(default_factory=list)


class TaskInput(BaseModel):
    """Input for a task"""
    task_id: str
    action: str
    input_data: Dict[str, Any]
    user_id: Optional[str] = None
    priority: str = "medium"


class TaskResult(BaseModel):
    """Result of a task execution"""
    task_id: str
    status: str  # completed, failed
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    conversation: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """
    Base class for all AI agents
    
    Provides:
    - LLM integration via LLM Router (local-first with cloud fallback)
    - Tool registration and execution
    - Memory management
    - Logging and error handling
    - Conversation tracking
    
    All LLM calls go through the centralized LLM Router which handles:
    - Provider selection (local-first)
    - Automatic fallback
    - Usage tracking (tokens, costs, latency)
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = logging.getLogger(f"Agent.{config.agent_type}")
        self.tools: List[BaseTool] = []
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Initialize LLM Router
        self.router = get_router()
        
        # Initialize LLM through router
        self.llm = self._create_llm()
        
        # Register agent-specific tools
        self._register_tools()
        
        self.logger.info(f"Initialized {config.name} with {len(self.tools)} tools")
    
    def _create_llm(self):
        """
        Create LLM through centralized router
        
        The router handles:
        - Local-first provider selection
        - Automatic fallback if local unavailable
        - Usage tracking
        - Health checks
        """
        # Determine intent based on agent type
        intent = self._get_intent_for_agent()
        
        # Get model preference (if specified in config)
        model_preference = None
        if self.config.model:
            # If model is specified, try to use it
            # Format: "provider:model" or just "model"
            model_preference = self.config.model
        
        # Get LLM client from router
        # Router will select best provider based on:
        # - LLM_MODE (local_first, cloud_only, local_only)
        # - Provider health
        # - Priority order
        llm = self.router.get_chat_client(
            caller=self.config.agent_type,
            intent=intent,
            model_preference=model_preference,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        self.logger.info(
            f"LLM client created via router - Agent: {self.config.agent_type}, "
            f"Intent: {intent.value if intent else 'chat'}, "
            f"Model preference: {model_preference or 'auto'}"
        )
        
        return llm
    
    def _get_intent_for_agent(self) -> Optional[Intent]:
        """
        Determine LLM intent based on agent type
        
        This helps the router select the best model for the task.
        """
        agent_type = self.config.agent_type.lower()
        
        if "blog" in agent_type:
            return Intent.LONG_FORM
        elif "research" in agent_type or "analysis" in agent_type:
            return Intent.ANALYSIS
        elif "code" in agent_type:
            return Intent.CODE
        else:
            return Intent.CHAT
    
    @abstractmethod
    def _register_tools(self):
        """Register agent-specific tools - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get agent-specific system prompt - must be implemented by subclasses"""
        pass
    
    def add_tool(self, tool: BaseTool):
        """Add a tool to the agent"""
        self.tools.append(tool)
        self.logger.debug(f"Added tool: {tool.name}")
    
    def execute_task(self, task: TaskInput) -> TaskResult:
        """
        Execute a task with the agent
        
        Main entry point for task execution. Handles:
        - System prompt setup
        - Tool execution loop
        - Error handling
        - Result formatting
        """
        start_time = time.time()
        self.logger.info(f"Executing task {task.task_id}: {task.action}")
        
        try:
            # Build conversation context
            system_prompt = self._get_system_prompt()
            user_prompt = self._build_user_prompt(task)
            
            # Execute agent loop
            result = self._run_agent_loop(system_prompt, user_prompt, task)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            return TaskResult(
                task_id=task.task_id,
                status="completed",
                output=result,
                conversation=self.conversation_history,
                metadata={
                    "execution_time": execution_time,
                    "tools_used": [t.name for t in self.tools],
                    "model": self.config.model
                }
            )
            
        except Exception as e:
            self.logger.error(f"Task {task.task_id} failed: {str(e)}", exc_info=True)
            return TaskResult(
                task_id=task.task_id,
                status="failed",
                error=str(e),
                conversation=self.conversation_history,
                metadata={"execution_time": time.time() - start_time}
            )
    
    def _build_user_prompt(self, task: TaskInput) -> str:
        """Build user prompt from task input"""
        prompt_parts = [f"Action: {task.action}"]
        
        for key, value in task.input_data.items():
            prompt_parts.append(f"{key}: {value}")
        
        return "\n".join(prompt_parts)
    
    def _run_agent_loop(self, system_prompt: str, user_prompt: str, task: TaskInput) -> Dict[str, Any]:
        """
        Run the main agent loop using ReAct pattern
        
        For now, uses a simple LLM call. Can be enhanced with:
        - Tool calling loop
        - Multi-step reasoning
        - Self-reflection
        """
        # Log conversation
        self.conversation_history.append({
            "role": "system",
            "content": system_prompt
        })
        self.conversation_history.append({
            "role": "user",
            "content": user_prompt
        })
        
        # Create messages
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Get LLM response
        response = self.llm.invoke(messages)
        
        # Log response
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content
        })
        
        # Parse and return result
        return {
            "response": response.content,
            "action": task.action,
            "completed_at": datetime.utcnow().isoformat()
        }
    
    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.logger.debug("Conversation history reset")
