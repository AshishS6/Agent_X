# Dashboard Misinterpretation: Why Dashboards Lie

## Overview

**Dashboard data in Open Money is derived and informational. It is not authoritative and can mislead users into making incorrect financial decisions.**

This is a critical risk that can cause significant financial errors.

## Why Dashboards Can Mislead

### 1. Derived Data

**Risk:** Dashboard shows derived data, not actual data.

**Why it's misleading:**
- Data is calculated, not direct
- Calculations may be incorrect
- Data may be incomplete
- Data may be delayed

**Impact:**
- Users trust dashboard data
- Users make decisions based on derived data
- Decisions may be incorrect
- Financial errors occur

**Mitigation:**
- Always verify against source systems
- Understand data derivation
- Reconcile regularly
- Don't trust dashboard alone

### 2. Stale Data

**Risk:** Dashboard shows stale data, not current data.

**Why it's misleading:**
- Data sync is not real-time
- Data may be hours or days old
- Recent transactions may be missing
- Data freshness is not guaranteed

**Impact:**
- Users see outdated information
- Users make decisions based on stale data
- Decisions may be incorrect
- Financial errors occur

**Mitigation:**
- Check last sync timestamp
- Verify data freshness
- Reconcile regularly
- Don't assume data is current

### 3. Incomplete Data

**Risk:** Dashboard shows incomplete data, not all data.

**Why it's misleading:**
- Some transactions may be missing
- Sync may have failed
- Data may be filtered
- Not all data is displayed

**Impact:**
- Users see partial information
- Users make decisions based on incomplete data
- Decisions may be incorrect
- Financial errors occur

**Mitigation:**
- Verify data completeness
- Check for missing transactions
- Reconcile regularly
- Don't assume all data is shown

### 4. Status Misinterpretation

**Risk:** Misunderstanding transaction status meaning and finality verification.

**Important Context:**
- Open Money is a Payment Aggregator (PA) licensed by RBI and is liable for settlements
- Transaction statuses (success/failed) shown in Open Money are accurate and reliable
- Success status means Open Money has processed and settled the transaction
- Failed status means the transaction has failed
- Pending status means transaction is still being processed (cross-check with bank)

**Why verification is still recommended:**
- For absolute finality verification, bank statements remain the authoritative source
- Pending statuses require cross-checking as updates depend on bank callbacks
- Reconciliation ensures accuracy and matches with bank records

**Impact:**
- Users may misunderstand pending status meaning
- Users may not verify against bank statements for absolute finality
- Decisions may be made without full verification

**Mitigation:**
- Understand that success/failed statuses are reliable (Open Money processes settlements)
- For pending statuses, cross-check with bank
- For absolute finality verification, verify against bank statements
- Reconcile regularly to ensure accuracy

## Common Misinterpretations

### Misinterpretation 1: Balance Accuracy

**Wrong:** "Dashboard shows ₹X, so I have ₹X."

**Risk:** Balance is derived and may be incorrect.

**Correct:** "Dashboard shows ₹X derived from bank sync. Verify against bank statement to confirm actual balance."

### Misinterpretation 2: Payment Finality

**Wrong:** "Payment shows success, so money is received."

**Risk:** Payment status is from payment rail, not bank confirmation.

**Correct:** "Payment shows success in payment rail. Verify against bank statement and reconcile to confirm money is received."

### Misinterpretation 3: Overdue Accuracy

**Wrong:** "Invoice shows overdue, so customer hasn't paid."

**Risk:** Overdue is based on due date, not payment status.

**Correct:** "Invoice shows overdue based on due date. Verify payment status and reconciliation to confirm if payment was received."

### Misinterpretation 4: Cashflow Accuracy

**Wrong:** "Cashflow shows positive, so I'm profitable."

**Risk:** Cashflow is calculated from available data, not all data.

**Correct:** "Cashflow shows positive calculated from transactions. Verify data completeness and accuracy through reconciliation."

## What NOT to Trust

### ❌ Don't Trust Dashboard For:

1. **Actual Bank Balance**
   - Dashboard balance is derived
   - Verify against bank statement
   - Don't assume balance is accurate

2. **Payment Finality**
   - Dashboard status is from payment rail
   - Verify against bank statement
   - Don't assume status confirms finality

3. **Transaction Completeness**
   - Dashboard may miss transactions
   - Verify against bank statement
   - Don't assume all transactions are shown

4. **Data Freshness**
   - Dashboard data may be stale
   - Check last sync timestamp
   - Don't assume data is current

5. **Financial Decisions**
   - Dashboard is informational
   - Verify against source systems
   - Don't make critical decisions based on dashboard alone

## Mitigation Strategies

### 1. Always Verify

**Strategy:** Always verify dashboard data against source systems.

**How:**
- Check bank statements
- Verify payment records
- Reconcile regularly
- Confirm data accuracy

### 2. Understand Data Source

**Strategy:** Understand where dashboard data comes from.

**How:**
- Know data derivation
- Understand data limitations
- Check sync status
- Verify data freshness

### 3. Reconcile Regularly

**Strategy:** Reconcile dashboard data regularly.

**How:**
- Reconcile daily/weekly/monthly
- Match dashboard with source systems
- Verify all transactions
- Confirm data accuracy

### 4. Don't Trust Alone

**Strategy:** Never trust dashboard data alone.

**How:**
- Always verify against source systems
- Don't make critical decisions based on dashboard
- Reconcile before important decisions
- Confirm data accuracy

## Real-World Failure Scenarios

### Scenario 1: Balance Misinterpretation

**What happens:**
- Dashboard shows ₹100,000
- Actual bank balance: ₹50,000
- User makes decision based on ₹100,000
- Decision is incorrect

**Why it happened:**
- Dashboard balance is derived
- Sync is delayed
- Recent transactions not included
- User trusted dashboard

**How to prevent:**
- Verify against bank statement
- Check last sync timestamp
- Reconcile regularly
- Don't trust dashboard alone

### Scenario 2: Payment Status Misinterpretation

**What happens:**
- Dashboard shows payment success
- Bank statement shows no credit
- User assumes payment received
- Payment was not actually received

**Why it happened:**
- Dashboard status is from payment rail
- Bank settlement delayed
- User trusted dashboard status
- No reconciliation performed

**How to prevent:**
- Verify against bank statement
- Reconcile payments
- Don't trust status alone
- Confirm bank settlement

## Summary

- **Dashboards are derived** — Data is calculated, not direct
- **Dashboards can be stale** — Data may be hours or days old
- **Dashboards can be incomplete** — Some data may be missing
- **Dashboards are informational** — Not authoritative
- **Always verify** — Check against source systems
- **Reconcile regularly** — Match dashboard with source systems
- **Don't trust alone** — Never make critical decisions based on dashboard alone

**Bottom line:** Dashboard data is useful for visibility but must be verified against source systems. Never trust dashboard data alone for critical financial decisions.

## Related Documentation

- [Derived vs Actual Balances](../data_semantics/derived_vs_actual_balances.md) — Balance interpretation
- [Dashboard Misinterpretation](./dashboard_misinterpretation.md) — Dashboard risks
- [Stale Bank Data](./stale_bank_data.md) — Bank sync risks
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Backend Authority](../principles/backend_authority.md) — Backend ownership

