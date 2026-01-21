#!/bin/bash
# Test script for assistant runner

echo "Testing Assistant Runner..."
echo ""

# Test with fintech assistant
python3 backend/assistants/runner.py --input '{
  "message": "How do I integrate Zwitch payment gateway?",
  "assistant": "fintech",
  "knowledge_base": "fintech"
}'
