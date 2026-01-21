# Overdue Calculation Logic

## Overview

Overdue calculation in Open Money is based on document due dates, not payment status. Understanding this distinction is critical for interpreting overdue amounts correctly.

## How Overdue Is Calculated

Overdue is calculated as:
- Current date minus invoice/bill due date
- If current date > due date, document is overdue
- Overdue days = current date - due date

**Overdue calculation does NOT consider payment status.**

## What Overdue Means

Overdue means:
- Payment due date has passed
- Document is past due
- Payment is expected but not confirmed

**Overdue does NOT mean:**
- Payment was not received
- Payment will not be received
- Document is uncollectible

## Limitations of Overdue Calculation

### Does Not Consider Payment Status

**Limitation:** Overdue is calculated from due date, not payment status.

**Impact:** Document may show overdue even if payment was received.

**Example:**
- Invoice due date: January 1
- Payment received: January 5 (not reconciled)
- Current date: January 10
- Overdue days: 10 days (even though payment was received)

**Mitigation:** Reconcile payments to update overdue status.

### Does Not Consider Partial Payments

**Limitation:** Overdue is calculated for full amount, not remaining amount.

**Impact:** Document may show overdue even if partially paid.

**Example:**
- Invoice amount: ₹1000
- Partial payment: ₹500 (not reconciled)
- Remaining: ₹500
- Overdue: Calculated for ₹1000, not ₹500

**Mitigation:** Reconcile partial payments to update overdue status.

### Does Not Consider Payment Timing

**Limitation:** Overdue is calculated from due date, not payment date.

**Impact:** Document may show overdue even if payment was made on time.

**Example:**
- Invoice due date: January 1
- Payment made: January 1 (not reconciled)
- Current date: January 10
- Overdue days: 10 days (even though payment was on time)

**Mitigation:** Reconcile payments to update overdue status.

## Common Misinterpretations

### Misinterpretation 1: Overdue = Unpaid

**Wrong:** "Invoice shows 600 days overdue, so customer hasn't paid."

**Correct:** "Invoice shows 600 days overdue based on due date. Verify payment status and reconciliation to confirm if payment was received."

### Misinterpretation 2: Overdue Days = Days Since Payment

**Wrong:** "Overdue shows 30 days, so payment is 30 days late."

**Correct:** "Overdue shows 30 days based on due date. Verify payment date to confirm actual payment timing."

### Misinterpretation 3: Overdue = Uncollectible

**Wrong:** "Invoice shows overdue, so it will never be paid."

**Correct:** "Invoice shows overdue, meaning due date passed. Payment may still be received and reconciled."

## How Overdue Is Updated

Overdue is updated when:
- Document is reconciled with payment
- Payment status is confirmed
- Document status changes to paid

**Overdue is NOT updated automatically. Reconciliation is required.**

## Reconciliation Impact on Overdue

After reconciliation:
- Paid documents: Overdue is cleared
- Partially paid documents: Overdue is recalculated for remaining amount
- Unpaid documents: Overdue remains

**Reconciliation is required to update overdue status accurately.**

## Business vs Technical Meaning

### Business Meaning

**Business:** "Customer owes money and payment is past due."

**Reality:** Overdue is based on due date, not payment status.

### Technical Meaning

**Technical:** "Due date has passed and payment is not confirmed."

**Reality:** Payment may have been received but not reconciled.

## How AI Should Explain Overdue

When explaining overdue:

1. **State the calculation:** "Overdue is calculated from due date, not payment status."
2. **Explain the limitation:** "Overdue may show even if payment was received but not reconciled."
3. **Recommend verification:** "Verify payment status and reconciliation to confirm actual payment status."
4. **Suggest action:** "Reconcile payments to update overdue status accurately."

**AI must not assume overdue means unpaid without verification.**

## Related Documentation

- [Invoice State Lifecycle](../states/invoice_state_lifecycle.md) — Invoice states
- [Bill State Lifecycle](../states/bill_state_lifecycle.md) — Bill states
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Reconciliation Logic](./reconciliation_logic.md) — Reconciliation meaning
- [Reconciliation Gaps](../risks/reconciliation_gaps.md) — Reconciliation risks

