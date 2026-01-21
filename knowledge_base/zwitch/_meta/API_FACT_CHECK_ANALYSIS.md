# Zwitch API Fact Check Analysis

## Overview
This document analyzes the accuracy of a fintech assistant's response about Zwitch API services by comparing it against the official Zwitch documentation at [developers.zwitch.io](https://developers.zwitch.io).

## Critical Inaccuracies Found

### 1. ❌ Collections Endpoint - INCORRECT

**Assistant's Claim:**
- Endpoint: `POST /v1/collections`
- Endpoint: `GET /v1/collections/{collection_id}`

**Actual Zwitch Documentation:**
- **Correct Endpoint**: `POST /v1/accounts/{account_id}/payments/upi/collect`
- **Reference**: [Create UPI Collect Request](https://developers.zwitch.io/reference/payments-upi-collect-create)

**Analysis:**
- There is **NO** `/v1/collections` endpoint in Zwitch API
- Collections are handled through the **UPI Collect** API which requires:
  - An `account_id` path parameter (virtual account ID)
  - The endpoint is under `/v1/accounts/{account_id}/payments/upi/collect`
- To get collection details, use: `GET /v1/payments/{id}` (not `/v1/collections/{id}`)

**Correct Implementation:**
```javascript
// CORRECT - Create UPI Collect Request
const response = await fetch(
  `https://api.zwitch.io/v1/accounts/${accountId}/payments/upi/collect`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      remitter_vpa_handle: 'payer@upi',
      amount: 500.00,
      expiry_in_minutes: 30,
      remark: 'Test collection',
      merchant_reference_id: 'ref_123'
    })
  }
);
```

### 2. ❌ Payment Token Endpoint - INCORRECT

**Assistant's Claim:**
- Endpoint: `POST /v1/payments`
- Request body includes: `amount`, `currency`

**Actual Zwitch Documentation:**
- **Correct Endpoint**: `POST /v1/pg/sandbox/payment_token` (sandbox) or `POST /v1/pg/payment_token` (production)
- **Reference**: [Create Payment Token](https://developers.zwitch.io/reference/create-payment-token)

**Analysis:**
- Payment token creation is under the **Payment Gateway (PG)** namespace, not `/v1/payments`
- The endpoint is `/v1/pg/payment_token` (or `/v1/pg/sandbox/payment_token` for sandbox)
- This is specifically for Layer.js payment gateway integration

**Correct Implementation:**
```javascript
// CORRECT - Create Payment Token for Layer.js
const response = await fetch(
  'https://api.zwitch.io/v1/pg/sandbox/payment_token', // or /v1/pg/payment_token for production
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      amount: 500.00,
      currency: 'INR',
      order_id: 'order_123',
      customer: {
        name: 'John Doe',
        email: 'john@example.com',
        phone: '+919876543210'
      }
    })
  }
);
```

### 3. ❌ Payment Processing Endpoint - DOES NOT EXIST

**Assistant's Claim:**
- Endpoint: `POST /v1/payments/{payment_id}/process`
- Request body includes: `payment_method`

**Actual Zwitch Documentation:**
- **This endpoint does NOT exist** in Zwitch API
- Payment processing for Layer.js happens client-side through the Layer.js library
- After creating a payment token, you use `Layer.checkout()` on the frontend
- Status can be checked using: `GET /v1/payments/token/{payment_token_id}/status`

**Analysis:**
- The assistant invented a non-existent endpoint
- Payment processing in Zwitch's payment gateway is handled through:
  1. Create payment token (server-side)
  2. Use Layer.js on frontend to process payment
  3. Check status using status check API

### 4. ✅ Transfers Endpoint - CORRECT

**Assistant's Claim:**
- Endpoint: `POST /v1/transfers`
- Endpoint: `GET /v1/transfers/{transfer_id}`

**Actual Zwitch Documentation:**
- **Correct**: `POST /v1/transfers`
- **Correct**: `GET /v1/transfers/{id}`
- **Reference**: [Create Transfer - Account Beneficiary](https://developers.zwitch.io/reference/transfers-virtual-accounts-create-to-account-beneficiary)

**Analysis:**
- The transfers endpoint is correct
- However, the assistant's example code is missing the required `account_id` parameter
- Correct request body should include:
  - `account_id` (required): Source virtual account ID
  - `beneficiary_id` (required): Beneficiary ID
  - `amount` (required): Transfer amount

**Correct Implementation:**
```javascript
// CORRECT - Create Transfer
const response = await fetch('https://api.zwitch.io/v1/transfers', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    account_id: 'acc_1234567890',  // REQUIRED - Missing in assistant's example
    beneficiary_id: 'ben_1234567890',
    amount: 1000.00,
    remark: 'Test transfer'
  })
});
```

## Service Categorization Issues

### Assistant's Categorization:
1. **Transfers**: Sending funds to bank accounts ✅
2. **Collections**: Receiving payments from customers ❌ (incorrect endpoint)
3. **Payment Gateway**: Processing online payments ❌ (incorrect endpoint)

### Correct Zwitch Service Structure:

1. **Transfers** (`/v1/transfers`)
   - Purpose: Send funds from virtual accounts to bank accounts
   - Requires: Beneficiary creation first
   - ✅ Correctly identified by assistant

2. **Collections (UPI Collect)** (`/v1/accounts/{account_id}/payments/upi/collect`)
   - Purpose: Receive payments via UPI
   - Requires: Virtual account with VPA
   - ❌ Assistant used wrong endpoint (`/v1/collections`)

3. **Payment Gateway (Layer.js)** (`/v1/pg/payment_token`)
   - Purpose: Process payments through hosted payment page
   - Supports: Multiple payment methods (UPI, cards, net banking)
   - ❌ Assistant used wrong endpoint (`/v1/payments`)

## Authentication Issues

**Assistant's Code:**
```javascript
'Authorization': `Bearer ${process.env.ZWITCH_API_KEY}`
```

**Correct Format:**
```javascript
'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`
```

**Analysis:**
- Zwitch uses Bearer token with format: `ACCESS_KEY:SECRET_KEY`
- The assistant's code suggests a single API key, which is incorrect
- Zwitch requires both Access Key and Secret Key separated by a colon

## Summary of Errors

| Issue | Assistant's Claim | Actual | Status |
|-------|------------------|--------|--------|
| Collections Endpoint | `POST /v1/collections` | `POST /v1/accounts/{account_id}/payments/upi/collect` | ❌ Wrong |
| Get Collection | `GET /v1/collections/{id}` | `GET /v1/payments/{id}` | ❌ Wrong |
| Payment Token | `POST /v1/payments` | `POST /v1/pg/payment_token` | ❌ Wrong |
| Payment Process | `POST /v1/payments/{id}/process` | Does not exist | ❌ Wrong |
| Transfers Endpoint | `POST /v1/transfers` | `POST /v1/transfers` | ✅ Correct |
| Transfer Request Body | Missing `account_id` | Requires `account_id` | ⚠️ Incomplete |
| Authentication Format | Single API key | `ACCESS_KEY:SECRET_KEY` | ❌ Wrong |

## Recommendations

1. **For Collections**: Use UPI Collect API at `/v1/accounts/{account_id}/payments/upi/collect`
2. **For Payment Gateway**: Use Layer.js with payment token at `/v1/pg/payment_token`
3. **For Transfers**: Add required `account_id` parameter
4. **Authentication**: Use correct format `Bearer ACCESS_KEY:SECRET_KEY`

## References

- [Zwitch API Documentation](https://developers.zwitch.io)
- [Create UPI Collect Request](https://developers.zwitch.io/reference/payments-upi-collect-create)
- [Create Payment Token](https://developers.zwitch.io/reference/create-payment-token)
- [Create Transfer](https://developers.zwitch.io/reference/transfers-virtual-accounts-create-to-account-beneficiary)

