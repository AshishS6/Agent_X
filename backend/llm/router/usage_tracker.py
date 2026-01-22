"""
Usage Tracker - Token and cost tracking for LLM calls

This module tracks:
- Token usage (input/output)
- Cost calculations
- Latency
- Provider selection
- Caller information

All usage data is stored in memory (ready for database integration later).
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import logging
import time

from .model_registry import ModelRegistry, get_registry

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    """Record of a single LLM call"""
    timestamp: datetime
    caller: str  # Agent or assistant name
    provider: str  # ollama, openai, anthropic
    model_id: str  # Full model ID
    intent: str  # chat, code, analysis, etc.
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    latency_ms: float
    success: bool = True
    error: Optional[str] = None
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "caller": self.caller,
            "provider": self.provider,
            "model_id": self.model_id,
            "intent": self.intent,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "latency_ms": round(self.latency_ms, 2),
            "success": self.success,
            "error": self.error,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
        }


class UsageTracker:
    """
    Tracks LLM usage across all agents and assistants
    
    Provides:
    - Per-call tracking
    - Aggregated statistics
    - Cost calculations
    - Budget tracking
    """
    
    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or get_registry()
        self.records: List[UsageRecord] = []
        self._daily_costs: Dict[str, float] = defaultdict(float)  # Date -> cost
        self._caller_costs: Dict[str, float] = defaultdict(float)  # Caller -> total cost
        self._caller_tokens: Dict[str, Dict[str, int]] = defaultdict(lambda: {"input": 0, "output": 0})
        
    def record_usage(
        self,
        caller: str,
        provider: str,
        model_id: str,
        intent: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        success: bool = True,
        error: Optional[str] = None,
        fallback_used: bool = False,
        fallback_reason: Optional[str] = None
    ) -> UsageRecord:
        """
        Record a single LLM usage
        
        Args:
            caller: Name of the agent/assistant making the call
            provider: LLM provider (ollama, openai, anthropic)
            model_id: Full model ID
            intent: Usage intent (chat, code, analysis, etc.)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            latency_ms: Request latency in milliseconds
            success: Whether the call succeeded
            error: Error message if failed
            fallback_used: Whether this was a fallback call
            fallback_reason: Reason for fallback
            
        Returns:
            UsageRecord instance
        """
        # Calculate cost
        cost = self.registry.calculate_cost(model_id, input_tokens, output_tokens)
        
        # Create record
        record = UsageRecord(
            timestamp=datetime.utcnow(),
            caller=caller,
            provider=provider,
            model_id=model_id,
            intent=intent,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=cost,
            latency_ms=latency_ms,
            success=success,
            error=error,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason
        )
        
        # Store record
        self.records.append(record)
        
        # Update aggregates
        if success:
            today = datetime.utcnow().date().isoformat()
            self._daily_costs[today] += cost
            self._caller_costs[caller] += cost
            self._caller_tokens[caller]["input"] += input_tokens
            self._caller_tokens[caller]["output"] += output_tokens
        
        # Log usage
        if cost > 0:
            logger.info(
                f"💰 LLM Usage - Caller: {caller}, Provider: {provider}, "
                f"Model: {model_id}, Tokens: {input_tokens}+{output_tokens}, "
                f"Cost: ${cost:.6f}, Latency: {latency_ms:.0f}ms"
            )
        else:
            logger.info(
                f"🆓 LLM Usage (Local) - Caller: {caller}, Provider: {provider}, "
                f"Model: {model_id}, Tokens: {input_tokens}+{output_tokens}, "
                f"Latency: {latency_ms:.0f}ms"
            )
        
        if fallback_used:
            logger.warning(
                f"⚠️  Fallback used - Caller: {caller}, Reason: {fallback_reason}, "
                f"Provider: {provider}, Model: {model_id}"
            )
        
        return record
    
    def get_daily_cost(self, date: Optional[str] = None) -> float:
        """Get total cost for a specific date (default: today)"""
        if date is None:
            date = datetime.utcnow().date().isoformat()
        return self._daily_costs.get(date, 0.0)
    
    def get_caller_cost(self, caller: str) -> float:
        """Get total cost for a specific caller"""
        return self._caller_costs.get(caller, 0.0)
    
    def get_caller_tokens(self, caller: str) -> Dict[str, int]:
        """Get total tokens for a specific caller"""
        return self._caller_tokens.get(caller, {"input": 0, "output": 0})
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregated usage statistics"""
        total_records = len(self.records)
        successful_records = [r for r in self.records if r.success]
        failed_records = [r for r in self.records if not r.success]
        fallback_records = [r for r in self.records if r.fallback_used]
        
        total_cost = sum(r.estimated_cost_usd for r in successful_records)
        total_input_tokens = sum(r.input_tokens for r in successful_records)
        total_output_tokens = sum(r.output_tokens for r in successful_records)
        
        provider_counts = defaultdict(int)
        for record in successful_records:
            provider_counts[record.provider] += 1
        
        return {
            "total_calls": total_records,
            "successful_calls": len(successful_records),
            "failed_calls": len(failed_records),
            "fallback_calls": len(fallback_records),
            "total_cost_usd": round(total_cost, 6),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
            "provider_distribution": dict(provider_counts),
            "daily_cost": self.get_daily_cost(),
            "caller_costs": dict(self._caller_costs),
        }
    
    def get_recent_records(self, limit: int = 100) -> List[UsageRecord]:
        """Get most recent usage records"""
        return self.records[-limit:]
    
    def clear(self):
        """Clear all usage records (for testing)"""
        self.records.clear()
        self._daily_costs.clear()
        self._caller_costs.clear()
        self._caller_tokens.clear()


# Global tracker instance
_tracker: Optional[UsageTracker] = None


def get_tracker() -> UsageTracker:
    """Get the global usage tracker instance"""
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker
