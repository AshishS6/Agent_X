# Derived vs Actual Balances

## Critical Distinction

**Balances shown in Open Money are derived, not actual. Actual balances exist only in bank statements.**

## What Is Actual Balance

Actual balance is:
- Balance shown in bank statement
- Balance from bank API
- Balance in passbook
- Balance confirmed by bank
- Authoritative balance

**Actual balance is owned by the bank, not Open Money.**

## What Is Derived Balance

Derived balance is:
- Balance calculated by Open Money
- Based on last bank sync
- Based on known transactions
- Based on pending transactions
- Computed balance

**Derived balance is calculated by Open Money, not owned by bank.**

## How Derived Balance Is Calculated

Derived balance is calculated from:
- Last known bank balance (from sync)
- Plus known credits (payments received)
- Minus known debits (payouts made)
- Plus/minus pending transactions
- Adjusted for categorization

**Derived balance is a computation, not a direct bank balance.**

## Limitations of Derived Balance

### Not Real-Time

**Limitation:** Derived balance is not updated in real-time.

**Impact:** Balance may be delayed by hours or days.

**Mitigation:** Check last sync timestamp. Verify against bank statement.

### May Be Incomplete

**Limitation:** Derived balance may not include all transactions.

**Impact:** Balance may be incorrect if transactions are missing.

**Mitigation:** Reconcile regularly. Verify against bank statement.

### May Have Errors

**Limitation:** Derived balance may have calculation errors.

**Impact:** Balance may be incorrect.

**Mitigation:** Reconcile regularly. Verify against bank statement.

### May Not Account for Pending Transactions

**Limitation:** Derived balance may not accurately reflect pending transactions.

**Impact:** Balance may not match actual available balance.

**Mitigation:** Check pending transactions. Verify against bank statement.

## When to Use Derived Balance

Derived balance is useful for:
- High-level visibility
- Cash planning
- Forecasting
- Trend analysis
- Quick reference

**Derived balance is NOT suitable for:**
- Critical financial decisions
- Audits
- Legal confirmation
- Final settlement decisions
- Regulatory reporting

## When to Use Actual Balance

Actual balance must be used for:
- Critical financial decisions
- Audits
- Legal confirmation
- Final settlement decisions
- Regulatory reporting
- Bank reconciliation

**Actual balance is the only authoritative balance.**

## Common Misinterpretations

### Misinterpretation 1: Derived Balance = Actual Balance

**Wrong:** "Open Money shows ₹X, so I have ₹X in my bank."

**Correct:** "Open Money shows ₹X derived from bank sync. Verify against bank statement to confirm actual balance."

### Misinterpretation 2: Balance Accuracy = Data Accuracy

**Wrong:** "Balance looks correct, so all data is accurate."

**Correct:** "Balance is derived from available data. Verify data completeness and accuracy through reconciliation."

### Misinterpretation 3: Sync Status = Balance Accuracy

**Wrong:** "Bank is synced, so balance is accurate."

**Correct:** "Bank is synced, but derived balance may still be delayed or incomplete. Verify against bank statement."

## Reconciliation Requirement

Derived balance must be reconciled with:
- Actual bank balance
- Bank statement entries
- All transactions

**Without reconciliation, derived balance is provisional and may be inaccurate.**

## How to Verify Balance

To verify balance accuracy:

1. **Check last sync timestamp** — When was balance last updated?
2. **Check bank statement** — What is actual bank balance?
3. **Reconcile transactions** — Do all transactions match?
4. **Verify pending transactions** — Are pending transactions accounted for?
5. **Compare amounts** — Does derived balance match actual balance?

**Only after verification can you trust derived balance for non-critical decisions.**

## Related Documentation

- [Banking Module](../modules/banking.md) — Banking module
- [Stale Bank Data](../risks/stale_bank_data.md) — Bank sync risks
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Reconciliation Logic](./reconciliation_logic.md) — Reconciliation meaning
- [Open Money vs Bank](../concepts/open_money_vs_bank.md) — Platform comparison

