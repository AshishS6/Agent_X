# Double Credit Risk: Preventing Duplicate Money Movement

## Overview

**Double credit risk** is the danger of crediting a customer's account or marking a payment as successful **twice** for the same transaction. This is a critical financial risk that can cause significant losses.

## What is Double Credit?

**Double credit** occurs when:
- Same payment is processed twice
- Customer receives credit twice for one payment
- Order is fulfilled twice for one payment
- Money is credited when it shouldn't be

**Example:**
- Customer pays ₹1000 once
- Your system marks order as paid twice
- Customer receives product twice (or credit twice)
- You lose ₹1000

## Common Causes

### 1. Duplicate Webhook Processing

**Scenario:**
- Zwitch sends `payment.completed` webhook
- Your server processes it
- Zwitch retries webhook (your server was slow to respond)
- Your server processes it again
- **Result:** Payment processed twice

**Prevention:**
- Implement idempotency checks
- Store processed webhook events
- See [Retries and Idempotency](../decisions/retries_and_idempotency.md)

### 2. Webhook + Polling Both Process Same Payment

**Scenario:**
- Webhook arrives and processes payment
- Polling job also checks same payment
- Both mark payment as completed
- **Result:** Payment processed twice

**Prevention:**
- Use webhooks as primary source
- Use polling only for reconciliation
- Check idempotency in both paths
- See [Polling vs Webhooks](../decisions/polling_vs_webhooks.md)

### 3. Race Conditions

**Scenario:**
- Two webhook handlers process same event simultaneously
- Both check "not processed" at same time
- Both process payment
- **Result:** Payment processed twice

**Prevention:**
- Use database transactions with locks
- Use atomic operations (e.g., `INSERT ... ON CONFLICT`)
- Implement proper concurrency control

### 4. Manual Intervention Errors

**Scenario:**
- Payment webhook failed to process
- Admin manually marks payment as completed
- Webhook retry arrives later
- System processes webhook again
- **Result:** Payment processed twice

**Prevention:**
- Always check idempotency, even for manual operations
- Log all manual interventions
- Prevent manual operations if already processed

### 5. Reconciliation Errors

**Scenario:**
- Reconciliation job finds payment not marked as completed
- Marks payment as completed
- Webhook arrives later (was delayed)
- Processes webhook
- **Result:** Payment processed twice

**Prevention:**
- Reconciliation should also check idempotency
- Use same processing logic as webhooks
- Mark reconciliation source in database

## Prevention Strategies

### 1. Idempotency Checks (Mandatory)

**Always check if payment already processed:**

```python
def process_payment_completed(payment_id):
    # Idempotency check
    if db.is_payment_processed(payment_id):
        return  # Already processed, skip
    
    # Process payment
    mark_order_as_paid(payment_id)
    update_inventory(payment_id)
    send_confirmation(payment_id)
    
    # Mark as processed
    db.mark_payment_processed(payment_id)
```

**Database check:**
```sql
-- Check if already processed
SELECT * FROM processed_payments 
WHERE payment_id = 'pay_abc123';

-- If exists, skip processing
-- If not, process and insert
INSERT INTO processed_payments (payment_id, processed_at)
VALUES ('pay_abc123', NOW())
ON CONFLICT (payment_id) DO NOTHING;  -- Atomic insert
```

### 2. Atomic Operations

**Use database transactions and locks:**

```python
def process_payment_completed(payment_id):
    with db.transaction():
        # Lock payment row
        payment = db.get_payment_for_update(payment_id)
        
        # Check if already processed
        if payment.status == 'completed':
            return  # Already processed
        
        # Process payment
        mark_order_as_paid(payment_id)
        
        # Update status atomically
        db.update_payment_status(payment_id, 'completed')
```

### 3. Single Source of Truth

**Use payment status as source of truth:**

```python
def should_process_payment(payment_id):
    payment = db.get_payment(payment_id)
    
    # Only process if status is not completed
    if payment.status == 'completed':
        return False  # Already processed
    
    # Verify with Zwitch API (optional, for extra safety)
    zwitch_payment = zwitch_api.get_payment(payment_id)
    if zwitch_payment.status == 'completed' and payment.status != 'completed':
        # Status mismatch - process it
        return True
    
    return payment.status != 'completed'
```

### 4. Idempotency Keys

**Use consistent idempotency keys:**

```python
# For webhooks
idempotency_key = f"{payment_id}:payment.completed"

# For reconciliation
idempotency_key = f"{payment_id}:reconciliation:{date}"

# Store and check
if db.is_idempotency_key_processed(idempotency_key):
    return  # Skip
```

### 5. Database Constraints

**Use unique constraints:**

```sql
-- Prevent duplicate processing
CREATE TABLE processed_payments (
  payment_id VARCHAR(255) PRIMARY KEY,  -- Unique constraint
  processed_at TIMESTAMP,
  source VARCHAR(50),  -- 'webhook', 'reconciliation', 'manual'
  UNIQUE (payment_id)  -- Prevents duplicates
);

-- Or use composite key for different sources
CREATE TABLE processed_payments (
  payment_id VARCHAR(255),
  source VARCHAR(50),
  processed_at TIMESTAMP,
  PRIMARY KEY (payment_id, source)  -- Can process from different sources once each
);
```

## Detection and Monitoring

### 1. Log All Processing Attempts

**Log every attempt to process payment:**

```python
def process_payment_completed(payment_id):
    # Log attempt
    db.log_processing_attempt(payment_id, 'webhook', 'attempting')
    
    # Check idempotency
    if db.is_payment_processed(payment_id):
        db.log_processing_attempt(payment_id, 'webhook', 'skipped_duplicate')
        return
    
    # Process
    mark_order_as_paid(payment_id)
    db.log_processing_attempt(payment_id, 'webhook', 'completed')
```

### 2. Monitor for Duplicates

**Alert on duplicate processing attempts:**

```python
def check_for_duplicates():
    # Find payments processed multiple times
    duplicates = db.query("""
        SELECT payment_id, COUNT(*) as count
        FROM processed_payments
        GROUP BY payment_id
        HAVING COUNT(*) > 1
    """)
    
    if duplicates:
        alert_operations_team(duplicates)
```

### 3. Reconciliation Checks

**Regular reconciliation to catch issues:**

```python
def reconcile_payments():
    # Get all completed payments from Zwitch
    zwitch_payments = zwitch_api.get_completed_payments()
    
    for payment in zwitch_payments:
        # Check your database
        local_payment = db.get_payment(payment.id)
        
        if local_payment.status != 'completed':
            # Mismatch - investigate
            log_mismatch(payment.id, local_payment.status, 'completed')
            
            # Process if not already processed (with idempotency check)
            if not db.is_payment_processed(payment.id):
                process_payment_completed(payment.id)
```

## Recovery Procedures

### If Double Credit Detected:

1. **Immediate Actions:**
   - Stop processing payments (if systemic issue)
   - Identify affected payments
   - Calculate financial impact

2. **Investigation:**
   - Review logs for duplicate processing
   - Identify root cause
   - Check idempotency implementation

3. **Correction:**
   - Reverse duplicate credits (if possible)
   - Contact affected customers
   - Update records

4. **Prevention:**
   - Fix idempotency implementation
   - Add monitoring
   - Review processes

## Best Practices

### ✅ Do:
1. **Always check idempotency** before processing
2. **Use atomic operations** (database transactions, locks)
3. **Log all processing attempts** (audit trail)
4. **Monitor for duplicates** (alerts)
5. **Reconcile regularly** (catch issues early)
6. **Use single source of truth** (payment status)
7. **Test idempotency** in development

### ❌ Don't:
1. **Don't process without idempotency check**
2. **Don't ignore duplicate processing attempts**
3. **Don't skip reconciliation**
4. **Don't process same payment from multiple sources** without coordination
5. **Don't assume webhooks are unique** (they can be retried)

## Testing

**Test idempotency:**

```python
def test_payment_idempotency():
    payment_id = 'pay_test123'
    
    # Process first time
    process_payment_completed(payment_id)
    assert db.get_payment(payment_id).status == 'completed'
    
    # Process second time (should be idempotent)
    process_payment_completed(payment_id)
    assert db.get_payment(payment_id).status == 'completed'  # Still completed
    
    # Verify order not fulfilled twice
    order = db.get_order_by_payment(payment_id)
    assert order.fulfillment_count == 1  # Only fulfilled once
```

## Summary

- **Double credit is a critical financial risk**
- **Always implement idempotency checks**
- **Use atomic operations** (transactions, locks)
- **Monitor for duplicates**
- **Reconcile regularly**
- **Test idempotency** in development

**Bottom line:** Never process the same payment twice. Idempotency is not optional—it's mandatory for financial operations.

## Related Documentation

- [Retries and Idempotency](../decisions/retries_and_idempotency.md) - Idempotency implementation
- [Polling vs Webhooks](../decisions/polling_vs_webhooks.md) - Avoiding duplicate processing
- [Payment Status Lifecycle](../states/payment_status_lifecycle.md) - Understanding states

