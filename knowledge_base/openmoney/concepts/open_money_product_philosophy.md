# Open Money Product Philosophy

## Core Philosophy

Open Money is built on one simple idea: **know who owns the data and what its limits are**.

## Design Principles

### 1. Aggregation, Not Ownership

Open Money aggregates data from multiple sources but does not own the primary truth. This principle shapes every feature:

- Bank balances are aggregated, not owned
- Payment statuses are tracked from payment rails and should be reconciled against bank entries for financial finality
- Compliance data is tracked, not created
- Financial documents are managed, not finalized

### 2. Reconciliation as First-Class Concept

Reconciliation is not an afterthought—it is a core requirement. Every financial operation must be reconcilable:

- Documents must link to payments
- Payments must link to bank entries
- Bank entries must be verifiable
- Discrepancies must be detectable

### 3. Derived Data Transparency

Open Money makes it clear when data is derived vs actual:

- Derived balances are labeled as such
- Sample data is clearly marked
- Overdue calculations are explained
- Cashflow projections are distinguished from actuals

### 4. Backend Authority

All financial decisions must be made on the backend. The dashboard is informational:

- Frontend displays what backend tells it
- Backend processes webhooks and updates
- Backend verifies payment status
- Backend authorizes operations

### 5. Conservative by Default

Open Money errs on the side of caution:

- Does not assume money is received until bank credits are reconciled
- Does not assume bank sync accuracy
- Does not assume reconciliation completeness
- Does not assume data freshness

## Product Boundaries

### What Open Money Provides

- Document creation and management
- Payment initiation and tracking
- Bank aggregation and visibility
- Reconciliation tools and workflows
- Compliance assistance
- Analytics and reporting

### What Open Money Does NOT Provide

- Bank account ownership
- Tax authority data
- Accounting system replacement
- Financial truth verification

## User Mental Model

Users should understand Open Money as:

> "A connected banking platform for business payments that helps me send, receive, and reconcile payments across my bank accounts—but I must always verify critical decisions against source systems."

This mental model prevents:
- Over-reliance on dashboard data
- Misinterpretation of derived metrics
- Incorrect financial decisions
- Reconciliation gaps

## Implementation Philosophy

Every feature in Open Money is designed with these questions in mind:

1. **Where does this data come from?**
2. **When was it last synced?**
3. **Has it been reconciled?**
4. **What are the limitations?**

If these questions cannot be answered clearly, the feature may mislead users.

## Related Documentation

- [What Is Open Money](./what_is_open_money.md) — Core identity
- [Data Ownership and Limitations](./data_ownership_and_limitations.md) — Data boundaries
- [Backend Authority](../principles/backend_authority.md) — Backend ownership

