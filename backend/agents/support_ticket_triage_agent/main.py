"""
Support Ticket Triage Agent

Goal: Given a support ticket payload, produce a structured triage result:
- classification (category, confidence, language, urgency)
- required_fields_missing
- suggested_next_steps
- draft_reply
- risk_flags (mandatory for downstream routing)
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict

from shared.base_agent import BaseAgent, AgentConfig


class SupportTicketTriageAgent(BaseAgent):
    def _register_tools(self):
        # MVP: no external tools. Pure LLM reasoning + structured output.
        return

    def _get_system_prompt(self) -> str:
        return """You are a Support Ticket Triage Agent.

You do NOT take actions in external systems. You only analyze the ticket and produce a structured JSON output for a human support agent to review.

Return ONLY a raw JSON object. Do NOT wrap it in markdown, do NOT use ``` fences, and do NOT add any commentary.

Output MUST be valid JSON with this exact shape:
{
  "classification": {
    "category": "billing|technical|account|integration|compliance|kyc|payout|refund|general|unknown",
    "confidence": 0.0,
    "language": "en",
    "urgency": "low|medium|high"
  },
  "required_fields_missing": ["field_name", "..."],
  "suggested_next_steps": ["...", "..."],
  "draft_reply": "string",
  "risk_flags": ["legal|financial|escalation|security|compliance"],
  "notes_for_agent": "string"
}

Rules:
- Always include all keys. Use empty arrays/strings where needed.
- confidence must be between 0 and 1.
- risk_flags MUST be present; include only applicable flags; otherwise [].
- draft_reply must be concise, polite, and actionable. Do not hallucinate internal policy; ask clarifying questions if needed.
- If information is missing, list it in required_fields_missing and reflect it in the draft_reply (ask for it).
"""

    def _extract_json_object(self, text: str) -> Dict[str, Any] | None:
        """
        Extract a JSON object from common LLM wrappers (markdown fences, pre/post text).
        Returns a parsed dict on success, else None.
        """
        if not text:
            return None

        raw = text.strip()

        # 1) Direct parse
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            pass

        # 2) Markdown fenced code block: ```json ... ``` or ``` ... ```
        # Use a non-greedy capture to pull the first fenced block.
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, flags=re.IGNORECASE)
        if fence_match:
            fenced = fence_match.group(1).strip()
            try:
                parsed = json.loads(fenced)
                return parsed if isinstance(parsed, dict) else None
            except Exception:
                # keep trying other extraction strategies
                pass

        # 3) Heuristic: take substring from first "{" to last "}"
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = raw[start : end + 1].strip()
            try:
                parsed = json.loads(candidate)
                return parsed if isinstance(parsed, dict) else None
            except Exception:
                pass

        return None

    def _run_agent_loop(self, system_prompt: str, user_prompt: str, task: Any) -> Dict[str, Any]:
        # Use the BaseAgent's LLM client directly, but enforce JSON parsing.
        from langchain.schema import HumanMessage, SystemMessage

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = self.llm.invoke(messages)
        raw = response.content or ""

        # Best-effort JSON extraction
        parsed: Dict[str, Any]
        extracted = self._extract_json_object(raw)
        if isinstance(extracted, dict):
            parsed = extracted
        else:
            parsed = {
                "classification": {
                    "category": "unknown",
                    "confidence": 0.0,
                    "language": "en",
                    "urgency": "medium",
                },
                "required_fields_missing": [],
                "suggested_next_steps": [
                    "Review the ticket details and confirm the customer’s request.",
                    "Ask clarifying questions to gather missing information.",
                ],
                "draft_reply": raw.strip()[:5000],
                "risk_flags": [],
                "notes_for_agent": "Model did not return valid JSON; draft_reply contains raw response.",
                "_parse_error": "invalid_json",
            }

        return {
            "triage": parsed,
        }


def create_support_ticket_triage_agent(llm_provider: str = "openai") -> SupportTicketTriageAgent:
    import os

    model = os.getenv("LLM_LOCAL_MODEL") or os.getenv("LLM_CLOUD_MODEL") or ""

    config = AgentConfig(
        agent_type="support_ticket_triage",
        name="Support Ticket Triage Agent",
        description="Classifies support tickets and drafts replies for human review",
        llm_provider=llm_provider,
        model=model,
        temperature=0.2,
        tools=[],
        max_tokens=1500,
    )
    return SupportTicketTriageAgent(config)

