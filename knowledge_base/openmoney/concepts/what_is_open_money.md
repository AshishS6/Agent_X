# What Is Open Money

Open Money is a **business finance operating system** designed to help companies:

- Collect money
- Pay money
- Track money
- Reconcile money
- Stay compliant

It is **not** a bank and **not** a payment gateway.

## Core Role

Open Money sits **between**:
- Banks
- Payment gateways
- Accounting systems
- Compliance systems
- Business users

Its role is to **orchestrate**, not to finalize.

## What Open Money Does

Open Money provides a **platform/dashboard/app** that enables businesses to:

- **Access financial management features** through web dashboard and mobile app
- Create financial documents (invoices, bills, payment links) through the platform
- Initiate collections and payouts through the dashboard
- Connect and manage bank accounts (Connected Banking) through the platform
- Aggregate balances across banks and view them in the dashboard
- Track outstanding receivables and payables through the app
- Reconcile documents with cash movement using platform tools
- Access GST compliance features through the dashboard
- Manage expenses and corporate cards through the platform
- Process payroll through Open Payroll dashboard

**Open Money is a user-facing platform, not an API provider.** APIs for payment processing and banking services are provided by Zwitch.

## Transaction Status and Settlement

**Open Money is a Payment Aggregator (PA) licensed by RBI** and is **liable for settlements**. 

### Transaction Status Handling

Open Money provides accurate transaction statuses based on real-time updates:

- **Success Status**: When Open Money shows a transaction as "success", it means the transaction has been successfully processed and settled. You can trust this status.
- **Failed Status**: When Open Money shows a transaction as "failed", it means the transaction has failed. This status is accurate and reliable.
- **Pending Status**: When a transaction shows as "pending", it means the transaction is still being processed. In this case, it's best to cross-check with your bank for the latest status, as Open Money's status is updated based on callbacks from the respective bank.

### Settlement Responsibility

- **Open Money is responsible for settlements** as a licensed Payment Aggregator (PA) under RBI regulations.
- Settlements are processed by Open Money, not by banks directly.
- In cases where a transaction goes to a pending status, Open Money depends on the bank to provide callbacks or status updates to update the transaction status accordingly.

### What Open Money Does Not Do

- It does not override bank data (bank statements remain the authoritative source)
- It does not replace accounting systems (it integrates with them)
- It does not own financial truth (it aggregates and presents data from authoritative sources)

## Mental Model

Think of Open Money as:

> "A control tower for business finance — orchestrating and managing financial operations across multiple systems."

Open Money aggregates data from authoritative sources (banks, payment rails, compliance systems) and presents it in a unified platform, while maintaining clear attribution to source systems.

## Authority Hierarchy

When interpreting data in Open Money, understand the authority hierarchy:

1. **Bank statements** — Absolute truth for balances and transactions
2. **Payment rails** (e.g., Zwitch, UPI, NEFT) — Transactional truth
3. **GST / IRP** — Compliance truth
4. **Open Money Dashboard** — Derived / Informational

Open Money aggregates and presents data from these sources, but it does not own the truth.

## Key Distinction

**Open Money is a financial orchestration platform, not a source of financial truth.**

This distinction is critical for:
- Understanding data limitations
- Making correct financial decisions
- Preventing misinterpretation
- Ensuring proper reconciliation

## Related Documentation

- [Data Ownership and Limitations](./data_ownership_and_limitations.md) — What Open Money does and does not own
- [Open Money vs Bank](./open_money_vs_bank.md) — Platform comparison
- [Open Money vs Accounting Software](./open_money_vs_accounting_software.md) — Software comparison

