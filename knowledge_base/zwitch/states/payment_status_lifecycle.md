# Payment Status Lifecycle: Complete State Machine

## Overview

This document defines the **complete state machine** for payments in Zwitch. Understanding these states is critical for building reliable payment systems.

## Payment States

### 1. `pending`
**Meaning:** Payment request created, waiting for customer to pay.

**When it occurs:**
- Immediately after creating payment request via API
- Payment token created for Layer.js
- UPI Collect request created

**What it means:**
- Payment is valid and can be paid
- Customer can scan QR code or use payment link
- No money has been transferred yet

**Can transition to:**
- `processing` (customer initiated payment)
- `expired` (time limit reached)
- `cancelled` (payment cancelled)

**Is reversible:** Yes (can be cancelled or expired)

**What to do:**
- Show payment UI to customer (QR code, payment link)
- Monitor for status changes (webhook or polling)
- Handle expiry if customer doesn't pay

---

### 2. `processing`
**Meaning:** Customer has initiated payment, Zwitch is processing it.

**When it occurs:**
- Customer authorized payment in their UPI app/bank app
- Payment is being processed by bank/UPI network
- Money is in transit

**What it means:**
- Payment is being processed
- Money may or may not be transferred (still uncertain)
- Usually a short-lived state (seconds to minutes)

**Can transition to:**
- `completed` (payment successful)
- `failed` (payment rejected)

**Is reversible:** No (once processing, it will complete or fail)

**What to do:**
- Show "Processing" message to customer
- Wait for final status (webhook)
- Don't mark order as paid yet

---

### 3. `completed`
**Meaning:** Payment successful, money received in your account.

**When it occurs:**
- Bank/UPI network confirmed payment
- Money credited to your virtual account
- Payment is final

**What it means:**
- Payment is successful
- Money is in your account
- This is a **terminal state** (cannot change)

**Can transition to:**
- None (terminal state)

**Is reversible:** No (irreversible - money is in your account)

**What to do:**
- Mark order as paid
- Fulfill order/service
- Update customer account
- Send confirmation
- **This is the only state where you should mark payment as successful**

---

### 4. `failed`
**Meaning:** Payment was rejected or failed.

**When it occurs:**
- Insufficient funds in customer's account
- Bank rejected payment
- Network/system error
- Invalid credentials

**What it means:**
- Payment did not succeed
- No money was transferred
- Customer can retry

**Can transition to:**
- None (terminal state for this payment)
- Customer can create new payment (new payment_id)

**Is reversible:** No (this payment failed, but customer can create new payment)

**What to do:**
- Keep order as pending
- Allow customer to retry
- Show user-friendly error message
- Don't penalize customer

---

### 5. `expired`
**Meaning:** Payment request expired (customer didn't pay in time).

**When it occurs:**
- `expiry_in_minutes` time limit reached
- Payment was never completed

**What it means:**
- Payment can no longer be used
- No money was transferred
- Customer must create new payment

**Can transition to:**
- None (terminal state)
- Customer can create new payment (new payment_id)

**Is reversible:** No (expired payment cannot be revived)

**What to do:**
- Mark payment as expired
- Keep order as pending
- Allow customer to create new payment
- Don't cancel order automatically

---

### 6. `cancelled`
**Meaning:** Payment was cancelled.

**When it occurs:**
- You cancelled payment via API (if supported)
- Customer closed payment page without paying
- Payment cancelled via dashboard

**What it means:**
- Payment is no longer valid
- No money was transferred
- Customer can create new payment

**Can transition to:**
- None (terminal state)

**Is reversible:** No (cancelled payment cannot be revived)

**What to do:**
- Mark payment as cancelled
- Keep order as pending (customer may return)
- Allow customer to create new payment

---

## State Transition Diagram

```
                    ┌─────────┐
                    │ pending │
                    └────┬────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                 │
        ▼                ▼                 ▼
   ┌─────────┐      ┌──────────┐     ┌──────────┐
   │expired  │      │processing│     │cancelled │
   └─────────┘      └────┬─────┘     └──────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
        ┌──────────┐          ┌─────────┐
        │completed │          │ failed  │
        └──────────┘          └─────────┘
```

## Terminal States

**Terminal states** (cannot change further):
- `completed` ✅
- `failed` ❌
- `expired` ⏰
- `cancelled` 🚫

**Non-terminal states:**
- `pending` (can become processing, expired, or cancelled)
- `processing` (can become completed or failed)

## Critical Rules

### ✅ Safe to Mark as Paid:
- **Only when status is `completed`**
- Verify via webhook signature
- Check idempotency

### ❌ Never Mark as Paid When:
- Status is `pending` (customer hasn't paid yet)
- Status is `processing` (payment may still fail)
- Status is `failed`, `expired`, or `cancelled`

### State Verification:
- Always verify final state via webhook
- Use API to verify if webhook is delayed: `GET /v1/payments/{id}`
- Don't trust intermediate states

## Database Representation

```sql
CREATE TABLE payments (
  payment_id VARCHAR(255) PRIMARY KEY,
  status VARCHAR(50) NOT NULL,  -- pending, processing, completed, failed, expired, cancelled
  amount DECIMAL(10, 2),
  created_at TIMESTAMP,
  completed_at TIMESTAMP,  -- Only set when status = 'completed'
  failed_at TIMESTAMP,    -- Only set when status = 'failed'
  expired_at TIMESTAMP,   -- Only set when status = 'expired'
  cancelled_at TIMESTAMP, -- Only set when status = 'cancelled'
  
  -- Add constraint to ensure only one timestamp is set
  CHECK (
    (status = 'completed' AND completed_at IS NOT NULL) OR
    (status = 'failed' AND failed_at IS NOT NULL) OR
    (status = 'expired' AND expired_at IS NOT NULL) OR
    (status = 'cancelled' AND cancelled_at IS NOT NULL) OR
    (status IN ('pending', 'processing'))
  )
);
```

## Webhook Events

Each state change triggers a webhook:

| State | Webhook Event |
|-------|---------------|
| `pending` | `payment.created` |
| `processing` | `payment.processing` |
| `completed` | `payment.completed` |
| `failed` | `payment.failed` |
| `expired` | `payment.expired` |
| `cancelled` | `payment.cancelled` |

## Common Mistakes

### ❌ Mistake 1: Marking as Paid on `processing`
```python
# WRONG
if payment.status == 'processing':
    mark_order_as_paid()  # ❌ Payment may still fail!
```

### ✅ Correct: Only on `completed`
```python
# CORRECT
if payment.status == 'completed':
    mark_order_as_paid()  # ✅ Payment is final
```

### ❌ Mistake 2: Not Handling Terminal States
```python
# WRONG - Doesn't handle failed/expired
if payment.status == 'completed':
    mark_order_as_paid()
# What about failed? expired? ❌
```

### ✅ Correct: Handle All Terminal States
```python
# CORRECT
if payment.status == 'completed':
    mark_order_as_paid()
elif payment.status in ['failed', 'expired', 'cancelled']:
    mark_order_as_pending()  # Allow retry
```

## State Checking Best Practices

1. **Webhooks are primary source of truth**
   - Don't poll unnecessarily
   - But verify via API if webhook delayed

2. **Check idempotency**
   - Don't process same state change twice
   - Use payment_id + status as idempotency key

3. **Handle all states**
   - Don't ignore failed/expired states
   - Allow customers to retry

4. **Log state transitions**
   - Track when and why states change
   - Useful for debugging and audit

## Summary

- **6 states total:** pending, processing, completed, failed, expired, cancelled
- **4 terminal states:** completed, failed, expired, cancelled
- **Only `completed` = money received**
- **Always verify via webhook**
- **Handle all states properly**

Understanding payment states prevents financial errors and improves user experience.

## Related Documentation

- [Payin Happy Path](../flows/payin_happy_path.md) - Successful payment flow
- [Payin Failure Path](../flows/payin_failure_path.md) - Failure handling
- [Polling vs Webhooks](../decisions/polling_vs_webhooks.md) - State checking strategy

