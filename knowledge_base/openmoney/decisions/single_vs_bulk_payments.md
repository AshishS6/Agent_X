# Single vs Bulk Payments: When to Use Each

## Recommendation

**Use single payments for individual transactions. Use bulk payments for batch processing of multiple transactions.**

This is not just a preference—it's a best practice for managing payments efficiently.

## When to Use Single Payments

### ✅ Use Single Payments For:

1. **Individual Transactions**
   - One invoice at a time
   - One payment link at a time
   - Individual customer payments
   - One-off transactions

2. **Immediate Processing**
   - Urgent payments
   - Time-sensitive transactions
   - Immediate collection needs
   - Quick processing

3. **Error Handling**
   - When errors need individual attention
   - When transactions need verification
   - When manual review is required
   - When precision is critical

4. **Low Volume**
   - Few transactions
   - Occasional payments
   - Manual processing acceptable
   - No batch processing needed

### Why Single Payments Are Preferred for Individual Transactions

- **Precision** — Each transaction is handled individually
- **Error handling** — Errors are caught and handled per transaction
- **Verification** — Each transaction can be verified separately
- **Control** — Full control over each transaction

## When to Use Bulk Payments

### ✅ Use Bulk Payments For:

1. **Batch Processing**
   - Multiple invoices at once
   - Multiple payment links at once
   - Batch collections
   - Batch payouts

2. **High Volume**
   - Many transactions
   - Regular batch processing
   - Automated processing
   - Efficiency needed

3. **Efficiency**
   - Time-saving
   - Reduced manual work
   - Automated workflows
   - Streamlined processing

4. **Consistent Processing**
   - Same process for all transactions
   - No individual variations
   - Standardized handling
   - Predictable outcomes

### Why Bulk Payments Are Preferred for Batch Processing

- **Efficiency** — Process multiple transactions at once
- **Time-saving** — Reduced manual work
- **Automation** — Can be automated
- **Scalability** — Handles high volume

## Decision Matrix

| Scenario | Use Single? | Use Bulk? |
|----------|------------|----------|
| One transaction | ✅ Yes | ❌ No |
| Multiple transactions | ❌ No | ✅ Yes |
| Urgent payment | ✅ Yes | ❌ No |
| Batch processing | ❌ No | ✅ Yes |
| Error handling needed | ✅ Yes | ⚠️ Depends |
| High volume | ❌ No | ✅ Yes |
| Low volume | ✅ Yes | ❌ No |
| Automated processing | ❌ No | ✅ Yes |

## What NOT to Do

### ❌ Don't Use Single Payments For:

1. **High Volume Batch Processing**
   - Don't process hundreds of transactions individually
   - Don't waste time on manual batch processing
   - Don't skip bulk processing when available

2. **Consistent Batch Operations**
   - Don't use single payments for regular batch operations
   - Don't ignore bulk payment capabilities

### ❌ Don't Use Bulk Payments For:

1. **Individual Critical Transactions**
   - Don't use bulk for urgent individual payments
   - Don't mix critical and non-critical in bulk
   - Don't skip individual verification for critical transactions

2. **Error-Prone Transactions**
   - Don't use bulk when errors need individual attention
   - Don't process error-prone transactions in bulk
   - Don't skip individual verification for error-prone transactions

## Bulk Payment Processing

### Individual Item Processing

Bulk payments process items individually:
- Each item is processed separately
- Each item has its own status
- Each item can succeed or fail independently
- Failures don't affect other items

### Reconciliation Requirements

Each item in bulk payment must be reconciled:
- Reconcile each item separately
- Verify each item individually
- Handle failures per item
- Complete reconciliation for all items

**Bulk payments do not change reconciliation requirements. Each item must be reconciled.**

## Common Mistakes

### ❌ Mistake 1: Using Single for High Volume

**Wrong:** "I'll process 100 invoices one by one."

**Correct:** "Use bulk processing for high volume. Single payments are for individual transactions."

### ❌ Mistake 2: Using Bulk for Critical Transactions

**Wrong:** "I'll include urgent payment in bulk batch."

**Correct:** "Process critical transactions individually. Bulk payments are for non-critical batch processing."

### ❌ Mistake 3: Assuming Bulk Success

**Wrong:** "Bulk payment shows success, so all items are successful."

**Correct:** "Bulk payment processes items individually. Verify each item status separately."

## Best Practices

### For Single Payments

1. **Verify before processing** — Check details before processing
2. **Monitor individually** — Track each transaction separately
3. **Handle errors immediately** — Address errors as they occur
4. **Reconcile individually** — Reconcile each transaction

### For Bulk Payments

1. **Verify batch data** — Check batch data before processing
2. **Monitor individual items** — Track each item separately
3. **Handle failures individually** — Address failures per item
4. **Reconcile per item** — Reconcile each item separately

## Summary

- **Single Payments:** Use for individual transactions, urgent payments, and error handling
- **Bulk Payments:** Use for batch processing, high volume, and efficiency
- **Reconciliation:** Required for both, but each item in bulk must be reconciled separately
- **Error Handling:** Individual for single, per-item for bulk

**Bottom line:** Choose based on transaction volume and processing needs. Single for individual, bulk for batch.

## Related Documentation

- [Bulk Collection Flow](../workflows/bulk_collection_flow.md) — Bulk collection process
- [Invoice State Lifecycle](../states/invoice_state_lifecycle.md) — Invoice states
- [Payment Link State Lifecycle](../states/payment_link_state_lifecycle.md) — Payment link states
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process

