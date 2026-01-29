# Blog Agent Output Generation Flow (OPEN + Zwitch House Style)

## Overview
The Blog Agent generates:
- **Outlines**: JSON outline structure (H1/H2/H3 + intent)
- **Drafts**: JSON payload containing a full markdown blog post + metadata

This flow is implemented as a **Go API → async task → Python CLI → BlogAgent** pipeline, with **brand-specific house-style enforcement** for **OPEN** and **Zwitch**.

Key upgrades vs. the older implementation:
- **Per-brand style spec** embedded verbatim into prompts (`style_spec.py`)
- **House-style outline archetypes** (OPEN vs Zwitch) while keeping the same outline JSON schema
- **Draft prompt enforcement** for required section patterns (Zwitch: Challenges/With Zwitch/Outcome + FAQs; OPEN: pain points + step-by-step + How OPEN helps)
- **Post-generation enforcement** (heading/brand normalization + heuristic “style lint” + one editor rewrite pass)
- **Longer timeouts** for local LLM + RAG runs (Go handler + server config)

## Primary API paths (Blog Documents v2)
The blog editor flow uses the Blog Documents API:
- **Generate outline**: `POST /api/blog/documents/:id/outlines` → async task `generate_outline_v2`
- **Approve outline**: `PUT /api/blog/documents/:id/outlines/:versionId` (set `status=approved`)
- **Generate draft**: `POST /api/blog/documents/:id/drafts` → async task `generate_draft_v2`
- **Fetch latest**: `GET /api/blog/documents/:id` (returns `document`, latest `outline`, latest `draft`)

## End-to-end flow diagram (v2)

```
┌──────────────────────────────────────────────────────────────────┐
│ 1) Frontend (Blog Editor / Blog Agent UI)                         │
│    - Create/select a Blog Document                                │
│    - POST /api/blog/documents/:id/outlines                         │
│    - Later: approve outline, then POST /drafts                    │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2) Go backend: BlogDocumentsHandler (blog_documents.go)           │
│    - Validates document + approved outline (for draft)            │
│    - Creates Task rows (action: generate_outline_v2 / draft_v2)   │
│    - Spawns goroutine to execute tool via Executor                │
│    - Uses longer per-call timeouts                                │
│      • Outline: 20 minutes                                        │
│      • Draft:   25 minutes                                        │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3) Executor → Python CLI (backend/agents/blog_agent/cli.py)       │
│    - Reads JSON input (action + payload)                          │
│    - Creates a TaskInput and calls BlogAgent.execute_task()       │
│    - LLM provider selection starts from env LLM_PROVIDER          │
│      (router may still choose a local model when available)       │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4) BlogAgent (backend/agents/blog_agent/main.py)                  │
│    - Routes by action:                                            │
│      • generate_outline_v2 → _generate_outline_v2()               │
│      • generate_draft_v2   → _generate_draft_v2()                 │
│    - Uses shared RAG pipeline when use_rag=true                   │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ 5) Prompt construction + style injection                          │
│    - Loads brand Style Spec (OPEN / Zwitch)                       │
│    - Adds house-style outline archetype (OPEN vs Zwitch)          │
│    - If RAG enabled: injects KB context (strict: no new facts)    │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ 6) LLM invocation                                                  │
│    - Sends SystemMessage(system prompt) + HumanMessage(prompt)     │
│    - Provider/model chosen via environment + router availability   │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ 7) Response parsing + repair                                       │
│    - Extract JSON from ```json blocks or raw braces                │
│    - Repairs common outline JSON issues (missing commas)           │
│    - Draft parsing has extra robustness for control chars          │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ 8) Post-generation enforcement (draft_v2 only)                     │
│    - Normalize headings (H1/H2 Title Case; H3+ sentence case)      │
│    - Normalize brand spelling (OPEN / Zwitch)                      │
│    - Strip common LLM preambles before first heading               │
│    - Heuristic style lint (required sections/patterns)             │
│    - If lint fails: single editor rewrite pass                     │
│    - Deterministic guardrails: ensure CTA/FAQs/With Zwitch (Zwitch)│
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ 9) Storage (Postgres)                                              │
│    - Outline: blog_outline_versions (status='draft')               │
│    - Draft:   blog_draft_versions (status='draft')                 │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ 10) UI fetch + render                                               │
│     - GET /api/blog/documents/:id returns latest outline + draft    │
│     - UI renders markdown and version history                       │
└──────────────────────────────────────────────────────────────────┘
```

## House-style encoding (OPEN vs Zwitch)

### Style specs (`backend/agents/blog_agent/style_spec.py`)
The Blog Agent embeds a **plain-text “Brand Style Spec”** into prompts. It encodes:
- **Voice**: trustworthy, friendly, empathetic, politely confident, lightly witty
- **Clarity**: short sentences, short paragraphs, avoid jargon
- **Formatting rules**:
  - American English
  - Brand capitalization: **OPEN** and **Zwitch**
  - H1/H2 Title Case; H3+ sentence case
  - Numbers: words for 0–9, numerals for 10+
  - Acronyms spelled out on first mention
- **No-hallucination rule**: product claims/metrics/partners only if present in provided context

### Outline archetypes (prompt scaffolds)
In `_generate_outline()` the prompt adds a brand-specific archetype:
- **OPEN**: practical SME/MSME pain framing → definition → pain points → step-by-step → How OPEN helps → conclusion
- **Zwitch**: problem-first → Enter Zwitch → pillar sections with “Challenges/With Zwitch/Outcome” → why Zwitch stands out → real-world impact → conclusion → **CTA** → **FAQs**

## Draft post-processing + enforcement (what changed)
Draft generation (`generate_draft_v2`) includes an enforcement pipeline **after** JSON parsing:

1) **Normalize markdown**
- Title-case H1/H2; sentence-case H3+
- Fix brand spellings (OPEN, Zwitch)
- Remove common LLM preambles before first heading

2) **Heuristic style lint**
- Requires `## Conclusion`
- For Zwitch drafts: requires `## CTA`, `## FAQs`, and body labels:
  - `Challenges Solved:`
  - `Outcome:`
  - `With Zwitch …`

3) **Single editor rewrite pass (only if lint fails)**
`_editor_rewrite_markdown()` asks the model to rewrite the markdown to fix issues:
- Preserves coverage/order
- Does not invent facts
- Does not add links unless already present

4) **Deterministic guardrails**
If the model still omits required Zwitch sections, `_ensure_house_style_sections()` appends or injects:
- `## CTA`
- `## FAQs` (basic FAQs)
- A “With Zwitch, you can:” bullet block (inserted under “Challenges Solved:” when possible)

## Timeouts (important operational detail)
Long-form generation on local models + RAG frequently exceeds 5 minutes.

Current defaults:
- **Go server config**: `BLOG_AGENT_TIMEOUT` default is **25 minutes** (`backend/internal/config/config.go`)
- **Go handler** (`backend/internal/handlers/blog_documents.go`):
  - Outline execution context: **20 minutes**
  - Draft execution context: **25 minutes**

## Files involved (current)
- **Agent logic**: `backend/agents/blog_agent/main.py`
  - `get_style_spec()` integration
  - Outline archetypes + prompt updates
  - Draft post-processing pipeline (normalize/lint/rewrite/guardrails)
- **Style specs**: `backend/agents/blog_agent/style_spec.py`
- **CLI**: `backend/agents/blog_agent/cli.py`
- **Go handlers**: `backend/internal/handlers/blog_documents.go`
- **Timeout config**: `backend/internal/config/config.go`

## Notes / guardrails
- **Links in CTA**: the editor pass is instructed not to add links unless already present in the text/context.
- **No hallucinations**: the style spec and RAG prompt both emphasize “only use facts present in context.”
