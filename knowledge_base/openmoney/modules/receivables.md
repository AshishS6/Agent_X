# Receivables Module

## Overview

The Receivables module in Open Money manages money that customers owe to your business. It includes invoices, payment links, credit notes, and related documents.

## What This Module Does

- Creates and manages invoices
- Creates and manages payment links
- Tracks outstanding receivables
- Manages credit notes and adjustments
- Tracks payment status
- Calculates overdue amounts
- Provides receivables visibility

## Transaction Status and Limitations

**Open Money is a licensed Payment Aggregator (PA) under RBI and is liable for settlements.** Transaction statuses shown in Open Money are accurate and reliable:

- **Success status**: When a payment shows as "success", it means the transaction has been successfully processed and settled. This status is reliable.
- **Failed status**: When a payment shows as "failed", it means the transaction has failed. This status is accurate.
- **Pending status**: When a payment shows as "pending", it means the transaction is still being processed. In this case, cross-check with your bank as Open Money's status is updated based on callbacks from the respective bank.

**What This Module Does NOT Do:**
- It does not replace accounting systems (it integrates with them)
- It does not guarantee data accuracy without reconciliation (reconciliation ensures accuracy)
- It does not own bank balances (bank statements remain the authoritative source)

## Core Components

### Invoices

**Purpose:** Formal requests for payment from customers.

**What it does:**
- Creates invoices with customer, amount, due date
- Sends invoices to customers
- Tracks invoice status
- Calculates overdue days

**Transaction Status:**
- Payment status (success/failed) is accurate and reliable as Open Money is a licensed Payment Aggregator
- For pending payments, status updates depend on bank callbacks
- Does not replace accounting records (integrates with accounting systems)

### Payment Links

**Purpose:** Shareable links for customers to make payments.

**What it does:**
- Creates payment links
- Shares links with customers
- Tracks payment status
- Manages link expiration

**Transaction Status:**
- Payment status (success/failed) is accurate and reliable as Open Money is a licensed Payment Aggregator
- For pending payments, status updates depend on bank callbacks
- Does not process payments directly (uses payment rails)

### Credit Notes

**Purpose:** Adjustments or refunds to invoices.

**What it does:**
- Creates credit notes
- Links credit notes to invoices
- Adjusts invoice amounts
- Tracks credit note status

**What it does not do:**
- Process refunds directly
- Confirm refund finality
- Replace accounting records

## Data Sources

### Owned by Open Money

- Invoice records
- Payment link records
- Credit note records
- Document status
- Overdue calculations

### Derived from Other Sources

- Payment status (from payment rails)
- Bank balances (from banks)
- Payment finality (from bank statements)

## Limitations

### Outstanding Amount

**What it shows:** Amount customers owe based on invoices.

**Limitations:**
- Does not account for unrecorded payments
- May not reflect partial payments accurately
- Requires reconciliation for accuracy

### Overdue Calculation

**What it shows:** Days since invoice due date.

**Limitations:**
- Based on due date, not payment status
- May show overdue even if payment received
- Requires reconciliation to verify

### Payment Status

**What it shows:** Payment status from payment rails.

**Limitations:**
- Payment rail status, not bank confirmation
- May not reflect bank settlement
- Requires reconciliation for finality

## Reconciliation Requirement

Receivables data must be reconciled with:
- Payment records from payment rails
- Bank entries from bank statements
- Accounting records (if applicable)

**Without reconciliation, receivables data is provisional and may be inaccurate.**

## Common Misinterpretations

### Misinterpretation 1: Outstanding = Unpaid

**Wrong:** "Outstanding amount shows ₹X, so customers owe ₹X."

**Correct:** "Outstanding amount shows ₹X based on invoices. Verify payment status and reconciliation to confirm actual amount owed."

### Misinterpretation 2: Overdue = Unpaid

**Wrong:** "Invoice shows 600 days overdue, so customer hasn't paid."

**Correct:** "Invoice shows 600 days overdue based on due date. Verify payment status and reconciliation to confirm if payment was received."

### Misinterpretation 3: Payment Status = Finality

**Wrong:** "Payment shows success, so money is received."

**Correct:** "Payment shows success in payment rail. Verify against bank statement and reconcile to confirm money is received."

## Related Documentation

- [Invoice State Lifecycle](../states/invoice_state_lifecycle.md) — Invoice states
- [Payment Link State Lifecycle](../states/payment_link_state_lifecycle.md) — Payment link states
- [Invoice to Collection Workflow](../workflows/invoice_to_collection.md) — Collection flow
- [Payment Link to Settlement Workflow](../workflows/payment_link_to_settlement.md) — Settlement flow
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Overdue Calculation Logic](../data_semantics/overdue_calculation_logic.md) — Overdue computation

