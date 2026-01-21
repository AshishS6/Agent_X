# Stale Bank Data: Bank Sync Delays and Failures

## Overview

**Bank data in Open Money is synced periodically, not in real-time. Sync may be delayed or fail, resulting in stale or incomplete data.**

This is a critical risk that can cause users to make decisions based on outdated information.

## Why Bank Data Can Be Stale

### 1. Sync Frequency Limitations

**Risk:** Bank sync is not continuous.

**Why it's a risk:**
- Sync occurs periodically (not real-time)
- Sync frequency is limited by bank APIs
- Sync may be delayed by hours or days
- Recent transactions may not be synced

**Impact:**
- Users see outdated balances
- Users see incomplete transactions
- Users make decisions based on stale data
- Financial errors occur

**Mitigation:**
- Check last sync timestamp
- Verify data freshness
- Reconcile regularly
- Don't assume data is current

### 2. Sync Failures

**Risk:** Bank sync may fail.

**Why it's a risk:**
- Network errors
- Bank API issues
- Authentication failures
- System errors

**Impact:**
- Data is not updated
- Users see stale data
- Users make decisions based on outdated information
- Financial errors occur

**Mitigation:**
- Monitor sync status
- Retry failed syncs
- Verify data completeness
- Reconcile regularly

### 3. Missing Transactions

**Risk:** Some transactions may not be synced.

**Why it's a risk:**
- Sync may miss recent transactions
- Sync may have gaps
- Transactions may be filtered
- Not all transactions are synced

**Impact:**
- Users see incomplete data
- Users make decisions based on incomplete information
- Financial errors occur

**Mitigation:**
- Verify transaction completeness
- Check for missing transactions
- Reconcile regularly
- Don't assume all transactions are synced

### 4. Timing Differences

**Risk:** Transaction timestamps may not reflect actual timing.

**Why it's a risk:**
- Sync timestamp vs actual transaction time
- Bank processing delays
- Time zone differences
- Timing discrepancies

**Impact:**
- Users see incorrect timing
- Users make decisions based on incorrect timing
- Financial errors occur

**Mitigation:**
- Verify transaction timing
- Check timestamps
- Reconcile regularly
- Don't assume timing is accurate

## Common Misinterpretations

### Misinterpretation 1: Synced = Current

**Wrong:** "Bank is synced, so data is current."

**Risk:** Sync may be hours or days old.

**Correct:** "Bank is synced, but check last sync timestamp. Data may be delayed."

### Misinterpretation 2: Connected = Accurate

**Wrong:** "Bank is connected, so data is accurate."

**Risk:** Connection does not guarantee data freshness.

**Correct:** "Bank is connected, but verify data freshness and completeness through reconciliation."

### Misinterpretation 3: All Transactions Synced

**Wrong:** "All transactions are shown, so sync is complete."

**Risk:** Some transactions may be missing.

**Correct:** "Transactions shown are from last sync. Verify against bank statements to confirm all transactions are synced."

## What NOT to Trust

### ❌ Don't Trust Bank Data For:

1. **Real-Time Balance**
   - Bank data is not real-time
   - Verify against bank statement
   - Don't assume balance is current

2. **Transaction Completeness**
   - Some transactions may be missing
   - Verify against bank statement
   - Don't assume all transactions are synced

3. **Data Freshness**
   - Data may be hours or days old
   - Check last sync timestamp
   - Don't assume data is current

4. **Critical Decisions**
   - Bank data is synced, not real-time
   - Verify against bank statement
   - Don't make critical decisions based on synced data alone

## Mitigation Strategies

### 1. Check Sync Status

**Strategy:** Always check bank sync status.

**How:**
- Check last sync timestamp
- Verify sync success
- Monitor sync failures
- Retry failed syncs

### 2. Verify Data Freshness

**Strategy:** Verify data is current enough for decisions.

**How:**
- Check last sync timestamp
- Compare with current time
- Determine if data is fresh enough
- Reconcile if data is stale

### 3. Reconcile Regularly

**Strategy:** Reconcile bank data regularly.

**How:**
- Reconcile daily/weekly/monthly
- Match synced data with bank statements
- Verify all transactions
- Confirm data accuracy

### 4. Don't Trust Alone

**Strategy:** Never trust synced data alone.

**How:**
- Always verify against bank statements
- Don't make critical decisions based on synced data
- Reconcile before important decisions
- Confirm data accuracy

## Real-World Failure Scenarios

### Scenario 1: Stale Balance

**What happens:**
- Last sync: 2 days ago
- Dashboard shows ₹100,000
- Actual balance: ₹50,000 (after recent payout)
- User makes decision based on ₹100,000
- Decision is incorrect

**Why it happened:**
- Sync is delayed
- Recent transactions not synced
- User trusted synced balance
- No verification performed

**How to prevent:**
- Check last sync timestamp
- Verify against bank statement
- Reconcile regularly
- Don't trust synced data alone

### Scenario 2: Missing Transactions

**What happens:**
- Sync completed successfully
- Recent payment not shown
- User assumes payment not received
- Payment was actually received

**Why it happened:**
- Sync missed recent transaction
- Transaction not yet in bank API
- User trusted synced data
- No reconciliation performed

**How to prevent:**
- Verify transaction completeness
- Check for missing transactions
- Reconcile regularly
- Don't assume all transactions are synced

## Bank Account States and Staleness

Bank accounts can be in different states:
- `connected` — Connected and syncing (data may still be stale)
- `sync_failed` — Sync failed (data is definitely stale)
- `inactive` — Connected but inactive (data is stale)

**Connection status does not guarantee data freshness. Always check last sync timestamp.**

## Summary

- **Bank data is synced** — Not real-time, periodic sync
- **Sync may be delayed** — Data may be hours or days old
- **Sync may fail** — Data may not be updated
- **Transactions may be missing** — Sync may be incomplete
- **Always check sync status** — Verify last sync timestamp
- **Reconcile regularly** — Match synced data with bank statements
- **Don't trust alone** — Never make critical decisions based on synced data alone

**Bottom line:** Bank data sync is useful but has limitations. Always verify data freshness and reconcile regularly. Never trust synced data alone for critical financial decisions.

## Related Documentation

- [Bank Account States](../states/bank_account_states.md) — Bank account states
- [Banking Module](../modules/banking.md) — Banking module
- [Derived vs Actual Balances](../data_semantics/derived_vs_actual_balances.md) — Balance interpretation
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Open Money vs Bank](../concepts/open_money_vs_bank.md) — Platform comparison

