"""
Model Registry - Single source of truth for LLM models, pricing, and capabilities

This module defines all available models (local and cloud) with their:
- Context limits
- Pricing (for cloud models)
- Provider information
- Recommended use cases
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Provider(str, Enum):
    """LLM provider types"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class Intent(str, Enum):
    """LLM usage intent types"""
    CHAT = "chat"
    CODE = "code"
    ANALYSIS = "analysis"
    LONG_FORM = "long_form"
    REASONING = "reasoning"


@dataclass
class ModelInfo:
    """Information about an LLM model"""
    id: str  # Unique identifier (e.g., "ollama:qwen2.5:7b-instruct", "openai:gpt-4-turbo-preview")
    provider: Provider
    name: str  # Display name
    context_limit: int  # Maximum context window in tokens
    input_price_per_1k: float = 0.0  # Price per 1k input tokens (USD)
    output_price_per_1k: float = 0.0  # Price per 1k output tokens (USD)
    recommended_intents: List[Intent] = None  # Recommended use cases
    is_local: bool = False  # Whether this is a local model
    
    def __post_init__(self):
        if self.recommended_intents is None:
            self.recommended_intents = []


class ModelRegistry:
    """
    Central registry for all LLM models
    
    This is the SINGLE SOURCE OF TRUTH for:
    - Available models
    - Pricing information
    - Context limits
    - Model capabilities
    """
    
    def __init__(self):
        self._models: Dict[str, ModelInfo] = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all available models"""
        
        # ===== LOCAL MODELS (Ollama) =====
        # These are free but have estimated token costs for tracking
        
        # Qwen models
        self._register_model(ModelInfo(
            id="ollama:qwen2.5:7b-instruct",
            provider=Provider.OLLAMA,
            name="Qwen 2.5 7B Instruct",
            context_limit=32768,
            input_price_per_1k=0.0,  # Free (local)
            output_price_per_1k=0.0,
            recommended_intents=[Intent.CHAT, Intent.CODE, Intent.ANALYSIS],
            is_local=True
        ))
        
        self._register_model(ModelInfo(
            id="ollama:qwen2.5:14b-instruct",
            provider=Provider.OLLAMA,
            name="Qwen 2.5 14B Instruct",
            context_limit=32768,
            input_price_per_1k=0.0,
            output_price_per_1k=0.0,
            recommended_intents=[Intent.CHAT, Intent.CODE, Intent.ANALYSIS, Intent.REASONING],
            is_local=True
        ))
        
        # DeepSeek models
        self._register_model(ModelInfo(
            id="ollama:deepseek-r1:7b",
            provider=Provider.OLLAMA,
            name="DeepSeek R1 7B",
            context_limit=64000,
            input_price_per_1k=0.0,
            output_price_per_1k=0.0,
            recommended_intents=[Intent.REASONING, Intent.ANALYSIS, Intent.LONG_FORM],
            is_local=True
        ))
        
        # Llama models
        self._register_model(ModelInfo(
            id="ollama:llama3:8b",
            provider=Provider.OLLAMA,
            name="Llama 3 8B",
            context_limit=8192,
            input_price_per_1k=0.0,
            output_price_per_1k=0.0,
            recommended_intents=[Intent.CHAT, Intent.CODE],
            is_local=True
        ))
        
        # Mistral models
        self._register_model(ModelInfo(
            id="ollama:mistral:7b",
            provider=Provider.OLLAMA,
            name="Mistral 7B",
            context_limit=8192,
            input_price_per_1k=0.0,
            output_price_per_1k=0.0,
            recommended_intents=[Intent.CHAT, Intent.CODE],
            is_local=True
        ))
        
        # ===== CLOUD MODELS (OpenAI) =====
        # Pricing as of 2024 (update as needed)
        
        self._register_model(ModelInfo(
            id="openai:gpt-4-turbo-preview",
            provider=Provider.OPENAI,
            name="GPT-4 Turbo",
            context_limit=128000,
            input_price_per_1k=0.01,  # $0.01 per 1k input tokens
            output_price_per_1k=0.03,  # $0.03 per 1k output tokens
            recommended_intents=[Intent.ANALYSIS, Intent.REASONING, Intent.LONG_FORM],
            is_local=False
        ))
        
        self._register_model(ModelInfo(
            id="openai:gpt-4",
            provider=Provider.OPENAI,
            name="GPT-4",
            context_limit=8192,
            input_price_per_1k=0.03,
            output_price_per_1k=0.06,
            recommended_intents=[Intent.ANALYSIS, Intent.REASONING],
            is_local=False
        ))
        
        self._register_model(ModelInfo(
            id="openai:gpt-3.5-turbo",
            provider=Provider.OPENAI,
            name="GPT-3.5 Turbo",
            context_limit=16385,
            input_price_per_1k=0.0005,  # $0.0005 per 1k input tokens
            output_price_per_1k=0.0015,  # $0.0015 per 1k output tokens
            recommended_intents=[Intent.CHAT, Intent.CODE],
            is_local=False
        ))
        
        # ===== CLOUD MODELS (Anthropic) =====
        
        self._register_model(ModelInfo(
            id="anthropic:claude-3-sonnet-20240229",
            provider=Provider.ANTHROPIC,
            name="Claude 3 Sonnet",
            context_limit=200000,
            input_price_per_1k=0.003,  # $0.003 per 1k input tokens
            output_price_per_1k=0.015,  # $0.015 per 1k output tokens
            recommended_intents=[Intent.ANALYSIS, Intent.LONG_FORM, Intent.REASONING],
            is_local=False
        ))
        
        self._register_model(ModelInfo(
            id="anthropic:claude-3-opus-20240229",
            provider=Provider.ANTHROPIC,
            name="Claude 3 Opus",
            context_limit=200000,
            input_price_per_1k=0.015,
            output_price_per_1k=0.075,
            recommended_intents=[Intent.ANALYSIS, Intent.LONG_FORM, Intent.REASONING],
            is_local=False
        ))
        
        self._register_model(ModelInfo(
            id="anthropic:claude-3-haiku-20240307",
            provider=Provider.ANTHROPIC,
            name="Claude 3 Haiku",
            context_limit=200000,
            input_price_per_1k=0.00025,
            output_price_per_1k=0.00125,
            recommended_intents=[Intent.CHAT, Intent.CODE],
            is_local=False
        ))
    
    def _register_model(self, model: ModelInfo):
        """Register a model in the registry"""
        self._models[model.id] = model
        logger.debug(f"Registered model: {model.id} ({model.name})")
    
    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Get model information by ID"""
        return self._models.get(model_id)
    
    def get_models_by_provider(self, provider: Provider) -> List[ModelInfo]:
        """Get all models for a specific provider"""
        return [m for m in self._models.values() if m.provider == provider]
    
    def get_local_models(self) -> List[ModelInfo]:
        """Get all local models"""
        return [m for m in self._models.values() if m.is_local]
    
    def get_cloud_models(self) -> List[ModelInfo]:
        """Get all cloud models"""
        return [m for m in self._models.values() if not m.is_local]
    
    def calculate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for a model usage
        
        Args:
            model_id: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        model = self.get_model(model_id)
        if not model:
            logger.warning(f"Unknown model {model_id}, cost calculation skipped")
            return 0.0
        
        input_cost = (input_tokens / 1000.0) * model.input_price_per_1k
        output_cost = (output_tokens / 1000.0) * model.output_price_per_1k
        
        return input_cost + output_cost
    
    def parse_model_id(self, provider: str, model_name: str) -> str:
        """
        Parse a model ID from provider and model name
        
        Args:
            provider: Provider name (ollama, openai, anthropic)
            model_name: Model name (e.g., "qwen2.5:7b-instruct", "gpt-4-turbo-preview")
            
        Returns:
            Full model ID (e.g., "ollama:qwen2.5:7b-instruct")
        """
        provider_lower = provider.lower()
        return f"{provider_lower}:{model_name}"
    
    def get_default_model_for_provider(self, provider: Provider, intent: Optional[Intent] = None) -> Optional[ModelInfo]:
        """
        Get default model for a provider, optionally filtered by intent
        
        Args:
            provider: Provider type
            intent: Optional intent to filter by
            
        Returns:
            ModelInfo or None
        """
        models = self.get_models_by_provider(provider)
        
        if intent:
            # Filter by intent
            models = [m for m in models if intent in m.recommended_intents]
        
        if not models:
            return None
        
        # Return first model (can be enhanced with priority logic)
        return models[0]


# Global registry instance
_registry: Optional[ModelRegistry] = None


def get_registry() -> ModelRegistry:
    """Get the global model registry instance"""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
