# Payment Link State Lifecycle: Complete State Machine

## Overview

This document defines the **complete state machine** for payment links in Open Money. Understanding these states is critical for building reliable collection systems.

## Payment Link States

### 1. `active`

**Meaning:** Payment link is active and can be used for payment.

**When it occurs:**
- Immediately after creating payment link
- Payment link is available to customers
- Payment has not been completed

**What it means:**
- Payment link is valid
- Customer can make payment
- Payment is expected
- Link has not expired

**Can transition to:**
- `paid` (payment completed and reconciled)
- `expired` (link expiration time reached)
- `cancelled` (link cancelled)
- `partially_paid` (partial payment received)

**Is reversible:** Yes (can become paid, expired, or cancelled)

**What to do:**
- Share payment link with customer
- Monitor for payment
- Wait for payment confirmation

---

### 2. `partially_paid`

**Meaning:** Customer has paid part of the payment link amount.

**When it occurs:**
- Partial payment received
- Payment amount is less than link amount
- Payment is reconciled

**What it means:**
- Payment link is not fully paid
- Outstanding amount remains
- Customer may pay remaining amount
- Link is still active

**Can transition to:**
- `paid` (remaining amount paid)
- `expired` (link expiration time reached)
- `cancelled` (link cancelled)

**Is reversible:** Yes (can become paid or expired)

**What to do:**
- Track remaining amount
- Monitor for full payment
- Send reminder if needed

---

### 3. `paid`

**Meaning:** Payment link has been fully paid and reconciled.

**When it occurs:**
- Full payment received
- Payment is reconciled with bank entry
- All amounts match

**What it means:**
- Payment link is fully settled
- No outstanding amount
- Payment is confirmed
- This is a **terminal state** (cannot change)

**Can transition to:**
- None (terminal state)

**Is reversible:** No (irreversible - payment link is settled)

**What to do:**
- Mark payment link as paid
- Update records
- Close payment link
- **This is the only state where payment link is truly settled**

---

### 4. `expired`

**Meaning:** Payment link has expired and can no longer be used.

**When it occurs:**
- Link expiration time reached
- Payment was not completed
- Link is no longer valid

**What it means:**
- Payment link cannot be used
- Customer cannot pay via this link
- Link is closed
- This is a **terminal state** (cannot change)

**Can transition to:**
- None (terminal state)

**Is reversible:** No (expired link cannot be revived)

**What to do:**
- Mark payment link as expired
- Create new link if payment is still needed
- Update records

---

### 5. `cancelled`

**Meaning:** Payment link has been cancelled.

**When it occurs:**
- Link is cancelled by user
- Link is no longer valid
- Payment is not expected

**What it means:**
- Payment link cannot be used
- Customer should not pay
- Link is closed
- This is a **terminal state** (cannot change)

**Can transition to:**
- None (terminal state)

**Is reversible:** No (cancelled link cannot be revived)

**What to do:**
- Mark payment link as cancelled
- Update records
- Do not expect payment

---

## State Transition Diagram

```
                    ┌─────────┐
                    │ active  │
                    └────┬────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                 │
        ▼                ▼                 ▼
   ┌──────────┐    ┌──────────┐     ┌──────────┐
   │cancelled │    │partially │     │ expired  │
   │          │    │  paid    │     │          │
   └──────────┘    └────┬─────┘     └──────────┘
                        │
                        │
                        ▼
                  ┌──────────┐
                  │   paid   │
                  └──────────┘
```

## Terminal States

**Terminal states** (cannot change further):
- `paid` ✅
- `expired` ⏰
- `cancelled` 🚫

**Non-terminal states:**
- `active` (can become paid, expired, cancelled, or partially_paid)
- `partially_paid` (can become paid, expired, or cancelled)

## Critical Rules

### ✅ Safe to Mark as Paid:
- **Only when status is `paid`**
- Payment is reconciled with bank entry
- Amount matches payment link amount
- No outstanding balance

### ❌ Never Mark as Paid When:
- Status is `active` (not paid yet)
- Status is `partially_paid` (not fully paid)
- Status is `expired` (link expired)
- Status is `cancelled` (link cancelled)

### State Verification:
- Always verify payment via reconciliation
- Check bank statement for actual payment
- Don't trust dashboard status alone
- Reconcile before marking as paid

## Common Misinterpretations

### Misinterpretation 1: Active = Paid

**Wrong:** "Payment link shows active, so payment is received."

**Correct:** "Payment link shows active, meaning link is available but payment not yet received."

### Misinterpretation 2: Partially Paid = Paid

**Wrong:** "Payment link shows partially_paid, so it's paid."

**Correct:** "Payment link shows partially_paid, meaning only part of amount is paid. Outstanding balance remains."

### Misinterpretation 3: Expired = Failed

**Wrong:** "Payment link shows expired, so payment failed."

**Correct:** "Payment link shows expired, meaning link expiration time reached. Payment may or may not have been received before expiration."

## Reconciliation Requirement

Payment link state `paid` requires:
- Payment received (from payment rail)
- Payment reconciled (with bank entry)
- Amount matches (payment = link amount)
- No outstanding balance

**Without reconciliation, payment link cannot be considered truly paid.**

## Expiration Behavior

Payment links expire based on:
- Expiration time set at creation
- Time elapsed since creation
- No payment received before expiration

**Expired links cannot be used for payment, but payments received before expiration are valid.**

## Related Documentation

- [Payment Link to Settlement Workflow](../workflows/payment_link_to_settlement.md) — Payment link settlement flow
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Reconciliation Logic](../data_semantics/reconciliation_logic.md) — Reconciliation meaning
- [Financial Finality Rules](../principles/financial_finality_rules.md) — When money is final

