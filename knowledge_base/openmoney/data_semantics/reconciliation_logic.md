# Reconciliation Logic

## Overview

Reconciliation is the process of matching documents, payments, and bank entries to ensure financial accuracy. Understanding reconciliation logic is critical for using Open Money correctly.

## What Reconciliation Means

Reconciliation means:
- Matching documents to payments
- Matching payments to bank entries
- Verifying amounts match
- Confirming alignment between all records

**Reconciliation is the only way to confirm financial accuracy.**

## Why Reconciliation Is Required

Reconciliation is required because:
- Data comes from multiple sources
- Data may be delayed or incomplete
- Data may have errors or discrepancies
- Financial accuracy requires verification

**Without reconciliation, financial data is provisional and may be inaccurate.**

## Reconciliation Process

### Step 1: Match Documents to Payments

**Purpose:** Link documents (invoices, bills) with payments.

**Process:**
- Find payment for each document
- Verify payment amount matches document amount
- Confirm payment status
- Link document to payment

**Result:** Documents are linked to payments.

### Step 2: Match Payments to Bank Entries

**Purpose:** Link payments with bank entries.

**Process:**
- Find bank entry for each payment
- Verify bank entry amount matches payment amount
- Confirm bank settlement
- Link payment to bank entry

**Result:** Payments are linked to bank entries.

### Step 3: Verify Amounts Match

**Purpose:** Ensure all amounts align.

**Process:**
- Verify document amount = payment amount
- Verify payment amount = bank entry amount
- Confirm all amounts match
- Identify any discrepancies

**Result:** All amounts are verified.

### Step 4: Confirm Reconciliation

**Purpose:** Confirm reconciliation is complete.

**Process:**
- Verify all records are matched
- Confirm no discrepancies remain
- Update reconciliation status
- Document reconciliation completion

**Result:** Reconciliation is confirmed.

## Reconciliation Status

### `pending`

**Meaning:** Reconciliation has not been performed.

**What it means:**
- Records are not reconciled
- Matching has not been done
- Verification is pending
- Reconciliation is required

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

## What Reconciliation Confirms

Reconciliation confirms:
- Documents are paid (or not paid)
- Payments are received (or not received)
- Bank entries match payments
- All amounts align
- No discrepancies exist

**Reconciliation is the only way to confirm these facts.**

## What Reconciliation Does NOT Confirm

Reconciliation does NOT confirm:
- Payment finality (requires bank confirmation)
- Compliance (requires tax authority confirmation)
- Accounting accuracy (requires accounting verification)
- Legal validity (requires legal verification)

**Reconciliation confirms alignment, not finality or compliance.**

## Common Misinterpretations

### Misinterpretation 1: Reconciliation = Finality

**Wrong:** "Reconciliation is done, so payment is final."

**Correct:** "Reconciliation confirms alignment between records. Finality requires bank confirmation."

### Misinterpretation 2: Reconciled = Accurate

**Wrong:** "Records are reconciled, so all data is accurate."

**Correct:** "Reconciliation confirms alignment. Accuracy requires verification against source systems."

### Misinterpretation 3: No Reconciliation = No Issues

**Wrong:** "No reconciliation needed, everything looks correct."

**Correct:** "Reconciliation is mandatory. Without reconciliation, data accuracy cannot be confirmed."

## Reconciliation Frequency

Reconciliation should be performed:
- **Daily** for active businesses
- **Weekly** for moderate activity
- **Monthly** for low activity
- **Before financial reporting**
- **Before tax filing**

**Reconciliation frequency depends on business activity and risk tolerance.**

## Reconciliation Requirements

Reconciliation requires:
- Access to bank statements
- Access to payment records
- Access to document records
- Time to perform reconciliation
- Tools to match records

**Without these requirements, reconciliation cannot be performed.**

## Related Documentation

- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Reconciliation Is Not Optional](../principles/reconciliation_is_not_optional.md) — Reconciliation requirement
- [Reconciliation Gaps](../risks/reconciliation_gaps.md) — Reconciliation risks
- [When to Reconcile](../decisions/when_to_reconcile.md) — Reconciliation timing

