# Zwitch Knowledge Base — Hierarchy and Precedence

## Knowledge Precedence

This README defines the **authoritative hierarchy** for knowledge retrieval and decision-making in the Zwitch knowledge base.

When information conflicts or ambiguity arises, **higher layers override lower layers**.

## Hierarchy (Top to Bottom)

### 1. `states/` — Source of Truth for Finality & Transitions

**Authority:** Highest

**Purpose:** Defines state machines, terminal states, and irreversible transitions.

**Rules:**
- States define what is final and what is reversible
- Terminal states (`completed`, `failed`, `expired`, `cancelled`) are absolute
- State transitions are authoritative—no API call can override state rules
- Only `completed` status means money movement is final

**Files:**
- `payment_status_lifecycle.md` — Payment state machine
- `transfer_status_lifecycle.md` — Transfer state machine
- `verification_states.md` — Verification state machine

**Override Authority:** States override all other layers. If an API response conflicts with state definitions, states win.

---

### 2. `flows/` — End-to-End System Behavior

**Authority:** Second highest

**Purpose:** Describes complete journeys, step-by-step processes, and system behavior.

**Rules:**
- Flows define the correct sequence of operations
- Flows specify which APIs to call at each step
- Flows define what must be stored in the database
- Flows identify final vs reversible steps

**Files:**
- `payin_happy_path.md` — Successful payment flow
- `payin_failure_path.md` — Payment failure handling
- `refund_flow.md` — Refund process
- `settlement_flow.md` — Settlement process

**Override Authority:** Flows override APIs, best practices, and decisions. If a flow conflicts with API documentation, flows win.

---

### 3. `api/` — Exact Interfaces, Endpoints, Fields

**Authority:** Factual reference

**Purpose:** Documents exact API endpoints, request/response formats, parameters, and field definitions.

**Rules:**
- APIs document facts—endpoints, fields, enums, status codes
- APIs do not define business logic or state transitions
- APIs are reference material, not decision guides
- API examples are illustrative, not prescriptive

**Files:**
- All numbered API documentation files (`00_introduction.md` through `15_layer_js.md`)

**Override Authority:** APIs are factual and cannot be overridden by interpretations. However, states and flows define how to use APIs correctly.

---

### 4. `best_practices/` — Production Recommendations

**Authority:** Recommended guidance

**Purpose:** Provides production-ready recommendations, schemas, checklists, and operational guidance.

**Rules:**
- Best practices are recommendations, not requirements
- Best practices can be overridden by states and flows
- Best practices focus on production safety and reliability

**Files:**
- `recommended_db_schema.md` — Database design recommendations
- `production_checklist.md` — Pre-launch checklist
- `logging_and_audits.md` — Logging requirements

**Override Authority:** Best practices can be overridden by states, flows, or decisions if safety requires it.

---

### 5. `decisions/` — Opinionated Trade-offs

**Authority:** Opinionated guidance

**Purpose:** Provides clear recommendations on architectural and implementation choices.

**Rules:**
- Decisions are opinionated—they recommend one approach over others
- Decisions explain trade-offs and when NOT to do something
- Decisions can be overridden by states and flows if they conflict

**Files:**
- `polling_vs_webhooks.md` — Webhooks are primary, polling is fallback
- `frontend_vs_backend_calls.md` — Backend authority for financial operations
- `retries_and_idempotency.md` — Retry strategies and idempotency requirements

**Override Authority:** Decisions can be overridden by states and flows. Decisions never override facts in APIs.

---

### 6. `risks/` — Safety and Failure Scenarios

**Authority:** Safety warnings

**Purpose:** Highlights risks, failure scenarios, and compliance boundaries.

**Rules:**
- Risks are conservative and safety-focused
- Risks highlight what NOT to do
- Risks can override best practices if safety requires it

**Files:**
- `double_credit_risk.md` — Preventing duplicate processing
- `webhook_signature_verification.md` — Security requirement
- `reconciliation_failures.md` — Handling discrepancies
- `compliance_boundaries.md` — Legal and compliance responsibilities

**Override Authority:** Risks can override best practices and decisions if safety requires it. Risks never override states or flows.

---

### 7. `concepts/` — High-Level Explanations

**Authority:** Explanatory only

**Purpose:** Provides non-technical explanations, analogies, and conceptual understanding.

**Rules:**
- Concepts are explanatory, not authoritative
- Concepts help understanding but don't define behavior
- Concepts can be overridden by any other layer

**Files:**
- `payment_token_vs_order.md` — Conceptual distinction
- `payin_vs_payout.md` — Money flow explanation
- `merchant_vs_platform.md` — Business model distinction
- `zwitch_vs_open_money.md` — Platform comparison

**Override Authority:** Concepts have the lowest authority. Any other layer can override concepts.

---

## Conflict Resolution Rules

1. **States override everything** — If a state says something is terminal, it is terminal, regardless of API or flow.

2. **Flows override APIs** — If a flow specifies a sequence, follow the flow even if API documentation suggests otherwise.

3. **APIs never override states** — API responses must be interpreted through state definitions.

4. **Decisions never override facts** — Decisions are opinions, not facts. API facts are immutable.

5. **Risks can override best practices** — If a risk identifies a safety issue, prioritize safety over convenience.

6. **Concepts are lowest priority** — Concepts help understanding but don't define behavior.

## Usage Guidelines

- **For state questions:** Consult `states/` first
- **For process questions:** Consult `flows/` first
- **For API questions:** Consult `api/` for facts, but verify against `states/` and `flows/`
- **For implementation questions:** Consult `best_practices/` and `decisions/`
- **For safety questions:** Consult `risks/` first
- **For explanation questions:** Consult `concepts/` for understanding, but verify with authoritative layers

## Principles Layer

See `principles/` folder for foundational rules that apply across all layers:
- `source_of_truth.md` — Webhooks are primary source of truth
- `backend_authority.md` — Backend owns critical decisions
- `idempotency.md` — Idempotency is mandatory

These principles are **always applicable** and cannot be overridden.

