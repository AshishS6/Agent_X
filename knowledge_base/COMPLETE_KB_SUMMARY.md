# Complete Knowledge Base Summary

## Overview

This document provides a comprehensive summary of the entire Knowledge Base (KB), including all folders, files, and their contents. The KB is organized into two main sections: **Open Money** and **Zwitch**, both of which are fintech platforms operating in India.

---

## Knowledge Base Structure

```
knowledge_base/
├── README.md                          # Main KB overview and usage guide
├── KNOWLEDGE_BASE_EXPLAINED.md        # Explanation of KB folder vs RAG system
├── COMPLETE_KB_SUMMARY.md            # This document
├── openmoney/                         # Open Money platform documentation
│   ├── README.md                      # Open Money hierarchy and precedence
│   ├── company_overview.md            # Company identity and positioning
│   ├── concepts/                      # High-level explanations
│   ├── principles/                    # Foundational rules (highest authority)
│   ├── states/                        # State machines and finality
│   ├── workflows/                     # End-to-end system behavior
│   ├── data_semantics/                # Data meaning and limitations
│   ├── risks/                         # Safety warnings
│   ├── decisions/                     # Opinionated trade-offs
│   └── modules/                       # Product surface documentation
└── zwitch/                            # Zwitch platform documentation
    ├── README.md                      # Zwitch hierarchy and precedence
    ├── company_overview.md            # Company identity and positioning
    ├── FAQ.md                         # Frequently asked questions
    ├── PAYMENT_GATEWAY.md             # Payment gateway confirmation
    ├── _meta/                         # Metadata and analysis
    ├── api/                           # API documentation (factual reference)
    ├── states/                         # State machines (highest authority)
    ├── flows/                          # End-to-end system behavior
    ├── best_practices/                 # Production recommendations
    ├── decisions/                      # Opinionated trade-offs
    ├── risks/                          # Safety warnings
    ├── principles/                     # Foundational rules
    └── concepts/                      # High-level explanations
```

---

## Root Level Files

### 1. `README.md`
**Purpose:** Main knowledge base overview and usage guide

**Contents:**
- Current knowledge base contents summary
- How to use the KB in the frontend
- Testing questions to verify RAG is working
- Methods for adding more documents
- File structure overview
- Next steps for expanding the KB

**Key Points:**
- Documents are organized into chunks when ingested
- Currently contains 8 chunks (2 general fintech, 3 Open Money, 3 Zwitch)
- Provides guidance on testing and expanding the KB

### 2. `KNOWLEDGE_BASE_EXPLAINED.md`
**Purpose:** Explains the distinction between the KB folder and the RAG system

**Contents:**
- Important distinction between `knowledge_base/` folder (organizational) and `knowledge_base` parameter (ChromaDB collection)
- How the RAG system actually works
- Where data is stored (ChromaDB in `backend/data/chromadb/`)
- Alternative approaches for file processing

**Key Points:**
- The folder is just for organization, not used directly by RAG
- RAG uses ChromaDB collections, not the folder structure
- Files must be uploaded via API to be ingested into RAG

---

## Open Money Section

### Overview
Open Money is a **business finance operating system** that helps companies collect money, pay money, track money, reconcile money, and stay compliant. It is NOT a bank and NOT a payment gateway. It sits between banks, payment gateways, accounting systems, compliance systems, and business users to orchestrate financial operations.

### Hierarchy and Authority
The Open Money KB follows a strict hierarchy where higher layers override lower layers:
1. **Principles** (highest authority) - Foundational rules
2. **States** - Source of truth for finality
3. **Workflows** - End-to-end system behavior
4. **Data Semantics** - Data meaning and limitations
5. **Risks** - Safety warnings
6. **Decisions** - Opinionated trade-offs
7. **Modules** - Product surface documentation
8. **Concepts** (lowest authority) - High-level explanations

### Files by Category

#### Core Files

**`openmoney/README.md`**
- Defines the authoritative hierarchy for knowledge retrieval
- Explains precedence rules and conflict resolution
- Lists absolute principles that cannot be overridden
- Usage guidelines for different types of questions

**`openmoney/company_overview.md`**
- Company identity: Indian fintech infrastructure platform
- Core focus areas: Embedded banking, business payments, financial operations
- Target customers: SMEs, startups, fintech companies
- Primary capabilities: Banking infrastructure, payment collections/payouts, virtual accounts
- What Open Money is NOT: Not a consumer banking app, not a personal finance app
- Operating geography: India
- Regulatory context: RBI guidelines via partner banks

#### Concepts (`openmoney/concepts/`)

**`what_is_open_money.md`**
- Defines Open Money as a business finance operating system
- Core role: Orchestrates between banks, payment gateways, accounting systems
- What it does: Creates documents, initiates payments, aggregates balances, tracks receivables/payables
- Transaction Status and Settlement: Open Money is a Payment Aggregator (PA) licensed by RBI and is liable for settlements. Success/failed statuses are accurate and reliable. Pending statuses require cross-checking with bank.
- What it does NOT do: Override bank data, replace accounting systems, own financial truth (it aggregates and presents data from authoritative sources)
- Authority hierarchy: Bank statements > Payment rails > GST/IRP > Open Money Dashboard

**`open_money_vs_bank.md`**
- Critical distinction: Open Money is not a bank
- What banks own: Accounts, balances, transaction history, bank statement records (authoritative source for verification)
- What Open Money owns: Financial documents, payment links, reconciliation records
- Payment Processing and Settlement: Open Money is a Payment Aggregator (PA) licensed by RBI and is liable for settlements. Processes and settles payments. Transaction statuses (success/failed) are reliable.
- Bank balance vs Open Money balance (authoritative vs derived)
- When to trust bank vs Open Money
- Bank sync limitations and reconciliation requirements

**`open_money_vs_accounting_software.md`**
- Core distinction: Financial orchestration vs record-keeping
- What accounting software does: Books of accounts, journal entries, financial statements, tax reports
- What Open Money does: Document creation, payment initiation, bank aggregation, cashflow visibility
- Key differences: Purpose, data model, authority
- Integration relationship and data flow
- When to use each system

**`open_money_product_philosophy.md`**
- Core philosophy: Aggregation, not ownership
- Design principles: Reconciliation as first-class concept, derived data transparency, backend authority, conservative by default
- Product boundaries: What Open Money provides vs does not provide
- User mental model: "Financial control center"
- Implementation philosophy questions

**`data_ownership_and_limitations.md`**
- Data sources and ownership table
- Derived data warnings
- Sample data mode isolation
- Hard limitations: Cannot detect missed webhooks, guarantee sync timing, override bank data
- Data freshness dependencies
- What Open Money owns vs does not own
- Interpretation rules and common misinterpretations

#### Principles (`openmoney/principles/`)

**`backend_authority.md`**
- Absolute rule: Frontend is informational only, backend makes all financial decisions
- Why frontend cannot be trusted: Client-side manipulation, network issues, race conditions, security
- Backend authority requirements: Process webhooks, verify statuses, update database, authorize operations
- What frontend can/cannot do
- Implementation requirements for backend and frontend
- Common mistakes and correct patterns
- Override authority: Cannot be overridden by any other layer

**`reconciliation_is_not_optional.md`**
- Absolute rule: Reconciliation is mandatory, not optional
- Why it's mandatory: Financial accuracy, data integrity, regulatory compliance
- What reconciliation means: Matching documents to payments, payments to bank entries, verifying completeness
- When reconciliation is required: Daily/weekly/monthly based on activity
- What happens without reconciliation: Missed payments, duplicate entries, discrepancies
- Reconciliation process steps
- Common excuses (all invalid)
- Implementation requirements

**`financial_finality_rules.md`**
- Absolute rule: Money movement is final only when confirmed by authoritative source
- Authority hierarchy: Bank statement (highest) > Payment rail confirmation > Open Money Dashboard (not authoritative)
- When money movement is final: For collections and payouts
- States that look final but are NOT: Dashboard success, invoice paid status, payout completed status
- Terminal states vs financial finality
- Common misinterpretations
- Verification process
- Reversals and refunds

#### States (`openmoney/states/`)

**`invoice_state_lifecycle.md`**
- Complete state machine for invoices
- States: `draft`, `payment_due`, `partially_paid`, `paid`, `overdue`, `cancelled`, `written_off`
- Terminal states: `paid`, `cancelled`, `written_off`
- State transitions and reversibility
- Critical rules: Only mark as paid when status is `paid` and reconciled
- Common misinterpretations
- Reconciliation requirement

**`bill_state_lifecycle.md`**
- Complete state machine for bills
- States: `draft`, `payment_due`, `partially_paid`, `paid`, `overdue`, `cancelled`
- Terminal states: `paid`, `cancelled`
- State transitions and reversibility
- Critical rules: Only mark as paid when status is `paid` and reconciled
- Common misinterpretations
- Reconciliation requirement

**`payment_link_state_lifecycle.md`**
- Complete state machine for payment links
- States: `active`, `partially_paid`, `paid`, `expired`, `cancelled`
- Terminal states: `paid`, `expired`, `cancelled`
- State transitions and reversibility
- Critical rules: Only mark as paid when status is `paid` and reconciled
- Expiration behavior
- Common misinterpretations

**`payout_state_lifecycle.md`**
- Complete state machine for payouts
- States: `initiated`, `processing`, `completed`, `failed`, `cancelled`
- Terminal states: `completed`, `failed`, `cancelled`
- State transitions and reversibility
- Critical rules: Only mark as completed when status is `completed` and reconciled
- Failure handling
- Common misinterpretations

**`bank_account_states.md`**
- States for bank account connections
- States: `disconnected`, `connecting`, `connected`, `sync_failed`, `inactive`
- All states are reversible (no terminal states)
- Critical rules: When to trust bank data
- Sync limitations: Not real-time, may be delayed, may fail, may be incomplete
- Common misinterpretations
- Reconciliation requirement even when connected

#### Workflows (`openmoney/workflows/`)

**`invoice_to_collection.md`**
- Complete system-level flow from invoice creation to collection
- Steps: Invoice creation → Invoice sent → Payment method selection → Payment initiation → Payment confirmation → Bank settlement → Reconciliation → Invoice marked as paid
- Critical checkpoints: Must wait for confirmation, bank settlement, reconciliation
- Timeline example
- Success criteria
- Common failure points: Payment rail failure, bank sync delay, amount mismatch

**`bill_to_payout.md`**
- Complete system-level flow from bill creation to payout
- Steps: Bill creation → Bill finalized → Payout initiation → Payout processing → Payout confirmation → Bank settlement → Reconciliation → Bill marked as paid
- Critical checkpoints: Must wait for confirmation, bank settlement, reconciliation
- Timeline example
- Success criteria
- Common failure points: Payout rail failure, bank sync delay, amount mismatch
- Bulk payout handling

**`reconciliation_flow.md`**
- Complete system-level flow for reconciliation
- Steps: Data gathering → Matching → Verification → Discrepancy detection → Resolution → Confirmation
- Reconciliation types: Document-to-payment, payment-to-bank, full reconciliation
- Reconciliation status: `pending`, `in_progress`, `reconciled`, `discrepancy`
- Critical checkpoints
- Common discrepancies: Amount mismatch, missing payment, missing bank entry, duplicate entry
- Reconciliation frequency: Daily/weekly/monthly

**`payment_link_to_settlement.md`**
- Payment link settlement flow (similar structure to invoice flow)

**`bulk_collection_flow.md`**
- Bulk collection process documentation

**`gst_compliance_flow.md`**
- GST compliance process documentation

#### Data Semantics (`openmoney/data_semantics/`)

**`derived_vs_actual_balances.md`**
- Critical distinction: Balances shown are derived, not actual
- What is actual balance: Bank statement, bank API, passbook
- What is derived balance: Calculated by Open Money from last sync
- Limitations: Not real-time, may be incomplete, may have errors, may not account for pending transactions
- When to use derived vs actual balance
- Common misinterpretations
- Reconciliation requirement
- How to verify balance

**`reconciliation_logic.md`**
- What reconciliation means: Matching documents to payments, payments to bank entries
- Why reconciliation is required: Multiple data sources, delays, errors
- Reconciliation process: Match documents to payments, match payments to bank entries, verify amounts, confirm reconciliation
- Reconciliation status: `pending`, `reconciled`, `discrepancy`
- What reconciliation confirms vs does not confirm
- Common misinterpretations
- Reconciliation frequency

**`cashflow_calculation.md`**
- How cashflow is calculated: From bank transactions, payment records, document records, derived calculations
- Cash inflow (collections) and cash outflow (payouts)
- Net cashflow calculation
- Limitations: Based on synced data, may miss recent transactions, timing differences, may not account for pending transactions
- When to use cashflow vs when to verify
- Common misinterpretations
- Reconciliation requirement

**`overdue_calculation_logic.md`**
- Overdue calculation based on due date, not payment status
- May show overdue even if payment received
- Requires reconciliation to verify

**`sample_data_vs_real_data.md`**
- Sample data isolation: No real money, no valid compliance data, no reconciliation should be trusted
- Sample data exists only for demonstration

#### Risks (`openmoney/risks/`)

**`dashboard_misinterpretation.md`**
- Why dashboards can mislead: Derived data, stale data, incomplete data, status misinterpretation
- Common misinterpretations: Balance accuracy, payment finality, overdue accuracy, cashflow accuracy
- What NOT to trust dashboard for: Actual bank balance, payment finality, transaction completeness, data freshness, financial decisions
- Mitigation strategies: Always verify, understand data source, reconcile regularly, don't trust alone
- Real-world failure scenarios

**`stale_bank_data.md`**
- Bank sync delays and failures
- Data freshness issues
- Impact on decision-making

**`reconciliation_gaps.md`**
- Reconciliation failures and their consequences
- How to identify and resolve gaps

**`gst_compliance_risks.md`**
- GST compliance risks and requirements
- How to avoid compliance issues

#### Decisions (`openmoney/decisions/`)

**`invoice_vs_payment_link.md`**
- Recommendation: Use invoices for formal business transactions, payment links for quick collections
- When to use invoices: Formal transactions, compliance requirements, customer records, accounting integration
- When to use payment links: Quick collections, customer convenience, non-compliance scenarios, temporary collections
- Decision matrix
- What NOT to do
- Hybrid approach
- Reconciliation requirements

**`single_vs_bulk_payments.md`**
- Guidance on when to use single vs bulk payments
- Trade-offs and recommendations

**`when_to_reconcile.md`**
- Reconciliation timing recommendations
- Frequency guidelines based on business activity

**`handling_failed_payouts.md`**
- How to handle payout failures
- Retry strategies and error handling

#### Modules (`openmoney/modules/`)

**`receivables.md`**
- Manages money customers owe to business
- Components: Invoices, payment links, credit notes
- What it does vs does not do
- Data sources: Owned by Open Money vs derived
- Limitations: Outstanding amount, overdue calculation, payment status
- Reconciliation requirement
- Common misinterpretations

**`payables.md`**
- Manages money business owes to vendors
- Components: Bills, payouts, debit notes
- What it does vs does not do
- Data sources: Owned by Open Money vs derived
- Limitations: Outstanding amount, overdue calculation, payout status
- Reconciliation requirement
- Common misinterpretations

**`banking.md`**
- Aggregates and displays bank account data
- Components: Bank connections, balance aggregation, transaction sync
- What it does vs does not do
- Data sources: Owned by banks vs derived by Open Money
- Limitations: Balance accuracy, transaction completeness, sync timing
- Reconciliation requirement
- Common misinterpretations
- Bank account states

**`cashflow_analytics.md`**
- Cashflow visibility and analytics
- Derived metrics and calculations

**`payments_and_payouts.md`**
- Payment and payout management
- Payment initiation and tracking

**`compliance.md`**
- Compliance assistance and workflows
- GST and regulatory compliance

---

## Zwitch Section

### Overview
Zwitch is an Indian fintech infrastructure platform that provides API-based banking and payment solutions. It offers four main product categories: Payment Gateway, Payouts, Zwitch Bill Connect, and Verification Suite. It enables companies to integrate financial services without managing banking partnerships or regulatory complexity.

### Hierarchy and Authority
The Zwitch KB follows a strict hierarchy where higher layers override lower layers:
1. **States** (highest authority) - Source of truth for finality
2. **Flows** - End-to-end system behavior
3. **API** - Exact interfaces and endpoints (factual reference)
4. **Best Practices** - Production recommendations
5. **Decisions** - Opinionated trade-offs
6. **Risks** - Safety warnings
7. **Concepts** (lowest authority) - High-level explanations

### Files by Category

#### Core Files

**`zwitch/README.md`**
- Defines the authoritative hierarchy for knowledge retrieval
- Explains precedence rules and conflict resolution
- Usage guidelines for different types of questions
- Principles layer overview

**`zwitch/company_overview.md`**
- Company identity: Indian fintech infrastructure platform
- Core focus areas: BaaS, payment and payout APIs, embedded finance
- Target customers: Fintech startups, SaaS companies, marketplaces
- Primary capabilities: Payment Gateway (150+ methods), payouts, virtual accounts, compliance workflows
- Product categories: Payment Gateway, Payouts, Zwitch Bill Connect, Verification Suite
- What Zwitch is NOT: Not a licensed bank, not consumer-facing
- Operating geography: India
- Regulatory context: Works with regulated partner banks

**`zwitch/FAQ.md`**
- Does Zwitch offer Payment Gateway services? YES
- Payment Gateway features: 150+ payment options, payment links, instant refunds, recurring payments, native SDKs
- Integration methods: Layer.js (web), mobile SDKs, UPI Collect
- Key statistics: 4M+ businesses, 150+ payment methods, $35B+ transactions
- Getting started guide
- Related documentation links

**`zwitch/PAYMENT_GATEWAY.md`**
- Direct confirmation: YES, Zwitch offers Payment Gateway services
- Quick facts: Product category #1, 150+ payment methods, multiple integration options
- Direct quote from Zwitch website
- Integration options: Layer.js, mobile SDKs, UPI Collect
- Conclusion: Core product offering with dedicated API endpoints

#### Metadata (`zwitch/_meta/`)

**`API_FACT_CHECK_ANALYSIS.md`**
- Fact check analysis of API documentation
- Verification of endpoints and accuracy
- Corrections and updates made

**`UPDATE_SUMMARY.md`**
- Summary of all updates made to Zwitch API KB
- Corrections: Payment token endpoint, status check endpoint, collections clarification
- Verification status of all endpoints
- Files modified and verified

#### API Documentation (`zwitch/api/`)

**`00_introduction.md`**
- Overview: India's leading online payment API solution
- Payment Gateway Services: YES, core product with 150+ payment methods
- Platform statistics: 4M+ businesses, 150+ payment methods, $35B+ transactions
- Base URL: `https://api.zwitch.io/v1`
- API versioning: v1
- Authentication: Bearer token
- Rate limits, request/response format
- Core product categories: Payment Gateway, Payouts, Zwitch Bill Connect, Verification Suite
- Additional API services: Accounts, Beneficiaries, Connected Banking, Webhooks
- Getting started guide
- SDKs and libraries
- Support and resources
- Best practices

**`01_authentication.md`**
- Bearer token authentication
- Format: `Bearer ACCESS_KEY:SECRET_KEY`
- How to generate API keys
- Security best practices

**`02_error_codes.md`**
- Error response format
- Common error codes and meanings
- Error handling guidelines

**`03_accounts.md`**
- Account management APIs
- Create and manage virtual accounts
- Account details and information

**`04_account_balance_statement.md`**
- Account balance retrieval
- Statement generation
- Balance inquiry APIs

**`05_payments.md`**
- Payment collection APIs
- UPI Collect: `POST /v1/accounts/{account_id}/payments/upi/collect`
- Payment Gateway: `POST /v1/pg/payment_token`
- Payment status check: `GET /v1/payments/token/{payment_token_id}/status`
- Request/response formats
- Code examples

**`06_beneficiaries.md`**
- Beneficiary management APIs
- Create, list, update beneficiaries
- Beneficiary verification

**`07_transfers.md`**
- Transfer/payout APIs
- Single transfers: `POST /v1/transfers`
- Bulk transfers: `POST /v1/transfers/bulk`
- Transfer status and details
- Request/response formats

**`08_verification.md`**
- Verification APIs
- VPA verification: `/v1/verifications/vpa`
- Bank account verification: `/v1/verifications/bank-account/pennyless`
- PAN verification: `/v1/verifications/pan`
- Name verification: `/v1/verifications/name`

**`09_bharat_connect.md`**
- Zwitch Bill Connect APIs
- Business onboarding: `/v1/bharat-connect/onboarding/`
- Invoice management: `/v1/bharat-connect/invoice/`
- Payment requests: `/v1/bharat-connect/payment`
- ERP integration capabilities

**`10_webhooks.md`**
- Webhook setup and configuration
- Webhook events and payloads
- Signature verification
- Webhook best practices

**`11_api_constants.md`**
- API constants and enums
- Status codes, payment methods, etc.

**`12_connected_banking.md`**
- Connected Banking APIs
- Account linking with 150+ banks
- Transaction history
- Balance inquiries

**`13_examples_node.md`**
- Node.js code examples
- Payment collection examples
- Transfer examples
- Webhook handling examples

**`14_examples_python.md`**
- Python code examples
- Payment collection examples
- Transfer examples
- Webhook handling examples

**`15_layer_js.md`**
- Layer.js integration guide
- Payment Gateway frontend integration
- JavaScript library usage
- Payment token creation and handling

#### States (`zwitch/states/`)

**`payment_status_lifecycle.md`**
- Complete state machine for payments
- States: `pending`, `processing`, `completed`, `failed`, `expired`, `cancelled`
- Terminal states: `completed`, `failed`, `expired`, `cancelled`
- State transitions and reversibility
- Critical rules: Only mark as paid when status is `completed`
- Database representation
- Webhook events for each state
- Common mistakes and correct patterns
- State checking best practices

**`transfer_status_lifecycle.md`**
- Complete state machine for transfers/payouts
- States and transitions similar to payment lifecycle
- Terminal states and critical rules

**`verification_states.md`**
- Verification state machine
- States for different verification types

#### Flows (`zwitch/flows/`)

**`payin_happy_path.md`**
- Successful end-to-end payment flow
- Steps: Customer initiates → Create payment request → Customer completes payment → Zwitch processes → Webhook received → Verify status → Customer sees success
- Database schema recommendations
- Critical checkpoints: Store payment_id, verify webhook signature, check idempotency, update database atomically
- Timeline example
- Success criteria
- Next steps after successful payin

**`payin_failure_path.md`**
- Payment failure handling flow
- What happens when payment fails
- Error handling and retry strategies

**`refund_flow.md`**
- Refund process flow
- How to process refunds
- Refund status tracking

**`settlement_flow.md`**
- Settlement process flow
- How settlements work
- Settlement timing and confirmation

#### Best Practices (`zwitch/best_practices/`)

**`recommended_db_schema.md`**
- Database schema recommendations
- Tables for orders, payments, webhooks
- Indexes and constraints
- Best practices for data modeling

**`production_checklist.md`**
- Pre-launch checklist
- Security requirements
- Performance considerations
- Monitoring setup

**`logging_and_audits.md`**
- Logging requirements
- Audit trail best practices
- What to log and how

#### Decisions (`zwitch/decisions/`)

**`polling_vs_webhooks.md`**
- Recommendation: Use webhooks as primary, polling as fallback
- Why webhooks are preferred: Real-time, efficient, lower latency, reduced API load
- When to use polling: Reconciliation, webhook delivery failures, initial status check, development/testing
- Hybrid approach: Webhooks + reconciliation polling
- Polling frequency guidelines
- Webhook implementation requirements
- Common mistakes and correct patterns
- Performance comparison

**`frontend_vs_backend_calls.md`**
- Backend authority for financial operations
- What frontend can/cannot do
- Security considerations

**`retries_and_idempotency.md`**
- Retry strategies
- Idempotency requirements
- How to implement idempotency
- Testing idempotency

#### Risks (`zwitch/risks/`)

**`double_credit_risk.md`**
- Risk of crediting customer account twice for same transaction
- Common causes: Duplicate webhook processing, webhook + polling both process, race conditions, manual intervention errors, reconciliation errors
- Prevention strategies: Idempotency checks, atomic operations, single source of truth, idempotency keys, database constraints
- Detection and monitoring
- Recovery procedures
- Best practices and testing

**`webhook_signature_verification.md`**
- Security requirement: Always verify webhook signatures
- How to verify signatures
- Consequences of not verifying

**`reconciliation_failures.md`**
- Reconciliation failure scenarios
- How to handle discrepancies
- Prevention strategies

**`compliance_boundaries.md`**
- Legal and compliance responsibilities
- What Zwitch handles vs what you must handle
- Compliance requirements

#### Principles (`zwitch/principles/`)

**`source_of_truth.md`**
- Webhooks are primary source of truth
- How to handle webhook delivery failures
- Reconciliation as backup

**`backend_authority.md`**
- Backend owns critical decisions
- Frontend is informational only
- Security and authority model

**`idempotency.md`**
- Idempotency is mandatory for financial operations
- Why idempotency is required: Financial risk, webhook retries, API retries, reconciliation
- Where idempotency applies: Payment processing, transfer processing, webhook processing, API calls
- Risks of not using idempotency: Double credit, double debit, duplicate fulfillment
- Implementation requirements: Database schema, atomic operations, idempotency keys
- Testing idempotency
- Override authority: Cannot be overridden

#### Concepts (`zwitch/concepts/`)

**`payin_vs_payout.md`**
- Simple explanation: Payin = money coming IN, Payout = money going OUT
- Payin examples: Customer buys product, user subscribes, marketplace commission
- Payout examples: Paying salaries, sending refunds, paying vendors
- Visual flow diagrams
- Key differences table
- Common use cases
- Important notes and considerations
- What NOT to confuse

**`payment_token_vs_order.md`**
- Conceptual distinction between payment tokens and orders
- When to use each
- Relationship between them

**`merchant_vs_platform.md`**
- Business model distinction
- Merchant vs platform roles
- Responsibilities and boundaries

**`zwitch_vs_open_money.md`**
- Platform comparison
- Key differences and similarities
- When to use each platform

---

## Key Themes Across Both KBs

### 1. Authority and Source of Truth
- **Open Money**: Bank statements > Payment rails > GST/IRP > Open Money Dashboard
- **Zwitch**: Webhooks > API verification > Polling (fallback)

### 2. Reconciliation
- **Open Money**: Reconciliation is mandatory, not optional
- **Zwitch**: Reconciliation as backup to webhooks

### 3. Backend Authority
- Both emphasize backend makes financial decisions
- Frontend is informational only

### 4. Idempotency
- Both require idempotency for financial operations
- Critical for preventing double processing

### 5. State Machines
- Both define complete state machines for financial entities
- Terminal states are clearly defined
- Only certain states confirm financial finality

### 6. Data Limitations
- Both emphasize derived vs actual data
- Both warn about stale data and sync delays
- Both require verification against source systems

### 7. Risk Management
- Both document financial risks extensively
- Both provide prevention strategies
- Both emphasize safety over convenience

---

## Summary Statistics

### Open Money KB
- **Total Files**: ~40 files
- **Categories**: 8 (concepts, principles, states, workflows, data_semantics, risks, decisions, modules)
- **Core Principles**: 3 (backend authority, reconciliation mandatory, financial finality)
- **State Machines**: 5 (invoice, bill, payment link, payout, bank account)
- **Workflows**: 6 (invoice to collection, bill to payout, reconciliation, payment link, bulk collection, GST compliance)

### Zwitch KB
- **Total Files**: ~46 files
- **Categories**: 8 (api, states, flows, best_practices, decisions, risks, principles, concepts)
- **API Documentation**: 16 files (00-15)
- **State Machines**: 3 (payment, transfer, verification)
- **Flows**: 4 (payin happy path, payin failure, refund, settlement)
- **Core Principles**: 3 (source of truth, backend authority, idempotency)

---

## Usage Guidelines

### For Open Money Questions
1. **State questions**: Consult `states/` first
2. **Process questions**: Consult `workflows/` first
3. **Data meaning**: Consult `data_semantics/` for facts, verify against `states/` and `workflows/`
4. **Implementation**: Consult `decisions/`
5. **Safety**: Consult `risks/` first
6. **Explanation**: Consult `concepts/` for understanding, verify with authoritative layers

### For Zwitch Questions
1. **State questions**: Consult `states/` first
2. **Process questions**: Consult `flows/` first
3. **API questions**: Consult `api/` for facts, verify against `states/` and `flows/`
4. **Implementation**: Consult `best_practices/` and `decisions/`
5. **Safety**: Consult `risks/` first
6. **Explanation**: Consult `concepts/` for understanding, verify with authoritative layers

---

## Conclusion

This Knowledge Base provides comprehensive documentation for both Open Money and Zwitch platforms, covering:
- Company overviews and positioning
- Complete API documentation (Zwitch)
- State machines and lifecycles
- End-to-end workflows
- Principles and best practices
- Risk management
- Implementation guidance
- Conceptual explanations

The KB is structured with clear authority hierarchies to ensure accurate information retrieval and decision-making. All documentation emphasizes safety, accuracy, and proper financial practices.





