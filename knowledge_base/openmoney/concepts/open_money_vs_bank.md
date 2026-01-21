# Open Money vs Bank

## Critical Distinction

**Open Money is not a bank. It aggregates and orchestrates banking data, but it does not own bank accounts or bank balances.**

## What Banks Own

Banks own:
- Bank accounts
- Account balances
- Transaction history
- Bank statement records (authoritative source for verification)
- Regulatory compliance (for their operations)

## What Open Money Owns

Open Money owns:
- Financial documents (invoices, bills)
- Payment links
- Reconciliation records
- Derived analytics
- User workflows

## Bank Balance vs Open Money Balance

### Bank Balance (Authoritative)

- Exists in bank systems
- Updated in real-time by bank
- Cannot be disputed (it is the truth)
- Used for legal and regulatory purposes
- Final for all financial decisions

### Open Money Balance (Derived)

- Aggregated from bank APIs
- Updated when bank sync occurs
- May be delayed or incomplete
- Useful for visibility and planning
- Not final for critical decisions

## When to Trust Bank vs Open Money

### Trust Bank For:
- Actual account balance
- Bank statement records (authoritative source for verification)
- Regulatory reporting
- Legal documentation

### Trust Open Money For:
- Document management
- Payment initiation
- Workflow orchestration
- Reconciliation assistance
- High-level visibility

## Common Misinterpretation

**Wrong:** "My Open Money balance shows ₹X, so I have ₹X in my bank account."

**Correct:** "My Open Money balance shows ₹X, which is derived from my last bank sync. I should verify against my bank statement for the actual balance."

## Bank Sync Limitations

Open Money syncs with banks, but:

- Sync frequency is limited (not real-time)
- Sync may fail or be delayed
- Sync may miss recent transactions
- Sync may show pending transactions as settled

These limitations mean Open Money balance is **informational, not authoritative**.

## Payment Processing and Settlement

**Open Money is a Payment Aggregator (PA) licensed by RBI and is liable for settlements.**

When Open Money processes a payment:

- Open Money creates the payment request
- Open Money processes and settles the payment (as a licensed PA)
- Payment rails process the transaction
- Open Money receives status updates from banks/payment rails
- Open Money updates transaction status (success/failed/pending)

**Transaction Statuses:**
- **Success**: Transaction has been successfully processed and settled by Open Money. This status is reliable and accurate.
- **Failed**: Transaction has failed. This status is accurate and reliable.
- **Pending**: Transaction is still being processed. Cross-check with bank as status updates depend on bank callbacks.

Open Money **processes and settles** payments as a licensed Payment Aggregator. For absolute verification, bank statements remain the authoritative source.

## Reconciliation Requirement

Because Open Money balance is derived, reconciliation is mandatory:

- Compare Open Money transactions with bank statements
- Verify all payments are accounted for
- Identify discrepancies
- Update records as needed

Only after reconciliation can you trust that Open Money data aligns with bank truth.

## Related Documentation

- [Derived vs Actual Balances](../data_semantics/derived_vs_actual_balances.md) — Balance interpretation
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Stale Bank Data](../risks/stale_bank_data.md) — Bank sync risks

