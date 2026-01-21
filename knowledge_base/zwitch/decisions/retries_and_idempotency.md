# Retries and Idempotency: Handling Failures Safely

## Overview

This document provides **opinionated guidance** on when and how to retry API calls and webhook processing, with emphasis on preventing duplicate processing (idempotency).

## Core Principle

**All financial operations must be idempotent. Retries must never cause duplicate money movement or duplicate processing.**

## What is Idempotency?

**Idempotency** means performing the same operation multiple times produces the same result as performing it once.

**Example:**
- Calling `GET /v1/payments/{id}` multiple times → Same result (idempotent)
- Processing `payment.completed` webhook multiple times → Should have same effect (idempotent)
- Creating payment multiple times with same `merchant_reference_id` → Should not create duplicates (idempotent)

## When to Retry

### ✅ Retry For:

1. **Transient Network Errors**
   - Connection timeout
   - DNS resolution failure
   - Temporary network issues
   - **Retry:** Yes, with exponential backoff

2. **5XX Server Errors**
   - 500 Internal Server Error
   - 502 Bad Gateway
   - 503 Service Unavailable
   - **Retry:** Yes, with exponential backoff

3. **Rate Limiting (429)**
   - Too Many Requests
   - **Retry:** Yes, after delay specified in response

4. **Webhook Processing Failures**
   - Your server was down
   - Database connection failed
   - Processing error (non-financial)
   - **Retry:** Yes, with idempotency check

### ❌ Don't Retry For:

1. **4XX Client Errors**
   - 400 Bad Request (invalid data)
   - 401 Unauthorized (wrong credentials)
   - 404 Not Found (resource doesn't exist)
   - **Retry:** No (error won't change)

2. **Business Logic Errors**
   - Insufficient balance
   - Invalid beneficiary
   - Payment already completed
   - **Retry:** No (error is permanent)

3. **Already Processed**
   - Webhook already processed (idempotency check)
   - Payment already marked as completed
   - **Retry:** No (duplicate processing)

## Retry Strategy: Exponential Backoff

**Recommended retry pattern:**

```
Attempt 1: Immediate
Attempt 2: After 1 second
Attempt 3: After 2 seconds
Attempt 4: After 4 seconds
Attempt 5: After 8 seconds
Attempt 6: After 16 seconds
Max attempts: 5-6
```

**Implementation:**
```python
import time

def retry_with_backoff(func, max_attempts=5):
    for attempt in range(max_attempts):
        try:
            return func()
        except TransientError as e:
            if attempt == max_attempts - 1:
                raise  # Last attempt failed
            wait_time = 2 ** attempt  # Exponential backoff
            time.sleep(wait_time)
    raise MaxRetriesExceeded()
```

## Idempotency Implementation

### For API Calls:

**Use idempotency keys:**
- Zwitch may support idempotency keys (check documentation)
- Use same key for retries of same operation
- Store key to prevent duplicates

**Example:**
```python
# Create payment with idempotency key
def create_payment(amount, order_id, idempotency_key):
    # Check if already processed
    existing = db.get_payment_by_idempotency_key(idempotency_key)
    if existing:
        return existing  # Return existing, don't create duplicate
    
    # Create payment
    payment = zwitch_api.create_payment(amount, order_id, idempotency_key)
    db.save_payment(payment, idempotency_key)
    return payment
```

### For Webhook Processing:

**Use webhook event ID as idempotency key:**
```python
def process_webhook(event):
    # Idempotency key: payment_id + event_type
    idempotency_key = f"{event.data.payment_id}:{event.event}"
    
    # Check if already processed
    if db.is_webhook_processed(idempotency_key):
        return  # Already processed, skip
    
    # Process webhook
    if event.event == 'payment.completed':
        mark_order_as_paid(event.data.payment_id)
    
    # Mark as processed
    db.mark_webhook_processed(idempotency_key)
```

**Database schema:**
```sql
CREATE TABLE webhook_events (
  idempotency_key VARCHAR(255) PRIMARY KEY,  -- payment_id:event_type
  payment_id VARCHAR(255),
  event_type VARCHAR(100),
  payload JSONB,
  processed_at TIMESTAMP,
  created_at TIMESTAMP
);
```

## Retry Scenarios

### Scenario 1: API Call Failure (Creating Payment)

**Situation:**
- You call `POST /v1/payments/upi/collect`
- Request times out
- Don't know if payment was created

**What to do:**
1. **Check if payment exists:**
   ```python
   # Try to get payment by merchant_reference_id
   existing = zwitch_api.get_payment_by_reference(order_id)
   if existing:
       return existing  # Payment was created, use it
   ```

2. **Retry with idempotency:**
   ```python
   # Retry creation (with same merchant_reference_id)
   # Zwitch should return existing payment if duplicate
   payment = retry_with_backoff(
       lambda: zwitch_api.create_payment(amount, order_id)
   )
   ```

3. **Store payment ID:**
   - Once you have payment_id, store it
   - Don't create duplicate payments

### Scenario 2: Webhook Delivery Failure

**Situation:**
- Zwitch sends webhook: `payment.completed`
- Your server was down
- Webhook delivery failed
- Zwitch retries webhook

**What to do:**
1. **Idempotency check:**
   ```python
   def handle_webhook(event):
       idempotency_key = f"{event.data.payment_id}:{event.event}"
       
       # Check if already processed
       if db.is_processed(idempotency_key):
           return 200  # Already processed, return success
       
       # Process webhook
       process_payment_completed(event.data)
       
       # Mark as processed
       db.mark_processed(idempotency_key)
       return 200
   ```

2. **Reconciliation (backup):**
   - Periodically check payment status
   - Catch missed webhooks
   - Process if not already processed

### Scenario 3: Transfer Failure

**Situation:**
- You create transfer: `POST /v1/transfers`
- Transfer fails: `insufficient_balance`
- You add funds
- Want to retry

**What to do:**
1. **Check transfer status:**
   ```python
   transfer = zwitch_api.get_transfer(transfer_id)
   if transfer.status == 'failed':
       # Check failure reason
       if transfer.failure_reason == 'insufficient_balance':
           # Add funds, then create NEW transfer (not retry same one)
           new_transfer = zwitch_api.create_transfer(...)
   ```

2. **Create new transfer (not retry):**
   - Failed transfers cannot be retried
   - Create new transfer with new transfer_id
   - Link to original in metadata

## Idempotency Keys

### What to Use as Idempotency Key:

**For Payments:**
- `merchant_reference_id` (your order ID)
- Combination: `order_id:payment_attempt_number`

**For Webhooks:**
- `payment_id:event_type` (e.g., `pay_123:payment.completed`)
- Or: `payment_id:event_type:timestamp` (if events can repeat)

**For Transfers:**
- `settlement_id` or `refund_id` (your internal ID)
- Combination: `order_id:transfer_type`

### Storing Idempotency Keys:

```sql
-- Webhook idempotency
CREATE TABLE processed_webhooks (
  idempotency_key VARCHAR(255) PRIMARY KEY,
  payment_id VARCHAR(255),
  event_type VARCHAR(100),
  processed_at TIMESTAMP,
  INDEX idx_payment (payment_id)
);

-- Payment idempotency
CREATE TABLE payment_attempts (
  order_id VARCHAR(255),
  attempt_number INT,
  payment_id VARCHAR(255),
  created_at TIMESTAMP,
  PRIMARY KEY (order_id, attempt_number)
);
```

## Common Mistakes

### ❌ Mistake 1: No Idempotency Check
```python
# ❌ WRONG - Processes webhook multiple times
def handle_webhook(event):
    if event.event == 'payment.completed':
        mark_order_as_paid(event.data.payment_id)  # ❌ Duplicate processing!
```

### ✅ Correct: Idempotency Check
```python
# ✅ CORRECT - Checks before processing
def handle_webhook(event):
    if is_already_processed(event):
        return  # Skip if already processed
    
    if event.event == 'payment.completed':
        mark_order_as_paid(event.data.payment_id)  # ✅ Safe
    mark_as_processed(event)
```

### ❌ Mistake 2: Retrying Non-Idempotent Operations
```python
# ❌ WRONG - Retries without idempotency
def create_payment():
    for attempt in range(5):
        try:
            return zwitch_api.create_payment(...)  # ❌ May create duplicates!
        except:
            time.sleep(2 ** attempt)
```

### ✅ Correct: Idempotency + Retry
```python
# ✅ CORRECT - Checks before retry
def create_payment(order_id):
    # Check if already exists
    existing = get_payment_by_order_id(order_id)
    if existing:
        return existing
    
    # Retry with idempotency
    return retry_with_backoff(
        lambda: zwitch_api.create_payment(..., merchant_reference_id=order_id)
    )
```

## Best Practices

### ✅ Do:
1. **Always check idempotency** before processing
2. **Use idempotency keys** for API calls
3. **Store processed events** in database
4. **Retry transient errors** with exponential backoff
5. **Don't retry permanent errors**
6. **Log all retries** for debugging
7. **Set max retry attempts** (prevent infinite loops)

### ❌ Don't:
1. **Don't process same event twice** (idempotency check)
2. **Don't retry permanent errors** (4XX client errors)
3. **Don't retry without idempotency** (may cause duplicates)
4. **Don't retry forever** (set max attempts)
5. **Don't ignore idempotency** (financial operations must be safe)

## Summary

- **Idempotency is mandatory** for financial operations
- **Retry transient errors** with exponential backoff
- **Don't retry permanent errors** (4XX, business logic errors)
- **Always check idempotency** before processing
- **Store processed events** to prevent duplicates
- **Use idempotency keys** for API calls

**Bottom line:** Retries are necessary for reliability, but idempotency is mandatory for safety. Never retry without idempotency checks.

## Related Documentation

- [Polling vs Webhooks](./polling_vs_webhooks.md) - Webhook handling
- [Webhook Signature Verification](../risks/webhook_signature_verification.md) - Webhook security
- [Double Credit Risk](../risks/double_credit_risk.md) - Preventing duplicate credits

