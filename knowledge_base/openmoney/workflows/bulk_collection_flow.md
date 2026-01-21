# Bulk Collection Flow

## Overview

This document describes the **complete system-level flow** for bulk collection operations in Open Money. This covers creating multiple payment links or invoices and processing them in bulk.

## Flow Diagram

```
Bulk Creation → Individual Processing → Payment Collection → Bank Settlement → Reconciliation → Bulk Status Update
```

## Step-by-Step Flow

### Step 1: Bulk Creation

**What happens:**
- Multiple payment links or invoices are created
- Bulk operation is initiated
- Individual items are created

**Bulk creation methods:**
- CSV/XLS upload
- API bulk creation
- Batch processing

**What you do:**
- Prepare bulk data
- Upload or submit bulk request
- Monitor bulk creation status

**What to store:**
- Bulk operation ID
- Individual item IDs
- Bulk creation status
- Individual item statuses

---

### Step 2: Individual Item Processing

**What happens:**
- Each item is processed individually
- Items are created one by one
- Each item has its own status

**Individual processing:**
- Each payment link/invoice is independent
- Each has its own ID
- Each has its own status
- Processing may succeed or fail for individual items

**What you do:**
- Monitor individual item creation
- Handle creation failures
- Track item statuses

**What to store:**
- Individual item IDs
- Individual item statuses
- Creation timestamps
- Failure reasons (if any)

---

### Step 3: Payment Collection (Per Item)

**What happens:**
- Each item is collected independently
- Customers pay individual items
- Payments are processed separately

**Payment collection:**
- Each payment link/invoice is paid separately
- Each payment has its own status
- Payments may succeed or fail independently

**What you do:**
- Monitor individual payments
- Track payment statuses
- Handle payment failures

**What to store:**
- Individual payment IDs
- Individual payment statuses
- Payment timestamps
- Payment amounts

---

### Step 4: Bank Settlement (Per Payment)

**What happens:**
- Each payment settles independently
- Bank receives payments separately
- Bank statement shows individual credits

**Bank settlement:**
- Each payment appears in bank statement separately
- Each credit is independent
- Settlement timing may vary per payment

**What you do:**
- Monitor bank settlement per payment
- Track bank entries
- Wait for all payments to settle

**What to store:**
- Individual bank transaction IDs
- Individual bank settlement timestamps
- Bank credit amounts per payment

---

### Step 5: Reconciliation (Per Item)

**What happens:**
- Each item is reconciled individually
- Reconciliation is performed per payment
- Items are reconciled independently

**Reconciliation process:**
- Link each item to its payment
- Link each payment to its bank entry
- Verify amounts match per item
- Reconcile each item separately

**What you do:**
- Reconcile each item individually
- Verify amounts per item
- Resolve discrepancies per item
- Update item statuses

**What to store:**
- Reconciliation status per item
- Reconciliation timestamps per item
- Matched records per item

---

### Step 6: Bulk Status Update

**What happens:**
- Individual item statuses are aggregated
- Bulk operation status is updated
- Overall status is computed

**Bulk status:**
- Based on individual item statuses
- Shows overall progress
- Indicates completion status

**What you do:**
- Monitor bulk status
- Track overall progress
- Handle remaining items

**What to store:**
- Bulk operation status
- Overall progress
- Completed items count
- Remaining items count

---

## Critical Checkpoints

### ✅ Must Do:

1. **Process items individually** — Each item is independent
2. **Reconcile per item** — Reconciliation is required for each item
3. **Track individual statuses** — Monitor each item separately
4. **Handle failures individually** — Failures don't affect other items
5. **Verify amounts per item** — Each item must be verified separately

### ❌ Must NOT Do:

1. **Don't assume bulk success** — Individual items may fail
2. **Don't skip reconciliation** — Each item must be reconciled
3. **Don't aggregate before reconciliation** — Reconcile individually first
4. **Don't trust bulk status alone** — Verify individual item statuses
5. **Don't mark all as paid** — Mark items individually after reconciliation

## Bulk Status States

### `processing`

**Meaning:** Bulk operation is in progress.

**What it means:**
- Items are being created or processed
- Some items may be complete
- Some items may be pending
- Overall operation is not complete

### `partially_complete`

**Meaning:** Some items are complete, some are pending.

**What it means:**
- Some items are paid/reconciled
- Some items are still pending
- Operation is not fully complete
- Individual item statuses vary

### `complete`

**Meaning:** All items are complete.

**What it means:**
- All items are paid/reconciled
- All items are processed
- Operation is fully complete
- No pending items remain

### `failed`

**Meaning:** Bulk operation failed.

**What it means:**
- Operation could not be completed
- Some or all items failed
- Individual item statuses show failures
- Operation needs to be retried or fixed

## Common Failure Points

### Failure Point 1: Individual Item Creation Failure

**What happens:**
- Some items fail to create
- Bulk operation shows partial success
- Some items are created, some are not

**What to do:**
- Review failure reasons
- Retry failed items
- Process successful items
- Handle failures individually

### Failure Point 2: Individual Payment Failure

**What happens:**
- Some payments succeed, some fail
- Bulk status shows partial completion
- Individual item statuses vary

**What to do:**
- Monitor individual payment statuses
- Handle payment failures individually
- Process successful payments
- Retry failed payments if appropriate

### Failure Point 3: Partial Reconciliation

**What happens:**
- Some items are reconciled, some are not
- Bulk status shows partial completion
- Some items are paid, some are pending

**What to do:**
- Reconcile items individually
- Process reconciled items
- Wait for pending items to settle
- Complete reconciliation for all items

## Best Practices

### 1. Monitor Individual Items

- Track each item separately
- Don't rely on bulk status alone
- Verify individual item statuses
- Handle items individually

### 2. Reconcile Per Item

- Reconcile each item separately
- Don't aggregate before reconciliation
- Verify amounts per item
- Complete reconciliation for all items

### 3. Handle Failures Individually

- Failures don't affect other items
- Handle each failure separately
- Retry failed items individually
- Process successful items independently

### 4. Verify Before Aggregating

- Verify individual item statuses
- Reconcile all items before aggregating
- Don't assume bulk success
- Confirm all items are complete

## Related Documentation

- [Payment Link State Lifecycle](../states/payment_link_state_lifecycle.md) — Payment link states
- [Invoice State Lifecycle](../states/invoice_state_lifecycle.md) — Invoice states
- [Reconciliation Flow](./reconciliation_flow.md) — Reconciliation process
- [Reconciliation Logic](../data_semantics/reconciliation_logic.md) — Reconciliation meaning
- [Single vs Bulk Payments](../decisions/single_vs_bulk_payments.md) — Bulk payment guidance

