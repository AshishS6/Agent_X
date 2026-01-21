# Invoice State Lifecycle: Complete State Machine

## Overview

This document defines the **complete state machine** for invoices in Open Money. Understanding these states is critical for building reliable receivables systems.

## Invoice States

### 1. `draft`

**Meaning:** Invoice is being created, not yet sent to customer.

**When it occurs:**
- Immediately after creating invoice
- Before sending to customer
- While editing invoice details

**What it means:**
- Invoice is not yet finalized
- Customer has not seen invoice
- Payment is not expected yet
- Invoice can be modified or deleted

**Can transition to:**
- `payment_due` (invoice sent to customer)
- `cancelled` (invoice cancelled)

**Is reversible:** Yes (can be edited, cancelled, or sent)

**What to do:**
- Complete invoice details
- Review before sending
- Send to customer when ready

---

### 2. `payment_due`

**Meaning:** Invoice has been sent to customer, payment is expected.

**When it occurs:**
- After sending invoice to customer
- Customer has received invoice
- Payment deadline has not passed

**What it means:**
- Invoice is active and payable
- Customer can make payment
- Payment is expected
- Invoice is not yet overdue

**Can transition to:**
- `paid` (payment received and reconciled)
- `overdue` (payment deadline passed)
- `cancelled` (invoice cancelled)
- `partially_paid` (partial payment received)

**Is reversible:** Yes (can become overdue or paid)

**What to do:**
- Monitor for payment
- Send reminders if needed
- Wait for payment confirmation

---

### 3. `partially_paid`

**Meaning:** Customer has paid part of the invoice amount.

**When it occurs:**
- Partial payment received
- Payment amount is less than invoice amount
- Payment is reconciled

**What it means:**
- Invoice is not fully paid
- Outstanding amount remains
- Customer may pay remaining amount
- Invoice is still active

**Can transition to:**
- `paid` (remaining amount paid)
- `overdue` (payment deadline passed for remaining amount)
- `cancelled` (invoice cancelled)

**Is reversible:** Yes (can become paid or overdue)

**What to do:**
- Track remaining amount
- Send reminder for balance
- Monitor for full payment

---

### 4. `paid`

**Meaning:** Invoice has been fully paid and reconciled.

**When it occurs:**
- Full payment received
- Payment is reconciled with bank entry
- All amounts match

**What it means:**
- Invoice is fully settled
- No outstanding amount
- Payment is confirmed
- This is a **terminal state** (cannot change)

**Can transition to:**
- None (terminal state)

**Is reversible:** No (irreversible - invoice is settled)

**What to do:**
- Mark invoice as paid
- Update customer records
- Close invoice
- **This is the only state where invoice is truly settled**

---

### 5. `overdue`

**Meaning:** Payment deadline has passed, invoice is overdue.

**When it occurs:**
- Payment due date has passed
- Invoice is not paid
- Outstanding amount remains

**What it means:**
- Invoice is past due
- Customer has not paid on time
- Payment is still expected
- Overdue days are calculated

**Can transition to:**
- `paid` (payment received and reconciled)
- `partially_paid` (partial payment received)
- `cancelled` (invoice cancelled)
- `written_off` (invoice written off)

**Is reversible:** Yes (can become paid)

**What to do:**
- Send overdue reminders
- Follow up with customer
- Consider collection actions
- Monitor for payment

---

### 6. `cancelled`

**Meaning:** Invoice has been cancelled.

**When it occurs:**
- Invoice is cancelled by user
- Invoice is no longer valid
- Payment is not expected

**What it means:**
- Invoice is no longer active
- Customer should not pay
- Invoice cannot be used
- This is a **terminal state** (cannot change)

**Can transition to:**
- None (terminal state)

**Is reversible:** No (cancelled invoice cannot be revived)

**What to do:**
- Mark invoice as cancelled
- Update records
- Do not expect payment

---

### 7. `written_off`

**Meaning:** Invoice has been written off as uncollectible.

**When it occurs:**
- Invoice is deemed uncollectible
- Customer cannot or will not pay
- Invoice is written off for accounting purposes

**What it means:**
- Invoice will not be collected
- Outstanding amount is written off
- Invoice is closed
- This is a **terminal state** (cannot change)

**Can transition to:**
- None (terminal state)

**Is reversible:** No (written off invoice cannot be revived)

**What to do:**
- Mark invoice as written off
- Update accounting records
- Close invoice
- Do not expect payment

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
                        │
                        ▼
                  ┌──────────┐
                  │written_  │
                  │   off    │
                  └──────────┘
```

## Terminal States

**Terminal states** (cannot change further):
- `paid` ✅
- `cancelled` 🚫
- `written_off` 📝

**Non-terminal states:**
- `draft` (can become payment_due or cancelled)
- `payment_due` (can become paid, overdue, partially_paid, or cancelled)
- `partially_paid` (can become paid, overdue, or cancelled)
- `overdue` (can become paid, partially_paid, cancelled, or written_off)

## Critical Rules

### ✅ Safe to Mark as Paid:
- **Only when status is `paid`**
- Payment is reconciled with bank entry
- Amount matches invoice amount
- No outstanding balance

### ❌ Never Mark as Paid When:
- Status is `draft` (not sent yet)
- Status is `payment_due` (not paid yet)
- Status is `partially_paid` (not fully paid)
- Status is `overdue` (not paid yet)
- Status is `cancelled` or `written_off`

### State Verification:
- Always verify payment via reconciliation
- Check bank statement for actual payment
- Don't trust dashboard status alone
- Reconcile before marking as paid

## Common Misinterpretations

### Misinterpretation 1: Payment Due = Paid

**Wrong:** "Invoice shows payment_due, so customer will pay."

**Correct:** "Invoice shows payment_due, meaning payment is expected but not yet received."

### Misinterpretation 2: Overdue = Unpaid Forever

**Wrong:** "Invoice shows overdue, so it will never be paid."

**Correct:** "Invoice shows overdue, meaning payment deadline passed. Customer can still pay."

### Misinterpretation 3: Partially Paid = Paid

**Wrong:** "Invoice shows partially_paid, so it's paid."

**Correct:** "Invoice shows partially_paid, meaning only part of amount is paid. Outstanding balance remains."

## Reconciliation Requirement

Invoice state `paid` requires:
- Payment received (from payment rail)
- Payment reconciled (with bank entry)
- Amount matches (payment = invoice)
- No outstanding balance

**Without reconciliation, invoice cannot be considered truly paid.**

## Related Documentation

- [Invoice to Collection Workflow](../workflows/invoice_to_collection.md) — Invoice collection flow
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Reconciliation Logic](../data_semantics/reconciliation_logic.md) — Reconciliation meaning
- [Financial Finality Rules](../principles/financial_finality_rules.md) — When money is final

