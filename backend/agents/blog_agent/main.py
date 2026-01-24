"""
Blog Agent Implementation
Generates structured blog outlines and drafts for marketing teams
"""

from typing import Dict, Any
import json
import re
from shared.base_agent import BaseAgent, AgentConfig


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
- Follow brand guidelines (OPEN brand: technical, detailed | Zwitch brand: friendly, accessible)
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
    
    def _run_agent_loop(self, system_prompt: str, user_prompt: str, task) -> Dict[str, Any]:
        """
        Enhanced agent loop for blog tasks
        """
        start_time = task.metadata.get("start_time") if hasattr(task, 'metadata') else None
        
        if task.action == "generate_outline":
            return self._generate_outline(task)
        elif task.action == "generate_post_from_outline":
            return self._generate_post_from_outline(task)
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
        
        prompt = f"""Generate a structured blog outline for the following specifications:

Brand: {brand} ({brand_guidance.get(brand, "")})
Topic: {topic}
Target Audience: {target_audience} ({audience_guidance.get(target_audience.upper(), "")})
Intent: {intent} ({intent_guidance.get(intent.lower(), "")})

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
        
        return {
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
        
        try:
            post_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse post JSON: {e}")
            self.logger.error(f"Response was: {response_text}")
            raise ValueError(f"Failed to parse post response as JSON: {str(e)}")
        
        # Calculate reading time (average reading speed: 200 words per minute)
        word_count = post_data.get("word_count", 0)
        reading_time = max(1, round(word_count / 200))
        
        return {
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
