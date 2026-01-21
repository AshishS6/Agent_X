# Payin Happy Path: Complete Flow

## Overview

This document describes the **successful end-to-end flow** of a customer paying you (payin/collection). This is the "happy path" where everything works correctly.

## Flow Diagram

```
Customer → Payment Initiation → Zwitch Processing → Your Account → Webhook → Your System
```

## Step-by-Step Flow

### Step 1: Customer Initiates Payment

**What happens:**
- Customer clicks "Pay Now" on your website/app
- Customer selects payment method (UPI, card, net banking, etc.)

**What you do:**
- Display payment options
- Prepare order details

**What to store:**
- Order ID in your database
- Customer information
- Payment amount
- Order status: `pending_payment`

---

### Step 2: Create Payment Request (Your Backend)

**API Call:** `POST /v1/accounts/{account_id}/payments/upi/collect` (for UPI)
**OR** `POST /v1/pg/payment_token` (for Payment Gateway)

**What happens:**
- Your backend creates a payment request with Zwitch
- Zwitch generates payment details (QR code, payment link, or payment token)

**Request Example:**
```json
{
  "amount": 1000.00,
  "expiry_in_minutes": 30,
  "remark": "Order #12345",
  "merchant_reference_id": "order_12345",
  "metadata": {
    "order_id": "order_12345",
    "customer_id": "cust_789"
  }
}
```

**Response Example:**
```json
{
  "id": "pay_abc123",
  "status": "pending",
  "upi_details": {
    "qr_code": "data:image/png;base64,...",
    "payment_link": "https://pay.zwitch.io/pay/pay_abc123"
  }
}
```

**What you do:**
- Store `payment_id` (e.g., `pay_abc123`) in your database
- Link `payment_id` to your `order_id`
- Update order status: `payment_initiated`
- Display QR code or payment link to customer

**What to store in DB:**
```sql
orders:
  - order_id: "order_12345"
  - payment_id: "pay_abc123"  -- Link to Zwitch payment
  - status: "payment_initiated"
  - amount: 1000.00
  - created_at: "2024-01-15T10:00:00Z"

payments:
  - payment_id: "pay_abc123"
  - order_id: "order_12345"
  - status: "pending"
  - amount: 1000.00
  - created_at: "2024-01-15T10:00:00Z"
```

---

### Step 3: Customer Completes Payment

**What happens:**
- Customer scans QR code or clicks payment link
- Customer authorizes payment in their UPI app/bank app
- Money is debited from customer's account

**What you do:**
- Nothing yet (you're waiting for webhook)
- Customer sees "Payment Processing" on your UI

**Note:** Do NOT mark payment as successful based on customer's confirmation alone. Wait for webhook.

---

### Step 4: Zwitch Processes Payment

**What happens:**
- Zwitch receives payment confirmation from bank/UPI network
- Payment status changes: `pending` → `processing` → `completed`
- Money is credited to your virtual account
- Your account balance increases

**Timeline:**
- Usually happens within seconds to minutes
- Can take up to a few minutes in some cases

---

### Step 5: Webhook Received (Your Backend)

**Webhook Event:** `payment.completed`

**What happens:**
- Zwitch sends HTTP POST to your webhook endpoint
- Payload contains payment details

**Webhook Payload:**
```json
{
  "event": "payment.completed",
  "data": {
    "id": "pay_abc123",
    "account_id": "acc_xyz789",
    "status": "completed",
    "amount": 1000.00,
    "merchant_reference_id": "order_12345",
    "completed_at": "2024-01-15T10:05:30Z"
  },
  "timestamp": "2024-01-15T10:05:30Z",
  "signature": "sha256=..."
}
```

**What you do:**
1. **Verify webhook signature** (CRITICAL - see risks/webhook_signature_verification.md)
2. **Check idempotency** (ensure you haven't processed this webhook before)
3. **Update database:**
   ```sql
   UPDATE payments 
   SET status = 'completed',
       completed_at = '2024-01-15T10:05:30Z'
   WHERE payment_id = 'pay_abc123';
   
   UPDATE orders 
   SET status = 'paid',
       paid_at = '2024-01-15T10:05:30Z'
   WHERE order_id = 'order_12345';
   ```
4. **Trigger business logic:**
   - Send confirmation email to customer
   - Update inventory
   - Initiate order fulfillment
   - Update analytics
5. **Respond to webhook:** Return `200 OK` quickly (process asynchronously)

**What to store:**
- Payment completion timestamp
- Final payment status
- Webhook received timestamp (for audit)

---

### Step 6: Verify Payment Status (Optional but Recommended)

**API Call:** `GET /v1/payments/{payment_id}`

**When to do this:**
- After receiving webhook (to double-check)
- If webhook is delayed or you're unsure
- As part of reconciliation process

**What you do:**
- Call API to get latest payment status
- Compare with your database
- Reconcile any discrepancies

**Note:** Webhooks are the source of truth, but verification API is good for reconciliation.

---

### Step 7: Customer Sees Success

**What happens:**
- Customer is redirected to success page
- Customer receives confirmation email/SMS
- Order is marked as paid in your system

**What you do:**
- Display success message
- Show order confirmation
- Provide order tracking details

---

## Database Schema Recommendations

```sql
-- Orders table
CREATE TABLE orders (
  order_id VARCHAR(255) PRIMARY KEY,
  customer_id VARCHAR(255),
  amount DECIMAL(10, 2),
  status VARCHAR(50),  -- pending_payment, payment_initiated, paid, fulfilled, cancelled
  payment_id VARCHAR(255),  -- Links to payments table
  created_at TIMESTAMP,
  paid_at TIMESTAMP,
  metadata JSONB
);

-- Payments table
CREATE TABLE payments (
  payment_id VARCHAR(255) PRIMARY KEY,  -- Zwitch payment ID
  order_id VARCHAR(255),
  account_id VARCHAR(255),  -- Your Zwitch virtual account
  amount DECIMAL(10, 2),
  status VARCHAR(50),  -- pending, processing, completed, failed, expired
  merchant_reference_id VARCHAR(255),
  created_at TIMESTAMP,
  completed_at TIMESTAMP,
  webhook_received_at TIMESTAMP,
  metadata JSONB,
  FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- Webhook events table (for idempotency)
CREATE TABLE webhook_events (
  event_id VARCHAR(255) PRIMARY KEY,  -- Use payment_id + timestamp
  payment_id VARCHAR(255),
  event_type VARCHAR(100),
  payload JSONB,
  processed BOOLEAN DEFAULT FALSE,
  received_at TIMESTAMP,
  processed_at TIMESTAMP
);
```

## Critical Checkpoints

### ✅ Must Do:
1. **Store payment_id immediately** after creating payment request
2. **Verify webhook signature** before processing
3. **Check idempotency** to prevent duplicate processing
4. **Update database atomically** (use transactions)
5. **Respond to webhook quickly** (200 OK, then process async)
6. **Log all webhook events** for audit trail

### ❌ Must NOT Do:
1. **Don't mark payment successful** based on customer confirmation alone
2. **Don't process webhook without signature verification**
3. **Don't process same webhook twice** (idempotency check)
4. **Don't expose API keys** in frontend code
5. **Don't create payment tokens** in client-side JavaScript

## Timeline Example

```
10:00:00 - Customer clicks "Pay Now"
10:00:05 - Your backend creates payment request
10:00:06 - Payment ID received: pay_abc123
10:00:10 - Customer scans QR code
10:00:15 - Customer authorizes in UPI app
10:00:20 - Zwitch receives payment confirmation
10:00:25 - Payment status: processing
10:00:30 - Payment status: completed
10:00:31 - Webhook sent to your server
10:00:32 - Your webhook handler receives event
10:00:33 - Database updated, order marked as paid
10:00:34 - Customer sees success page
```

## Success Criteria

A payin is successful when:
- ✅ Payment status is `completed` (from webhook or API)
- ✅ Your database shows order as `paid`
- ✅ Your virtual account balance increased
- ✅ Customer received confirmation
- ✅ Webhook was processed successfully

## Next Steps

After successful payin:
- Fulfill the order (ship product, activate service, etc.)
- Update customer account
- Send notifications
- Update analytics/reporting

## Related Documentation

- [Payin Failure Path](./payin_failure_path.md) - What happens when things go wrong
- [Payment Status Lifecycle](../states/payment_status_lifecycle.md) - All possible states
- [Webhook Signature Verification](../risks/webhook_signature_verification.md) - Security
- [Polling vs Webhooks](../decisions/polling_vs_webhooks.md) - Why webhooks are preferred

