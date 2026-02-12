
import sys
import os
import time
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.router.llm_router import _TrackedLangChainClient, UsageTracker, Provider, Intent

def test_metadata_injection():
    print("Testing metadata injection...")
    
    # Mock dependencies
    tracker = MagicMock(spec=UsageTracker)
    tracker.records = []
    
    # Mock record_usage to append to records
    def mock_record_usage(*args, **kwargs):
        record = MagicMock()
        record.to_dict.return_value = {
            "model_id": "test:model",
            "provider": "test",
            "input_tokens": 10,
            "output_tokens": 20,
            "latency_ms": 100,
            "estimated_cost_usd": 0.001
        }
        tracker.records.append(record)
        return record
    
    tracker.record_usage.side_effect = mock_record_usage
    
    # Mock LangChain client and response
    client = MagicMock()
    response = MagicMock()
    response.content = "Test response"
    response.response_metadata = {} # Empty dict to start
    client.invoke.return_value = response
    
    # Create tracked client
    tracked_client = _TrackedLangChainClient(
        client=client,
        tracker=tracker,
        caller="test_agent",
        provider=Provider.OPENAI,
        model_id="openai:gpt-4",
        intent=Intent.CHAT,
        start_time=time.time(),
        fallback_used=False,
        fallback_reason=None,
        estimate_tokens_fn=lambda x: len(x) // 4
    )
    
    # Invoke
    print("Invoking client...")
    result = tracked_client.invoke([MagicMock(content="Test input")])
    
    # Verify result
    print(f"Result metadata: {result.response_metadata}")
    
    if "llm_usage" in result.response_metadata:
        print("✅ SUCCESS: llm_usage found in response metadata")
        print(result.response_metadata["llm_usage"])
    else:
        print("❌ FAILURE: llm_usage NOT found in response metadata")
        exit(1)

if __name__ == "__main__":
    test_metadata_injection()
