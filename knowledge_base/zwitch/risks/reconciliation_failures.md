# Reconciliation Failures: Detecting and Resolving Discrepancies

## Overview

**Reconciliation** is the process of comparing your internal records with Zwitch's records to ensure they match. Reconciliation failures indicate discrepancies that need to be resolved.

## What is Reconciliation?

**Reconciliation** means:
- Comparing your database with Zwitch API data
- Identifying mismatches (payments marked differently)
- Resolving discrepancies
- Ensuring data consistency

**Why it matters:**
- Catches missed webhooks
- Detects processing errors
- Prevents financial discrepancies
- Ensures audit trail accuracy

## Common Reconciliation Failures

### 1. Payment Status Mismatch

**Scenario:**
- Zwitch shows: `payment.completed`
- Your database shows: `payment.pending`
- **Discrepancy:** Payment completed but not processed

**Causes:**
- Webhook was missed (server down, network issue)
- Webhook processing failed (database error, etc.)
- Webhook not configured

**Resolution:**
- Process payment completion (with idempotency check)
- Update database
- Log reconciliation fix

### 2. Transfer Status Mismatch

**Scenario:**
- Zwitch shows: `transfer.completed`
- Your database shows: `transfer.processing`
- **Discrepancy:** Transfer completed but not updated

**Causes:**
- Webhook was missed
- Webhook processing failed
- Manual transfer not tracked

**Resolution:**
- Update transfer status
- Update settlement/refund records
- Notify affected parties

### 3. Amount Mismatch

**Scenario:**
- Zwitch shows: Payment amount ₹1000
- Your database shows: Payment amount ₹1000.50
- **Discrepancy:** Amount recorded incorrectly

**Causes:**
- Data entry error
- Calculation error
- Currency conversion error

**Resolution:**
- Investigate source of error
- Correct database record
- Verify with original order

### 4. Missing Payments

**Scenario:**
- Zwitch shows: Payment `pay_abc123` exists
- Your database shows: Payment `pay_abc123` doesn't exist
- **Discrepancy:** Payment not recorded

**Causes:**
- Payment created outside your system
- Database insert failed
- Payment created manually

**Resolution:**
- Create payment record in database
- Link to order (if possible)
- Process payment (if completed)

### 5. Duplicate Payments

**Scenario:**
- Zwitch shows: One payment `pay_abc123`
- Your database shows: Two records for `pay_abc123`
- **Discrepancy:** Duplicate records

**Causes:**
- Duplicate processing
- Database insert error
- Reconciliation created duplicate

**Resolution:**
- Remove duplicate record
- Verify only one processing
- Check for double credits

## Reconciliation Process

### Step 1: Fetch Data from Zwitch

**Get all payments/transfers for period:**

```python
def fetch_zwitch_payments(start_date, end_date):
    payments = []
    page = 1
    
    while True:
        response = zwitch_api.get_payments(
            from_date=start_date,
            to_date=end_date,
            page=page,
            limit=100
        )
        
        payments.extend(response.data)
        
        if page >= response.pagination.total_pages:
            break
        page += 1
    
    return payments
```

### Step 2: Compare with Your Database

**Compare each payment:**

```python
def reconcile_payments(start_date, end_date):
    zwitch_payments = fetch_zwitch_payments(start_date, end_date)
    discrepancies = []
    
    for zwitch_payment in zwitch_payments:
        local_payment = db.get_payment(zwitch_payment.id)
        
        if not local_payment:
            # Missing payment
            discrepancies.append({
                'type': 'missing',
                'payment_id': zwitch_payment.id,
                'zwitch_status': zwitch_payment.status,
                'local_status': None
            })
        elif local_payment.status != zwitch_payment.status:
            # Status mismatch
            discrepancies.append({
                'type': 'status_mismatch',
                'payment_id': zwitch_payment.id,
                'zwitch_status': zwitch_payment.status,
                'local_status': local_payment.status
            })
        elif local_payment.amount != zwitch_payment.amount:
            # Amount mismatch
            discrepancies.append({
                'type': 'amount_mismatch',
                'payment_id': zwitch_payment.id,
                'zwitch_amount': zwitch_payment.amount,
                'local_amount': local_payment.amount
            })
    
    return discrepancies
```

### Step 3: Resolve Discrepancies

**Process each discrepancy:**

```python
def resolve_discrepancy(discrepancy):
    payment_id = discrepancy['payment_id']
    
    if discrepancy['type'] == 'missing':
        # Create payment record
        zwitch_payment = zwitch_api.get_payment(payment_id)
        db.create_payment(zwitch_payment)
        
        # Process if completed
        if zwitch_payment.status == 'completed':
            process_payment_completed(payment_id)  # With idempotency check
    
    elif discrepancy['type'] == 'status_mismatch':
        # Update status
        zwitch_payment = zwitch_api.get_payment(payment_id)
        db.update_payment_status(payment_id, zwitch_payment.status)
        
        # Process if now completed
        if zwitch_payment.status == 'completed':
            process_payment_completed(payment_id)  # With idempotency check
    
    elif discrepancy['type'] == 'amount_mismatch':
        # Investigate and correct
        log_amount_mismatch(discrepancy)
        # Manual review may be needed
        alert_operations_team(discrepancy)
```

## Reconciliation Schedule

### Recommended Frequency:

**Recent Payments (< 24 hours):**
- Every 1-2 hours
- Catch missed webhooks quickly
- Resolve before customer impact

**Older Payments (1-7 days):**
- Daily
- Catch any missed issues
- Maintain data consistency

**Historical Reconciliation:**
- Weekly or monthly
- Full reconciliation
- Audit trail verification

### Implementation:

```python
# Scheduled job (cron)
def scheduled_reconciliation():
    # Recent payments (last 24 hours)
    recent_start = datetime.now() - timedelta(hours=24)
    recent_discrepancies = reconcile_payments(recent_start, datetime.now())
    
    for discrepancy in recent_discrepancies:
        resolve_discrepancy(discrepancy)
    
    # Older payments (last 7 days, daily check)
    if datetime.now().hour == 2:  # Run at 2 AM
        older_start = datetime.now() - timedelta(days=7)
        older_discrepancies = reconcile_payments(older_start, datetime.now())
        
        for discrepancy in older_discrepancies:
            resolve_discrepancy(discrepancy)
```

## Handling Reconciliation Results

### Automatic Resolution:

**For safe discrepancies:**
- Missing payments (create record)
- Status mismatches (update status)
- Process with idempotency checks

### Manual Review Required:

**For risky discrepancies:**
- Amount mismatches (investigate source)
- Duplicate payments (check for double credits)
- Unusual patterns (potential fraud)

### Alerting:

```python
def handle_reconciliation_results(discrepancies):
    for discrepancy in discrepancies:
        if discrepancy['type'] in ['amount_mismatch', 'duplicate']:
            # High priority - manual review
            alert_operations_team(discrepancy, priority='high')
        else:
            # Auto-resolve
            resolve_discrepancy(discrepancy)
            log_reconciliation_fix(discrepancy)
```

## Database Schema for Reconciliation

```sql
-- Reconciliation runs
CREATE TABLE reconciliation_runs (
  run_id VARCHAR(255) PRIMARY KEY,
  start_date TIMESTAMP,
  end_date TIMESTAMP,
  discrepancies_found INT,
  discrepancies_resolved INT,
  status VARCHAR(50),  -- running, completed, failed
  started_at TIMESTAMP,
  completed_at TIMESTAMP
);

-- Reconciliation discrepancies
CREATE TABLE reconciliation_discrepancies (
  discrepancy_id VARCHAR(255) PRIMARY KEY,
  run_id VARCHAR(255),
  payment_id VARCHAR(255),
  discrepancy_type VARCHAR(50),  -- missing, status_mismatch, amount_mismatch, duplicate
  zwitch_data JSONB,
  local_data JSONB,
  status VARCHAR(50),  -- pending, resolved, requires_manual_review
  resolved_at TIMESTAMP,
  resolution_notes TEXT,
  FOREIGN KEY (run_id) REFERENCES reconciliation_runs(run_id)
);
```

## Best Practices

### ✅ Do:
1. **Run reconciliation regularly** (hourly for recent, daily for older)
2. **Resolve discrepancies automatically** when safe
3. **Log all reconciliation actions** (audit trail)
4. **Alert on high-priority discrepancies** (amount mismatches, duplicates)
5. **Use idempotency checks** when resolving (prevent double processing)
6. **Monitor reconciliation results** (track resolution rate)
7. **Investigate root causes** (why discrepancies occurred)

### ❌ Don't:
1. **Don't skip reconciliation** (critical for data consistency)
2. **Don't auto-resolve risky discrepancies** (amount mismatches need review)
3. **Don't ignore reconciliation failures** (they indicate problems)
4. **Don't resolve without idempotency** (may cause double processing)
5. **Don't delete records** during reconciliation (keep audit trail)

## Monitoring

**Track reconciliation metrics:**
- Number of discrepancies found
- Resolution rate
- Types of discrepancies
- Time to resolve
- Root causes

**Alert on:**
- High discrepancy rate (indicates systemic issue)
- Amount mismatches (financial risk)
- Duplicate payments (double credit risk)
- Reconciliation failures (process issue)

## Summary

- **Reconciliation is essential** for data consistency
- **Run regularly** (hourly for recent, daily for older)
- **Resolve automatically** when safe (with idempotency)
- **Manual review** for risky discrepancies
- **Log everything** (audit trail)
- **Monitor metrics** (track health)

**Bottom line:** Reconciliation catches issues that webhooks might miss. It's a safety net, not a replacement for webhooks.

## Related Documentation

- [Polling vs Webhooks](../decisions/polling_vs_webhooks.md) - Reconciliation as fallback
- [Double Credit Risk](./double_credit_risk.md) - Preventing duplicates
- [Retries and Idempotency](../decisions/retries_and_idempotency.md) - Safe resolution

