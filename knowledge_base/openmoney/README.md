# Open Money Knowledge Base — Hierarchy and Precedence

## Knowledge Precedence

This README defines the **authoritative hierarchy** for knowledge retrieval and decision-making in the Open Money knowledge base.

When information conflicts or ambiguity arises, **higher layers override lower layers**.

## Hierarchy (Top to Bottom)

### 1. `principles/` — Foundational Rules

**Authority:** Highest

**Purpose:** Defines absolute rules that cannot be overridden. These are foundational architectural principles.

**Rules:**
- Principles define what must, cannot, and always happen
- Principles override all other layers
- Principles establish the fundamental authority model
- Principles define what Open Money is and is not

**Files:**
- `backend_authority.md` — Backend owns critical decisions
- `reconciliation_is_not_optional.md` — Reconciliation is mandatory
- `financial_finality_rules.md` — When money movement is final

**Override Authority:** Principles override all other layers. If any documentation conflicts with principles, principles win.

---

### 2. `states/` — Source of Truth for Finality & Transitions

**Authority:** Second highest

**Purpose:** Defines state machines, terminal states, and irreversible transitions.

**Rules:**
- States define what is final and what is reversible
- Terminal states are absolute
- State transitions are authoritative—no dashboard can override state rules
- Only reconciled states mean financial finality

**Files:**
- `invoice_state_lifecycle.md` — Invoice state machine
- `bill_state_lifecycle.md` — Bill state machine
- `payment_link_state_lifecycle.md` — Payment link state machine
- `payout_state_lifecycle.md` — Payout state machine
- `bank_account_states.md` — Bank account connection states

**Override Authority:** States override workflows, modules, and concepts. If a dashboard or workflow conflicts with state definitions, states win.

---

### 3. `workflows/` — End-to-End System Behavior

**Authority:** Third highest

**Purpose:** Describes complete journeys, step-by-step processes, and system behavior.

**Rules:**
- Workflows define the correct sequence of operations
- Workflows specify where truth is confirmed
- Workflows define what must be stored and reconciled
- Workflows identify final vs reversible steps

**Files:**
- `invoice_to_collection.md` — Invoice collection flow
- `payment_link_to_settlement.md` — Payment link settlement flow
- `bill_to_payout.md` — Bill payout flow
- `bulk_collection_flow.md` — Bulk collection process
- `reconciliation_flow.md` — Reconciliation process
- `gst_compliance_flow.md` — GST compliance process

**Override Authority:** Workflows override modules, data semantics, and concepts. If a workflow conflicts with module documentation, workflows win.

---

### 4. `data_semantics/` — Data Meaning and Limitations

**Authority:** Factual reference

**Purpose:** Documents what data means, where it comes from, and what it does not mean.

**Rules:**
- Data semantics document facts—what data represents
- Data semantics clarify derived vs actual data
- Data semantics explain limitations and misinterpretations
- Data semantics are reference material, not decision guides

**Files:**
- `sample_data_vs_real_data.md` — Sample data isolation
- `derived_vs_actual_balances.md` — Balance interpretation
- `overdue_calculation_logic.md` — Overdue computation
- `cashflow_calculation.md` — Cashflow derivation
- `reconciliation_logic.md` — Reconciliation meaning

**Override Authority:** Data semantics are factual and cannot be overridden by interpretations. However, states and workflows define how to use data correctly.

---

### 5. `risks/` — Safety and Failure Scenarios

**Authority:** Safety warnings

**Purpose:** Highlights risks, failure scenarios, and what not to trust.

**Rules:**
- Risks are conservative and safety-focused
- Risks highlight what NOT to do
- Risks can override best practices if safety requires it
- Risks explain why dashboards and derived data can mislead

**Files:**
- `dashboard_misinterpretation.md` — Dashboard limitations
- `stale_bank_data.md` — Bank sync delays
- `reconciliation_gaps.md` — Reconciliation failures
- `gst_compliance_risks.md` — Compliance risks

**Override Authority:** Risks can override decisions and modules if safety requires it. Risks never override states, workflows, or principles.

---

### 6. `decisions/` — Opinionated Trade-offs

**Authority:** Opinionated guidance

**Purpose:** Provides clear recommendations on architectural and implementation choices.

**Rules:**
- Decisions are opinionated—they recommend one approach over others
- Decisions explain trade-offs and when NOT to do something
- Decisions can be overridden by states, workflows, and principles if they conflict

**Files:**
- `invoice_vs_payment_link.md` — When to use each
- `single_vs_bulk_payments.md` — Bulk payment guidance
- `when_to_reconcile.md` — Reconciliation timing
- `handling_failed_payouts.md` — Payout failure handling

**Override Authority:** Decisions can be overridden by states, workflows, and principles. Decisions never override facts in data semantics.

---

### 7. `modules/` — Product Surface Documentation

**Authority:** Explanatory

**Purpose:** Documents what each product module does and does not do.

**Rules:**
- Modules are explanatory, not authoritative
- Modules help understanding but don't define behavior
- Modules can be overridden by any other layer

**Files:**
- `receivables.md` — Receivables module
- `payables.md` — Payables module
- `banking.md` — Banking module
- `cashflow_analytics.md` — Cashflow module
- `payments_and_payouts.md` — Payments module
- `compliance.md` — Compliance module

**Override Authority:** Modules have lower authority. Any other layer can override modules.

---

### 8. `concepts/` — High-Level Explanations

**Authority:** Explanatory only

**Purpose:** Provides non-technical explanations, analogies, and conceptual understanding.

**Rules:**
- Concepts are explanatory, not authoritative
- Concepts help understanding but don't define behavior
- Concepts can be overridden by any other layer

**Files:**
- `what_is_open_money.md` — Open Money identity
- `open_money_product_philosophy.md` — Product philosophy
- `open_money_vs_bank.md` — Platform comparison
- `open_money_vs_accounting_software.md` — Software comparison
- `data_ownership_and_limitations.md` — Data boundaries

**Override Authority:** Concepts have the lowest authority. Any other layer can override concepts.

---

## Conflict Resolution Rules

1. **Principles override everything** — If a principle says something must happen, it must happen, regardless of other documentation.

2. **States override workflows** — If a state says something is terminal, it is terminal, regardless of workflow.

3. **Workflows override modules** — If a workflow specifies a sequence, follow the workflow even if module documentation suggests otherwise.

4. **Data semantics never override facts** — Data semantics document what data means, but states and workflows define how to use it.

5. **Risks can override decisions** — If a risk identifies a safety issue, prioritize safety over convenience.

6. **Concepts are lowest priority** — Concepts help understanding but don't define behavior.

## Usage Guidelines

- **For state questions:** Consult `states/` first
- **For process questions:** Consult `workflows/` first
- **For data meaning questions:** Consult `data_semantics/` for facts, but verify against `states/` and `workflows/`
- **For implementation questions:** Consult `decisions/`
- **For safety questions:** Consult `risks/` first
- **For explanation questions:** Consult `concepts/` for understanding, but verify with authoritative layers

## Absolute Principles

These principles are **always applicable** and cannot be overridden:

1. **Open Money is NOT a source of financial truth**
   - Bank statements are authoritative
   - Payment rails are authoritative
   - Compliance systems are authoritative
   - Open Money dashboards are derived and informational

2. **Reconciliation is mandatory**
   - Not optional
   - Required for financial accuracy
   - Only reconciliation confirms alignment between documents, payments, and bank entries

3. **Backend authority**
   - Frontend/dashboard is informational only
   - All financial decisions must be made on the backend
   - Dashboard state is never authoritative

4. **Derived data warnings**
   - Most values shown in Open Money are derived, not primary
   - Derived data can be temporarily incorrect, delayed, or incomplete
   - Always verify against source systems for critical decisions

5. **Sample data isolation**
   - Sample data must never be treated as real business data
   - Sample data exists only for demonstration
   - No compliance data is valid in sample mode

## Related Documentation

See `principles/` folder for foundational rules that apply across all layers:
- `backend_authority.md` — Backend owns critical decisions
- `reconciliation_is_not_optional.md` — Reconciliation is mandatory
- `financial_finality_rules.md` — When money movement is final

These principles are **always applicable** and cannot be overridden.

