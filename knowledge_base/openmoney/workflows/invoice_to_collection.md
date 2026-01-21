# Invoice → Collection Workflow

## Overview

This document describes the **complete system-level flow** from invoice creation to collection and reconciliation. This is the end-to-end process where everything works correctly.

## Flow Diagram

```
Invoice Creation → Payment Initiation → Payment Processing → Bank Settlement → Reconciliation → Invoice Paid
```

## Step-by-Step Flow

### Step 1: Invoice Creation

**What happens:**
- Invoice is created in Open Money
- Invoice details are stored
- Invoice status: `draft`

**What you do:**
- Create invoice with customer, amount, due date
- Review invoice details
- Finalize invoice

**What to store:**
- Invoice ID
- Customer information
- Invoice amount
- Due date
- Invoice status: `draft`

---

### Step 2: Invoice Sent to Customer

**What happens:**
- Invoice is sent to customer
- Customer receives invoice
- Invoice status: `draft` → `payment_due`

**What you do:**
- Send invoice to customer
- Update invoice status
- Monitor for payment

**What to store:**
- Invoice status: `payment_due`
- Sent timestamp
- Customer acknowledgment (if available)

---

### Step 3: Payment Method Selection

**What happens:**
- Customer chooses payment method
- Payment link may be created
- Payment initiation begins

**Payment methods:**
- Payment link (Open Money)
- Manual bank transfer
- External payment gateway
- Offline payment

**What you do:**
- Provide payment options
- Create payment link if needed
- Monitor payment initiation

**What to store:**
- Payment method
- Payment link ID (if applicable)
- Payment initiation timestamp

---

### Step 4: Payment Initiation

**What happens:**
- Customer initiates payment
- Payment rail processes payment
- Payment status updates asynchronously

**Payment rail processing:**
- Payment is submitted to payment rail
- Payment rail processes payment
- Payment status: `pending` → `processing` → `completed` or `failed`

**What you do:**
- Monitor payment status
- Wait for payment confirmation
- Do NOT mark invoice as paid yet

**What to store:**
- Payment ID
- Payment status
- Payment amount
- Payment timestamp

---

### Step 5: Payment Confirmation (Payment Rail)

**What happens:**
- Payment rail confirms payment
- Payment status: `completed`
- Payment rail sends webhook (if configured)

**Payment rail confirmation:**
- Payment is successful
- Money is in transit or settled
- Payment rail status is authoritative for payment rail

**What you do:**
- Receive payment confirmation
- Update payment status
- Do NOT mark invoice as paid yet (reconciliation required)

**What to store:**
- Payment status: `completed`
- Payment confirmation timestamp
- Payment rail transaction ID

---

### Step 6: Bank Settlement

**What happens:**
- Bank receives payment
- Money is credited to bank account
- Bank statement shows credit entry

**Bank settlement:**
- Payment appears in bank statement
- Credit is cleared (not pending)
- Bank statement is authoritative for bank balance

**What you do:**
- Wait for bank settlement
- Monitor bank statement
- Do NOT mark invoice as paid yet (reconciliation required)

**What to store:**
- Bank transaction ID
- Bank credit amount
- Bank settlement timestamp

---

### Step 7: Reconciliation (Critical)

**What happens:**
- Invoice is matched with payment
- Payment is matched with bank entry
- All amounts are verified

**Reconciliation process:**
- Link invoice to payment
- Link payment to bank entry
- Verify amounts match
- Confirm no discrepancies

**What you do:**
- Reconcile invoice with payment
- Reconcile payment with bank entry
- Verify all amounts match
- Resolve any discrepancies

**What to store:**
- Reconciliation status: `reconciled`
- Reconciliation timestamp
- Matched records (invoice, payment, bank entry)

---

### Step 8: Invoice Marked as Paid

**What happens:**
- Invoice is reconciled
- All amounts match
- Invoice status: `payment_due` → `paid`

**Invoice paid confirmation:**
- Invoice is fully paid
- Payment is confirmed
- Bank entry is verified
- Reconciliation is complete

**What you do:**
- Mark invoice as paid
- Update customer records
- Close invoice
- Update accounting records

**What to store:**
- Invoice status: `paid`
- Paid timestamp
- Reconciliation confirmation

---

## Critical Checkpoints

### ✅ Must Do:

1. **Wait for payment confirmation** — Don't mark invoice as paid based on customer confirmation alone
2. **Wait for bank settlement** — Don't mark invoice as paid based on payment rail status alone
3. **Reconcile before marking paid** — Reconciliation is mandatory
4. **Verify amounts match** — Invoice amount = Payment amount = Bank credit amount
5. **Store all records** — Invoice, payment, bank entry, reconciliation

### ❌ Must NOT Do:

1. **Don't mark invoice as paid** based on customer confirmation alone
2. **Don't mark invoice as paid** based on payment rail status alone
3. **Don't skip reconciliation** — It is mandatory
4. **Don't assume amounts match** — Always verify
5. **Don't trust dashboard status alone** — Verify against source systems

## Timeline Example

```
Day 1, 10:00:00 - Invoice created (status: draft)
Day 1, 10:05:00 - Invoice sent to customer (status: payment_due)
Day 1, 14:30:00 - Customer initiates payment
Day 1, 14:30:05 - Payment rail processing (status: processing)
Day 1, 14:30:30 - Payment rail confirms (status: completed)
Day 1, 14:35:00 - Bank receives payment
Day 1, 15:00:00 - Bank statement shows credit
Day 1, 16:00:00 - Reconciliation performed
Day 1, 16:05:00 - Invoice marked as paid (status: paid)
```

## Success Criteria

An invoice is successfully collected when:
- ✅ Invoice status is `paid`
- ✅ Payment is confirmed by payment rail
- ✅ Bank statement shows credit
- ✅ Reconciliation is complete
- ✅ All amounts match
- ✅ No discrepancies exist

## Common Failure Points

### Failure Point 1: Payment Rail Failure

**What happens:**
- Payment rail rejects payment
- Payment status: `failed`
- Invoice remains unpaid

**What to do:**
- Investigate failure reason
- Retry payment if appropriate
- Update invoice status
- Notify customer

### Failure Point 2: Bank Sync Delay

**What happens:**
- Payment rail confirms payment
- Bank statement does not show credit yet
- Reconciliation cannot be completed

**What to do:**
- Wait for bank settlement
- Monitor bank statement
- Reconcile when bank entry appears
- Don't mark invoice as paid until reconciled

### Failure Point 3: Amount Mismatch

**What happens:**
- Invoice amount: ₹1000
- Payment amount: ₹950
- Amounts do not match

**What to do:**
- Investigate mismatch
- Verify partial payment
- Update invoice status to `partially_paid`
- Reconcile partial payment
- Track remaining amount

## Related Documentation

- [Invoice State Lifecycle](../states/invoice_state_lifecycle.md) — Invoice states
- [Reconciliation Flow](./reconciliation_flow.md) — Reconciliation process
- [Reconciliation Logic](../data_semantics/reconciliation_logic.md) — Reconciliation meaning
- [Financial Finality Rules](../principles/financial_finality_rules.md) — When money is final

