# Reconciliation Flow

## Overview

This document describes the **complete system-level flow** for reconciliation in Open Money. Reconciliation is the process of matching documents, payments, and bank entries to ensure financial accuracy.

## Flow Diagram

```
Data Gathering → Matching → Verification → Discrepancy Detection → Resolution → Confirmation
```

## Step-by-Step Flow

### Step 1: Data Gathering

**What happens:**
- Documents are collected from Open Money
- Payments are collected from payment rails
- Bank entries are collected from bank statements
- All data is prepared for matching

**Data sources:**
- Open Money: Invoices, bills, payment links
- Payment rails: Payment statuses, transaction IDs
- Banks: Bank statements, transaction entries

**What you do:**
- Collect all documents
- Collect all payments
- Collect all bank entries
- Prepare data for matching

**What to store:**
- Document list
- Payment list
- Bank entry list
- Data collection timestamp

---

### Step 2: Matching

**What happens:**
- Documents are matched with payments
- Payments are matched with bank entries
- All records are linked together

**Matching process:**
- Link invoice to payment
- Link payment to bank credit
- Link bill to payout
- Link payout to bank debit
- Verify all links are correct

**What you do:**
- Match documents to payments
- Match payments to bank entries
- Create reconciliation records
- Verify all matches are correct

**What to store:**
- Matched records
- Reconciliation links
- Matching timestamps
- Matching confidence scores

---

### Step 3: Verification

**What happens:**
- Amounts are verified to match
- Dates are verified to align
- All details are checked

**Verification process:**
- Verify document amount = payment amount
- Verify payment amount = bank entry amount
- Verify dates are reasonable
- Verify all details match

**What you do:**
- Verify amounts match
- Verify dates align
- Check all details
- Confirm accuracy

**What to store:**
- Verification status
- Verification results
- Verification timestamp
- Verified records

---

### Step 4: Discrepancy Detection

**What happens:**
- Discrepancies are identified
- Mismatches are flagged
- Issues are detected

**Discrepancy types:**
- Amount mismatches
- Missing payments
- Missing bank entries
- Duplicate entries
- Timing differences

**What you do:**
- Identify discrepancies
- Flag mismatches
- Document issues
- Prepare for resolution

**What to store:**
- Discrepancy list
- Discrepancy types
- Discrepancy details
- Detection timestamp

---

### Step 5: Resolution

**What happens:**
- Discrepancies are investigated
- Issues are resolved
- Records are corrected

**Resolution process:**
- Investigate discrepancy cause
- Verify source data
- Correct records if needed
- Update reconciliation status

**What you do:**
- Investigate discrepancies
- Verify source data
- Correct records
- Update status

**What to store:**
- Resolution actions
- Resolution results
- Resolution timestamp
- Updated records

---

### Step 6: Confirmation

**What happens:**
- Reconciliation is confirmed
- All records are verified
- Reconciliation status is updated

**Confirmation process:**
- Verify all records are matched
- Confirm all amounts match
- Confirm no discrepancies remain
- Update reconciliation status

**What you do:**
- Confirm reconciliation
- Update status
- Close reconciliation
- Document completion

**What to store:**
- Reconciliation status: `reconciled`
- Confirmation timestamp
- Reconciliation summary
- Final records

---

## Reconciliation Types

### Document-to-Payment Reconciliation

**Purpose:** Match documents (invoices, bills) with payments.

**Process:**
- Link invoice to payment
- Link bill to payout
- Verify amounts match
- Confirm payment status

### Payment-to-Bank Reconciliation

**Purpose:** Match payments with bank entries.

**Process:**
- Link payment to bank credit
- Link payout to bank debit
- Verify amounts match
- Confirm bank settlement

### Full Reconciliation

**Purpose:** Match documents, payments, and bank entries together.

**Process:**
- Link document to payment
- Link payment to bank entry
- Verify all amounts match
- Confirm complete alignment

## Reconciliation Status

### `pending`

**Meaning:** Reconciliation has not been performed.

**What it means:**
- Records are not reconciled
- Matching has not been done
- Verification is pending
- Reconciliation is required

### `in_progress`

**Meaning:** Reconciliation is being performed.

**What it means:**
- Reconciliation is ongoing
- Matching is in progress
- Verification is being done
- Not yet complete

### `reconciled`

**Meaning:** Reconciliation is complete and verified.

**What it means:**
- All records are matched
- All amounts match
- No discrepancies exist
- Reconciliation is confirmed

### `discrepancy`

**Meaning:** Discrepancies were found during reconciliation.

**What it means:**
- Mismatches were detected
- Issues need resolution
- Reconciliation is incomplete
- Resolution is required

## Critical Checkpoints

### ✅ Must Do:

1. **Gather all data** — Collect documents, payments, and bank entries
2. **Match all records** — Link documents to payments to bank entries
3. **Verify amounts** — Ensure all amounts match
4. **Detect discrepancies** — Identify all mismatches
5. **Resolve issues** — Fix all discrepancies
6. **Confirm reconciliation** — Verify all records are reconciled

### ❌ Must NOT Do:

1. **Don't skip reconciliation** — It is mandatory
2. **Don't assume matches** — Always verify
3. **Don't ignore discrepancies** — Resolve all issues
4. **Don't mark as reconciled** — Until all records are verified
5. **Don't trust dashboard alone** — Verify against source systems

## Common Discrepancies

### Discrepancy 1: Amount Mismatch

**What happens:**
- Document amount ≠ Payment amount
- Payment amount ≠ Bank entry amount

**What to do:**
- Investigate mismatch cause
- Verify source data
- Correct records if needed
- Update reconciliation

### Discrepancy 2: Missing Payment

**What happens:**
- Document exists but no payment
- Payment expected but not found

**What to do:**
- Verify payment status
- Check payment rail
- Verify bank entry
- Update records

### Discrepancy 3: Missing Bank Entry

**What happens:**
- Payment exists but no bank entry
- Bank entry expected but not found

**What to do:**
- Wait for bank settlement
- Check bank statement
- Verify bank sync
- Update records

### Discrepancy 4: Duplicate Entry

**What happens:**
- Same payment recorded twice
- Same bank entry matched twice

**What to do:**
- Identify duplicate
- Remove duplicate entry
- Update reconciliation
- Verify accuracy

## Reconciliation Frequency

### Daily Reconciliation

**When:** For active businesses with high transaction volume.

**Purpose:** Catch discrepancies early, maintain accuracy.

### Weekly Reconciliation

**When:** For moderate activity businesses.

**Purpose:** Regular verification, manageable volume.

### Monthly Reconciliation

**When:** For low activity businesses.

**Purpose:** Periodic verification, compliance requirement.

## Related Documentation

- [Reconciliation Logic](../data_semantics/reconciliation_logic.md) — Reconciliation meaning
- [Reconciliation Is Not Optional](../principles/reconciliation_is_not_optional.md) — Reconciliation requirement
- [Reconciliation Gaps](../risks/reconciliation_gaps.md) — Reconciliation risks
- [When to Reconcile](../decisions/when_to_reconcile.md) — Reconciliation timing

