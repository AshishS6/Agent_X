# Polling vs Webhooks: Which Should You Use?

## Recommendation

**Use webhooks as the primary source of truth. Use polling only as a fallback for reconciliation.**

This is not just a preference—it's a best practice for production fintech systems.

## Why Webhooks Are Preferred

### 1. Real-Time Updates
- **Webhooks:** Instant notification when status changes
- **Polling:** Delayed discovery (depends on polling interval)

**Example:**
- Customer pays at 10:00:00
- Webhook received at 10:00:01 → Order fulfilled immediately
- Polling every 5 minutes → Order fulfilled at 10:05:00 (5-minute delay)

### 2. Efficiency
- **Webhooks:** One HTTP request per event
- **Polling:** Constant API calls, even when nothing changed

**Example:**
- 1000 payments per day
- Webhooks: 1000 requests (one per payment)
- Polling every minute: 1440 requests/day × 1000 payments = 1.44M requests (most return "no change")

### 3. Lower Latency
- **Webhooks:** Status updates in seconds
- **Polling:** Status updates delayed by polling interval

**Impact:**
- Faster order fulfillment
- Better customer experience
- Reduced customer support queries ("Why is my order still pending?")

### 4. Reduced API Load
- **Webhooks:** Push-based (Zwitch initiates)
- **Polling:** Pull-based (you initiate, even when unnecessary)

**Benefits:**
- Lower API usage
- Better rate limit management
- Reduced infrastructure costs

### 5. Reliability (When Implemented Correctly)
- **Webhooks:** Event-driven, no missed updates (if webhook delivery is reliable)
- **Polling:** Can miss updates if polling interval is too long

## When to Use Polling

### ✅ Use Polling For:

1. **Reconciliation (Backup)**
   - Periodically verify webhook-processed payments
   - Catch missed webhooks
   - Ensure data consistency

2. **Webhook Delivery Failures**
   - If webhook endpoint is down
   - If webhook processing failed
   - As a safety net

3. **Initial Status Check**
   - After creating payment, check status once
   - Before showing payment UI to customer
   - Not for continuous monitoring

4. **Development/Testing**
   - When webhooks are hard to test locally
   - For debugging
   - Not for production

### ❌ Don't Use Polling For:

1. **Primary Status Updates**
   - Don't rely on polling for real-time updates
   - Don't poll continuously in production
   - Don't replace webhooks with polling

2. **High-Frequency Checks**
   - Don't poll every few seconds
   - Don't poll for every payment individually
   - Don't create polling loops

## Hybrid Approach (Recommended)

**Best Practice:** Webhooks + Reconciliation Polling

```
Primary: Webhooks (real-time)
  ↓
If webhook fails or delayed
  ↓
Fallback: Polling (reconciliation)
```

### Implementation:

1. **Primary:** Process webhooks for real-time updates
2. **Reconciliation:** Poll pending payments hourly/daily
3. **Error Handling:** If webhook fails, poll to catch up

**Example:**
```python
# Primary: Webhook handler
def handle_webhook(event):
    process_payment_status(event.data)
    mark_as_processed(event.data.payment_id)

# Fallback: Reconciliation job (runs hourly)
def reconcile_payments():
    pending_payments = get_pending_payments()
    for payment in pending_payments:
        status = zwitch_api.get_payment(payment.id)
        if status != payment.status:
            # Webhook was missed - process now
            process_payment_status(status)
```

## Polling Frequency Guidelines

### ❌ Too Frequent (Don't Do This):
- Every 1 second: 86,400 requests/day per payment
- Every 5 seconds: 17,280 requests/day per payment
- **Impact:** Rate limits, unnecessary load, high costs

### ❌ Too Infrequent (Don't Do This):
- Every 24 hours: Miss real-time updates
- **Impact:** Poor user experience, delayed fulfillment

### ✅ Recommended Frequencies:

**For Reconciliation:**
- Recent payments (< 24 hours): Every 1-2 hours
- Older payments: Daily
- **Purpose:** Catch missed webhooks, not primary updates

**For Initial Check:**
- After creating payment: Check once after 30 seconds
- **Purpose:** Verify payment was created, not continuous monitoring

## Webhook Implementation Requirements

To use webhooks effectively, you must:

1. **Verify Signatures**
   - Always verify webhook signatures
   - Prevent fraud and ensure authenticity
   - See [Webhook Signature Verification](../risks/webhook_signature_verification.md)

2. **Handle Idempotency**
   - Don't process same webhook twice
   - Use payment_id + event as idempotency key
   - See [Retries and Idempotency](./retries_and_idempotency.md)

3. **Respond Quickly**
   - Return 200 OK within 5 seconds
   - Process asynchronously
   - Don't block webhook response

4. **Handle Failures**
   - Implement retry logic for webhook processing
   - Log failures for debugging
   - Use polling as fallback

5. **Secure Endpoint**
   - Use HTTPS (required)
   - Verify signatures
   - Implement rate limiting

## Common Mistakes

### ❌ Mistake 1: Polling Instead of Webhooks
```python
# WRONG - Polling every 5 seconds
while True:
    status = get_payment_status(payment_id)
    if status == 'completed':
        mark_order_as_paid()
    time.sleep(5)  # ❌ Inefficient, delayed
```

### ✅ Correct: Webhooks
```python
# CORRECT - Webhook handler
@app.post('/webhook')
def handle_webhook(event):
    if event.event == 'payment.completed':
        mark_order_as_paid()  # ✅ Instant, efficient
```

### ❌ Mistake 2: No Fallback
```python
# WRONG - Only webhooks, no reconciliation
def handle_webhook(event):
    process_payment(event)  # What if webhook is missed? ❌
```

### ✅ Correct: Webhooks + Reconciliation
```python
# CORRECT - Webhooks + reconciliation
def handle_webhook(event):
    process_payment(event)  # Primary

def reconcile_hourly():
    check_pending_payments()  # Fallback ✅
```

## Performance Comparison

### Scenario: 1000 payments per day

**Webhooks:**
- Requests: 1000 (one per payment)
- Latency: < 1 second
- API load: Minimal
- Cost: Low

**Polling (every 5 minutes):**
- Requests: 1440/day × 1000 payments = 1.44M requests
- Latency: Up to 5 minutes
- API load: High
- Cost: High

**Winner:** Webhooks (by far)

## Decision Matrix

| Scenario | Use Webhooks? | Use Polling? |
|----------|---------------|--------------|
| Production status updates | ✅ Yes (primary) | ❌ No |
| Reconciliation | ✅ Yes (as fallback) | ✅ Yes (hourly/daily) |
| Development/testing | ⚠️ If possible | ✅ Yes (easier) |
| Webhook endpoint down | ❌ Not possible | ✅ Yes (temporary) |
| Real-time requirements | ✅ Yes | ❌ No |

## Summary

- **Primary:** Use webhooks for real-time status updates
- **Fallback:** Use polling for reconciliation (hourly/daily)
- **Never:** Don't use polling as primary method in production
- **Always:** Verify webhook signatures, handle idempotency
- **Best Practice:** Hybrid approach (webhooks + reconciliation polling)

**Bottom line:** Although polling is possible, webhooks should be the primary source of truth in production. Use polling only as a safety net for reconciliation.

## Related Documentation

- [Webhooks API](../api/10_webhooks.md) - Webhook setup and configuration
- [Webhook Signature Verification](../risks/webhook_signature_verification.md) - Security
- [Retries and Idempotency](./retries_and_idempotency.md) - Handling duplicates
- [Payment Status Lifecycle](../states/payment_status_lifecycle.md) - Understanding states

