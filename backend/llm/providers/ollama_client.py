"""
Ollama client for LLM interactions

Extracted from Local-LLM project (backend/local_llm_staging/backend/ollama_client.py).

This module provides async HTTP client for Ollama API interactions including
model listing and streaming chat responses.
"""

import httpx
import os
import asyncio
import logging
from typing import List, Dict, Optional, AsyncIterator
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ModelInfo(BaseModel):
    """Model information"""
    id: str
    name: str
    provider: str
    size: Optional[str] = None
    contextWindow: Optional[int] = None
    description: Optional[str] = None


class OllamaClient:
    """
    Client for interacting with Ollama API
    
    Extracted from Local-LLM project. Provides async HTTP client for:
    - Health checks
    - Model listing
    - Streaming chat responses
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Ollama client
        
        Args:
            base_url: Ollama base URL (defaults to OLLAMA_BASE_URL env var or http://localhost:11434)
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        # Use a longer timeout for streaming requests (large models can take several minutes)
        # 30 seconds for regular requests, 15 minutes for streaming
        self.client = httpx.AsyncClient(timeout=30.0)
        self.streaming_timeout = float(os.getenv("OLLAMA_STREAMING_TIMEOUT", "900.0"))  # 15 minutes default

    async def health_check(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def get_models(self) -> List[ModelInfo]:
        """Fetch all available models from Ollama"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            
            models = []
            for model in data.get("models", []):
                model_name = model.get("name", "")
                
                # Filter out embedding models - they're not for chat
                if "embed" in model_name.lower():
                    continue
                
                # Parse model name to extract info
                parts = model_name.split(":")
                base_name = parts[0] if parts else model_name
                tag = parts[1] if len(parts) > 1 else "latest"
                
                # Extract size info from model name if available
                size = None
                if "20b" in model_name.lower() or "20.9b" in model_name.lower():
                    size = "20B"
                elif "7b" in model_name.lower() or "7.6b" in model_name.lower():
                    size = "7B"
                elif "13b" in model_name.lower():
                    size = "13B"
                elif "3b" in model_name.lower():
                    size = "3B"
                elif "8x7b" in model_name.lower() or "mixtral" in model_name.lower():
                    size = "8x7B"
                elif "70b" in model_name.lower():
                    size = "70B"
                
                # Get model details
                model_info = model.get("details", {})
                # parameter_size is a string like "20.9B", so we don't use it for contextWindow
                # contextWindow should be the actual context window size, not parameter count
                context_window = None
                
                # Generate description based on full model name (to catch variants like "instruct", "code", etc.)
                description = self._generate_description(model_name)
                
                models.append(ModelInfo(
                    id=model_name,
                    name=self._format_model_name(base_name),
                    provider=self._get_provider(base_name),
                    size=size,
                    contextWindow=context_window,
                    description=description
                ))
            
            return models
        except Exception as e:
            logger.error(f"Error fetching models: {e}", exc_info=True)
            return []

    async def chat_stream(
        self, 
        model: str, 
        messages: List[Dict[str, str]]
    ) -> AsyncIterator[str]:
        """Stream chat responses from Ollama"""
        # Create a client with longer timeout for streaming
        # Don't use context manager - let it be cleaned up when generator completes
        streaming_client = httpx.AsyncClient(timeout=self.streaming_timeout)
        
        try:
            async with streaming_client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        yield line
        except httpx.TimeoutException as e:
            logger.error(f"Timeout streaming chat: {e}", exc_info=True)
            yield f'{{"error": "Request timed out. Large models may take several minutes to respond."}}'
        except Exception as e:
            logger.error(f"Error streaming chat: {e}", exc_info=True)
            yield f'{{"error": "Failed to stream response: {str(e)}"}}'
        finally:
            # Close client after generator yields are complete
            # The finally block executes after the generator is done
            try:
                if not streaming_client.is_closed:
                    # Schedule cleanup in background to avoid blocking
                    asyncio.ensure_future(self._close_client_safely(streaming_client))
            except Exception:
                # Ignore cleanup errors - client will be GC'd if needed
                pass
    
    async def _close_client_safely(self, client: httpx.AsyncClient):
        """Safely close client"""
        try:
            await asyncio.sleep(0.1)  # Brief delay to ensure generator is done
            if not client.is_closed:
                await client.aclose()
        except Exception:
            # Ignore cleanup errors
            pass

    def _format_model_name(self, name: str) -> str:
        """Format model name for display"""
        # Convert snake_case or kebab-case to Title Case
        name = name.replace("-", " ").replace("_", " ")
        return " ".join(word.capitalize() for word in name.split())

    def _get_provider(self, name: str) -> str:
        """Determine provider from model name"""
        name_lower = name.lower()
        if "llama" in name_lower or "codellama" in name_lower:
            return "Meta"
        elif "mistral" in name_lower or "mixtral" in name_lower:
            return "Mistral AI"
        elif "phi" in name_lower:
            return "Microsoft"
        elif "gemma" in name_lower:
            return "Google"
        elif "qwen" in name_lower:
            return "Alibaba"
        elif "deepseek" in name_lower:
            return "DeepSeek"
        elif "gpt-oss" in name_lower or "gptoss" in name_lower:
            return "Open Source"
        else:
            return "Community"

    def _generate_description(self, name: str) -> str:
        """Generate a description based on model name"""
        name_lower = name.lower()
        if "code" in name_lower:
            return "Specialized for code generation and programming tasks"
        elif "deepseek" in name_lower:
            if "r1" in name_lower:
                return "Reasoning-focused model with enhanced problem-solving capabilities"
            return "High-performance model optimized for reasoning and coding"
        elif "gpt-oss" in name_lower or "gptoss" in name_lower:
            return "Open-source GPT-style model for general purpose tasks"
        elif "qwen" in name_lower:
            if "instruct" in name_lower:
                return "Instruction-tuned model optimized for following user instructions and conversations"
            elif "code" in name_lower:
                return "Code-specialized model for programming and technical tasks"
            return "High-performance multilingual model with strong reasoning capabilities"
        elif "mistral" in name_lower:
            return "Balanced performance and quality"
        elif "mixtral" in name_lower:
            return "Mixture of experts for complex reasoning"
        elif "llama" in name_lower:
            return "Fast and efficient for everyday tasks"
        else:
            return "General purpose language model"

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
