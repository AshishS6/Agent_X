# Idempotency: Mandatory for Financial Operations

## Absolute Rule

**All financial operations must be idempotent. Processing the same payment, transfer, or webhook multiple times must produce the same result as processing it once.**

Idempotency is **not optional**—it is a **mandatory requirement** for fintech systems.

## Why Idempotency Is Mandatory

### Financial Risk

**Without idempotency:**
- Same payment processed twice → Customer charged twice
- Same transfer processed twice → Money sent twice
- Same webhook processed twice → Order fulfilled twice

**Result:** Financial loss, customer complaints, compliance issues.

### Common Scenarios Requiring Idempotency

1. **Webhook Retries**
   - Zwitch retries webhooks if your server doesn't respond
   - Same webhook may arrive multiple times
   - Without idempotency: Payment processed multiple times

2. **API Retries**
   - Network failures cause retries
   - Same API call may succeed multiple times
   - Without idempotency: Duplicate operations

3. **Reconciliation**
   - Reconciliation checks same payment multiple times
   - Without idempotency: Payment processed on each check

4. **Manual Interventions**
   - Admin manually processes payment
   - Webhook arrives later
   - Without idempotency: Payment processed twice

## Where Idempotency Applies

### 1. Payment Processing

**Must be idempotent:**
- Processing `payment.completed` webhook
- Marking order as paid
- Updating payment status
- Fulfilling order

**Implementation:**
```python
def process_payment_completed(payment_id):
    # Idempotency check
    if db.is_payment_processed(payment_id):
        return  # Already processed, skip
    
    # Process payment
    mark_order_as_paid(payment_id)
    update_inventory(payment_id)
    
    # Mark as processed
    db.mark_payment_processed(payment_id)
```

### 2. Transfer Processing

**Must be idempotent:**
- Processing `transfer.completed` webhook
- Updating transfer status
- Updating settlement records
- Notifying beneficiaries

**Implementation:**
```python
def process_transfer_completed(transfer_id):
    # Idempotency check
    if db.is_transfer_processed(transfer_id):
        return  # Already processed, skip
    
    # Process transfer
    update_settlement(transfer_id)
    notify_beneficiary(transfer_id)
    
    # Mark as processed
    db.mark_transfer_processed(transfer_id)
```

### 3. Webhook Processing

**Must be idempotent:**
- Processing any webhook event
- Updating database based on webhook
- Triggering business logic

**Implementation:**
```python
def process_webhook(event):
    # Idempotency key: payment_id + event_type
    idempotency_key = f"{event.data.payment_id}:{event.event}"
    
    # Check if already processed
    if db.is_webhook_processed(idempotency_key):
        return  # Already processed, skip
    
    # Process webhook
    handle_event(event)
    
    # Mark as processed
    db.mark_webhook_processed(idempotency_key)
```

### 4. API Calls

**Must be idempotent:**
- Creating payments with same `merchant_reference_id`
- Creating transfers with same `reference_id`
- Any operation that can be retried

**Implementation:**
```python
def create_payment(amount, order_id):
    # Check if payment already exists for this order
    existing = db.get_payment_by_order_id(order_id)
    if existing:
        return existing  # Return existing, don't create duplicate
    
    # Create payment
    payment = zwitch_api.create_payment(amount, order_id)
    db.save_payment(payment)
    return payment
```

## Risks of Not Using Idempotency

### Double Credit Risk

**Scenario:**
- Payment webhook processed twice
- Order marked as paid twice
- Customer receives product twice
- **Loss:** Product value + shipping

**Prevention:** Idempotency check before processing.

### Double Debit Risk

**Scenario:**
- Transfer webhook processed twice
- Money sent to beneficiary twice
- **Loss:** Transfer amount

**Prevention:** Idempotency check before processing.

### Duplicate Fulfillment

**Scenario:**
- Payment processed multiple times
- Order fulfilled multiple times
- Inventory incorrectly updated
- **Loss:** Product value + operational cost

**Prevention:** Idempotency check before fulfillment.

## Implementation Requirements

### Database Schema

**Store idempotency keys:**
```sql
CREATE TABLE processed_webhooks (
  idempotency_key VARCHAR(255) PRIMARY KEY,  -- payment_id:event_type
  payment_id VARCHAR(255),
  event_type VARCHAR(100),
  processed_at TIMESTAMP,
  UNIQUE (idempotency_key)  -- Prevents duplicates
);

CREATE TABLE processed_payments (
  payment_id VARCHAR(255) PRIMARY KEY,
  processed_at TIMESTAMP,
  UNIQUE (payment_id)  -- Prevents duplicate processing
);
```

### Atomic Operations

**Use atomic database operations:**
```python
# Atomic insert (fails if already exists)
db.execute("""
  INSERT INTO processed_payments (payment_id, processed_at)
  VALUES (%s, NOW())
  ON CONFLICT (payment_id) DO NOTHING
  RETURNING payment_id
""", (payment_id,))

# If no row returned, already processed
if not result:
    return  # Already processed
```

### Idempotency Keys

**Use consistent idempotency keys:**
- Webhooks: `{payment_id}:{event_type}`
- Payments: `{order_id}` or `{merchant_reference_id}`
- Transfers: `{settlement_id}` or `{refund_id}`

## Testing Idempotency

### Test Cases

1. **Process same webhook twice** → Should process only once
2. **Retry API call** → Should not create duplicates
3. **Reconciliation on same payment** → Should not process twice
4. **Manual + webhook processing** → Should process only once

### Test Implementation

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

## Override Authority

This principle **cannot be overridden** by:
- API documentation
- Best practices
- Decisions
- Concepts

This is a **foundational safety principle** that applies to all layers.

## Related Documentation

- [Retries and Idempotency](../decisions/retries_and_idempotency.md) — Detailed implementation
- [Double Credit Risk](../risks/double_credit_risk.md) — Consequences of missing idempotency
- [Backend Authority](./backend_authority.md) — Backend enforces idempotency

