# Bill → Payout Workflow

## Overview

This document describes the **complete system-level flow** from bill creation to payout and reconciliation. This is the end-to-end process where everything works correctly.

## Flow Diagram

```
Bill Creation → Payout Initiation → Payout Processing → Bank Settlement → Reconciliation → Bill Paid
```

## Step-by-Step Flow

### Step 1: Bill Creation

**What happens:**
- Bill is created in Open Money
- Bill details are stored
- Bill status: `draft`

**What you do:**
- Create bill with vendor, amount, due date
- Review bill details
- Finalize bill

**What to store:**
- Bill ID
- Vendor information
- Bill amount
- Due date
- Bill status: `draft`

---

### Step 2: Bill Finalized

**What happens:**
- Bill is finalized
- Bill status: `draft` → `payment_due`
- Payment is expected

**What you do:**
- Finalize bill
- Update bill status
- Schedule payout

**What to store:**
- Bill status: `payment_due`
- Finalized timestamp

---

### Step 3: Payout Initiation

**What happens:**
- Payout request is created
- Payout is submitted to payment rail
- Payout status: `initiated`

**What you do:**
- Create payout request
- Submit payout to payment rail
- Monitor payout status

**What to store:**
- Payout ID
- Payout amount
- Beneficiary details
- Payout status: `initiated`

---

### Step 4: Payout Processing

**What happens:**
- Payment rail processes payout
- Payout status updates asynchronously
- Payout status: `initiated` → `processing` → `completed` or `failed`

**Payment rail processing:**
- Payout is validated
- Payout is processed
- Payout status is updated
- Webhook is sent (if configured)

**What you do:**
- Monitor payout status
- Wait for payout confirmation
- Do NOT mark bill as paid yet

**What to store:**
- Payout status
- Payout processing timestamp
- Payment rail transaction ID

---

### Step 5: Payout Confirmation (Payment Rail)

**What happens:**
- Payment rail confirms payout
- Payout status: `completed`
- Payment rail sends webhook (if configured)

**Payment rail confirmation:**
- Payout is successful
- Money is in transit or settled
- Payment rail status is authoritative for payment rail

**What you do:**
- Receive payout confirmation
- Update payout status
- Do NOT mark bill as paid yet (reconciliation required)

**What to store:**
- Payout status: `completed`
- Payout confirmation timestamp
- Payment rail transaction ID

---

### Step 6: Bank Settlement

**What happens:**
- Bank processes payout
- Money is debited from bank account
- Bank statement shows debit entry

**Bank settlement:**
- Payout appears in bank statement
- Debit is cleared (not pending)
- Bank statement is authoritative for bank balance

**What you do:**
- Wait for bank settlement
- Monitor bank statement
- Do NOT mark bill as paid yet (reconciliation required)

**What to store:**
- Bank transaction ID
- Bank debit amount
- Bank settlement timestamp

---

### Step 7: Reconciliation (Critical)

**What happens:**
- Bill is matched with payout
- Payout is matched with bank entry
- All amounts are verified

**Reconciliation process:**
- Link bill to payout
- Link payout to bank entry
- Verify amounts match
- Confirm no discrepancies

**What you do:**
- Reconcile bill with payout
- Reconcile payout with bank entry
- Verify all amounts match
- Resolve any discrepancies

**What to store:**
- Reconciliation status: `reconciled`
- Reconciliation timestamp
- Matched records (bill, payout, bank entry)

---

### Step 8: Bill Marked as Paid

**What happens:**
- Bill is reconciled
- All amounts match
- Bill status: `payment_due` → `paid`

**Bill paid confirmation:**
- Bill is fully paid
- Payout is confirmed
- Bank entry is verified
- Reconciliation is complete

**What you do:**
- Mark bill as paid
- Update vendor records
- Close bill
- Update accounting records

**What to store:**
- Bill status: `paid`
- Paid timestamp
- Reconciliation confirmation

---

## Critical Checkpoints

### ✅ Must Do:

1. **Wait for payout confirmation** — Don't mark bill as paid based on initiation alone
2. **Wait for bank settlement** — Don't mark bill as paid based on payment rail status alone
3. **Reconcile before marking paid** — Reconciliation is mandatory
4. **Verify amounts match** — Bill amount = Payout amount = Bank debit amount
5. **Store all records** — Bill, payout, bank entry, reconciliation

### ❌ Must NOT Do:

1. **Don't mark bill as paid** based on payout initiation alone
2. **Don't mark bill as paid** based on payment rail status alone
3. **Don't skip reconciliation** — It is mandatory
4. **Don't assume amounts match** — Always verify
5. **Don't trust dashboard status alone** — Verify against source systems

## Timeline Example

```
Day 1, 10:00:00 - Bill created (status: draft)
Day 1, 10:05:00 - Bill finalized (status: payment_due)
Day 1, 14:00:00 - Payout initiated (status: initiated)
Day 1, 14:00:05 - Payout processing (status: processing)
Day 1, 14:00:30 - Payout rail confirms (status: completed)
Day 1, 14:05:00 - Bank processes payout
Day 1, 14:10:00 - Bank statement shows debit
Day 1, 15:00:00 - Reconciliation performed
Day 1, 15:05:00 - Bill marked as paid (status: paid)
```

## Success Criteria

A bill is successfully paid when:
- ✅ Bill status is `paid`
- ✅ Payout is confirmed by payment rail
- ✅ Bank statement shows debit
- ✅ Reconciliation is complete
- ✅ All amounts match
- ✅ No discrepancies exist

## Common Failure Points

### Failure Point 1: Payout Rail Failure

**What happens:**
- Payout rail rejects payout
- Payout status: `failed`
- Bill remains unpaid

**What to do:**
- Investigate failure reason
- Check account balance
- Verify beneficiary details
- Retry payout if appropriate
- Update bill status

### Failure Point 2: Bank Sync Delay

**What happens:**
- Payout rail confirms payout
- Bank statement does not show debit yet
- Reconciliation cannot be completed

**What to do:**
- Wait for bank settlement
- Monitor bank statement
- Reconcile when bank entry appears
- Don't mark bill as paid until reconciled

### Failure Point 3: Amount Mismatch

**What happens:**
- Bill amount: ₹1000
- Payout amount: ₹1000
- Bank debit amount: ₹950
- Amounts do not match

**What to do:**
- Investigate mismatch
- Verify bank charges
- Verify payout amount
- Update records as needed
- Reconcile with correct amount

## Bulk Payout Handling

For bulk payouts:
- Each payout is processed separately
- Each payout must be reconciled separately
- Bills are marked as paid individually
- Reconciliation is required for each payout

**Bulk payouts do not change reconciliation requirements. Each payout must be reconciled.**

## Related Documentation

- [Bill State Lifecycle](../states/bill_state_lifecycle.md) — Bill states
- [Payout State Lifecycle](../states/payout_state_lifecycle.md) — Payout states
- [Reconciliation Flow](./reconciliation_flow.md) — Reconciliation process
- [Reconciliation Logic](../data_semantics/reconciliation_logic.md) — Reconciliation meaning
- [Financial Finality Rules](../principles/financial_finality_rules.md) — When money is final
- [Handling Failed Payouts](../decisions/handling_failed_payouts.md) — Payout failure handling

