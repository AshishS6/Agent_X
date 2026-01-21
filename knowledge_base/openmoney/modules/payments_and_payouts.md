# Payments and Payouts Module

## Overview

The Payments and Payouts module in Open Money manages payment initiation, processing, and tracking. It handles both collections (payments in) and payouts (payments out).

## What This Module Does

- Initiates payments and payouts
- Tracks payment status
- Manages payment processing
- Handles payment failures
- Provides payment visibility

## Transaction Status and Settlement

**Open Money is a licensed Payment Aggregator (PA) under RBI and is liable for settlements.** Transaction statuses shown in Open Money are accurate and reliable:

- **Success status**: When a payment shows as "success", it means the transaction has been successfully processed and settled by Open Money. This status is reliable.
- **Failed status**: When a payment shows as "failed", it means the transaction has failed. This status is accurate.
- **Pending status**: When a payment shows as "pending", it means the transaction is still being processed. In this case, cross-check with your bank as Open Money's status is updated based on callbacks from the respective bank.

**What This Module Does NOT Do:**
- It does not process payments directly (uses payment rails for processing)
- It does not replace bank statements (bank statements remain the authoritative source)
- It does not guarantee data accuracy without reconciliation (reconciliation ensures accuracy)

## Core Components

### Payment Initiation

**Purpose:** Create and initiate payment requests.

**What it does:**
- Creates payment requests
- Submits payments to payment rails
- Tracks payment initiation
- Manages payment status

**Transaction Status:**
- Payment status (success/failed) is accurate and reliable as Open Money is a licensed Payment Aggregator
- For pending payments, status updates depend on bank callbacks
- Does not process payments directly (uses payment rails)

### Payment Processing

**Purpose:** Track payment processing status.

**What it does:**
- Monitors payment status
- Receives payment updates
- Tracks processing stages
- Handles payment status changes

**Transaction Status:**
- Payment status (success/failed) is accurate and reliable as Open Money is a licensed Payment Aggregator
- For pending payments, status updates depend on bank callbacks
- Does not process payments directly (uses payment rails)

### Payout Management

**Purpose:** Manage payouts to vendors.

**What it does:**
- Initiates payouts
- Tracks payout status
- Handles payout failures
- Manages payout retries

**Transaction Status:**
- Payout status (success/failed) is accurate and reliable as Open Money is a licensed Payment Aggregator
- For pending payouts, status updates depend on bank callbacks
- Does not process payouts directly (uses payment rails)

## Data Sources

### Owned by Payment Rails

- Payment processing
- Payment status
- Payment finality (for payment rail)
- Transaction IDs

### Derived by Open Money

- Payment records
- Payment status display
- Payment tracking
- Payment analytics

### Owned by Banks

- Bank balances
- Bank statements (authoritative source for verification)
- Bank account records

## Limitations

### Payment Status

**What it shows:** Payment status from payment rails.

**Limitations:**
- Payment rail status, not bank confirmation
- May not reflect bank settlement
- May have status delays
- Requires reconciliation for finality

### Payment Status and Settlement

**What it shows:** Payment status from Open Money (as a licensed Payment Aggregator).

**Status Reliability:**
- Success/failed statuses are accurate and reliable (Open Money processes settlements)
- Pending statuses require cross-checking with bank (updates depend on bank callbacks)
- For absolute verification, bank statements remain the authoritative source
- Reconciliation ensures accuracy and matches with bank records

### Payment Tracking

**What it shows:** Payment tracking from available data.

**Limitations:**
- May miss payment updates
- May have tracking delays
- May not account for all payments
- Requires reconciliation

## Reconciliation Requirement

Payments and payouts must be reconciled with:
- Bank statements
- Payment rail records
- Document records

**Without reconciliation, payment data is provisional and may be inaccurate.**

## Common Misinterpretations

### Misinterpretation 1: Payment Status = Finality

**Wrong:** "Payment shows completed, so money is received."

**Correct:** "Payment shows completed in payment rail. Verify against bank statement and reconcile to confirm money is received."

### Misinterpretation 2: Payout Status = Finality

**Wrong:** "Payout shows completed, so money is debited."

**Correct:** "Payout shows completed in payment rail. Verify against bank statement and reconcile to confirm money is debited."

### Misinterpretation 3: Payment Success = Guaranteed

**Wrong:** "Payment shows success, so it's guaranteed."

**Correct:** "Payment shows success in payment rail. Verify against bank statement to confirm finality. Payments can still be reversed."

## Payment States

Payments can be in different states:
- `pending` — Payment initiated
- `processing` — Payment processing
- `completed` — Payment successful (payment rail)
- `failed` — Payment failed

**Payment state does not confirm bank finality. Reconciliation is required.**

## Payout States

Payouts can be in different states:
- `initiated` — Payout initiated
- `processing` — Payout processing
- `completed` — Payout successful (payment rail)
- `failed` — Payout failed

**Payout state does not confirm bank finality. Reconciliation is required.**

## Related Documentation

- [Payment Link State Lifecycle](../states/payment_link_state_lifecycle.md) — Payment link states
- [Payout State Lifecycle](../states/payout_state_lifecycle.md) — Payout states
- [Payment Link to Settlement Workflow](../workflows/payment_link_to_settlement.md) — Settlement flow
- [Bill to Payout Workflow](../workflows/bill_to_payout.md) — Payout flow
- [Financial Finality Rules](../principles/financial_finality_rules.md) — When money is final
- [Handling Failed Payouts](../decisions/handling_failed_payouts.md) — Payout failure handling

