"""
LLM Router - Centralized LLM provider selection with local-first fallback

This is the SINGLE POINT OF ENTRY for all LLM calls in AgentX.

Responsibilities:
1. Decide provider based on mode, health, and intent
2. Implement local-first strategy (Ollama → OpenAI → Anthropic)
3. Handle fallbacks automatically
4. Track all usage (tokens, costs, latency)
5. Provide unified interface for agents and assistants

NO component should call OpenAI, Anthropic, or Ollama directly.
All LLM calls MUST go through this router.
"""

import os
import time
import logging
import re
from typing import Optional, Dict, Any, List, Union, AsyncIterator
from enum import Enum

from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama

from .model_registry import ModelRegistry, Provider, Intent, get_registry
from .usage_tracker import UsageTracker, get_tracker
from .health import HealthChecker, ProviderStatus, get_health_checker
from ..providers.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


from langchain_core.runnables import Runnable, RunnableConfig

class _TrackedLangChainClient(Runnable):
    """
    Wrapper around a LangChain chat model that tracks usage on invoke().

    LangChain clients (ChatOllama, ChatOpenAI, etc.) are Pydantic models and
    reject arbitrary attribute assignment. We avoid monkey-patching by
    wrapping the client and delegating invoke + __getattr__.
    
    Inheriting from Runnable ensures that methods like .bind() wrap THIS object
    instead of the underlying client, preserving the tracking behavior.
    """

    def __init__(
        self,
        client,
        tracker,
        caller: str,
        provider: "Provider",
        model_id: str,
        intent: "Intent",
        start_time: float,
        fallback_used: bool,
        fallback_reason: Optional[str],
        estimate_tokens_fn,
    ):
        self._client = client
        self._tracker = tracker
        self._caller = caller
        self._provider = provider
        self._model_id = model_id
        self._intent = intent
        self._start_time = start_time
        self._fallback_used = fallback_used
        self._fallback_reason = fallback_reason
        self._estimate_tokens = estimate_tokens_fn

    def invoke(self, input: Union[str, List[BaseMessage]], config: Optional[RunnableConfig] = None, **kwargs):
        invoke_start = time.time()
        try:
            # Handle input normalization if needed, but usually it's List[BaseMessage]
            response = self._client.invoke(input, config=config, **kwargs)
            
            latency_ms = (time.time() - invoke_start) * 1000
            
            # Extract text for token estimation
            input_text = ""
            if isinstance(input, str):
                input_text = input
            elif isinstance(input, list):
                input_text = "\n".join([getattr(m, "content", str(m)) for m in input])
                
            output_text = getattr(response, "content", str(response))
            
            input_tokens = self._estimate_tokens(input_text)
            output_tokens = self._estimate_tokens(output_text)
            
            self._tracker.record_usage(
                caller=self._caller,
                provider=self._provider.value,
                model_id=self._model_id,
                intent=self._intent.value,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                success=True,
                fallback_used=self._fallback_used,
                fallback_reason=self._fallback_reason,
            )
            
            # Inject usage into response metadata if possible
            if hasattr(response, "response_metadata") and isinstance(response.response_metadata, dict):
                usage_record = self._tracker.records[-1]  # Get the record we just added
                response.response_metadata["llm_usage"] = usage_record.to_dict()
                
            return response
        except Exception as e:
            latency_ms = (time.time() - invoke_start) * 1000
            self._tracker.record_usage(
                caller=self._caller,
                provider=self._provider.value,
                model_id=self._model_id,
                intent=self._intent.value,
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                success=False,
                error=str(e),
                fallback_used=self._fallback_used,
                fallback_reason=self._fallback_reason,
            )
            raise

    def __getattr__(self, name: str):
        return getattr(self._client, name)


class LLMMode(str, Enum):
    """LLM routing mode"""
    LOCAL_FIRST = "local_first"  # Try local, fallback to cloud
    CLOUD_ONLY = "cloud_only"  # Only use cloud providers
    LOCAL_ONLY = "local_only"  # Only use local providers


class LLMRouter:
    """
    Centralized LLM router with local-first fallback
    
    Usage:
        router = LLMRouter()
        
        # For agents (LangChain)
        llm = router.get_chat_client(
            caller="blog_agent",
            intent=Intent.LONG_FORM,
            temperature=0.7
        )
        
        # For assistants (direct completion)
        response = await router.generate_completion(
            caller="fintech_assistant",
            prompt="...",
            model_preference="qwen2.5:7b-instruct"
        )
    """
    
    def __init__(
        self,
        mode: Optional[LLMMode] = None,
        priority: Optional[List[str]] = None,
        fallback_enabled: bool = True,
        registry: Optional[ModelRegistry] = None,
        tracker: Optional[UsageTracker] = None,
        health_checker: Optional[HealthChecker] = None
    ):
        """
        Initialize LLM router
        
        Args:
            mode: Routing mode (defaults to env var or LOCAL_FIRST)
            priority: Provider priority list (defaults to env var or ollama,openai,anthropic)
            fallback_enabled: Whether to enable fallback
            registry: Model registry (uses global if None)
            tracker: Usage tracker (uses global if None)
            health_checker: Health checker (uses global if None)
        """
        # Load configuration from environment
        mode_str = mode or os.getenv("LLM_MODE", "local_first")
        self.mode = LLMMode(mode_str.lower())
        
        priority_str = priority or os.getenv("LLM_PRIORITY", "ollama,openai,anthropic")
        self.priority = [p.strip().lower() for p in priority_str.split(",")]
        
        self.fallback_enabled = fallback_enabled if fallback_enabled is not None else (
            os.getenv("LLM_FALLBACK_ENABLED", "true").lower() == "true"
        )
        
        # Initialize components
        self.registry = registry or get_registry()
        self.tracker = tracker or get_tracker()
        self.health_checker = health_checker or get_health_checker()
        
        # Default models from env
        self.default_local_model = os.getenv("LLM_LOCAL_MODEL", "qwen2.5:7b-instruct")
        self.default_cloud_model = os.getenv("LLM_CLOUD_MODEL", "openai:gpt-4-turbo-preview")
        self.model_overrides = self._load_model_overrides()
        
        logger.info(
            f"🔀 LLM Router initialized - Mode: {self.mode.value}, "
            f"Priority: {self.priority}, Fallback: {self.fallback_enabled}"
        )
        
        # Initialize health checks (async, non-blocking)
        # This pre-warms the health cache
        self._initialize_health_checks()

    def _normalize_caller_key(self, caller: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", (caller or "").strip().lower()).strip("_")

    def _load_model_overrides(self) -> Dict[str, Dict[str, str]]:
        """
        Load model override rules from environment.

        Supported env vars:
        - LLM_MODEL_OVERRIDES:
          "caller:blog=ollama:llama3.2:8b,intent:long_form=ollama:llama3.2:8b"
        - LLM_MODEL_OVERRIDE_<CALLER>:
          "ollama:llama3.2:8b" (caller key normalized to upper snake case)
        - LLM_MODEL_OVERRIDE_INTENT_<INTENT>:
          "ollama:deepseek-r1:7b"
        """
        overrides: Dict[str, Dict[str, str]] = {"caller": {}, "intent": {}}

        encoded = (os.getenv("LLM_MODEL_OVERRIDES", "") or "").strip()
        if encoded:
            parts = [p.strip() for p in encoded.split(",") if p.strip()]
            for part in parts:
                if "=" not in part:
                    continue
                key, model = part.split("=", 1)
                key = key.strip().lower()
                model = model.strip()
                if not model:
                    continue

                if key.startswith("caller:"):
                    caller_key = self._normalize_caller_key(key.split(":", 1)[1])
                    if caller_key:
                        overrides["caller"][caller_key] = model
                elif key.startswith("intent:"):
                    intent_key = key.split(":", 1)[1].strip().lower()
                    if intent_key:
                        overrides["intent"][intent_key] = model

        for env_name, value in os.environ.items():
            if not value:
                continue
            if env_name.startswith("LLM_MODEL_OVERRIDE_INTENT_"):
                intent_key = env_name.replace("LLM_MODEL_OVERRIDE_INTENT_", "", 1).strip().lower()
                if intent_key:
                    overrides["intent"][intent_key] = value.strip()
            elif env_name.startswith("LLM_MODEL_OVERRIDE_"):
                suffix = env_name.replace("LLM_MODEL_OVERRIDE_", "", 1).strip()
                if suffix and suffix != "INTENT":
                    caller_key = self._normalize_caller_key(suffix.lower())
                    if caller_key:
                        overrides["caller"][caller_key] = value.strip()

        if overrides["caller"] or overrides["intent"]:
            logger.info(
                "🧭 LLM model overrides loaded - callers: %s, intents: %s",
                sorted(overrides["caller"].keys()),
                sorted(overrides["intent"].keys()),
            )

        return overrides

    def _resolve_model_preference(
        self,
        caller: str,
        intent: Optional[Intent],
        model_preference: Optional[str],
    ) -> Optional[str]:
        """
        Resolve effective model preference with override precedence.

        Priority:
        1) Caller-specific override
        2) Intent-specific override
        3) Provided model_preference
        """
        caller_key = self._normalize_caller_key(caller)
        intent_key = (intent.value if intent else "").lower()

        caller_override = self.model_overrides.get("caller", {}).get(caller_key)
        if caller_override:
            logger.info(
                "🎯 Caller model override applied - caller: %s, model: %s",
                caller,
                caller_override,
            )
            return caller_override

        intent_override = self.model_overrides.get("intent", {}).get(intent_key)
        if intent_override:
            logger.info(
                "🎯 Intent model override applied - intent: %s, model: %s",
                intent_key,
                intent_override,
            )
            return intent_override

        return model_preference
    
    def _initialize_health_checks(self):
        """Initialize health checks for all providers (non-blocking)"""
        import asyncio
        
        async def check_all():
            """Check health of all providers"""
            for provider_name in self.priority:
                if provider_name == "ollama":
                    await self.health_checker.check_ollama()
                # OpenAI and Anthropic are checked synchronously (just API key presence)
        
        # Run in background (don't wait)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule task
                asyncio.create_task(check_all())
            else:
                # If no loop, create one and run
                asyncio.run(check_all())
        except RuntimeError:
            # No event loop, skip (will check on first use)
            pass
    
    def get_chat_client(
        self,
        caller: str,
        intent: Optional[Intent] = None,
        model_preference: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ):
        """
        Get a LangChain chat client for agents
        
        This method:
        1. Selects the best provider based on mode and health
        2. Creates appropriate LangChain client
        3. Returns client ready for use
        
        Args:
            caller: Name of the agent/assistant making the call
            intent: Usage intent (for model selection)
            model_preference: Preferred model ID (optional)
            temperature: Temperature setting
            max_tokens: Maximum tokens
            **kwargs: Additional client parameters
            
        Returns:
            LangChain chat model instance
        """
        start_time = time.time()
        
        # Select provider and model
        provider, model_id, fallback_used, fallback_reason = self._select_provider(
            caller=caller,
            intent=intent,
            model_preference=model_preference
        )
        
        # Get model info
        model_info = self.registry.get_model(model_id)
        if not model_info:
            raise ValueError(f"Model {model_id} not found in registry")
        
        # Create LangChain client
        client = self._create_langchain_client(
            provider=provider,
            model_id=model_id,
            model_info=model_info,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Log selection
        logger.info(
            f"✅ LLM Client selected - Caller: {caller}, Provider: {provider.value}, "
            f"Model: {model_id}, Fallback: {fallback_used}"
        )
        
        # Wrap client to track usage
        return self._wrap_client_for_tracking(
            client=client,
            caller=caller,
            provider=provider,
            model_id=model_id,
            intent=intent or Intent.CHAT,
            start_time=start_time,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason
        )
    
    async def generate_completion(
        self,
        caller: str,
        prompt: str,
        model_preference: Optional[str] = None,
        intent: Optional[Intent] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate completion (for assistants using direct API calls)
        
        This method:
        1. Selects provider and model
        2. Calls appropriate API
        3. Tracks usage
        4. Returns response with metadata
        
        Args:
            caller: Name of the assistant making the call
            prompt: Full prompt text
            model_preference: Preferred model (optional)
            intent: Usage intent
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with:
            - text: Response text
            - provider: Provider used
            - model_id: Model used
            - usage: Usage metadata (tokens, cost, latency)
        """
        start_time = time.time()
        
        # Select provider and model
        provider, model_id, fallback_used, fallback_reason = self._select_provider(
            caller=caller,
            intent=intent,
            model_preference=model_preference
        )
        
        # Get model info
        model_info = self.registry.get_model(model_id)
        if not model_info:
            raise ValueError(f"Model {model_id} not found in registry")
        
        # Generate completion
        try:
            if provider == Provider.OLLAMA:
                response_text = await self._generate_ollama(
                    model_id=model_id,
                    prompt=prompt,
                    **kwargs
                )
            elif provider == Provider.OPENAI:
                response_text = await self._generate_openai(
                    model_id=model_id,
                    prompt=prompt,
                    **kwargs
                )
            elif provider == Provider.ANTHROPIC:
                response_text = await self._generate_anthropic(
                    model_id=model_id,
                    prompt=prompt,
                    **kwargs
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Estimate tokens (for local models, we estimate)
            input_tokens = self._estimate_tokens(prompt)
            output_tokens = self._estimate_tokens(response_text)
            
            # Track usage
            usage_record = self.tracker.record_usage(
                caller=caller,
                provider=provider.value,
                model_id=model_id,
                intent=(intent or Intent.CHAT).value,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                success=True,
                fallback_used=fallback_used,
                fallback_reason=fallback_reason
            )
            
            return {
                "text": response_text,
                "provider": provider.value,
                "model_id": model_id,
                "usage": usage_record.to_dict()
            }
            
        except Exception as e:
            # Track failure
            latency_ms = (time.time() - start_time) * 1000
            self.tracker.record_usage(
                caller=caller,
                provider=provider.value,
                model_id=model_id,
                intent=(intent or Intent.CHAT).value,
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                success=False,
                error=str(e),
                fallback_used=fallback_used,
                fallback_reason=fallback_reason
            )
            raise
    
    async def stream_completion(
        self,
        caller: str,
        prompt: str,
        model_preference: Optional[str] = None,
        intent: Optional[Intent] = None,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream completion chunks.
        
        Yields:
            Dict with type: "meta" | "chunk" | "usage"
        """
        start_time = time.time()
        
        # Select provider and model
        provider, model_id, fallback_used, fallback_reason = self._select_provider(
            caller=caller,
            intent=intent,
            model_preference=model_preference
        )
        
        # Get model info
        model_info = self.registry.get_model(model_id)
        if not model_info:
            raise ValueError(f"Model {model_id} not found in registry")
            
        # Yield metadata first
        yield {
            "type": "control",
            "event": "metadata",
            "data": {
                "provider": provider.value,
                "model_id": model_id,
                "fallback_used": fallback_used,
                "fallback_reason": fallback_reason
            }
        }
        
        accumulated_text = ""
        
        try:
            stream_gen = None
            if provider == Provider.OLLAMA:
                stream_gen = self._stream_ollama(model_id, prompt, **kwargs)
            elif provider == Provider.OPENAI:
                stream_gen = self._stream_openai(model_id, prompt, **kwargs)
            elif provider == Provider.ANTHROPIC:
                stream_gen = self._stream_anthropic(model_id, prompt, **kwargs)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            async for chunk_text in stream_gen:
                if chunk_text:
                    accumulated_text += chunk_text
                    yield {
                        "type": "content",
                        "content": chunk_text
                    }
            
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            input_tokens = self._estimate_tokens(prompt)
            output_tokens = self._estimate_tokens(accumulated_text)
            
            # Record usage
            self.tracker.record_usage(
                caller=caller,
                provider=provider.value,
                model_id=model_id,
                intent=(intent or Intent.CHAT).value,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                success=True,
                fallback_used=fallback_used,
                fallback_reason=fallback_reason
            )
            
            # Yield usage
            yield {
                "type": "control",
                "event": "usage",
                "data": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "latency_ms": latency_ms,
                    "cost": 0.0 # TODO: Calculate cost
                }
            }
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.tracker.record_usage(
                caller=caller,
                provider=provider.value,
                model_id=model_id,
                intent=(intent or Intent.CHAT).value,
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                success=False,
                error=str(e),
                fallback_used=fallback_used,
                fallback_reason=fallback_reason
            )
            # Yield error
            yield {
                "type": "error",
                "error": str(e)
            }
            raise
    
    def _select_provider(
        self,
        caller: str,
        intent: Optional[Intent] = None,
        model_preference: Optional[str] = None
    ) -> tuple[Provider, str, bool, Optional[str]]:
        """
        Select provider and model based on mode, health, and priority
        
        Returns:
            Tuple of (provider, model_id, fallback_used, fallback_reason)
        """
        # Resolve effective model preference (caller/intent overrides may replace defaults)
        effective_model_preference = self._resolve_model_preference(
            caller=caller,
            intent=intent,
            model_preference=model_preference,
        )

        # If model preference is specified, try to use it
        preferred_provider = None
        preferred_model = None
        
        if effective_model_preference:
            # Check if it's a full model ID (provider:model)
            if ":" in effective_model_preference:
                parts = effective_model_preference.split(":", 1)
                potential_provider = parts[0].lower()
                
                # Check if first part is a known provider
                if potential_provider in ["ollama", "openai", "anthropic"]:
                    # Full model ID (e.g., "ollama:qwen2.5:7b-instruct")
                    preferred_provider = potential_provider
                    preferred_model = parts[1]
                else:
                    # Model name with colon but not provider prefix (e.g., "qwen2.5:7b-instruct")
                    # Try to find in registry
                    model_info = None
                    for provider in [Provider.OLLAMA, Provider.OPENAI, Provider.ANTHROPIC]:
                        model_id = self.registry.parse_model_id(provider.value, effective_model_preference)
                        model_info = self.registry.get_model(model_id)
                        if model_info:
                            preferred_provider = provider.value
                            preferred_model = effective_model_preference
                            break
                    
                    if not model_info:
                        # Default to local
                        preferred_provider = Provider.OLLAMA.value
                        preferred_model = effective_model_preference
            else:
                # Just model name (e.g., "qwen2.5:7b-instruct" without provider prefix)
                preferred_model = effective_model_preference
                # Try to find in registry
                model_info = None
                for provider in [Provider.OLLAMA, Provider.OPENAI, Provider.ANTHROPIC]:
                    model_id = self.registry.parse_model_id(provider.value, preferred_model)
                    model_info = self.registry.get_model(model_id)
                    if model_info:
                        preferred_provider = provider.value
                        break
                
                if not model_info:
                    # Default to local
                    preferred_provider = Provider.OLLAMA.value
        
        # Determine provider priority based on mode
        if self.mode == LLMMode.LOCAL_ONLY:
            candidate_providers = [p for p in self.priority if p == "ollama"]
        elif self.mode == LLMMode.CLOUD_ONLY:
            candidate_providers = [p for p in self.priority if p in ["openai", "anthropic"]]
        else:  # LOCAL_FIRST
            candidate_providers = self.priority
        
        # Try providers in priority order
        fallback_used = False
        fallback_reason = None
        
        for provider_name in candidate_providers:
            try:
                provider = Provider(provider_name)
                
                # Check health (async for Ollama if needed)
                if provider_name == "ollama":
                    # For Ollama, we need async check
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # If loop is running, use cached status or schedule check
                            status = self.health_checker.get_provider_status(provider_name)
                            # If unknown, try to check (non-blocking)
                            if status == ProviderStatus.UNKNOWN:
                                asyncio.create_task(self.health_checker.check_ollama())
                                # Assume healthy for now, will fail on actual call if not
                                status = ProviderStatus.HEALTHY
                        else:
                            # No loop, check synchronously (creates new loop)
                            status = asyncio.run(self.health_checker.check_ollama())
                    except RuntimeError:
                        # No event loop available, use cached status
                        status = self.health_checker.get_provider_status(provider_name)
                        if status == ProviderStatus.UNKNOWN:
                            # Assume healthy, will fail on actual call if not
                            status = ProviderStatus.HEALTHY
                else:
                    # For cloud providers, synchronous check is fine
                    status = self.health_checker.get_provider_status(provider_name)
                
                if status != ProviderStatus.HEALTHY:
                    logger.debug(f"Provider {provider_name} is not healthy: {status}")
                    if self.fallback_enabled and provider_name != candidate_providers[-1]:
                        fallback_used = True
                        fallback_reason = f"Provider {provider_name} unhealthy ({status.value})"
                        continue
                    else:
                        raise ValueError(f"Provider {provider_name} is not available ({status.value})")
                
                # Select model
                if effective_model_preference and provider_name == preferred_provider:
                    model_id = self.registry.parse_model_id(provider_name, preferred_model)
                else:
                    # Use LLM_LOCAL_MODEL / LLM_CLOUD_MODEL when set; else registry default
                    if provider_name == "ollama":
                        default_val = (self.default_local_model or "").strip()
                        if default_val:
                            # Allow "llama3.1:8b" or "ollama:llama3.1:8b"
                            model_id = default_val if default_val.startswith("ollama:") else self.registry.parse_model_id("ollama", default_val)
                        else:
                            model_id = None
                        if not model_id:
                            reg = self.registry.get_default_model_for_provider(provider, intent)
                            model_id = reg.id if reg else None
                    elif provider_name in ("openai", "anthropic"):
                        dc = (self.default_cloud_model or "").strip()
                        if dc.startswith(f"{provider_name}:"):
                            model_id = dc
                        else:
                            reg = self.registry.get_default_model_for_provider(provider, intent)
                            model_id = reg.id if reg else None
                    else:
                        reg = self.registry.get_default_model_for_provider(provider, intent)
                        model_id = reg.id if reg else None
                    if not model_id:
                        if self.fallback_enabled and provider_name != candidate_providers[-1]:
                            fallback_used = True
                            fallback_reason = f"No suitable model for {provider_name}"
                            continue
                        else:
                            raise ValueError(f"No model available for provider {provider_name}")
                
                # Verify model exists
                model_info = self.registry.get_model(model_id)
                if not model_info:
                    if self.fallback_enabled and provider_name != candidate_providers[-1]:
                        fallback_used = True
                        fallback_reason = f"Model {model_id} not found"
                        continue
                    else:
                        raise ValueError(f"Model {model_id} not found")
                
                return (provider, model_id, fallback_used, fallback_reason)
                
            except ValueError as e:
                if self.fallback_enabled and provider_name != candidate_providers[-1]:
                    fallback_used = True
                    fallback_reason = str(e)
                    continue
                else:
                    raise
        
        # If we get here, all providers failed
        raise RuntimeError(
            f"All providers failed. Last error: {fallback_reason}. "
            f"Mode: {self.mode.value}, Priority: {self.priority}"
        )
    
    def _create_langchain_client(
        self,
        provider: Provider,
        model_id: str,
        model_info: Any,
        temperature: float,
        max_tokens: int,
        **kwargs
    ):
        """Create appropriate LangChain client"""
        model_name = model_id.split(":", 1)[1] if ":" in model_id else model_id
        
        if provider == Provider.OLLAMA:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            return ChatOllama(
                model=model_name,
                temperature=temperature,
                base_url=base_url,
                **kwargs
            )
        elif provider == Provider.OPENAI:
            # Newer OpenAI models (o1, o3, gpt-5.x) dropped the `max_tokens`
            # parameter in favour of `max_completion_tokens`. langchain-openai
            # 0.1.x doesn't have a first-class field for it, but we can pass it
            # via model_kwargs which is forwarded verbatim to the OpenAI API.
            _uses_completion_tokens = any(
                model_name.startswith(p) for p in ("o1", "o3", "gpt-5")
            )
            if _uses_completion_tokens:
                return ChatOpenAI(
                    model=model_name,
                    temperature=temperature,
                    api_key=os.getenv("OPENAI_API_KEY"),
                    model_kwargs={"max_completion_tokens": max_tokens},
                    **kwargs
                )
            else:
                return ChatOpenAI(
                    model=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    api_key=os.getenv("OPENAI_API_KEY"),
                    **kwargs
                )
        elif provider == Provider.ANTHROPIC:
            return ChatAnthropic(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _wrap_client_for_tracking(
        self,
        client,
        caller: str,
        provider: Provider,
        model_id: str,
        intent: Intent,
        start_time: float,
        fallback_used: bool,
        fallback_reason: Optional[str]
    ):
        """Wrap LangChain client to track usage via a wrapper (no monkey-patching).

        LangChain chat models are Pydantic-based and reject attribute assignment.
        We return a _TrackedLangChainClient that delegates invoke + other attrs.
        """
        return _TrackedLangChainClient(
            client=client,
            tracker=self.tracker,
            caller=caller,
            provider=provider,
            model_id=model_id,
            intent=intent,
            start_time=start_time,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            estimate_tokens_fn=self._estimate_tokens,
        )
    
    async def _generate_ollama(self, model_id: str, prompt: str, **kwargs) -> str:
        """Generate using Ollama"""
        model_name = model_id.split(":", 1)[1] if ":" in model_id else model_id
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        client = OllamaClient(base_url=base_url)
        try:
            response = await client.generate(
                model=model_name,
                prompt=prompt,
                stream=False
            )
            return response
        finally:
            await client.close()
    
    async def _generate_openai(self, model_id: str, prompt: str, **kwargs) -> str:
        """Generate using OpenAI (direct API)"""
        # For now, use LangChain client wrapped
        # In production, could use direct API for better control
        model_name = model_id.split(":", 1)[1] if ":" in model_id else model_id
        client = ChatOpenAI(
            model=model_name,
            api_key=os.getenv("OPENAI_API_KEY"),
            **kwargs
        )
        messages = [HumanMessage(content=prompt)]
        response = client.invoke(messages)
        return response.content
    
    async def _generate_anthropic(self, model_id: str, prompt: str, **kwargs) -> str:
        """Generate using Anthropic (direct API)"""
        model_name = model_id.split(":", 1)[1] if ":" in model_id else model_id
        client = ChatAnthropic(
            model=model_name,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            **kwargs
        )
        messages = [HumanMessage(content=prompt)]
        response = client.invoke(messages)
        return response.content

    async def _stream_ollama(self, model_id: str, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream using Ollama"""
        import json
        model_name = model_id.split(":", 1)[1] if ":" in model_id else model_id
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        client = OllamaClient(base_url=base_url)
        try:
            async for line in await client.generate(
                model=model_name,
                prompt=prompt,
                stream=True
            ):
                if not line: continue
                try:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
                except Exception:
                    pass
        finally:
            await client.close()

    async def _stream_openai(self, model_id: str, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream using OpenAI"""
        model_name = model_id.split(":", 1)[1] if ":" in model_id else model_id
        client = ChatOpenAI(
            model=model_name,
            api_key=os.getenv("OPENAI_API_KEY"),
            streaming=True,
            **kwargs
        )
        async for chunk in client.astream(prompt):
            if hasattr(chunk, "content"):
                yield chunk.content
            elif isinstance(chunk, str):
                yield chunk

    async def _stream_anthropic(self, model_id: str, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream using Anthropic"""
        model_name = model_id.split(":", 1)[1] if ":" in model_id else model_id
        client = ChatAnthropic(
            model=model_name,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            streaming=True,
            **kwargs
        )
        async for chunk in client.astream(prompt):
            if hasattr(chunk, "content"):
                yield chunk.content
            elif isinstance(chunk, str):
                yield chunk
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation)
        
        For cloud providers, actual token counts will be available from API.
        For local models, we estimate using a simple heuristic.
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4


# Global router instance
_router: Optional[LLMRouter] = None


def get_router() -> LLMRouter:
    """Get the global LLM router instance"""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
