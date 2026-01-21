# Payment Link → Settlement Workflow

## Overview

This document describes the **complete system-level flow** from payment link creation to settlement and reconciliation. This is the end-to-end process where everything works correctly.

## Flow Diagram

```
Payment Link Creation → Customer Payment → Payment Processing → Bank Settlement → Reconciliation → Payment Link Paid
```

## Step-by-Step Flow

### Step 1: Payment Link Creation

**What happens:**
- Payment link is created in Open Money
- Payment link details are stored
- Payment link status: `active`

**What you do:**
- Create payment link with amount, description
- Set expiration time (if applicable)
- Share payment link with customer

**What to store:**
- Payment link ID
- Payment link amount
- Expiration time
- Payment link status: `active`

---

### Step 2: Customer Accesses Payment Link

**What happens:**
- Customer clicks payment link
- Payment page is displayed
- Customer sees payment details

**What you do:**
- Monitor payment link access
- Track customer interactions
- Wait for payment initiation

**What to store:**
- Access timestamp
- Customer information (if available)
- Payment page views

---

### Step 3: Customer Initiates Payment

**What happens:**
- Customer selects payment method
- Customer authorizes payment
- Payment is submitted to payment rail

**Payment methods:**
- UPI
- Net Banking
- Card
- Other payment methods

**What you do:**
- Monitor payment initiation
- Wait for payment processing
- Do NOT mark payment link as paid yet

**What to store:**
- Payment ID
- Payment method
- Payment initiation timestamp

---

### Step 4: Payment Processing

**What happens:**
- Payment rail processes payment
- Payment status updates asynchronously
- Payment status: `pending` → `processing` → `completed` or `failed`

**Payment rail processing:**
- Payment is validated
- Payment is processed
- Payment status is updated
- Webhook is sent (if configured)

**What you do:**
- Monitor payment status
- Wait for payment confirmation
- Do NOT mark payment link as paid yet

**What to store:**
- Payment status
- Payment processing timestamp
- Payment rail transaction ID

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
- Do NOT mark payment link as paid yet (reconciliation required)

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
- Do NOT mark payment link as paid yet (reconciliation required)

**What to store:**
- Bank transaction ID
- Bank credit amount
- Bank settlement timestamp

---

### Step 7: Reconciliation (Critical)

**What happens:**
- Payment link is matched with payment
- Payment is matched with bank entry
- All amounts are verified

**Reconciliation process:**
- Link payment link to payment
- Link payment to bank entry
- Verify amounts match
- Confirm no discrepancies

**What you do:**
- Reconcile payment link with payment
- Reconcile payment with bank entry
- Verify all amounts match
- Resolve any discrepancies

**What to store:**
- Reconciliation status: `reconciled`
- Reconciliation timestamp
- Matched records (payment link, payment, bank entry)

---

### Step 8: Payment Link Marked as Paid

**What happens:**
- Payment link is reconciled
- All amounts match
- Payment link status: `active` → `paid`

**Payment link paid confirmation:**
- Payment link is fully paid
- Payment is confirmed
- Bank entry is verified
- Reconciliation is complete

**What you do:**
- Mark payment link as paid
- Update records
- Close payment link
- Update accounting records

**What to store:**
- Payment link status: `paid`
- Paid timestamp
- Reconciliation confirmation

---

## Critical Checkpoints

### ✅ Must Do:

1. **Wait for payment confirmation** — Don't mark payment link as paid based on customer confirmation alone
2. **Wait for bank settlement** — Don't mark payment link as paid based on payment rail status alone
3. **Reconcile before marking paid** — Reconciliation is mandatory
4. **Verify amounts match** — Payment link amount = Payment amount = Bank credit amount
5. **Store all records** — Payment link, payment, bank entry, reconciliation

### ❌ Must NOT Do:

1. **Don't mark payment link as paid** based on customer confirmation alone
2. **Don't mark payment link as paid** based on payment rail status alone
3. **Don't skip reconciliation** — It is mandatory
4. **Don't assume amounts match** — Always verify
5. **Don't trust dashboard status alone** — Verify against source systems

## Timeline Example

```
10:00:00 - Payment link created (status: active)
10:05:00 - Customer accesses payment link
10:10:00 - Customer initiates payment
10:10:05 - Payment rail processing (status: processing)
10:10:30 - Payment rail confirms (status: completed)
10:15:00 - Bank receives payment
10:20:00 - Bank statement shows credit
10:30:00 - Reconciliation performed
10:35:00 - Payment link marked as paid (status: paid)
```

## Success Criteria

A payment link is successfully settled when:
- ✅ Payment link status is `paid`
- ✅ Payment is confirmed by payment rail
- ✅ Bank statement shows credit
- ✅ Reconciliation is complete
- ✅ All amounts match
- ✅ No discrepancies exist

## Expiration Handling

If payment link expires before payment:
- Payment link status: `active` → `expired`
- Payment link cannot be used
- Customer cannot pay via expired link
- New payment link must be created if payment is still needed

**Expired payment links cannot be revived, but payments received before expiration are valid.**

## Common Failure Points

### Failure Point 1: Payment Rail Failure

**What happens:**
- Payment rail rejects payment
- Payment status: `failed`
- Payment link remains unpaid

**What to do:**
- Investigate failure reason
- Customer can retry payment
- Update payment link status
- Notify customer if needed

### Failure Point 2: Bank Sync Delay

**What happens:**
- Payment rail confirms payment
- Bank statement does not show credit yet
- Reconciliation cannot be completed

**What to do:**
- Wait for bank settlement
- Monitor bank statement
- Reconcile when bank entry appears
- Don't mark payment link as paid until reconciled

### Failure Point 3: Link Expiration

**What happens:**
- Payment link expires before payment
- Payment link status: `expired`
- Customer cannot pay via expired link

**What to do:**
- Create new payment link if payment is still needed
- Update records
- Notify customer if needed

## Related Documentation

- [Payment Link State Lifecycle](../states/payment_link_state_lifecycle.md) — Payment link states
- [Reconciliation Flow](./reconciliation_flow.md) — Reconciliation process
- [Reconciliation Logic](../data_semantics/reconciliation_logic.md) — Reconciliation meaning
- [Financial Finality Rules](../principles/financial_finality_rules.md) — When money is final

