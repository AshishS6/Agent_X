"""
Blog Agent Implementation
Generates structured blog outlines and drafts for marketing teams
"""

from typing import Dict, Any
import json
import re
from shared.base_agent import BaseAgent, AgentConfig
try:
    # When imported as a package module
    from .style_spec import get_style_spec
except ImportError:
    # When executed/imported as a top-level module via CLI
    from style_spec import get_style_spec


class BlogAgent(BaseAgent):
    """
    Blog Agent - Generates blog outlines and drafts
    
    Capabilities:
    - Generate structured blog outlines
    - Generate blog drafts from approved outlines
    - Maintain brand consistency (OPEN | Zwitch)
    - Target audience-specific content (SME | Developer | Founder | Enterprise)
    """
    
    def _register_tools(self):
        """Register blog-specific tools"""
        # No tools required in Phase 1 - pure LLM-based generation
        pass
    
    def _get_system_prompt(self) -> str:
        """Blog agent system prompt"""
        return """You are a professional Blog Content Agent AI assistant for AgentX.

Your role is to help marketing teams create high-quality blog content by:
- Generating structured, actionable blog outlines
- Writing full blog drafts from approved outlines
- Maintaining brand voice and tone consistency
- Targeting specific audiences effectively

**Language: Always write all output in English only.** All titles, headings, section intents, and body text must be in English. Never use any other language.

Guidelines:
- Be professional, clear, and engaging
- Follow the provided Brand Style Spec exactly (voice, structure, formatting)
- Structure content logically with clear sections
- Include actionable insights and examples
- Maintain appropriate tone based on target audience

When generating outlines:
- Create a clear, compelling title (H1)
- Structure with logical H2 and H3 sections
- Provide one-line intent for each section
- Ensure outline supports the content intent (education | product | announcement)

When generating drafts:
- Follow the provided outline exactly
- Use appropriate tone (professional | friendly | explanatory)
- Match the specified length (short: ~800 words | medium: ~1200 words | long: ~2000 words)
- Include engaging introductions and clear conclusions
- Use markdown formatting properly
- Provide meta descriptions and word counts

Always produce structured, publishable-quality content."""

    def _get_brand_style_spec(
        self,
        *,
        brand: str,
        target_audience: str,
        intent: str,
        tone: str = "professional",
        length: str = "medium",
    ) -> str:
        spec = get_style_spec(
            brand,
            target_audience=target_audience,
            intent=intent,
            tone=tone,
            length=length,
        )
        return spec.spec_text

    def _count_words_markdown(self, md: str) -> int:
        text = re.sub(r'`[^`]*`', ' ', md or '')  # inline code
        text = re.sub(r'```[\s\S]*?```', ' ', text)  # fenced blocks
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', text)  # links -> text
        words = re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", text)
        return len(words)

    def _decode_json_like_string(self, value: str) -> str:
        """Best-effort decode for JSON-like string fragments."""
        if value is None:
            return ""
        try:
            return json.loads(f"\"{value}\"")
        except Exception:
            # Fallback for partially escaped payloads.
            return (
                value.replace("\\r\\n", "\n")
                .replace("\\n", "\n")
                .replace("\\r", "\n")
                .replace("\\t", "\t")
                .replace('\\"', '"')
                .replace("\\\\", "\\")
            )

    def _extract_post_data_from_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse post JSON from LLM output.

        Handles common local-model failure modes:
        - fenced markdown JSON (with or without trailing fence)
        - stray preamble/suffix text around JSON
        - partially escaped JSON strings
        """
        raw = (response_text or "").strip()
        if not raw:
            raise ValueError("Empty response from LLM")

        # Remove common leading/trailing markdown fences first.
        unfenced = re.sub(r"^\s*```(?:json)?\s*", "", raw, flags=re.IGNORECASE).strip()
        unfenced = re.sub(r"\s*```\s*$", "", unfenced).strip()

        candidates = []
        for candidate in (raw, unfenced):
            if candidate and candidate not in candidates:
                candidates.append(candidate)

        first_brace = unfenced.find("{")
        if first_brace != -1:
            from_first = unfenced[first_brace:].strip()
            if from_first and from_first not in candidates:
                candidates.append(from_first)
            last_brace = from_first.rfind("}")
            if last_brace != -1:
                bounded = from_first[: last_brace + 1].strip()
                if bounded and bounded not in candidates:
                    candidates.append(bounded)

        parse_error = None
        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError as e:
                parse_error = e
                # Remove invalid control chars and retry.
                cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', candidate)
                try:
                    return json.loads(cleaned)
                except json.JSONDecodeError as e2:
                    parse_error = e2

        # Fallback: extract fields from JSON-like text (handles unescaped newlines in "content").
        text = candidates[-1] if candidates else raw

        title = ""
        title_match = re.search(r'"title"\s*:\s*"((?:\\.|[^"\\])*)"', text, re.DOTALL)
        if title_match:
            title = self._decode_json_like_string(title_match.group(1)).strip()

        content = ""
        content_patterns = [
            r'"content"\s*:\s*"([\s\S]*?)"\s*,\s*"(?:meta_description|word_count)"\s*:',
            r'"content"\s*:\s*"([\s\S]*?)"\s*}\s*$',
            r'"content"\s*:\s*"([\s\S]*)$',
        ]
        for pattern in content_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                content = match.group(1)
                break
        content = self._decode_json_like_string(content).strip()

        meta_description = ""
        meta_match = re.search(r'"meta_description"\s*:\s*"((?:\\.|[^"\\])*)"', text, re.DOTALL)
        if meta_match:
            meta_description = self._decode_json_like_string(meta_match.group(1)).strip()

        word_count = 0
        wc_match = re.search(r'"word_count"\s*:\s*(\d+)', text)
        if wc_match:
            try:
                word_count = int(wc_match.group(1))
            except Exception:
                word_count = 0

        if not content:
            self.logger.error(f"Failed to parse post JSON: {parse_error}")
            self.logger.error(f"Response was (first 1000 chars): {raw[:1000]}")
            raise ValueError(f"Failed to parse post response as JSON: {parse_error}")

        if not word_count:
            word_count = self._count_words_markdown(content)

        self.logger.warning(
            "Recovered post payload using JSON-like fallback parser; model response was not strict JSON"
        )
        return {
            "title": title,
            "content": content,
            "meta_description": meta_description,
            "word_count": word_count,
        }

    def _title_case_heading(self, heading: str) -> str:
        """
        Title Case rules (approx. OPEN/Zwitch guideline):
        - lowercase articles/conjunctions/short prepositions (<4 letters) unless first/last
        - preserve ALLCAPS tokens (API, KYC, GST, OPEN)
        """
        if not heading:
            return heading
        small = {
            "a", "an", "the",
            "and", "or", "but", "nor", "for", "so", "yet",
            "as", "at", "by", "in", "of", "on", "to", "up", "via",
            "with",  # (exception: >3 letters; keep here for house style consistency)
        }
        tokens = re.split(r"(\s+)", heading.strip())
        words = [t for t in tokens if not t.isspace()]
        out = []
        word_idx = 0
        last_word_index = len(words) - 1

        for tok in tokens:
            if tok.isspace():
                out.append(tok)
                continue

            original = tok
            core = re.sub(r"^[\"'“”‘’(\\[]+|[\"'“”‘’).,;:!?\\]]+$", "", original)
            prefix = original[: original.find(core)] if core and core in original else ""
            suffix = original[original.find(core) + len(core):] if core and core in original else ""

            if core.isupper() and len(core) >= 2:
                cased = core
            else:
                lower = core.lower()
                is_first = word_idx == 0
                is_last = word_idx == last_word_index
                if (lower in small or (len(lower) < 4 and lower in {"of", "in", "to", "as", "at", "by", "on", "up"})) and not (is_first or is_last):
                    cased = lower
                else:
                    cased = lower[:1].upper() + lower[1:] if lower else lower

            out.append(f"{prefix}{cased}{suffix}")
            word_idx += 1

        return "".join(out).strip()

    def _sentence_case_heading(self, heading: str) -> str:
        if not heading:
            return heading
        h = heading.strip()
        # If heading starts with an acronym/brand, keep it as is and sentence-case remainder.
        m = re.match(r"^((?:OPEN|Zwitch|API|KYC|GST)(?:\\b|\\s+))(.*)$", h)
        if m:
            lead, rest = m.group(1), m.group(2)
            rest = rest.strip()
            if not rest:
                return h
            return lead + (rest[:1].upper() + rest[1:])
        return h[:1].upper() + h[1:]

    def _normalize_brand_spelling_in_line(self, line: str, brand: str) -> str:
        # Avoid touching URLs/markdown links.
        if "http://" in line or "https://" in line or "](" in line:
            return line
        if brand == "OPEN":
            # Replace possessive and stand-alone brand usage; avoid "open banking" (lowercase).
            line = re.sub(r"\bOpen(?:’s|'s)\b", "OPEN’s", line)
            line = re.sub(r"\bOpen\s+Money\b", "OPEN Money", line)
            line = re.sub(
                r"\bOpen\b(?=\s+(?:APIs?|dashboard|platform|account|payouts?|collections?)\b)",
                "OPEN",
                line,
            )
            line = re.sub(r"\bOpen\b", "OPEN", line)
        else:
            line = re.sub(r"\bZWITCH\b", "Zwitch", line)
            line = re.sub(r"\bzwitch\b", "Zwitch", line)
        return line

    def _normalize_markdown_content(self, md: str, brand: str) -> str:
        lines = (md or "").splitlines()
        # Remove common LLM preambles before the first heading.
        # Example: "Here is the revised markdown..."
        preamble_patterns = (
            r"^here (is|are) (the )?(revised )?markdown\b",
            r"^sure[,!].*",
            r"^of course[,!].*",
        )
        cleaned = []
        saw_heading = False
        for line in lines:
            if not saw_heading:
                if re.match(r"^#{1,6}\s+", line):
                    saw_heading = True
                else:
                    if not line.strip():
                        continue
                    lowered = line.strip().lower()
                    if any(re.match(pat, lowered) for pat in preamble_patterns):
                        continue
            cleaned.append(line)
        lines = cleaned
        out = []
        for line in lines:
            # Headings normalization
            m = re.match(r"^(#{1,6})\s+(.*)$", line)
            if m:
                level = len(m.group(1))
                text = m.group(2).strip()
                if level <= 2:
                    text = self._title_case_heading(text)
                else:
                    text = self._sentence_case_heading(text)
                line = f"{m.group(1)} {text}"

            line = self._normalize_brand_spelling_in_line(line, brand)
            out.append(line)
        # Collapse excessive blank lines (keep at most 1)
        normalized = "\n".join(out)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip() + "\n"

    def _ensure_house_style_sections(self, md: str, brand: str) -> str:
        """
        Deterministically ensure required house-style sections exist.

        This is a guardrail in case the model omits required sections, and we
        cannot rely on a rewrite pass (timeouts, refusal, etc.).
        """
        text = (md or "").strip()
        if not text:
            return ""

        if brand != "OPEN":
            if "## CTA" not in text:
                text += "\n\n## CTA\n\nTell us what you’re building, and we’ll help you map the right APIs for your use case.\n"
            if not re.search(r"With\s+Zwitch\b", text):
                insert = (
                    "With Zwitch, you can:\n"
                    "- Integrate key payment and finance workflows via APIs\n"
                    "- Automate repetitive steps to reduce manual effort\n"
                    "- Build clearer operational visibility and controls\n"
                )
                if "Challenges Solved:" in text:
                    text = text.replace("Challenges Solved:", f"Challenges Solved:\n{insert}", 1)
                else:
                    text += f"\n\n{insert}"
            if "## FAQs" not in text and "## FAQ" not in text:
                text += (
                    "\n\n## FAQs\n\n"
                    "### What is FinOps?\n"
                    "FinOps is the practice of making financial operations faster, more reliable, and more scalable through automation, clear workflows, and real-time visibility.\n\n"
                    "### Why do enterprises need FinOps automation?\n"
                    "At scale, manual processes and fragmented systems create delays, errors, and compliance risk. Automation helps teams move faster with better control.\n\n"
                    "### How do I decide what to integrate first?\n"
                    "Start with the highest-friction workflows (collections, payouts, reconciliation, or compliance). Then expand step-by-step as you validate outcomes.\n\n"
                    "### How do I validate integration requirements safely?\n"
                    "Use the provider’s documentation and test environments (where available) to verify request/response flows, edge cases, and operational alerts before going live.\n"
                )
        return text.strip() + "\n"

    def _lint_markdown(self, md: str, brand: str) -> list:
        issues = []
        text = md or ""

        if not re.search(r"^##\s+Conclusion\b", text, flags=re.IGNORECASE | re.MULTILINE):
            issues.append("Missing required H2 section: Conclusion")

        if brand != "OPEN":
            if not re.search(r"^##\s+FAQs?\b", text, flags=re.IGNORECASE | re.MULTILINE):
                issues.append("Missing required H2 section: FAQs")
            if "Challenges Solved:" not in text:
                issues.append("Missing required section label in body: Challenges Solved:")
            if "Outcome:" not in text:
                issues.append("Missing required section label in body: Outcome:")
            if not re.search(r"With\s+Zwitch\b", text):
                issues.append("Missing required phrase in body: With Zwitch <product/API>, you can")
        else:
            if not re.search(r"step-?by-?step", text, flags=re.IGNORECASE):
                issues.append("Missing required concept: Step-by-step guide")
            if "How OPEN helps" not in text and not re.search(r"^##\s+How\s+OPEN\s+helps\b", text, flags=re.IGNORECASE | re.MULTILINE):
                issues.append("Missing required H2 section: How OPEN helps")

        # Long sentence check (heuristic)
        long_sentences = 0
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        for p in paragraphs:
            # Skip headings/lists/code blocks-ish
            if re.match(r"^#{1,6}\s+", p):
                continue
            if re.match(r"^(-|\*|\d+\.)\s+", p):
                continue
            if "```" in p:
                continue
            for s in re.split(r"(?<=[.!?])\s+", p):
                words = re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", s)
                if len(words) > 30:
                    long_sentences += 1
                    if long_sentences >= 3:
                        issues.append("Too many long sentences (>30 words). Shorten for readability.")
                        return issues

        return issues

    def _editor_rewrite_markdown(
        self,
        *,
        brand: str,
        style_spec: str,
        outline_text: str,
        markdown: str,
        issues: list,
    ) -> str:
        from langchain.schema import HumanMessage, SystemMessage

        issues_block = "\n".join(f"- {i}" for i in issues)
        issues_block = "\n".join(f"- {i}" for i in issues)
        prompt = f"""You are an expert blog editor.

Rewrite the blog markdown to fix the issues below while strictly following the Brand Style Spec.

Brand: {brand}

Brand Style Spec (follow exactly):
{style_spec}

Issues to fix:
{issues_block}

Constraints:
- Keep the same overall outline order and coverage.
- You MAY add missing house-style sections that are required by the style spec (e.g., CTA, FAQs), even if they are missing from the outline.
- Do not invent facts, product features, or numbers.
- Keep CTA links contextual: do NOT add links unless they are already present in the text.
- Output ONLY the revised markdown (no JSON, no commentary).

Outline (for reference):
{outline_text}

Current markdown:
{markdown}
"""
        messages = [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(content=prompt),
        ]
        resp = self.llm.invoke(messages)
        return (resp.content or "").strip()
    
    def _run_agent_loop(self, system_prompt: str, user_prompt: str, task) -> Dict[str, Any]:
        """
        Enhanced agent loop for blog tasks
        """
        start_time = task.metadata.get("start_time") if hasattr(task, 'metadata') else None
        
        if task.action == "generate_outline":
            return self._generate_outline(task)
        elif task.action == "generate_post_from_outline":
            return self._generate_post_from_outline(task)
        elif task.action == "generate_outline_v2":
            return self._generate_outline_v2(task)
        elif task.action == "generate_draft_v2":
            return self._generate_draft_v2(task)
        else:
            # Default handling for unknown actions
            return super()._run_agent_loop(system_prompt, user_prompt, task)
    
    def _generate_outline(self, task) -> Dict[str, Any]:
        """Generate a structured blog outline"""
        input_data = task.input_data
        
        # Extract required fields
        brand = input_data.get("brand", "OPEN").upper()
        topic = input_data.get("topic", "")
        target_audience = input_data.get("target_audience", "SME")
        intent = input_data.get("intent", "education")
        use_rag = input_data.get("use_rag", False)
        
        # Validate inputs
        if not topic:
            raise ValueError("'topic' is required for generate_outline action")
        
        valid_brands = ["OPEN", "ZWITCH"]
        if brand not in valid_brands:
            raise ValueError(f"Invalid brand. Must be one of: {', '.join(valid_brands)}")
        
        valid_audiences = ["SME", "DEVELOPER", "FOUNDER", "ENTERPRISE"]
        if target_audience.upper() not in valid_audiences:
            raise ValueError(f"Invalid target_audience. Must be one of: {', '.join(valid_audiences)}")
        
        valid_intents = ["education", "product", "announcement"]
        if intent.lower() not in valid_intents:
            raise ValueError(f"Invalid intent. Must be one of: {', '.join(valid_intents)}")
        
        # Get RAG context if enabled
        rag_context = ""
        if use_rag:
            try:
                rag_context = self._get_rag_context(brand, topic, target_audience, intent, feedback=None)
            except Exception as e:
                self.logger.warning(f"Failed to get RAG context for outline: {e}")
                rag_context = ""
        
        # Build prompt
        brand_guidance = {
            "OPEN": "Technical, detailed, developer-focused content",
            "ZWITCH": "Friendly, accessible, business-focused content"
        }
        
        audience_guidance = {
            "SME": "Small to medium enterprises - practical, actionable advice",
            "DEVELOPER": "Technical audience - code examples, implementation details",
            "FOUNDER": "Entrepreneurial audience - strategic insights, growth stories",
            "ENTERPRISE": "Large organizations - scalability, security, compliance"
        }
        
        intent_guidance = {
            "education": "Educational content that teaches and informs",
            "product": "Product-focused content highlighting features and benefits",
            "announcement": "Announcement content sharing news and updates"
        }
        
        style_spec = self._get_brand_style_spec(
            brand=brand,
            target_audience=target_audience,
            intent=intent,
            tone="professional",
            length="medium",
        )

        # Include RAG context in prompt if available
        rag_section = ""
        if rag_context:
            rag_section = f"""

BRAND CONTEXT FROM KNOWLEDGE BASE:
{rag_context}

Use this context to inform your outline structure. Ensure sections align with actual product offerings, features, and capabilities mentioned in the context. Do not include information that is not present in the context above.
"""
        
        brand_outline_archetype = ""
        if brand == "OPEN":
            brand_outline_archetype = """
OPEN OUTLINE ARCHETYPE (use this as your default structure)
- Start with an empathetic introduction that frames the day-to-day operational pain.
- Include a clear definition section (“What is <concept>?”).
- Include a pain points section (bulleted list).
- Include a practical step-by-step section (numbered steps).
- Include a “How OPEN helps” section (benefits-first; no overclaims).
- End with a clear Conclusion.
"""
        else:
            brand_outline_archetype = """
ZWITCH OUTLINE ARCHETYPE (use this as your default structure)
- Start with a problem-first introduction (manual ops, fragmentation, compliance friction, scale).
- Include a short “Enter Zwitch” section that frames the platform role.
- Include pillar sections that map to the product-led pattern:
  - Challenges Solved
  - With Zwitch <product/API>, you can
  - Outcome
- Include “Why Zwitch stands out”, a brief “Real-world impact” scenario, and a Conclusion.
- MUST include an H2 section titled "CTA" (plain text; link only if present in context).
- MUST include an H2 section titled "FAQs" as the final section.
"""

        prompt = f"""Generate a structured blog outline for the following specifications:

Brand: {brand} ({brand_guidance.get(brand, "")})
Topic: {topic}
Target Audience: {target_audience} ({audience_guidance.get(target_audience.upper(), "")})
Intent: {intent} ({intent_guidance.get(intent.lower(), "")}){rag_section}

BRAND STYLE SPEC (follow exactly):
{style_spec}

{brand_outline_archetype}

**Important: Write the entire outline in English only.** All titles, headings, section intents, and descriptions must be in English.

Please provide:
1. A compelling title (H1) - should be engaging and SEO-friendly
2. A structured outline with:
   - H2 sections (main topics)
   - H3 subsections (as needed)
   - One-line intent for each section describing what that section should cover

Format your response as a valid JSON object. Use a comma after every key-value pair (including after "intent" when followed by "subsections"). Example:

{{
    "title": "Blog Title Here",
    "outline": [
        {{
            "heading": "Section Title (H2)",
            "intent": "What this section covers",
            "subsections": [
                {{
                    "heading": "Subsection Title (H3)",
                    "intent": "What this subsection covers"
                }}
            ]
        }},
        {{
            "heading": "Another Section Without Subsections",
            "intent": "What this section covers"
        }}
    ]
}}

Sections may omit "subsections" if not needed. Return only valid JSON, no other text."""
        
        # Get LLM response
        from langchain.schema import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse JSON response
        response_text = response.content.strip()
        
        # Extract JSON if wrapped in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        else:
            # Try to find JSON object in response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
        
        # Repair common LLM JSON mistakes (e.g. missing comma between "intent" and "subsections")
        response_text = self._repair_outline_json(response_text)
        
        try:
            outline_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse outline JSON: {e}")
            self.logger.error(f"Response was: {response_text}")
            raise ValueError(f"Failed to parse outline response as JSON: {str(e)}")
        
        result = {
            "action": "generate_outline",
            "response": {
                "title": outline_data.get("title", ""),
                "outline": outline_data.get("outline", []),
                "brand": brand,
                "topic": topic,
                "target_audience": target_audience,
                "intent": intent
            }
        }
        
        # Preserve LLM usage
        if hasattr(response, "response_metadata") and isinstance(response.response_metadata, dict):
            if "llm_usage" in response.response_metadata:
                result["llm_usage"] = response.response_metadata["llm_usage"]
                
        return result
    
    def _repair_outline_json(self, raw: str) -> str:
        """Fix common LLM JSON mistakes before parsing (e.g. missing commas)."""
        # Missing comma between "intent": "..." and "subsections": [...]
        # Pattern: "intent": "..." newline "subsections" -> add comma after "..."
        raw = re.sub(
            r'("intent":\s*"(?:[^"\\]|\\.)*")(\s*\n\s*)("subsections")',
            r'\1,\2\3',
            raw,
        )
        return raw
    
    def _generate_post_from_outline(self, task) -> Dict[str, Any]:
        """Generate a full blog draft from an outline"""
        input_data = task.input_data
        
        # Extract required fields
        brand = input_data.get("brand", "OPEN").upper()
        outline = input_data.get("outline")
        tone = input_data.get("tone", "professional")
        length = input_data.get("length", "medium")
        
        # Validate inputs
        if not outline:
            raise ValueError("'outline' is required for generate_post_from_outline action")
        
        valid_brands = ["OPEN", "ZWITCH"]
        if brand not in valid_brands:
            raise ValueError(f"Invalid brand. Must be one of: {', '.join(valid_brands)}")
        
        valid_tones = ["professional", "friendly", "explanatory"]
        if tone.lower() not in valid_tones:
            raise ValueError(f"Invalid tone. Must be one of: {', '.join(valid_tones)}")
        
        valid_lengths = ["short", "medium", "long"]
        if length.lower() not in valid_lengths:
            raise ValueError(f"Invalid length. Must be one of: {', '.join(valid_lengths)}")
        
        # Length guidance
        length_guidance = {
            "short": "approximately 800 words",
            "medium": "approximately 1200 words",
            "long": "approximately 2000 words"
        }
        
        # Build outline structure for prompt
        outline_text = ""
        if isinstance(outline, dict):
            outline_text = self._format_outline_for_prompt(outline)
        elif isinstance(outline, list):
            outline_text = self._format_outline_list_for_prompt(outline)
        else:
            outline_text = str(outline)
        
        prompt = f"""Generate a full blog post following this outline exactly:

Brand: {brand}
Tone: {tone}
Target Length: {length} ({length_guidance.get(length.lower(), "medium length")})

**Important: Write the entire blog post in English only.** All content must be in English.

OUTLINE:
{outline_text}

Please generate:
1. A complete blog post in markdown format following the outline structure
2. Use appropriate markdown formatting (H1, H2, H3, paragraphs, lists, etc.)
3. Write engaging, informative content that matches the tone and brand
4. Include an introduction that hooks the reader
5. Include a conclusion that summarizes key points
6. Follow the outline structure exactly but write full, detailed content for each section

After the blog content, also provide:
- A meta description (150-160 characters, SEO-optimized)
- Word count

Format your response as a JSON object:
{{
    "title": "Blog Title (from outline)",
    "content": "# Full markdown blog content here...",
    "meta_description": "SEO meta description here",
    "word_count": 1200
}}

Return only valid JSON, no additional text."""
        
        # Get LLM response
        from langchain.schema import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse JSON response
        post_data = self._extract_post_data_from_llm_response(response.content)
        
        # Calculate reading time (average reading speed: 200 words per minute)
        word_count = post_data.get("word_count", 0)
        reading_time = max(1, round(word_count / 200))
        
        result = {
            "action": "generate_post_from_outline",
            "response": {
                "title": post_data.get("title", ""),
                "content": post_data.get("content", ""),
                "meta_description": post_data.get("meta_description", ""),
                "word_count": word_count,
                "estimated_reading_time": reading_time,
                "brand": brand,
                "tone": tone,
                "length": length
            }
        }
        
        # Preserve LLM usage
        if hasattr(response, "response_metadata") and isinstance(response.response_metadata, dict):
            if "llm_usage" in response.response_metadata:
                result["llm_usage"] = response.response_metadata["llm_usage"]
                
        return result
    
    def _format_outline_for_prompt(self, outline: Dict[str, Any]) -> str:
        """Format outline dict for prompt"""
        result = []
        if "title" in outline:
            result.append(f"Title: {outline['title']}")
        if "outline" in outline:
            result.append("\nSections:")
            for section in outline["outline"]:
                result.append(f"\n## {section.get('heading', '')}")
                result.append(f"Intent: {section.get('intent', '')}")
                if "subsections" in section:
                    for subsection in section["subsections"]:
                        result.append(f"  ### {subsection.get('heading', '')}")
                        result.append(f"  Intent: {subsection.get('intent', '')}")
        return "\n".join(result)
    
    def _format_outline_list_for_prompt(self, outline: list) -> str:
        """Format outline list for prompt"""
        result = []
        for section in outline:
            if isinstance(section, dict):
                result.append(f"\n## {section.get('heading', '')}")
                result.append(f"Intent: {section.get('intent', '')}")
                if "subsections" in section:
                    for subsection in section["subsections"]:
                        result.append(f"  ### {subsection.get('heading', '')}")
                        result.append(f"  Intent: {subsection.get('intent', '')}")
        return "\n".join(result)
    
    def _generate_outline_v2(self, task) -> Dict[str, Any]:
        """Generate outline v2 - saves to database and returns structure"""
        input_data = task.input_data
        
        document_id = input_data.get("document_id")
        version = input_data.get("version", 1)
        
        if not document_id:
            raise ValueError("'document_id' is required for generate_outline_v2 action")
        
        # Generate outline using existing logic
        outline_result = self._generate_outline(task)
        outline_response = outline_result.get("response", {})
        
        # Save to database
        from shared.db_utils import get_db_connection
        import psycopg2.extras
        
        structure = {
            "title": outline_response.get("title", ""),
            "outline": outline_response.get("outline", [])
        }
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                query = """
                    INSERT INTO blog_outline_versions (id, document_id, version, structure, status)
                    VALUES (gen_random_uuid(), %s, %s, %s, 'draft')
                    RETURNING id
                """
                cursor.execute(query, (document_id, version, psycopg2.extras.Json(structure)))
                version_id = cursor.fetchone()[0]
                conn.commit()
                
                self.logger.info(f"Saved outline version {version} for document {document_id}")
        except Exception as e:
            self.logger.error(f"Failed to save outline to database: {e}")
            # Continue anyway - return the result
        
        result = {
            "action": "generate_outline_v2",
            "response": {
                "document_id": document_id,
                "version": version,
                "structure": structure
            }
        }
        
        # Propagate LLM usage from underlying call
        if "llm_usage" in outline_result:
            result["llm_usage"] = outline_result["llm_usage"]
            
        return result
    
    def _get_rag_context(self, brand: str, topic: str, target_audience: str, intent: str, feedback: list = None) -> str:
        """Get RAG context from knowledge base (synchronous wrapper)"""
        try:
            import asyncio
            import sys
            import os
            # Add backend directory to path for knowledge imports
            backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backend')
            if backend_dir not in sys.path:
                sys.path.insert(0, backend_dir)
            from knowledge.retrieval.pipeline import KnowledgePipeline
            from knowledge.vector_store.embedding_client import OllamaEmbeddingClient
            from knowledge.vector_store.chromadb_store import ChromaDBStore
            
            # Initialize pipeline components
            embedding_client = OllamaEmbeddingClient()
            vector_store = ChromaDBStore()
            knowledge_pipeline = KnowledgePipeline(embedding_client, vector_store)
            
            # Build query - incorporate feedback to make it more specific
            query_parts = [topic]
            
            # Extract key terms from feedback to enhance RAG query
            # This makes RAG retrieval more targeted to what the user actually wants
            if feedback:
                for fb in feedback:
                    comment = fb.get("comment", "")
                    # If feedback mentions product offerings, features, or specific capabilities,
                    # add those terms to the RAG query to get more relevant results
                    comment_lower = comment.lower()
                    if any(keyword in comment_lower for keyword in ["product", "offering", "feature", "capability", "api", "service"]):
                        # Extract the key part of the feedback for RAG query
                        # For example: "List all product offerings by Zwitch" -> "product offerings Zwitch"
                        # This helps RAG find relevant product information
                        query_parts.append(comment)
            
            # Add audience and intent for context
            query_parts.append(target_audience)
            query_parts.append(intent)
            
            query = " ".join(query_parts)
            
            # Smart vendor detection: check if topic/feedback mentions a specific brand
            # This handles cases where document brand doesn't match topic content
            vendor = "openmoney" if brand == "OPEN" else "zwitch"
            
            # Override vendor if topic/feedback clearly mentions a different brand
            query_lower = query.lower()
            if "zwitch" in query_lower and brand == "OPEN":
                vendor = "zwitch"
                self.logger.info(f"Vendor override: topic mentions Zwitch, switching from openmoney to zwitch")
            elif ("open money" in query_lower or "openmoney" in query_lower) and brand == "Zwitch":
                vendor = "openmoney"
                self.logger.info(f"Vendor override: topic mentions Open Money, switching from zwitch to openmoney")
            
            self.logger.info(f"RAG query: {query} (vendor: {vendor})")
            
            # Query knowledge base (run async in sync context)
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                # If loop is already running, we can't use run_until_complete
                # Fall back to no RAG context
                self.logger.warning("Event loop is running, skipping RAG context retrieval")
                return ""
            
            rag_result = loop.run_until_complete(
                knowledge_pipeline.query(
                    user_query=query,
                    knowledge_base="fintech",
                    vendor=vendor,
                    n_results=10
                )
            )
            
            context = rag_result.get("context", "")
            context_length = len(context) if context else 0
            self.logger.info(f"RAG retrieved {context_length} characters of context")
            
            if context:
                # Log a preview of the context to verify it's relevant
                preview = context[:200] if len(context) > 200 else context
                self.logger.info(f"RAG context preview: {preview}...")
            
            return context
        except Exception as e:
            self.logger.warning(f"RAG retrieval failed: {e}")
            return ""
    
    def _generate_draft_v2(self, task) -> Dict[str, Any]:
        """Generate draft v2 - incorporates feedback and optional RAG"""
        input_data = task.input_data
        
        document_id = input_data.get("document_id")
        outline_version_id = input_data.get("outline_version_id")
        version = input_data.get("version", 1)
        outline_structure = input_data.get("outline_structure")
        feedback = input_data.get("feedback", [])
        use_rag = input_data.get("use_rag", False)
        
        if not document_id:
            raise ValueError("'document_id' is required for generate_draft_v2 action")
        
        if not outline_structure:
            raise ValueError("'outline_structure' is required for generate_draft_v2 action")
        
        # Extract fields
        brand = input_data.get("brand", "OPEN").upper()
        topic = input_data.get("topic", "")
        target_audience = input_data.get("target_audience", "SME")
        intent = input_data.get("intent", "education")
        tone = input_data.get("tone", "professional")
        length = input_data.get("length", "medium")
        
        # Parse outline structure
        if isinstance(outline_structure, str):
            outline_structure = json.loads(outline_structure)
        elif isinstance(outline_structure, dict):
            pass  # Already parsed
        else:
            raise ValueError("Invalid outline_structure format")
        
        # Format outline for prompt
        outline_text = self._format_outline_for_prompt(outline_structure)
        
        # Format feedback for prompt
        feedback_text = ""
        if feedback:
            feedback_lines = ["OUTLINE FEEDBACK:"]
            for fb in feedback:
                scope = fb.get("scope", "global")
                comment = fb.get("comment", "")
                section_id = fb.get("target_section_id")
                
                if scope == "global":
                    feedback_lines.append(f"- [Global] User comment: \"{comment}\"")
                else:
                    section_label = section_id if section_id else "Unknown section"
                    feedback_lines.append(f"- [Section: \"{section_label}\"] User comment: \"{comment}\"")
            
            feedback_text = "\n".join(feedback_lines) + "\n\nPlease address all feedback when writing the draft."
        
        # Get RAG context if enabled - pass feedback to enhance query
        rag_context = ""
        if use_rag:
            try:
                rag_context = self._get_rag_context(brand, topic, target_audience, intent, feedback)
            except Exception as e:
                self.logger.warning(f"Failed to get RAG context: {e}")
                rag_context = ""
        
        # Length guidance
        length_guidance = {
            "short": "approximately 800 words",
            "medium": "approximately 1200 words",
            "long": "approximately 2000 words"
        }
        
        style_spec = self._get_brand_style_spec(
            brand=brand,
            target_audience=target_audience,
            intent=intent,
            tone=tone,
            length=length,
        )

        brand_draft_requirements = ""
        if brand == "OPEN":
            brand_draft_requirements = """
OPEN DRAFT REQUIREMENTS
- Use an empathetic, practical voice (professional yet friendly).
- Include these H2 sections (wording can vary, but intent must match):
  - What is <core concept>?
  - Common pain points
  - Step-by-step guide (numbered steps)
  - Best practices (or pitfalls to avoid)
  - How OPEN helps
  - Conclusion
- Keep sentences short and avoid jargon; define terms simply.
- CTA: include a short CTA section near the end; only include links if present in the provided context (otherwise plain text).
"""
        else:
            brand_draft_requirements = """
ZWITCH DRAFT REQUIREMENTS
- Use a problem-first, confident, developer-friendly voice; keep paragraphs scannable.
- Use the product-led pattern in each pillar section (explicit labels in the body text):
  - Challenges Solved:
  - With Zwitch <product/API>, you can:
  - Outcome:
- Include these H2 sections (wording can vary, but intent must match):
  - Understanding <core concept>
  - Enter Zwitch
  - Pillar sections (collections/payouts/banking/compliance or topic-appropriate equivalents)
  - Why Zwitch stands out
  - Real-world impact
  - Conclusion
  - CTA (plain text; link only if present in the provided context)
  - FAQs (3–6 questions)
"""

        # Build prompt
        prompt = f"""Generate a full blog post following this outline exactly:

Brand: {brand}
Tone: {tone}
Target Length: {length} ({length_guidance.get(length.lower(), "medium length")})
Audience: {target_audience}
Intent: {intent}

**Important: Write the entire blog post in English only.** All content must be in English.

BRAND STYLE SPEC (follow exactly):
{style_spec}

{brand_draft_requirements}

OUTLINE:
{outline_text}
"""
        
        if feedback_text:
            prompt += f"\n{feedback_text}\n"
        
        if rag_context:
            prompt += f"""
BRAND CONTEXT FROM KNOWLEDGE BASE (use this to address feedback about product offerings, features, and capabilities):
{rag_context}

IMPORTANT INSTRUCTIONS FOR USING BRAND CONTEXT:
- Use the provided brand context to address specific feedback requests (e.g., "List all product offerings", "Add product features")
- When feedback asks for product offerings, features, or capabilities, extract and list them from the context above
- Only use information that is explicitly mentioned in the context - do not hallucinate
- If the context contains product names, API names, or feature lists, include them in your response
- Do not cite internal file references - only use public URLs if provided in the context
- If feedback asks for a list (e.g., "List all product offerings"), create a clear, structured list from the context
"""
        
        prompt += """
Please generate:
1. A complete blog post in markdown format following the outline structure
2. Use appropriate markdown formatting (H1, H2, H3, paragraphs, lists, etc.)
3. Write engaging, informative content that matches the tone and brand
4. Include an introduction that hooks the reader
5. Include a conclusion that summarizes key points
6. Follow the outline structure exactly but write full, detailed content for each section

After the blog content, also provide:
- A meta description (150-160 characters, SEO-optimized)
- Word count

Format your response as a JSON object:
{
    "title": "Blog Title (from outline)",
    "content": "# Full markdown blog content here...",
    "meta_description": "SEO meta description here",
    "word_count": 1200
}

Return only valid JSON, no additional text."""
        
        # Get LLM response
        from langchain.schema import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse JSON response (robust to fenced/partially escaped model outputs)
        post_data = self._extract_post_data_from_llm_response(response.content)

        # Normalize + lint + optional rewrite to match house style
        try:
            content = post_data.get("content", "") or ""
            normalized = self._normalize_markdown_content(content, brand)
            issues = self._lint_markdown(normalized, brand)

            if issues:
                rewritten = self._editor_rewrite_markdown(
                    brand=brand,
                    style_spec=style_spec,
                    outline_text=outline_text,
                    markdown=normalized,
                    issues=issues,
                )
                normalized = self._normalize_markdown_content(rewritten, brand)
                normalized = self._ensure_house_style_sections(normalized, brand)
                normalized = self._normalize_markdown_content(normalized, brand)
                issues2 = self._lint_markdown(normalized, brand)
                if issues2:
                    self.logger.warning(f"Style lint still failing after rewrite: {issues2}")
            else:
                normalized = self._ensure_house_style_sections(normalized, brand)
                normalized = self._normalize_markdown_content(normalized, brand)

            post_data["content"] = normalized

            # Recompute word count if missing/invalid
            wc = post_data.get("word_count")
            if not isinstance(wc, int) or wc <= 0:
                post_data["word_count"] = self._count_words_markdown(normalized)
        except Exception as e:
            # Never fail the task due to post-processing; just log and continue.
            self.logger.warning(f"Post-processing (normalize/lint) failed: {e}")
        
        # Calculate reading time
        word_count = post_data.get("word_count", 0)
        reading_time = max(1, round(word_count / 200))
        
        # Save to database
        from shared.db_utils import get_db_connection
        import psycopg2.extras
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                query = """
                    INSERT INTO blog_draft_versions (
                        id, document_id, outline_version_id, version, content, 
                        meta_description, word_count, estimated_reading_time, status
                    )
                    VALUES (
                        gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, 'draft'
                    )
                    RETURNING id
                """
                meta_desc = post_data.get("meta_description", "")
                cursor.execute(query, (
                    document_id,
                    outline_version_id,
                    version,
                    post_data.get("content", ""),
                    meta_desc if meta_desc else None,
                    word_count,
                    reading_time
                ))
                draft_id = cursor.fetchone()[0]
                conn.commit()
                
                self.logger.info(f"Saved draft version {version} for document {document_id}")
        except Exception as e:
            self.logger.error(f"Failed to save draft to database: {e}")
            # Continue anyway - return the result
        
        result = {
            "action": "generate_draft_v2",
            "response": {
                "document_id": document_id,
                "version": version,
                "title": post_data.get("title", ""),
                "content": post_data.get("content", ""),
                "meta_description": post_data.get("meta_description", ""),
                "word_count": word_count,
                "estimated_reading_time": reading_time,
                "brand": brand,
                "tone": tone,
                "length": length
            }
        }
        
        # Preserve LLM usage
        if hasattr(response, "response_metadata") and isinstance(response.response_metadata, dict):
            if "llm_usage" in response.response_metadata:
                result["llm_usage"] = response.response_metadata["llm_usage"]
                
        return result


# Factory function to create blog agent instance
def create_blog_agent(llm_provider: str = "openai") -> BlogAgent:
    """Factory function to create blog agent. LLM provider/model selection is via router (env: LLM_*)."""
    import os
    model = os.getenv("LLM_LOCAL_MODEL") or os.getenv("LLM_CLOUD_MODEL") or ""

    config = AgentConfig(
        agent_type="blog",
        name="Blog Agent",
        description="Generates structured blog outlines and drafts for marketing teams",
        llm_provider=llm_provider,
        model=model,
        temperature=0.7,
        max_tokens=4000,  # Higher for blog generation
        tools=[]  # No tools in Phase 1
    )
    return BlogAgent(config)
