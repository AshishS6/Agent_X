# Payin Failure Path: Handling Payment Failures

## Overview

This document describes what happens when a payment **fails, expires, or is cancelled**. Understanding failure paths is critical for building robust payment systems.

## Common Failure Scenarios

1. **Payment Expired**: Customer didn't pay within expiry time
2. **Payment Failed**: Customer's payment was rejected (insufficient funds, bank rejection, etc.)
3. **Payment Cancelled**: Customer or you cancelled the payment
4. **Network/System Failures**: Zwitch or bank systems are down
5. **Webhook Delivery Failures**: Webhook not received or processed incorrectly

## Failure Flow Diagram

```
Payment Created → Customer Attempts → Failure/Expiry → Webhook → Your System → Customer Notification
```

## Scenario 1: Payment Expired

### What Happens:

**Step 1: Payment Created**
- Payment request created with `expiry_in_minutes: 30`
- Status: `pending`
- Expires at: `created_at + 30 minutes`

**Step 2: Time Passes**
- Customer doesn't complete payment
- 30 minutes elapse

**Step 3: Payment Expires**
- Zwitch automatically marks payment as `expired`
- Payment can no longer be used
- No money is transferred

**Step 4: Webhook Received**
```json
{
  "event": "payment.expired",
  "data": {
    "id": "pay_abc123",
    "status": "expired",
    "expires_at": "2024-01-15T10:30:00Z",
    "expired_at": "2024-01-15T10:30:01Z"
  }
}
```

### What You Should Do:

1. **Update Database:**
   ```sql
   UPDATE payments 
   SET status = 'expired',
       expired_at = '2024-01-15T10:30:01Z'
   WHERE payment_id = 'pay_abc123';
   
   UPDATE orders 
   SET status = 'payment_expired'
   WHERE order_id = 'order_12345';
   ```

2. **Notify Customer:**
   - Show "Payment link expired" message
   - Offer to create new payment
   - Provide option to retry

3. **Business Logic:**
   - Keep order in `pending_payment` state
   - Allow customer to create new payment for same order
   - Don't cancel order automatically (customer may want to retry)

### Best Practice:
- Create new payment token for the same order
- Don't delete the expired payment record (keep for audit)

---

## Scenario 2: Payment Failed

### What Happens:

**Step 1: Customer Attempts Payment**
- Customer scans QR code or clicks payment link
- Customer authorizes payment in UPI app/bank app

**Step 2: Bank/UPI Network Rejects**
- Insufficient funds
- Bank account frozen
- Invalid credentials
- Network timeout
- Bank system error

**Step 3: Payment Fails**
- Zwitch receives failure notification
- Status changes: `pending` → `processing` → `failed`
- No money is transferred

**Step 4: Webhook Received**
```json
{
  "event": "payment.failed",
  "data": {
    "id": "pay_abc123",
    "status": "failed",
    "failure_reason": "insufficient_funds",  // or "bank_rejection", "network_error", etc.
    "failed_at": "2024-01-15T10:15:30Z"
  }
}
```

### What You Should Do:

1. **Update Database:**
   ```sql
   UPDATE payments 
   SET status = 'failed',
       failure_reason = 'insufficient_funds',
       failed_at = '2024-01-15T10:15:30Z'
   WHERE payment_id = 'pay_abc123';
   
   -- Keep order as pending_payment (allow retry)
   UPDATE orders 
   SET status = 'payment_failed',
       last_payment_attempt = '2024-01-15T10:15:30Z'
   WHERE order_id = 'order_12345';
   ```

2. **Notify Customer:**
   - Show user-friendly error message
   - Don't expose technical details ("insufficient funds" is OK, "bank_rejection_code_XYZ" is not)
   - Offer to retry payment
   - Suggest alternative payment methods if available

3. **Business Logic:**
   - Log failure reason (for analytics)
   - Track retry attempts (prevent infinite loops)
   - Consider rate limiting retries
   - Don't penalize customer for payment failures

### Failure Reasons to Handle:

| Reason | User Message | Action |
|--------|--------------|--------|
| `insufficient_funds` | "Insufficient balance. Please check your account." | Allow retry |
| `bank_rejection` | "Payment was declined by your bank. Please contact your bank or try another method." | Allow retry, suggest alternative |
| `network_error` | "Network error. Please try again." | Allow retry immediately |
| `invalid_credentials` | "Payment authentication failed. Please try again." | Allow retry |
| `timeout` | "Payment timed out. Please try again." | Allow retry immediately |

---

## Scenario 3: Payment Cancelled

### What Happens:

**Step 1: Payment Created**
- Status: `pending`

**Step 2: Cancellation**
- You call cancellation API (if supported)
- OR customer closes payment page without paying
- OR you cancel via dashboard

**Step 3: Payment Cancelled**
- Status changes to `cancelled`
- Payment can no longer be used

**Step 4: Webhook Received**
```json
{
  "event": "payment.cancelled",
  "data": {
    "id": "pay_abc123",
    "status": "cancelled",
    "cancelled_at": "2024-01-15T10:20:00Z"
  }
}
```

### What You Should Do:

1. **Update Database:**
   ```sql
   UPDATE payments 
   SET status = 'cancelled',
       cancelled_at = '2024-01-15T10:20:00Z'
   WHERE payment_id = 'pay_abc123';
   ```

2. **Business Logic:**
   - If customer cancelled: Keep order as `pending_payment` (they may return)
   - If you cancelled: Update order status accordingly
   - Don't automatically cancel order (customer may want to retry)

---

## Scenario 4: Webhook Not Received

### What Happens:

- Payment completes successfully on Zwitch side
- But webhook delivery fails (network issue, your server down, etc.)
- Your system doesn't know payment completed

### Detection:

1. **Reconciliation Process:**
   - Periodically check payment status via API
   - Compare with your database
   - Identify discrepancies

2. **Customer Reports:**
   - Customer says they paid but order not updated
   - Check payment status via API

### What You Should Do:

1. **Implement Reconciliation:**
   ```python
   # Pseudo-code
   def reconcile_payments():
       # Get all pending payments from your DB
       pending_payments = db.query("SELECT payment_id FROM payments WHERE status = 'pending'")
       
       for payment in pending_payments:
           # Check status with Zwitch
           zwitch_status = zwitch_api.get_payment(payment.payment_id)
           
           if zwitch_status.status == 'completed':
               # Webhook was missed - process now
               process_payment_completed(zwitch_status)
           elif zwitch_status.status == 'failed':
               process_payment_failed(zwitch_status)
   ```

2. **Run Reconciliation:**
   - Hourly for recent payments (< 24 hours)
   - Daily for older payments
   - After webhook delivery failures

3. **Update Database:**
   - Mark payment with correct status
   - Update order status
   - Log that reconciliation fixed the issue

### Best Practice:
- Implement reconciliation as a safety net
- Don't rely solely on webhooks
- Run reconciliation regularly

---

## Scenario 5: Partial Failures (Your System)

### What Happens:

- Webhook received and verified
- But your database update fails
- Or your business logic fails
- Payment is successful on Zwitch, but your system is inconsistent

### What You Should Do:

1. **Use Database Transactions:**
   ```python
   with db.transaction():
       update_payment_status(payment_id, 'completed')
       update_order_status(order_id, 'paid')
       send_confirmation_email(order_id)
       # If any step fails, rollback all
   ```

2. **Implement Retry Logic:**
   - If webhook processing fails, retry with exponential backoff
   - Log failures for manual intervention
   - Don't return 200 OK if processing failed

3. **Idempotency:**
   - Check if payment already processed before processing again
   - Prevents duplicate processing on retry

---

## Database Schema for Failures

```sql
-- Add failure tracking to payments table
ALTER TABLE payments ADD COLUMN failure_reason VARCHAR(255);
ALTER TABLE payments ADD COLUMN failed_at TIMESTAMP;
ALTER TABLE payments ADD COLUMN expired_at TIMESTAMP;
ALTER TABLE payments ADD COLUMN cancelled_at TIMESTAMP;
ALTER TABLE payments ADD COLUMN retry_count INTEGER DEFAULT 0;
ALTER TABLE payments ADD COLUMN last_retry_at TIMESTAMP;

-- Add webhook delivery tracking
ALTER TABLE webhook_events ADD COLUMN delivery_status VARCHAR(50);  -- delivered, failed, retrying
ALTER TABLE webhook_events ADD COLUMN retry_count INTEGER DEFAULT 0;
ALTER TABLE webhook_events ADD COLUMN last_retry_at TIMESTAMP;
```

## Error Handling Best Practices

### ✅ Do:
1. **Log all failures** with context (payment_id, reason, timestamp)
2. **Notify customer** with user-friendly messages
3. **Allow retries** for transient failures
4. **Implement reconciliation** to catch missed webhooks
5. **Use idempotency** to prevent duplicate processing
6. **Monitor failure rates** (alert if too high)

### ❌ Don't:
1. **Don't expose technical errors** to customers
2. **Don't automatically cancel orders** on first failure
3. **Don't ignore webhook failures** (implement reconciliation)
4. **Don't process same failure multiple times** (idempotency)
5. **Don't penalize customers** for payment failures

## Retry Strategy

### For Expired Payments:
- Customer must create new payment (can't retry expired payment)
- Create new payment token for same order

### For Failed Payments:
- Allow immediate retry (may be transient network issue)
- Track retry count (prevent infinite loops)
- Consider rate limiting (max 3-5 retries per hour)

### For Webhook Processing Failures:
- Retry with exponential backback: 1min, 5min, 15min, 1hr
- Log failures for manual intervention
- Don't retry forever (mark for manual review after max retries)

## Customer Communication

### Expired Payment:
> "Your payment link has expired. Please create a new payment to complete your order."

### Failed Payment:
> "We couldn't process your payment. This could be due to insufficient funds or a temporary bank issue. Please try again or use a different payment method."

### Network Error:
> "We encountered a network error. Your payment may have been processed. Please check your order status or contact support if you see a charge but no confirmation."

## Summary

- **Expired**: Customer didn't pay in time → Create new payment
- **Failed**: Bank/UPI rejected → Allow retry, suggest alternatives
- **Cancelled**: Payment was cancelled → Keep order pending, allow retry
- **Webhook Missed**: Implement reconciliation to catch
- **System Failures**: Use transactions, retry logic, idempotency

Always allow customers to retry failed payments. Don't automatically cancel orders on first failure.

## Related Documentation

- [Payin Happy Path](./payin_happy_path.md) - Successful flow
- [Payment Status Lifecycle](../states/payment_status_lifecycle.md) - All states
- [Retries and Idempotency](../decisions/retries_and_idempotency.md) - Retry strategies
- [Reconciliation Failures](../risks/reconciliation_failures.md) - Handling discrepancies

