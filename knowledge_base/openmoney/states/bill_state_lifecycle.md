# Bill State Lifecycle: Complete State Machine

## Overview

This document defines the **complete state machine** for bills in Open Money. Understanding these states is critical for building reliable payables systems.

## Bill States

### 1. `draft`

**Meaning:** Bill is being created, not yet finalized.

**When it occurs:**
- Immediately after creating bill
- Before finalizing bill
- While editing bill details

**What it means:**
- Bill is not yet finalized
- Payment is not expected yet
- Bill can be modified or deleted

**Can transition to:**
- `payment_due` (bill finalized, payment expected)
- `cancelled` (bill cancelled)

**Is reversible:** Yes (can be edited, cancelled, or finalized)

**What to do:**
- Complete bill details
- Review before finalizing
- Finalize when ready

---

### 2. `payment_due`

**Meaning:** Bill is finalized, payment is expected to be made.

**When it occurs:**
- After finalizing bill
- Payment deadline has not passed
- Payment has not been made

**What it means:**
- Bill is active and payable
- Payment should be made
- Payment is expected
- Bill is not yet overdue

**Can transition to:**
- `paid` (payment made and reconciled)
- `overdue` (payment deadline passed)
- `cancelled` (bill cancelled)
- `partially_paid` (partial payment made)

**Is reversible:** Yes (can become overdue or paid)

**What to do:**
- Schedule payment
- Monitor payment deadline
- Make payment when due

---

### 3. `partially_paid`

**Meaning:** Partial payment has been made for the bill.

**When it occurs:**
- Partial payment made
- Payment amount is less than bill amount
- Payment is reconciled

**What it means:**
- Bill is not fully paid
- Outstanding amount remains
- Remaining payment should be made
- Bill is still active

**Can transition to:**
- `paid` (remaining amount paid)
- `overdue` (payment deadline passed for remaining amount)
- `cancelled` (bill cancelled)

**Is reversible:** Yes (can become paid or overdue)

**What to do:**
- Track remaining amount
- Schedule remaining payment
- Monitor for full payment

---

### 4. `paid`

**Meaning:** Bill has been fully paid and reconciled.

**When it occurs:**
- Full payment made
- Payment is reconciled with bank entry
- All amounts match

**What it means:**
- Bill is fully settled
- No outstanding amount
- Payment is confirmed
- This is a **terminal state** (cannot change)

**Can transition to:**
- None (terminal state)

**Is reversible:** No (irreversible - bill is settled)

**What to do:**
- Mark bill as paid
- Update vendor records
- Close bill
- **This is the only state where bill is truly settled**

---

### 5. `overdue`

**Meaning:** Payment deadline has passed, bill is overdue.

**When it occurs:**
- Payment due date has passed
- Bill is not paid
- Outstanding amount remains

**What it means:**
- Bill is past due
- Payment should have been made
- Payment is still expected
- Overdue days are calculated

**Can transition to:**
- `paid` (payment made and reconciled)
- `partially_paid` (partial payment made)
- `cancelled` (bill cancelled)

**Is reversible:** Yes (can become paid)

**What to do:**
- Make payment immediately
- Monitor overdue status
- Update payment schedule

---

### 6. `cancelled`

**Meaning:** Bill has been cancelled.

**When it occurs:**
- Bill is cancelled by user
- Bill is no longer valid
- Payment is not expected

**What it means:**
- Bill is no longer active
- Payment should not be made
- Bill cannot be used
- This is a **terminal state** (cannot change)

**Can transition to:**
- None (terminal state)

**Is reversible:** No (cancelled bill cannot be revived)

**What to do:**
- Mark bill as cancelled
- Update records
- Do not make payment

---

## State Transition Diagram

```
                    ┌─────────┐
                    │  draft  │
                    └────┬────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                 │
        ▼                ▼                 ▼
   ┌──────────┐    ┌──────────┐     ┌──────────┐
   │cancelled │    │payment_  │     │payment_  │
   │          │    │  due     │     │  due     │
   └──────────┘    └────┬─────┘     └────┬─────┘
                        │                 │
                        │                 │
              ┌─────────┴─────────┐      │
              │                   │      │
              ▼                   ▼      ▼
        ┌──────────┐        ┌──────────┐
        │partially │        │ overdue  │
        │  paid    │        └────┬──────┘
        └────┬─────┘             │
             │                   │
             │                   │
             └──────────┬────────┘
                        │
                        ▼
                  ┌──────────┐
                  │   paid   │
                  └──────────┘
```

## Terminal States

**Terminal states** (cannot change further):
- `paid` ✅
- `cancelled` 🚫

**Non-terminal states:**
- `draft` (can become payment_due or cancelled)
- `payment_due` (can become paid, overdue, partially_paid, or cancelled)
- `partially_paid` (can become paid, overdue, or cancelled)
- `overdue` (can become paid, partially_paid, or cancelled)

## Critical Rules

### ✅ Safe to Mark as Paid:
- **Only when status is `paid`**
- Payout is reconciled with bank entry
- Amount matches bill amount
- No outstanding balance

### ❌ Never Mark as Paid When:
- Status is `draft` (not finalized yet)
- Status is `payment_due` (not paid yet)
- Status is `partially_paid` (not fully paid)
- Status is `overdue` (not paid yet)
- Status is `cancelled`

### State Verification:
- Always verify payout via reconciliation
- Check bank statement for actual debit
- Don't trust dashboard status alone
- Reconcile before marking as paid

## Common Misinterpretations

### Misinterpretation 1: Payment Due = Paid

**Wrong:** "Bill shows payment_due, so it's paid."

**Correct:** "Bill shows payment_due, meaning payment is expected but not yet made."

### Misinterpretation 2: Overdue = Unpaid Forever

**Wrong:** "Bill shows overdue, so it will never be paid."

**Correct:** "Bill shows overdue, meaning payment deadline passed. Payment can still be made."

### Misinterpretation 3: Partially Paid = Paid

**Wrong:** "Bill shows partially_paid, so it's paid."

**Correct:** "Bill shows partially_paid, meaning only part of amount is paid. Outstanding balance remains."

## Reconciliation Requirement

Bill state `paid` requires:
- Payout made (to vendor)
- Payout reconciled (with bank entry)
- Amount matches (payout = bill)
- No outstanding balance

**Without reconciliation, bill cannot be considered truly paid.**

## Related Documentation

- [Bill to Payout Workflow](../workflows/bill_to_payout.md) — Bill payout flow
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Reconciliation Logic](../data_semantics/reconciliation_logic.md) — Reconciliation meaning
- [Financial Finality Rules](../principles/financial_finality_rules.md) — When money is final

