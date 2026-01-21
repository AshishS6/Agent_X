# Settlement Flow: Platform-to-Seller Money Movement

## Overview

This document describes the **settlement flow** for platforms (marketplaces, multi-vendor systems) that need to pay sellers after deducting commissions. This is a critical flow for marketplace and platform businesses.

## What is Settlement?

**Settlement** is the process of:
1. Collecting money from customers (payin)
2. Holding funds temporarily (escrow)
3. Calculating commissions/fees
4. Transferring remaining amount to sellers (payout)

## Settlement Flow Diagram

```
Customer Payment → Escrow Account → Calculate Commission → Transfer to Seller → Update Records
```

## Use Cases

### Marketplace Model:
- Customer buys product from Seller A
- Platform collects ₹1000
- Platform takes 10% commission (₹100)
- Platform pays Seller A: ₹900

### Commission-Based Platform:
- Service provider completes job
- Customer pays ₹5000
- Platform takes 20% commission (₹1000)
- Platform pays service provider: ₹4000

### Escrow Model:
- Customer pays for service
- Funds held in escrow
- Service delivered
- Funds released to seller (minus commission)

## Step-by-Step Settlement Flow

### Step 1: Customer Payment Received

**What happens:**
- Customer pays for order/service
- Payment webhook received: `payment.completed`
- Money is in your virtual account (or escrow account)

**Webhook:**
```json
{
  "event": "payment.completed",
  "data": {
    "id": "pay_abc123",
    "amount": 1000.00,
    "merchant_reference_id": "order_12345"
  }
}
```

**What you do:**
- Store payment details
- Link payment to order
- Identify seller (from order metadata)
- Mark order as `paid_pending_settlement`

**Database:**
```sql
UPDATE orders 
SET 
  status = 'paid_pending_settlement',
  payment_id = 'pay_abc123',
  paid_at = '2024-01-15T10:00:00Z'
WHERE order_id = 'order_12345';
```

---

### Step 2: Determine Settlement Trigger

**When to settle:**

**Option A: Immediate Settlement**
- Settle as soon as payment received
- Good for: Digital products, instant services

**Option B: Delivery-Based Settlement**
- Wait for order fulfillment confirmation
- Good for: Physical products, services requiring delivery

**Option C: Time-Based Settlement**
- Settle daily/weekly (batch processing)
- Good for: High-volume platforms, reducing transfer fees

**Option D: Manual Settlement**
- Admin triggers settlement
- Good for: Dispute resolution, quality checks

**What you do:**
- Implement settlement trigger logic
- For delivery-based: Wait for fulfillment webhook/API call
- For time-based: Run scheduled job (cron)
- For manual: Provide admin interface

---

### Step 3: Calculate Settlement Amount

**What you do:**
- Get order details (amount, seller, commission rate)
- Calculate commission/fees
- Calculate seller payout amount

**Calculation Example:**
```python
# Pseudo-code
order_amount = 1000.00
commission_rate = 0.10  # 10%
platform_fee = 5.00     # Fixed fee

commission = order_amount * commission_rate  # 100.00
seller_payout = order_amount - commission - platform_fee  # 895.00

# Verify: commission + platform_fee + seller_payout = order_amount
# 100 + 5 + 895 = 1000 ✓
```

**What to store:**
```sql
INSERT INTO settlements (
  settlement_id,
  order_id,
  payment_id,
  seller_id,
  order_amount,      -- 1000.00
  commission_rate,   -- 0.10
  commission_amount, -- 100.00
  platform_fee,      -- 5.00
  seller_payout,     -- 895.00
  status,            -- pending
  created_at
) VALUES (...);
```

**Important:**
- Store all calculation details (for audit)
- Handle rounding correctly (currency precision)
- Support different commission models (percentage, fixed, tiered)

---

### Step 4: Verify Seller Beneficiary

**What you do:**
- Check if seller has beneficiary created
- If not, create beneficiary (may require seller to provide bank details)
- Verify beneficiary is active and verified

**API Call:** `GET /v1/beneficiaries/{beneficiary_id}`

**Check:**
- Beneficiary status: `active`
- Verification status: `verified` (if required)

**If beneficiary missing:**
- Trigger seller onboarding flow
- Request bank account details
- Create beneficiary: `POST /v1/beneficiaries/bank-account`
- Wait for verification (if required)

**Best Practice:**
- Onboard sellers with bank details during registration
- Verify beneficiaries before allowing listings
- Re-verify periodically (compliance)

---

### Step 5: Initiate Settlement Transfer

**API Call:** `POST /v1/transfers`

**What you do:**
- Create transfer from your account to seller's beneficiary
- Use settlement ID in metadata for tracking
- Set appropriate remark

**Request:**
```json
{
  "account_id": "acc_your_account",
  "beneficiary_id": "ben_seller123",
  "amount": 895.00,
  "currency": "INR",
  "remark": "Settlement for order_12345",
  "reference_id": "settlement_order_12345",
  "metadata": {
    "settlement_id": "sett_xyz789",
    "order_id": "order_12345",
    "payment_id": "pay_abc123",
    "seller_id": "seller_123",
    "commission_amount": 100.00,
    "platform_fee": 5.00
  }
}
```

**Response:**
```json
{
  "id": "trf_settlement123",
  "status": "processing",
  "amount": 895.00,
  "fees": {
    "amount": 2.50,
    "currency": "INR"
  },
  "created_at": "2024-01-15T11:00:00Z"
}
```

**What to store:**
```sql
UPDATE settlements 
SET 
  transfer_id = 'trf_settlement123',
  status = 'processing',
  transfer_initiated_at = '2024-01-15T11:00:00Z'
WHERE settlement_id = 'sett_xyz789';
```

---

### Step 6: Handle Settlement Webhook

**Webhook Event:** `transfer.completed` (success)
**OR** `transfer.failed` (failure)

**Success Webhook:**
```json
{
  "event": "transfer.completed",
  "data": {
    "id": "trf_settlement123",
    "status": "completed",
    "amount": 895.00,
    "completed_at": "2024-01-15T11:05:00Z",
    "metadata": {
      "settlement_id": "sett_xyz789"
    }
  }
}
```

**What you do:**
1. Verify webhook signature
2. Check idempotency
3. Update settlement:
   ```sql
   UPDATE settlements 
   SET 
     status = 'completed',
     completed_at = '2024-01-15T11:05:00Z'
   WHERE settlement_id = 'sett_xyz789';
   ```
4. Update order:
   ```sql
   UPDATE orders 
   SET status = 'settled'
   WHERE order_id = 'order_12345';
   ```
5. Notify seller (email/SMS)
6. Update seller balance/ledger
7. Log for accounting

---

### Step 7: Handle Settlement Failure

**Failure Webhook:**
```json
{
  "event": "transfer.failed",
  "data": {
    "id": "trf_settlement123",
    "status": "failed",
    "failure_reason": "insufficient_balance"  // or "invalid_account", etc.
  }
}
```

**What you do:**
1. Update settlement status to `failed`
2. Log failure reason
3. Notify operations team
4. Retry settlement (if appropriate)
5. Notify seller about delay

**Common failures:**
- Insufficient balance (you spent the money already)
- Invalid beneficiary account
- Bank rejection
- Network/system errors

**Retry Strategy:**
- Check account balance
- Verify beneficiary
- Retry transfer
- If still fails, manual intervention needed

---

## Batch Settlements

**For time-based settlements (daily/weekly):**

**Process:**
1. Query all pending settlements for period
2. Group by seller (optional: combine multiple orders)
3. Calculate total payout per seller
4. Create single transfer per seller (or multiple if preferred)
5. Update all settlement records

**Benefits:**
- Reduce transfer fees (fewer transfers)
- Simplify reconciliation
- Better cash flow management

**Example:**
```
Seller A: 3 orders → ₹500 + ₹300 + ₹200 = ₹1000 total payout
Create 1 transfer of ₹1000 (instead of 3 transfers)
```

## Settlement Reversal

**When needed:**
- Order cancelled after settlement
- Fraud detected
- Dispute resolved in customer's favor
- Accounting error

**How to handle:**
- Create reverse transfer (seller → you)
- OR: Deduct from next settlement
- Update settlement status to `reversed`
- Maintain audit trail

**Important:**
- Get seller consent (if possible)
- Follow dispute resolution process
- Maintain proper documentation

## Database Schema

```sql
-- Settlements table
CREATE TABLE settlements (
  settlement_id VARCHAR(255) PRIMARY KEY,
  order_id VARCHAR(255) NOT NULL,
  payment_id VARCHAR(255) NOT NULL,
  seller_id VARCHAR(255) NOT NULL,
  transfer_id VARCHAR(255),  -- Zwitch transfer ID
  
  -- Amounts
  order_amount DECIMAL(10, 2) NOT NULL,
  commission_rate DECIMAL(5, 4),  -- e.g., 0.1000 for 10%
  commission_amount DECIMAL(10, 2),
  platform_fee DECIMAL(10, 2),
  seller_payout DECIMAL(10, 2) NOT NULL,
  transfer_fee DECIMAL(10, 2),  -- Fee charged by Zwitch
  
  -- Status
  status VARCHAR(50),  -- pending, processing, completed, failed, reversed
  
  -- Timestamps
  created_at TIMESTAMP,
  transfer_initiated_at TIMESTAMP,
  completed_at TIMESTAMP,
  failed_at TIMESTAMP,
  
  -- Metadata
  metadata JSONB,
  
  FOREIGN KEY (order_id) REFERENCES orders(order_id),
  FOREIGN KEY (payment_id) REFERENCES payments(payment_id)
);

-- Indexes
CREATE INDEX idx_settlements_seller ON settlements(seller_id);
CREATE INDEX idx_settlements_status ON settlements(status);
CREATE INDEX idx_settlements_order ON settlements(order_id);
```

## Best Practices

### ✅ Do:
1. **Calculate accurately** (double-check math)
2. **Store all amounts** (order, commission, fees, payout)
3. **Handle failures gracefully** (retry, manual intervention)
4. **Notify sellers** at each step
5. **Maintain audit trail** (who, when, how much, why)
6. **Reconcile regularly** (settlements vs transfers)
7. **Support different commission models** (percentage, fixed, tiered)
8. **Handle edge cases** (partial refunds, cancellations, disputes)

### ❌ Don't:
1. **Don't settle before order fulfillment** (unless digital/instant)
2. **Don't ignore settlement failures** (sellers expect payment)
3. **Don't over-settle** (verify calculations)
4. **Don't settle to unverified beneficiaries** (compliance risk)
5. **Don't skip audit logging** (regulatory requirement)

## Commission Models

**Percentage-based:**
- 10% of order amount
- Simple, common model

**Fixed fee:**
- ₹50 per transaction
- Good for low-value orders

**Tiered:**
- 0-1000: 15%
- 1001-5000: 12%
- 5000+: 10%
- Rewards high-volume sellers

**Hybrid:**
- 10% + ₹5 fixed fee
- Combines percentage and fixed

## Reconciliation

**Regular checks:**
- Match settlements with transfers
- Verify all settlements were processed
- Check for failed settlements
- Ensure accounting records match
- Verify commission calculations

## Summary

- **Settlement = Transfer** (use `/v1/transfers` API)
- **Calculate accurately** (commission, fees, payout)
- **Handle failures** (retry, manual intervention)
- **Notify sellers** (transparency builds trust)
- **Maintain audit trail** (compliance requirement)
- **Reconcile regularly** (catch errors early)

Settlements are critical for platform operations. Get them right.

## Related Documentation

- [Transfers API](../api/07_transfers.md) - Transfer API details
- [Merchant vs Platform](../concepts/merchant_vs_platform.md) - Platform model
- [Transfer Status Lifecycle](../states/transfer_status_lifecycle.md) - Transfer states
- [Reconciliation Failures](../risks/reconciliation_failures.md) - Handling discrepancies

