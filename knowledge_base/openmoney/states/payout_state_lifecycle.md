# Payout State Lifecycle: Complete State Machine

## Overview

This document defines the **complete state machine** for payouts in Open Money. Understanding these states is critical for building reliable payout systems.

## Payout States

### 1. `initiated`

**Meaning:** Payout request has been created and submitted.

**When it occurs:**
- Immediately after creating payout request
- Payout is submitted to payment rail
- Payout is being processed

**What it means:**
- Payout request is valid
- Payment rail is processing
- Money has not been debited yet
- Payout may succeed or fail

**Can transition to:**
- `processing` (payment rail is processing)
- `failed` (payout failed)
- `cancelled` (payout cancelled)

**Is reversible:** Yes (can become processing, failed, or cancelled)

**What to do:**
- Monitor payout status
- Wait for processing confirmation
- Check for failures

---

### 2. `processing`

**Meaning:** Payment rail is processing the payout.

**When it occurs:**
- Payment rail received payout request
- Payout is being processed
- Money is in transit

**What it means:**
- Payout is being processed
- Money may or may not be debited (still uncertain)
- Usually a short-lived state (seconds to minutes)

**Can transition to:**
- `completed` (payout successful)
- `failed` (payout failed)

**Is reversible:** No (once processing, it will complete or fail)

**What to do:**
- Show "Processing" status
- Wait for final status (webhook)
- Don't mark as paid yet

---

### 3. `completed`

**Meaning:** Payout successful, money debited from account.

**When it occurs:**
- Payment rail confirmed payout
- Money debited from account
- Payout is final

**What it means:**
- Payout is successful
- Money has been debited
- This is a **terminal state** (cannot change)

**Can transition to:**
- None (terminal state)

**Is reversible:** No (irreversible - money has been debited)

**What to do:**
- Mark payout as completed
- Update vendor records
- Reconcile with bank entry
- **This is the only state where payout is truly completed**

---

### 4. `failed`

**Meaning:** Payout was rejected or failed.

**When it occurs:**
- Insufficient funds in account
- Payment rail rejected payout
- Network/system error
- Invalid beneficiary details

**What it means:**
- Payout did not succeed
- No money was debited
- Payout can be retried

**Can transition to:**
- None (terminal state for this payout)
- New payout can be created (new payout_id)

**Is reversible:** No (this payout failed, but new payout can be created)

**What to do:**
- Mark payout as failed
- Investigate failure reason
- Retry if appropriate
- Update records

---

### 5. `cancelled`

**Meaning:** Payout has been cancelled.

**When it occurs:**
- Payout is cancelled by user
- Payout is cancelled before processing
- Payout is no longer valid

**What it means:**
- Payout is no longer active
- Money was not debited
- Payout cannot be used
- This is a **terminal state** (cannot change)

**Can transition to:**
- None (terminal state)

**Is reversible:** No (cancelled payout cannot be revived)

**What to do:**
- Mark payout as cancelled
- Update records
- Do not expect debit

---

## State Transition Diagram

```
                    ┌──────────┐
                    │initiated │
                    └────┬─────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                 │
        ▼                ▼                 ▼
   ┌──────────┐    ┌──────────┐     ┌──────────┐
   │cancelled │    │processing│     │ failed   │
   │          │    └────┬─────┘     │          │
   └──────────┘         │           └──────────┘
                        │
                        │
                        ▼
                  ┌──────────┐
                  │completed │
                  └──────────┘
```

## Terminal States

**Terminal states** (cannot change further):
- `completed` ✅
- `failed` ❌
- `cancelled` 🚫

**Non-terminal states:**
- `initiated` (can become processing, failed, or cancelled)
- `processing` (can become completed or failed)

## Critical Rules

### ✅ Safe to Mark as Completed:
- **Only when status is `completed`**
- Payout is reconciled with bank entry
- Amount matches payout amount
- Bank statement shows debit

### ❌ Never Mark as Completed When:
- Status is `initiated` (not processed yet)
- Status is `processing` (may still fail)
- Status is `failed` (payout failed)
- Status is `cancelled` (payout cancelled)

### State Verification:
- Always verify payout via reconciliation
- Check bank statement for actual debit
- Don't trust dashboard status alone
- Reconcile before marking as completed

## Common Misinterpretations

### Misinterpretation 1: Processing = Completed

**Wrong:** "Payout shows processing, so money is debited."

**Correct:** "Payout shows processing, meaning payment rail is processing. Payout may still fail."

### Misinterpretation 2: Initiated = Completed

**Wrong:** "Payout shows initiated, so it's completed."

**Correct:** "Payout shows initiated, meaning payout request created but not yet processed."

### Misinterpretation 3: Completed = Final

**Wrong:** "Payout shows completed, so it's final."

**Correct:** "Payout shows completed in payment rail. Verify against bank statement to confirm debit and reconcile."

## Reconciliation Requirement

Payout state `completed` requires:
- Payout confirmed by payment rail
- Payout reconciled with bank entry
- Bank statement shows debit
- Amount matches (payout = debit)

**Without reconciliation, payout cannot be considered truly completed.**

## Failure Handling

When payout fails:
- Investigate failure reason
- Check account balance
- Verify beneficiary details
- Retry if appropriate
- Update records

**Failed payouts can be retried, but each retry is a new payout with new payout_id.**

## Related Documentation

- [Bill to Payout Workflow](../workflows/bill_to_payout.md) — Payout flow
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Reconciliation Logic](../data_semantics/reconciliation_logic.md) — Reconciliation meaning
- [Financial Finality Rules](../principles/financial_finality_rules.md) — When money is final
- [Handling Failed Payouts](../decisions/handling_failed_payouts.md) — Payout failure handling

