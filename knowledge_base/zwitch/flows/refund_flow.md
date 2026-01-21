# Refund Flow: Returning Money to Customers

## Overview

This document describes how to process refunds when you need to return money to customers. In Zwitch, refunds are typically processed as **transfers** (payouts) to the customer's bank account or UPI ID.

## Important Note

**Refunds are a type of payout/transfer**, not a separate API endpoint. You use the Transfers API (`/v1/transfers`) to send money back to customers.

## When to Issue Refunds

Common scenarios:
- Customer requests refund (product return, service cancellation)
- Order cancelled before fulfillment
- Payment error (double charge, incorrect amount)
- Service not delivered as promised
- Regulatory/compliance requirement

## Refund Flow Diagram

```
Refund Request → Create Beneficiary (if needed) → Transfer to Customer → Webhook → Update Order
```

## Step-by-Step Refund Flow

### Step 1: Validate Refund Request

**What you do:**
- Verify original payment exists and is `completed`
- Check refund eligibility (time limits, policy, etc.)
- Calculate refund amount (full or partial)
- Verify sufficient balance in your virtual account

**What to check:**
```sql
-- Check original payment
SELECT * FROM payments 
WHERE payment_id = 'pay_abc123' 
AND status = 'completed';

-- Check your account balance
-- (via API: GET /v1/accounts/{account_id}/balance)
```

**Business Rules:**
- Can only refund completed payments
- Refund amount ≤ original payment amount
- Must have sufficient balance
- Check refund policy (e.g., refunds within 7 days only)

---

### Step 2: Get Customer Payment Details

**What you do:**
- Retrieve original payment details from Zwitch API
- Extract customer's payment method details (if available)
- Get customer's bank account or UPI ID (if stored)

**API Call:** `GET /v1/payments/{payment_id}`

**Response may include:**
```json
{
  "id": "pay_abc123",
  "amount": 1000.00,
  "status": "completed",
  "payment_method": "upi",
  "upi_details": {
    "payer_vpa": "customer@upi"
  }
}
```

**Note:** You may need to store customer payment details at the time of original payment for refunds.

---

### Step 3: Create or Retrieve Beneficiary

**For Bank Account Refunds:**
- If customer paid via bank transfer/net banking, you need their bank account details
- Create beneficiary if not exists: `POST /v1/beneficiaries/bank-account`
- Or retrieve existing beneficiary if customer has refunded before

**For UPI Refunds:**
- If customer paid via UPI, you may be able to refund to their UPI ID
- Check if Zwitch supports UPI-to-UPI refunds (verify current API capabilities)
- May need to create beneficiary with UPI details

**API Call:** `POST /v1/beneficiaries/bank-account`

**Request:**
```json
{
  "name": "John Doe",
  "account_number": "1234567890",
  "ifsc": "HDFC0001234",
  "account_type": "savings"
}
```

**Best Practice:**
- Store customer payment details (bank account, UPI ID) when they make first payment
- Reuse beneficiary for future refunds
- Verify beneficiary before using for refund

---

### Step 4: Initiate Refund Transfer

**API Call:** `POST /v1/transfers`

**What you do:**
- Create transfer from your virtual account to customer's beneficiary
- Use original payment ID in metadata for tracking
- Set appropriate remark (e.g., "Refund for Order #12345")

**Request:**
```json
{
  "account_id": "acc_xyz789",
  "beneficiary_id": "ben_customer123",
  "amount": 1000.00,
  "currency": "INR",
  "remark": "Refund for payment pay_abc123",
  "reference_id": "refund_order_12345",
  "metadata": {
    "refund_type": "full",
    "original_payment_id": "pay_abc123",
    "original_order_id": "order_12345",
    "refund_reason": "customer_request"
  }
}
```

**Response:**
```json
{
  "id": "trf_refund123",
  "account_id": "acc_xyz789",
  "beneficiary_id": "ben_customer123",
  "amount": 1000.00,
  "status": "processing",
  "fees": {
    "amount": 2.50,
    "currency": "INR"
  },
  "created_at": "2024-01-15T11:00:00Z"
}
```

**What to store:**
```sql
INSERT INTO refunds (
  refund_id,           -- Use transfer ID: trf_refund123
  original_payment_id, -- pay_abc123
  order_id,            -- order_12345
  amount,
  status,              -- processing
  created_at
) VALUES (...);
```

---

### Step 5: Handle Refund Webhook

**Webhook Event:** `transfer.completed` (for successful refund)
**OR** `transfer.failed` (if refund fails)

**Webhook Payload:**
```json
{
  "event": "transfer.completed",
  "data": {
    "id": "trf_refund123",
    "status": "completed",
    "amount": 1000.00,
    "metadata": {
      "original_payment_id": "pay_abc123",
      "refund_type": "full"
    },
    "completed_at": "2024-01-15T11:05:00Z"
  }
}
```

**What you do:**
1. Verify webhook signature
2. Check idempotency
3. Update database:
   ```sql
   UPDATE refunds 
   SET status = 'completed',
       completed_at = '2024-01-15T11:05:00Z'
   WHERE refund_id = 'trf_refund123';
   
   UPDATE orders 
   SET status = 'refunded',
       refunded_at = '2024-01-15T11:05:00Z'
   WHERE order_id = 'order_12345';
   ```
4. Notify customer (email/SMS)
5. Update inventory/fulfillment system
6. Log for accounting/reconciliation

---

### Step 6: Handle Refund Failure

**If refund transfer fails:**

**Webhook:**
```json
{
  "event": "transfer.failed",
  "data": {
    "id": "trf_refund123",
    "status": "failed",
    "failure_reason": "insufficient_balance"  // or "invalid_account", etc.
  }
}
```

**What you do:**
1. Update refund status to `failed`
2. Log failure reason
3. Notify operations team (manual intervention may be needed)
4. Retry refund if appropriate (after resolving issue)
5. Notify customer about delay

**Common failure reasons:**
- Insufficient balance in your account
- Invalid beneficiary account
- Bank rejection
- Network/system errors

---

## Partial Refunds

**When to use:**
- Partial product return
- Service partially delivered
- Partial cancellation

**How to process:**
- Same flow as full refund
- Use partial amount in transfer
- Update order status to `partially_refunded`
- Track remaining refundable amount

**Example:**
```json
{
  "amount": 500.00,  // Partial: original was 1000.00
  "metadata": {
    "refund_type": "partial",
    "original_payment_id": "pay_abc123",
    "refund_reason": "partial_return"
  }
}
```

## Multiple Refunds for Same Payment

**Scenario:** Customer paid ₹1000, you refund ₹300, then refund remaining ₹700

**What to do:**
1. Track total refunded amount per payment
2. Ensure: `sum(refunds) ≤ original_payment_amount`
3. Prevent over-refunding (check before each refund)
4. Update order status appropriately

**Database check:**
```sql
SELECT SUM(amount) as total_refunded 
FROM refunds 
WHERE original_payment_id = 'pay_abc123';

-- Ensure: total_refunded + new_refund_amount <= original_payment_amount
```

## Refund Fees

**Important:** Check your Zwitch pricing:
- Some refunds may have fees
- Fees may be deducted from refund amount or charged separately
- Factor fees into refund calculations

**Example:**
- Original payment: ₹1000
- Refund amount: ₹1000
- Refund fee: ₹2.50
- Customer receives: ₹997.50 (if fee deducted)
- OR: You pay ₹1002.50 total (₹1000 refund + ₹2.50 fee)

## Database Schema for Refunds

```sql
CREATE TABLE refunds (
  refund_id VARCHAR(255) PRIMARY KEY,  -- Transfer ID from Zwitch
  original_payment_id VARCHAR(255) NOT NULL,
  order_id VARCHAR(255) NOT NULL,
  beneficiary_id VARCHAR(255),
  amount DECIMAL(10, 2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'INR',
  status VARCHAR(50),  -- processing, completed, failed, cancelled
  refund_type VARCHAR(50),  -- full, partial
  refund_reason VARCHAR(255),
  failure_reason VARCHAR(255),
  created_at TIMESTAMP,
  completed_at TIMESTAMP,
  failed_at TIMESTAMP,
  metadata JSONB,
  FOREIGN KEY (original_payment_id) REFERENCES payments(payment_id),
  FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- Index for tracking refunds per payment
CREATE INDEX idx_refunds_payment ON refunds(original_payment_id);
```

## Best Practices

### ✅ Do:
1. **Store customer payment details** at time of payment (for future refunds)
2. **Verify sufficient balance** before initiating refund
3. **Track refund amounts** to prevent over-refunding
4. **Use metadata** to link refunds to original payments/orders
5. **Notify customers** when refund is initiated and completed
6. **Handle refund failures** gracefully (retry, manual intervention)
7. **Maintain audit trail** (who, when, why, how much)

### ❌ Don't:
1. **Don't refund without verifying** original payment
2. **Don't over-refund** (check total refunded amount)
3. **Don't ignore refund failures** (customer expects money back)
4. **Don't refund to wrong account** (verify beneficiary)
5. **Don't process refunds without proper authorization** (fraud prevention)

## Refund Policy Considerations

**Time Limits:**
- Define refund window (e.g., 7 days, 30 days)
- Check policy before processing

**Partial vs Full:**
- Define when partial refunds are allowed
- Track partial refunds properly

**Fees:**
- Who pays refund fees? (you or customer)
- Communicate clearly to customers

**Processing Time:**
- Set customer expectations (refunds may take 1-3 business days)
- Communicate timeline

## Reconciliation

**Regular reconciliation:**
- Match refund transfers with refund records
- Verify all refunds were processed
- Check for failed refunds that need retry
- Ensure accounting records are accurate

## Summary

- **Refunds = Transfers** (use `/v1/transfers` API)
- **Require beneficiary** (customer's bank account or UPI)
- **Track refunds** to prevent over-refunding
- **Handle failures** (insufficient balance, invalid account, etc.)
- **Notify customers** at each step
- **Maintain audit trail** for compliance

Refunds are critical for customer trust. Handle them carefully and transparently.

## Related Documentation

- [Transfers API](../api/07_transfers.md) - Transfer API details
- [Beneficiaries API](../api/06_beneficiaries.md) - Creating beneficiaries
- [Transfer Status Lifecycle](../states/transfer_status_lifecycle.md) - Transfer states
- [Double Credit Risk](../risks/double_credit_risk.md) - Preventing over-refunds

