# Banking Module

## Overview

The Banking module in Open Money aggregates and displays bank account data from multiple banks. It provides visibility into bank balances, transactions, and account status.

## What This Module Does

- Connects to multiple bank accounts
- Aggregates bank balances
- Syncs bank transactions
- Displays bank data
- Categorizes transactions
- Provides bank visibility

## What This Module Does NOT Do

- It does not own bank accounts
- It does not own bank balances
- It does not guarantee data freshness
- It does not replace bank statements
- It does not guarantee sync accuracy

## Core Components

### Bank Connections

**Purpose:** Link bank accounts to Open Money.

**What it does:**
- Connects to bank accounts
- Authenticates with banks
- Enables data sync
- Manages connection status

**What it does not do:**
- Own bank accounts
- Guarantee sync success
- Replace bank authentication

### Balance Aggregation

**Purpose:** Show combined balance across multiple banks.

**What it does:**
- Aggregates balances from connected banks
- Displays combined balance
- Shows balance per bank
- Updates when sync occurs

**What it does not do:**
- Guarantee balance accuracy
- Replace bank statements
- Confirm balance finality

### Transaction Sync

**Purpose:** Sync transactions from banks.

**What it does:**
- Syncs transactions from banks
- Displays transaction history
- Categorizes transactions
- Updates transaction data

**What it does not do:**
- Guarantee sync completeness
- Guarantee sync timing
- Replace bank statements

## Data Sources

### Owned by Banks

- Bank accounts
- Bank balances
- Bank transactions
- Bank statements

### Derived by Open Money

- Aggregated balances
- Transaction categorization
- Derived metrics
- Sync status

## Limitations

### Balance Accuracy

**What it shows:** Balance aggregated from bank sync.

**Limitations:**
- Not real-time
- May be delayed
- May be incomplete
- Requires verification against bank statements

### Transaction Completeness

**What it shows:** Transactions synced from banks.

**Limitations:**
- May miss recent transactions
- May have sync delays
- May have sync failures
- Requires verification against bank statements

### Sync Timing

**What it shows:** Last sync timestamp.

**Limitations:**
- Sync is not continuous
- Sync may be delayed
- Sync may fail
- Data may be stale

## Reconciliation Requirement

Banking data must be reconciled with:
- Bank statements from banks
- Payment records from payment rails
- Document records from Open Money

**Without reconciliation, banking data is provisional and may be inaccurate.**

## Common Misinterpretations

### Misinterpretation 1: Aggregated Balance = Actual Balance

**Wrong:** "Open Money shows ₹X, so I have ₹X in my banks."

**Correct:** "Open Money shows ₹X aggregated from bank sync. Verify against bank statements to confirm actual balances."

### Misinterpretation 2: Synced Transactions = All Transactions

**Wrong:** "All transactions are shown, so sync is complete."

**Correct:** "Transactions shown are from last sync. Verify against bank statements to confirm all transactions are synced."

### Misinterpretation 3: Connected = Current Data

**Wrong:** "Bank is connected, so data is current."

**Correct:** "Bank is connected, but check last sync timestamp. Data may be delayed or stale."

## Bank Account States

Bank accounts can be in different states:
- `disconnected` — Not connected
- `connecting` — Connection in progress
- `connected` — Connected and syncing
- `sync_failed` — Sync failed
- `inactive` — Connected but inactive

**Connection status does not guarantee data accuracy. Reconciliation is still required.**

## Related Documentation

- [Bank Account States](../states/bank_account_states.md) — Bank account states
- [Derived vs Actual Balances](../data_semantics/derived_vs_actual_balances.md) — Balance interpretation
- [Stale Bank Data](../risks/stale_bank_data.md) — Bank sync risks
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Open Money vs Bank](../concepts/open_money_vs_bank.md) — Platform comparison

