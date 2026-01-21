# Transfer Status Lifecycle: Complete State Machine

## Overview

This document defines the **complete state machine** for transfers (payouts) in Zwitch. Understanding these states is critical for reliable money movement.

## Transfer States

### 1. `pending`
**Meaning:** Transfer initiated, awaiting processing.

**When it occurs:**
- Immediately after creating transfer via API
- Transfer is queued for processing

**What it means:**
- Transfer request is valid
- Not yet sent to bank/UPI network
- Money is still in your account

**Can transition to:**
- `processing` (transfer being processed)
- `cancelled` (transfer cancelled, if supported)

**Is reversible:** Yes (can be cancelled before processing)

**What to do:**
- Store transfer ID
- Monitor for status changes
- Don't mark as completed yet

---

### 2. `processing`
**Meaning:** Transfer is being processed by banking partner.

**When it occurs:**
- Transfer sent to bank/UPI network
- Bank is processing the transfer
- Money is in transit

**What it means:**
- Transfer is being processed
- Money may or may not reach beneficiary (still uncertain)
- Usually takes minutes to hours

**Can transition to:**
- `completed` (transfer successful)
- `failed` (transfer rejected)

**Is reversible:** No (once processing, it will complete or fail)

**What to do:**
- Show "Processing" status
- Wait for final status (webhook)
- Don't mark as completed yet
- Don't retry (wait for outcome)

---

### 3. `completed`
**Meaning:** Transfer successful, money sent to beneficiary.

**When it occurs:**
- Bank confirmed transfer
- Money debited from your account
- Money credited to beneficiary account

**What it means:**
- Transfer is successful
- Money is in beneficiary's account
- This is a **terminal state** (cannot change)

**Can transition to:**
- None (terminal state)

**Is reversible:** No (irreversible - money is sent)

**What to do:**
- Mark transfer as completed
- Update beneficiary/seller records
- Send confirmation notification
- Log for accounting
- **This is the only state where transfer is successful**

---

### 4. `failed`
**Meaning:** Transfer was rejected or failed.

**When it occurs:**
- Insufficient balance in your account
- Invalid beneficiary account
- Bank rejected transfer
- Network/system error
- Beneficiary account closed/frozen

**What it means:**
- Transfer did not succeed
- No money was transferred
- Money is still in your account (if it failed before debit)

**Can transition to:**
- None (terminal state for this transfer)
- You can create new transfer (new transfer_id)

**Is reversible:** No (this transfer failed, but you can retry)

**What to do:**
- Mark transfer as failed
- Log failure reason
- Notify operations team
- Retry transfer (if appropriate)
- Notify beneficiary about delay

**Common failure reasons:**
- `insufficient_balance`: Not enough money in your account
- `invalid_account`: Beneficiary account doesn't exist or is invalid
- `bank_rejection`: Bank rejected the transfer
- `network_error`: Temporary network issue
- `account_frozen`: Beneficiary account is frozen/closed

---

### 5. `cancelled`
**Meaning:** Transfer was cancelled.

**When it occurs:**
- You cancelled transfer via API (if supported)
- Transfer cancelled via dashboard
- Cancelled before processing started

**What it means:**
- Transfer is no longer valid
- No money was transferred
- Money is still in your account

**Can transition to:**
- None (terminal state)

**Is reversible:** No (cancelled transfer cannot be revived)

**What to do:**
- Mark transfer as cancelled
- Log cancellation reason
- Create new transfer if needed

**Note:** Cancellation may only be possible in `pending` state, not after `processing` starts.

---

## State Transition Diagram

```
                    ┌─────────┐
                    │ pending │
                    └────┬────┘
                         │
        ┌────────────────┼──────────────┐
        │                │               │
        ▼                ▼               ▼
   ┌──────────┐     ┌──────────┐   ┌──────────┐
   │cancelled │     │processing│   │ (stays)  │
   └──────────┘     └────┬─────┘   └──────────┘
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
- `cancelled` 🚫

**Non-terminal states:**
- `pending` (can become processing or cancelled)
- `processing` (can become completed or failed)

## Critical Rules

### ✅ Safe to Mark as Completed:
- **Only when status is `completed`**
- Verify via webhook signature
- Check idempotency

### ❌ Never Mark as Completed When:
- Status is `pending` (transfer not started)
- Status is `processing` (transfer may still fail)
- Status is `failed` or `cancelled`

### State Verification:
- Always verify final state via webhook
- Use API to verify if webhook is delayed: `GET /v1/transfers/{id}`
- Don't trust intermediate states

## Database Representation

```sql
CREATE TABLE transfers (
  transfer_id VARCHAR(255) PRIMARY KEY,
  account_id VARCHAR(255) NOT NULL,
  beneficiary_id VARCHAR(255) NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  status VARCHAR(50) NOT NULL,  -- pending, processing, completed, failed, cancelled
  failure_reason VARCHAR(255),
  fees DECIMAL(10, 2),
  
  created_at TIMESTAMP,
  processing_started_at TIMESTAMP,  -- When status changed to 'processing'
  completed_at TIMESTAMP,           -- Only set when status = 'completed'
  failed_at TIMESTAMP,               -- Only set when status = 'failed'
  cancelled_at TIMESTAMP,            -- Only set when status = 'cancelled'
  
  metadata JSONB,
  
  -- Add constraint to ensure only appropriate timestamp is set
  CHECK (
    (status = 'completed' AND completed_at IS NOT NULL) OR
    (status = 'failed' AND failed_at IS NOT NULL) OR
    (status = 'cancelled' AND cancelled_at IS NOT NULL) OR
    (status IN ('pending', 'processing'))
  )
);
```

## Webhook Events

Each state change triggers a webhook:

| State | Webhook Event |
|-------|---------------|
| `pending` | `transfer.created` |
| `processing` | `transfer.processing` |
| `completed` | `transfer.completed` |
| `failed` | `transfer.failed` |
| `cancelled` | `transfer.cancelled` |

## Handling Failed Transfers

### Failure Reasons and Actions

| Failure Reason | What It Means | What to Do |
|----------------|---------------|------------|
| `insufficient_balance` | Not enough money in your account | Check balance, add funds, retry |
| `invalid_account` | Beneficiary account doesn't exist | Verify beneficiary, update if needed, retry |
| `bank_rejection` | Bank rejected transfer | Contact beneficiary, verify account, retry |
| `network_error` | Temporary network issue | Retry immediately |
| `account_frozen` | Beneficiary account frozen | Contact beneficiary, resolve issue |
| `timeout` | Transfer timed out | Retry transfer |

### Retry Strategy

1. **For transient failures** (network_error, timeout):
   - Retry immediately or after short delay
   - May succeed on retry

2. **For account issues** (invalid_account, account_frozen):
   - Verify beneficiary details
   - Contact beneficiary if needed
   - Update beneficiary if incorrect
   - Retry after fixing

3. **For balance issues** (insufficient_balance):
   - Check account balance
   - Add funds if needed
   - Retry transfer

4. **For permanent failures**:
   - Log for manual review
   - Don't retry automatically
   - Notify operations team

## Common Mistakes

### ❌ Mistake 1: Marking as Completed on `processing`
```python
# WRONG
if transfer.status == 'processing':
    mark_settlement_as_completed()  # ❌ Transfer may still fail!
```

### ✅ Correct: Only on `completed`
```python
# CORRECT
if transfer.status == 'completed':
    mark_settlement_as_completed()  # ✅ Transfer is final
```

### ❌ Mistake 2: Not Handling Failures
```python
# WRONG - Doesn't handle failed transfers
if transfer.status == 'completed':
    mark_settlement_as_completed()
# What about failed? ❌
```

### ✅ Correct: Handle All Terminal States
```python
# CORRECT
if transfer.status == 'completed':
    mark_settlement_as_completed()
elif transfer.status == 'failed':
    handle_transfer_failure(transfer)
    retry_if_appropriate(transfer)
```

## State Checking Best Practices

1. **Webhooks are primary source of truth**
   - Don't poll unnecessarily
   - But verify via API if webhook delayed

2. **Check idempotency**
   - Don't process same state change twice
   - Use transfer_id + status as idempotency key

3. **Handle all states**
   - Don't ignore failed transfers
   - Retry when appropriate
   - Notify beneficiaries of delays

4. **Log state transitions**
   - Track when and why states change
   - Useful for debugging and audit

5. **Monitor failure rates**
   - Alert if failure rate is high
   - Investigate common failure reasons

## Transfer Timing

**Typical timelines:**
- `pending` → `processing`: Seconds to minutes
- `processing` → `completed`: Minutes to hours
  - IMPS: Usually within minutes
  - NEFT: May take hours (banking hours)
  - RTGS: Usually within hours (banking hours)
  - UPI: Usually within minutes

**Factors affecting timing:**
- Banking hours (NEFT/RTGS may be delayed outside hours)
- Bank processing time
- Network conditions
- Transfer amount (large amounts may take longer)

## Summary

- **5 states total:** pending, processing, completed, failed, cancelled
- **3 terminal states:** completed, failed, cancelled
- **Only `completed` = money sent**
- **Always verify via webhook**
- **Handle failures properly** (retry, notify, log)
- **Monitor failure rates**

Understanding transfer states prevents financial errors and ensures reliable payouts.

## Related Documentation

- [Settlement Flow](../flows/settlement_flow.md) - Using transfers for settlements
- [Refund Flow](../flows/refund_flow.md) - Using transfers for refunds
- [Transfers API](../api/07_transfers.md) - Transfer API details

