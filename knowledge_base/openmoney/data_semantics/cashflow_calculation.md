# Cashflow Calculation

## Overview

Cashflow calculation in Open Money aggregates cash movement from multiple sources to show cashflow trends. Understanding how cashflow is calculated is critical for interpreting cashflow data correctly.

## How Cashflow Is Calculated

Cashflow is calculated from:
- Bank transactions (from bank sync)
- Payment records (from payment rails)
- Document records (from Open Money)
- Derived calculations (computed by Open Money)

**Cashflow is a derived metric, not actual cash movement.**

## Cash Inflow (Collections)

Cash inflow includes:
- Payments received (from payment rails)
- Bank credits (from bank sync)
- Document payments (from invoices/payment links)

**Cash inflow is calculated from available data, not all cash received.**

## Cash Outflow (Payouts)

Cash outflow includes:
- Payouts made (from payment rails)
- Bank debits (from bank sync)
- Document payouts (from bills)

**Cash outflow is calculated from available data, not all cash paid.**

## Net Cashflow

Net cashflow is:
- Cash inflow minus cash outflow
- Calculated over a time period
- Shown as positive or negative

**Net cashflow is a derived calculation, not actual cash balance change.**

## Limitations of Cashflow Calculation

### Based on Synced Data

**Limitation:** Cashflow is calculated from synced data, not all data.

**Impact:** Cashflow may miss unsynced transactions.

**Mitigation:** Reconcile regularly. Verify data completeness.

### May Miss Recent Transactions

**Limitation:** Cashflow may not include recent transactions.

**Impact:** Cashflow may be incomplete or delayed.

**Mitigation:** Check sync status. Verify against bank statements.

### May Have Timing Differences

**Limitation:** Cashflow uses transaction timestamps, not actual cash movement timing.

**Impact:** Cashflow may not reflect actual cash movement timing.

**Mitigation:** Reconcile with bank statements. Verify timing accuracy.

### May Not Account for Pending Transactions

**Limitation:** Cashflow may not accurately reflect pending transactions.

**Impact:** Cashflow may not match actual cash movement.

**Mitigation:** Check pending transactions. Verify against bank statements.

## When to Use Cashflow

Cashflow is useful for:
- High-level visibility
- Trend analysis
- Cash planning
- Forecasting
- Quick reference

**Cashflow is NOT suitable for:**
- Critical financial decisions
- Audits
- Legal confirmation
- Final settlement decisions
- Regulatory reporting

## When to Verify Cashflow

Cashflow must be verified for:
- Critical financial decisions
- Audits
- Legal confirmation
- Final settlement decisions
- Regulatory reporting

**Cashflow must be verified against bank statements and reconciled.**

## Common Misinterpretations

### Misinterpretation 1: Cashflow = Actual Cash

**Wrong:** "Cashflow shows ₹X, so I have ₹X cash."

**Correct:** "Cashflow shows ₹X calculated from transactions. Verify against bank statements to confirm actual cash."

### Misinterpretation 2: Positive Cashflow = Profit

**Wrong:** "Positive cashflow means I'm profitable."

**Correct:** "Positive cashflow means more money in than out. Profitability requires accounting analysis."

### Misinterpretation 3: Cashflow Accuracy = Data Accuracy

**Wrong:** "Cashflow looks correct, so all data is accurate."

**Correct:** "Cashflow is based on available data. Verify data completeness and accuracy through reconciliation."

## Reconciliation Requirement

Cashflow must be reconciled with:
- Bank statements
- Payment records
- Document records
- Accounting records (if applicable)

**Without reconciliation, cashflow is provisional and may be inaccurate.**

## How to Verify Cashflow

To verify cashflow accuracy:

1. **Check data sources** — What data is used for calculation?
2. **Check sync status** — Is all data synced?
3. **Reconcile transactions** — Do all transactions match?
4. **Verify timing** — Do timestamps reflect actual cash movement?
5. **Compare with bank statements** — Does cashflow match bank statements?

**Only after verification can you trust cashflow for non-critical decisions.**

## Related Documentation

- [Cashflow Analytics Module](../modules/cashflow_analytics.md) — Cashflow module
- [Derived vs Actual Balances](./derived_vs_actual_balances.md) — Balance interpretation
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Reconciliation Logic](./reconciliation_logic.md) — Reconciliation meaning
- [Dashboard Misinterpretation](../risks/dashboard_misinterpretation.md) — Dashboard risks

