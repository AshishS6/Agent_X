# Bank Account States: Connection and Sync Status

## Overview

This document defines the **states for bank account connections** in Open Money. Understanding these states is critical for understanding bank data availability and limitations.

## Bank Account States

### 1. `disconnected`

**Meaning:** Bank account is not connected to Open Money.

**When it occurs:**
- Bank account has never been connected
- Bank account connection was removed
- Bank account connection failed

**What it means:**
- No bank data is available
- No transactions are synced
- No balance is shown
- Account must be connected to use

**Can transition to:**
- `connecting` (connection initiated)
- `connected` (connection successful)

**Is reversible:** Yes (can be connected)

**What to do:**
- Connect bank account
- Complete connection process
- Verify connection

---

### 2. `connecting`

**Meaning:** Bank account connection is in progress.

**When it occurs:**
- Connection process initiated
- User is authenticating with bank
- Connection is being established

**What it means:**
- Connection is in progress
- Bank data is not yet available
- Connection may succeed or fail
- Usually a short-lived state

**Can transition to:**
- `connected` (connection successful)
- `disconnected` (connection failed)

**Is reversible:** Yes (can become connected or disconnected)

**What to do:**
- Wait for connection to complete
- Monitor connection status
- Retry if connection fails

---

### 3. `connected`

**Meaning:** Bank account is connected and syncing.

**When it occurs:**
- Connection successful
- Bank account is linked
- Data sync is active

**What it means:**
- Bank account is connected
- Data sync is enabled
- Transactions are being synced
- Balance is being updated

**Can transition to:**
- `sync_failed` (sync failed)
- `disconnected` (connection removed)
- `inactive` (account inactive)

**Is reversible:** Yes (can become sync_failed, disconnected, or inactive)

**What to do:**
- Monitor sync status
- Verify data accuracy
- Reconcile regularly

---

### 4. `sync_failed`

**Meaning:** Bank account sync has failed.

**When it occurs:**
- Sync process failed
- Bank API error
- Authentication expired
- Network error

**What it means:**
- Connection exists but sync failed
- Data may be stale
- Balance may be outdated
- Transactions may be missing

**Can transition to:**
- `connected` (sync retried and successful)
- `disconnected` (connection removed)

**Is reversible:** Yes (can become connected after retry)

**What to do:**
- Investigate sync failure
- Retry sync
- Verify bank credentials
- Check bank API status

---

### 5. `inactive`

**Meaning:** Bank account is connected but inactive.

**When it occurs:**
- Account is manually deactivated
- Account is not being used
- Account sync is paused

**What it means:**
- Connection exists but sync is paused
- Data may be stale
- Balance may be outdated
- Transactions are not being synced

**Can transition to:**
- `connected` (account activated)
- `disconnected` (connection removed)

**Is reversible:** Yes (can become connected)

**What to do:**
- Activate account if needed
- Monitor account status
- Update if required

---

## State Transition Diagram

```
                    ┌──────────────┐
                    │ disconnected │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  connecting  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ connected │ │sync_    │ │ inactive │
        │           │ │ failed   │ │          │
        └─────┬─────┘ └────┬─────┘ └────┬────┘
              │            │            │
              │            │            │
              └────────────┴────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ disconnected │
                    └──────────────┘
```

## Terminal States

**Terminal states:** None (all states can change)

**All states are reversible:**
- `disconnected` can become `connected`
- `connected` can become `disconnected`, `sync_failed`, or `inactive`
- `sync_failed` can become `connected` or `disconnected`
- `inactive` can become `connected` or `disconnected`

## Critical Rules

### ✅ Safe to Use Bank Data When:
- Status is `connected`
- Last sync was recent
- Sync status is successful
- Data is reconciled

### ❌ Do NOT Trust Bank Data When:
- Status is `disconnected` (no data available)
- Status is `connecting` (data not yet available)
- Status is `sync_failed` (data may be stale)
- Status is `inactive` (data may be stale)

### Data Freshness:
- Always check last sync timestamp
- Verify sync status before using data
- Reconcile with bank statements
- Don't assume data is current

## Common Misinterpretations

### Misinterpretation 1: Connected = Current Data

**Wrong:** "Bank account shows connected, so data is current."

**Correct:** "Bank account shows connected, but check last sync timestamp. Data may be delayed."

### Misinterpretation 2: Sync Failed = No Data

**Wrong:** "Bank account shows sync_failed, so no data is available."

**Correct:** "Bank account shows sync_failed, meaning recent sync failed. Stale data may be available, but it's not current."

### Misinterpretation 3: Inactive = Disconnected

**Wrong:** "Bank account shows inactive, so it's disconnected."

**Correct:** "Bank account shows inactive, meaning connection exists but sync is paused. Connection can be reactivated."

## Sync Limitations

Bank account sync has limitations:

- **Not real-time** — Sync occurs periodically, not continuously
- **May be delayed** — Sync may lag behind actual bank transactions
- **May fail** — Sync can fail due to various reasons
- **May be incomplete** — Sync may miss some transactions

**These limitations mean bank data in Open Money is informational, not authoritative.**

## Reconciliation Requirement

Even when bank account is `connected`:
- Verify data against bank statements
- Reconcile transactions regularly
- Check for missing transactions
- Verify balance accuracy

**Connection status does not guarantee data accuracy. Reconciliation is still mandatory.**

## Related Documentation

- [Derived vs Actual Balances](../data_semantics/derived_vs_actual_balances.md) — Balance interpretation
- [Stale Bank Data](../risks/stale_bank_data.md) — Bank sync risks
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Open Money vs Bank](../concepts/open_money_vs_bank.md) — Platform comparison

