# Data Ownership & Limitations

Understanding data ownership is critical to using Open Money correctly.

## Data Sources

| Data Type | Owned By | Authority Level |
|---------|----------|----------------|
| Bank Balance | Bank | Absolute |
| Payment Status | Payment Rail | Transactional |
| Invoice Status | Open Money | Document |
| Cashflow Charts | Open Money | Derived |
| GST IRN | Government (IRP) | Compliance |
| Outstanding Amount | Open Money | Computed |
| Overdue Days | Open Money | Computed |

## Derived Data Warning

Most values shown in Open Money are **derived**, not primary.

Examples:
- Outstanding amount
- Overdue days
- Cashflow projections
- Net balance across accounts
- Collection efficiency metrics

Derived data can be:
- Temporarily incorrect
- Delayed
- Incomplete without reconciliation

## Sample Data Mode

When sample data is enabled:
- No data reflects real money
- No compliance data is valid
- No reconciliation should be trusted
- No financial decisions should be based on it

Sample data exists **only for demonstration**.

## Technical Limitations

Open Money has the following technical limitations:
- Cannot detect missed webhooks from payment rails
- Cannot guarantee bank sync timing (depends on bank API availability)
- Cannot prevent user misinterpretation of dashboards
- Cannot override bank statement data (bank statements remain authoritative)
- Cannot replace accounting systems (it integrates with them)

**Note:** Open Money is a licensed Payment Aggregator (PA) under RBI and is liable for settlements. Transaction statuses (success/failed) are accurate and reliable. For pending transactions, status updates depend on bank callbacks.

## Data Freshness

Open Money data freshness depends on:

1. **Bank Sync Frequency**
   - Not real-time
   - May be delayed by hours or days
   - May fail silently

2. **Webhook Delivery**
   - May be delayed
   - May fail to deliver
   - May be processed out of order

3. **Reconciliation Status**
   - Unreconciled data is provisional
   - Only reconciled data is confirmed
   - Reconciliation may lag behind transactions

## What Open Money Owns

Open Money owns:
- Document records (invoices, bills)
- Payment link configurations
- User workflows and preferences
- Reconciliation mappings
- Derived calculations

## What Open Money Does NOT Own

Open Money does not own:
- Bank balances
- Payment finality
- Tax authority data
- Accounting records
- Regulatory compliance data

## Interpretation Rules

When interpreting Open Money data:

1. **Always ask:** Where did this data come from?
2. **Always ask:** When was it last synced?
3. **Always ask:** Has it been reconciled?
4. **Always verify:** Critical decisions against source systems

## Common Misinterpretations

### Misinterpretation 1: Balance Authority

**Wrong:** "Open Money shows ₹X, so I have ₹X."

**Correct:** "Open Money shows ₹X derived from bank sync. Verify against bank statement."

### Misinterpretation 2: Payment Finality

**Wrong:** "Payment shows success in Open Money, so it's final."

**Correct:** "Payment shows success in Open Money, which means the transaction has been successfully processed and settled by Open Money (as a licensed Payment Aggregator). For pending transactions, cross-check with your bank as Open Money's status is updated based on bank callbacks."

### Misinterpretation 3: Overdue Accuracy

**Wrong:** "Invoice shows 600 days overdue, so customer hasn't paid."

**Correct:** "Invoice shows 600 days overdue based on due date. Verify payment status and reconciliation."

## Mitigation Strategies

To use Open Money data safely:

1. **Reconcile regularly** — Match Open Money data with bank statements
2. **Verify critical decisions** — Always check source systems
3. **Understand data source** — Know where each value comes from
4. **Check sync status** — Verify when data was last updated
5. **Use reconciliation flags** — Only trust reconciled data for critical operations

## Related Documentation

- [Derived vs Actual Balances](../data_semantics/derived_vs_actual_balances.md) — Balance interpretation
- [Reconciliation Logic](../data_semantics/reconciliation_logic.md) — Reconciliation meaning
- [Dashboard Misinterpretation](../risks/dashboard_misinterpretation.md) — Dashboard risks
- [Stale Bank Data](../risks/stale_bank_data.md) — Bank sync risks

