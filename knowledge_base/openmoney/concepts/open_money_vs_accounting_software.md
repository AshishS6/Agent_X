# Open Money vs Accounting Software

## Core Distinction

**Open Money is a financial orchestration platform. Accounting software is a record-keeping and reporting system. They serve different purposes and should not be confused.**

## What Accounting Software Does

Accounting software:
- Maintains books of accounts
- Records journal entries
- Generates financial statements
- Tracks assets, liabilities, equity
- Handles depreciation, accruals, adjustments
- Produces tax-ready reports
- Maintains audit trails

## What Open Money Does

Open Money:
- Creates financial documents (invoices, bills)
- Initiates payments and collections
- Aggregates bank data
- Tracks cash movement
- Assists with reconciliation
- Provides cashflow visibility

## Key Differences

### Purpose

**Accounting Software:**
- Record-keeping and compliance
- Financial reporting
- Tax preparation
- Audit readiness

**Open Money:**
- Payment orchestration
- Cash management
- Operational finance
- Real-time visibility

### Data Model

**Accounting Software:**
- Double-entry bookkeeping
- Chart of accounts
- Accrual vs cash basis
- Period-based reporting

**Open Money:**
- Document-based
- Cash-based tracking
- Real-time aggregation
- Transaction-level detail

### Authority

**Accounting Software:**
- Owns accounting records
- Authoritative for financial statements
- Required for compliance
- Used for audits

**Open Money:**
- Does not own accounting truth
- Informational for operations
- Not a replacement for accounting
- Must sync with accounting software

## Integration Relationship

Open Money and accounting software should work together:

1. **Open Money** creates invoices and initiates payments
2. **Accounting Software** records these as journal entries
3. **Open Money** tracks cash movement
4. **Accounting Software** reconciles with bank statements
5. **Both** must align for accurate financial records

## Common Misconception

**Wrong:** "Open Money replaces my accounting software."

**Correct:** "Open Money helps me manage payments and cashflow. I still need accounting software for books of accounts and compliance."

## When to Use Each

### Use Accounting Software For:
- Maintaining books of accounts
- Generating financial statements
- Tax compliance and reporting
- Audit preparation
- Regulatory filings
- Financial analysis and reporting

### Use Open Money For:
- Creating and sending invoices
- Initiating payments and payouts
- Tracking cashflow in real-time
- Managing receivables and payables
- Bank aggregation and visibility
- Payment link management

## Data Flow

Typical integration flow:

```
Open Money (Invoice Creation)
    ↓
Accounting Software (Sales Entry)
    ↓
Open Money (Payment Initiation)
    ↓
Bank (Payment Processing)
    ↓
Open Money (Payment Status)
    ↓
Accounting Software (Receipt Entry)
    ↓
Reconciliation (Both Systems)
```

## Reconciliation Between Systems

Reconciliation between Open Money and accounting software is necessary because:

- Open Money tracks cash movement
- Accounting software tracks accruals
- Timing differences exist
- Both must align for accuracy

## Limitations

### Open Money Cannot:
- Replace accounting software
- Generate financial statements
- Handle complex accounting entries
- Manage depreciation or accruals
- Produce tax-ready reports

### Accounting Software Cannot:
- Initiate payments directly
- Aggregate multiple bank accounts
- Provide real-time cashflow visibility
- Create payment links
- Track payment status in real-time

## Best Practice

Use both systems for their strengths:

- **Open Money** for operational finance and cash management
- **Accounting Software** for record-keeping and compliance

Sync data between them regularly to maintain accuracy.

## Related Documentation

- [What Is Open Money](./what_is_open_money.md) — Core identity
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Reconciliation Logic](../data_semantics/reconciliation_logic.md) — Reconciliation meaning

