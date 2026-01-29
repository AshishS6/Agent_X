"""
Brand style specifications for BlogAgent.

This module encodes OPEN and Zwitch voice + structure + formatting rules so the
agent can consistently match the house style seen on:
- https://open.money/blog/
- https://www.zwitch.io/blog/
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StyleSpec:
    brand: str
    spec_text: str


_COMMON_RULES = """\
CONTENT & COPY RULES (APPLY ALWAYS)
- Voice: trustworthy, friendly, empathetic, politely confident, and lightly witty (when appropriate).
- Clarity above all: prefer short sentences (aim <30 words) and short paragraphs.
- Use active voice; avoid passive voice where possible.
- Avoid jargon; when technical terms are required, define them simply on first use.
- Be positive and reader-focused: emphasize benefits and solutions.
- Be data-driven when making claims: only include facts that are either common knowledge or explicitly provided via context. Do not invent numbers.
- Use American English spelling.
- Use the Oxford comma in lists.

FORMATTING RULES
- Brand spelling:
  - Always write brand as OPEN (not Open).
  - Always write brand as Zwitch (not ZWITCH).
- Headings:
  - H1 and H2 must be Title Case.
  - H3 and below must be sentence case.
- Numbers:
  - Write numbers zero to nine in words; use numerals for 10+.
- Acronyms:
  - Spell out on first mention, followed by acronym in parentheses. Example: Goods and Services Tax (GST).
- Dates:
  - Use Month Date, Year (e.g., November 27, 2024).

NO-HALLUCINATION RULE
- If a claim depends on product specifics, links, pricing, coverage, counts, partners, banks, or features: only state it if it is explicitly present in the provided context.
"""


def get_style_spec(
    brand: str,
    *,
    target_audience: str,
    intent: str,
    tone: str,
    length: str,
) -> StyleSpec:
    """
    Return a plain-text style spec to be embedded verbatim into LLM prompts.
    """
    brand_norm = (brand or "").strip().upper()
    audience_norm = (target_audience or "").strip().upper()
    intent_norm = (intent or "").strip().lower()
    tone_norm = (tone or "").strip().lower()
    length_norm = (length or "").strip().lower()

    if brand_norm == "OPEN":
        spec = f"""\
BRAND: OPEN
Audience: {audience_norm}
Intent: {intent_norm}
Tone: {tone_norm}
Target length: {length_norm}

OPEN HOUSE STYLE (match open.money/blog)
- Start with an empathetic, practical hook for business finance teams (especially SMEs/MSMEs).
- Explain complex topics simply; avoid sounding like a whitepaper.
- Prefer actionable steps, checklists, and clear “what to do next”.
- Use calm, professional friendliness. Witty is okay, but never gimmicky.

STRUCTURE TEMPLATE (prefer this ordering)
1) Introduction: 2–4 short paragraphs; name the pain clearly.
2) What is <core concept>? (definition + simple example)
3) Common pain points (bulleted list)
4) How it works / how to automate (clear explanation)
5) Step-by-step guide (numbered steps with sub-bullets)
6) Best practices / pitfalls to avoid
7) How OPEN helps (benefits-first; avoid overclaiming)
8) Conclusion (recap + next action)

CTA RULE (contextual links only)
- Include a short CTA section near the end.
- Only include links if they are explicitly provided in the context; otherwise keep CTA text plain (no link).

{_COMMON_RULES}
"""
        return StyleSpec(brand="OPEN", spec_text=spec)

    # Default to Zwitch
    spec = f"""\
BRAND: Zwitch
Audience: {audience_norm}
Intent: {intent_norm}
Tone: {tone_norm}
Target length: {length_norm}

ZWITCH HOUSE STYLE (match zwitch.io/blog)
- Start with a problem-first hook that frames urgency (manual processes, fragmentation, compliance friction, scale).
- Keep paragraphs short and scannable; use crisp sectioning.
- Use a repeatable “Challenges Solved / With Zwitch… / Outcome” pattern for product-led sections.
- Be confidently helpful and developer-friendly; don’t overhype.

STRUCTURE TEMPLATE (prefer this ordering for product/education)
1) Introduction: 2–4 short paragraphs; show the operational pain and why it matters.
2) Explain the core concept (e.g., FinOps) in plain language.
3) Enter Zwitch (1 short section that sets up the platform role)
4) Pillar sections (each should use the pattern below):
   - Challenges Solved:
   - With Zwitch <product/API>, you can:
   - Outcome:
5) Why Zwitch stands out (bullets; keep crisp)
6) Real-world impact (brief scenario; no invented metrics)
7) Conclusion (recap)
8) CTA section (plain text; link only if present in context)
9) FAQs (3–6 concise FAQs)

CTA RULE (contextual links only)
- Include a short CTA section near the end.
- Only include links if they are explicitly provided in the context; otherwise keep CTA text plain (no link).

{_COMMON_RULES}
"""
    return StyleSpec(brand="Zwitch", spec_text=spec)

