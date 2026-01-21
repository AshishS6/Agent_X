# Payables Module

## Overview

The Payables module in Open Money manages money that your business owes to vendors. It includes bills, payouts, debit notes, and related documents.

## What This Module Does

- Creates and manages bills
- Initiates and manages payouts
- Tracks outstanding payables
- Manages debit notes and adjustments
- Tracks payout status
- Calculates overdue amounts
- Provides payables visibility

## Transaction Status and Settlement

**Open Money is a licensed Payment Aggregator (PA) under RBI and is liable for settlements.** Transaction statuses shown in Open Money are accurate and reliable:

- **Success status**: When a payout shows as "success", it means the transaction has been successfully processed and settled by Open Money. This status is reliable.
- **Failed status**: When a payout shows as "failed", it means the transaction has failed. This status is accurate.
- **Pending status**: When a payout shows as "pending", it means the transaction is still being processed. In this case, cross-check with your bank as Open Money's status is updated based on callbacks from the respective bank.

**What This Module Does NOT Do:**
- It does not replace accounting systems (it integrates with them)
- It does not guarantee data accuracy without reconciliation (reconciliation ensures accuracy)
- It does not own bank balances (bank statements remain the authoritative source)

## Core Components

### Bills

**Purpose:** Formal requests for payment to vendors.

**What it does:**
- Creates bills with vendor, amount, due date
- Tracks bill status
- Calculates overdue days
- Manages bill lifecycle

**Transaction Status:**
- Payout status (success/failed) is accurate and reliable as Open Money is a licensed Payment Aggregator
- For pending payouts, status updates depend on bank callbacks
- Does not replace accounting records (integrates with accounting systems)

### Payouts

**Purpose:** Payments made to vendors.

**What it does:**
- Initiates payouts to vendors
- Tracks payout status
- Manages payout processing
- Handles payout failures

**Transaction Status:**
- Payout status (success/failed) is accurate and reliable as Open Money is a licensed Payment Aggregator
- For pending payouts, status updates depend on bank callbacks
- Does not process payouts directly (uses payment rails)

### Debit Notes

**Purpose:** Adjustments or corrections to bills.

**What it does:**
- Creates debit notes
- Links debit notes to bills
- Adjusts bill amounts
- Tracks debit note status

**What it does not do:**
- Process adjustments directly
- Confirm adjustment finality
- Replace accounting records

## Data Sources

### Owned by Open Money

- Bill records
- Payout records
- Debit note records
- Document status
- Overdue calculations

### Derived from Other Sources

- Payout status (from payment rails)
- Bank balances (from banks)
- Payout finality (from bank statements)

## Limitations

### Outstanding Amount

**What it shows:** Amount owed to vendors based on bills.

**Limitations:**
- Does not account for unrecorded payouts
- May not reflect partial payouts accurately
- Requires reconciliation for accuracy

### Overdue Calculation

**What it shows:** Days since bill due date.

**Limitations:**
- Based on due date, not payout status
- May show overdue even if payout made
- Requires reconciliation to verify

### Payout Status

**What it shows:** Payout status from payment rails.

**Limitations:**
- Payment rail status, not bank confirmation
- May not reflect bank settlement
- Requires reconciliation for finality

## Reconciliation Requirement

Payables data must be reconciled with:
- Payout records from payment rails
- Bank entries from bank statements
- Accounting records (if applicable)

**Without reconciliation, payables data is provisional and may be inaccurate.**

## Common Misinterpretations

### Misinterpretation 1: Outstanding = Unpaid

**Wrong:** "Outstanding amount shows ₹X, so we owe ₹X."

**Correct:** "Outstanding amount shows ₹X based on bills. Verify payout status and reconciliation to confirm actual amount owed."

### Misinterpretation 2: Overdue = Unpaid

**Wrong:** "Bill shows 30 days overdue, so we haven't paid."

**Correct:** "Bill shows 30 days overdue based on due date. Verify payout status and reconciliation to confirm if payout was made."

### Misinterpretation 3: Payout Status = Finality

**Wrong:** "Payout shows completed, so money is debited."

**Correct:** "Payout shows completed in payment rail. Verify against bank statement and reconcile to confirm money is debited."

## Related Documentation

- [Bill State Lifecycle](../states/bill_state_lifecycle.md) — Bill states
- [Payout State Lifecycle](../states/payout_state_lifecycle.md) — Payout states
- [Bill to Payout Workflow](../workflows/bill_to_payout.md) — Payout flow
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Overdue Calculation Logic](../data_semantics/overdue_calculation_logic.md) — Overdue computation
- [Handling Failed Payouts](../decisions/handling_failed_payouts.md) — Payout failure handling

