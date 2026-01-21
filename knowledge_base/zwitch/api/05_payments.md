# Zwitch API — Payments

Zwitch supports multiple payment methods for collecting funds. The primary method is UPI Collect, which allows you to request payments from customers via UPI.

## Create UPI Collect Request
**POST** `/v1/accounts/{account_id}/payments/upi/collect`

### What this API does

Creates a UPI payment collection request. The customer can pay using any UPI app by scanning a QR code or using the payment link. This API generates a payment request that customers can fulfill via UPI.

### When to use this API

- ✅ You want to collect payments via UPI only
- ✅ You need QR codes or payment links for customers
- ✅ You're building a UPI-focused payment flow
- ✅ You want simple integration without full payment gateway features
- ✅ Customer is ready to pay (don't create payment requests prematurely)

### When NOT to use this API

- ❌ You need multiple payment methods (cards, net banking, wallets) → Use Payment Gateway (`/v1/pg/payment_token`) instead
- ❌ You want Layer.js integration → Use Payment Gateway API
- ❌ Customer hasn't confirmed payment intent → Wait until customer is ready
- ❌ You're testing without real account → Use sandbox environment
- ❌ You need recurring payments → Check if UPI Collect supports it or use Payment Gateway

### Required inputs

- `account_id` (path parameter): Your Zwitch virtual account ID that will receive the payment
- `amount` (required): Payment amount (minimum: ₹1.00)
- `expiry_in_minutes` (optional): Payment expiry time (default: 30 minutes, max: 1440 minutes)

### Common mistakes

1. **Creating payment requests too early** - Don't create payment requests before customer is ready to pay
2. **Not storing payment_id** - Always store the payment ID returned for tracking
3. **Marking as paid on `processing` status** - Only mark as paid when status is `completed` (see [Payment Status Lifecycle](../states/payment_status_lifecycle.md))
4. **Not handling expiry** - Monitor payment expiry and allow customers to create new requests
5. **Calling from frontend** - This API requires secret key, must be called from backend only
6. **Not using webhooks** - Don't poll for status, use webhooks for real-time updates

### Production recommendation

- **Always call from backend** - Never expose secret keys in frontend code
- **Use webhooks** - Set up webhooks for payment status updates (see [Polling vs Webhooks](../decisions/polling_vs_webhooks.md))
- **Store payment_id immediately** - Link payment_id to your order_id in database
- **Handle all statuses** - Implement handlers for completed, failed, expired, cancelled states
- **Implement idempotency** - Use `merchant_reference_id` to prevent duplicate payments
- **Monitor expiry** - Track payment expiry and notify customers or create new requests
- **Verify webhook signatures** - Always verify webhook signatures before processing (see [Webhook Signature Verification](../risks/webhook_signature_verification.md))

Creates a UPI payment collection request. The customer can pay using any UPI app by scanning a QR code or using the payment link.

### Path Parameters
- `account_id` (string, required): Virtual account ID that will receive the payment

### Request Body
```json
{
  "remitter_vpa_handle": "payer@upi",
  "amount": 100.50,
  "expiry_in_minutes": 30,
  "remark": "Order #123",
  "merchant_reference_id": "order_123",
  "metadata": {
    "order_id": "order_123",
    "customer_id": "cust_456"
  }
}
```

### Request Parameters
- `remitter_vpa_handle` (string, optional): Expected payer's UPI ID (for validation)
- `amount` (number, required): Payment amount (minimum: 1.00)
- `expiry_in_minutes` (integer, optional): Payment request expiry in minutes (default: 30, max: 1440)
- `remark` (string, optional): Payment remark/description (max: 100 characters)
- `merchant_reference_id` (string, optional): Your unique reference ID for tracking
- `metadata` (object, optional): Custom metadata key-value pairs

### Response
```json
{
  "id": "pay_1234567890",
  "account_id": "acc_1234567890",
  "amount": 100.50,
  "currency": "INR",
  "status": "pending",
  "payment_method": "upi",
  "upi_details": {
    "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANS...",
    "payment_link": "https://pay.zwitch.io/pay/pay_1234567890",
    "upi_id": "acc_1234567890@zwitch",
    "merchant_name": "Your Business Name"
  },
  "remitter_vpa_handle": "payer@upi",
  "remark": "Order #123",
  "merchant_reference_id": "order_123",
  "expires_at": "2024-01-15T11:00:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "metadata": {
    "order_id": "order_123",
    "customer_id": "cust_456"
  }
}
```

### Payment Status
- `pending`: Payment request created, awaiting payment
- `processing`: Payment received, being processed
- `completed`: Payment completed successfully
- `failed`: Payment failed
- `expired`: Payment request expired
- `cancelled`: Payment request cancelled

### Example (Node.js)
```js
const accountId = 'acc_1234567890';
const response = await fetch(`https://api.zwitch.io/v1/accounts/${accountId}/payments/upi/collect`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    amount: 100.50,
    expiry_in_minutes: 30,
    remark: 'Order #123',
    merchant_reference_id: 'order_123',
    metadata: {
      order_id: 'order_123',
      customer_id: 'cust_456'
    }
  })
});

const payment = await response.json();
console.log('Payment ID:', payment.id);
console.log('QR Code:', payment.upi_details.qr_code);
console.log('Payment Link:', payment.upi_details.payment_link);
```

### Example (Python)
```python
import requests

account_id = 'acc_1234567890'
url = f'https://api.zwitch.io/v1/accounts/{account_id}/payments/upi/collect'
headers = {
    'Authorization': f'Bearer {ACCESS_KEY}:{SECRET_KEY}',
    'Content-Type': 'application/json'
}
payload = {
    'amount': 100.50,
    'expiry_in_minutes': 30,
    'remark': 'Order #123',
    'merchant_reference_id': 'order_123',
    'metadata': {
        'order_id': 'order_123',
        'customer_id': 'cust_456'
    }
}

response = requests.post(url, json=payload, headers=headers)
payment = response.json()
print(f"Payment ID: {payment['id']}")
print(f"Payment Link: {payment['upi_details']['payment_link']}")
```

## List All Payments
**GET** `/v1/payments`

Returns a paginated list of all payments across all accounts.

### Query Parameters
- `page` (integer, optional): Page number (default: 1)
- `limit` (integer, optional): Number of results per page (default: 20, max: 100)
- `status` (string, optional): Filter by status (`pending`, `completed`, `failed`, `expired`, `cancelled`)
- `account_id` (string, optional): Filter by account ID
- `from_date` (string, optional): Start date in `YYYY-MM-DD` format
- `to_date` (string, optional): End date in `YYYY-MM-DD` format

### Response
```json
{
  "data": [
    {
      "id": "pay_1234567890",
      "account_id": "acc_1234567890",
      "amount": 100.50,
      "currency": "INR",
      "status": "completed",
      "payment_method": "upi",
      "remark": "Order #123",
      "merchant_reference_id": "order_123",
      "created_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:32:15Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

### Example
```js
const url = 'https://api.zwitch.io/v1/payments?status=completed&page=1&limit=20';
const response = await fetch(url, {
  headers: {
    'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`
  }
});

const data = await response.json();
data.data.forEach(payment => {
  console.log(`${payment.id}: ₹${payment.amount} - ${payment.status}`);
});
```

## Get Payment by ID
**GET** `/v1/payments/{id}`

Returns detailed information for a specific payment.

### Path Parameters
- `id` (string, required): Payment ID

### Response
```json
{
  "id": "pay_1234567890",
  "account_id": "acc_1234567890",
  "amount": 100.50,
  "currency": "INR",
  "status": "completed",
  "payment_method": "upi",
  "upi_details": {
    "upi_id": "acc_1234567890@zwitch",
    "payer_vpa": "payer@upi",
    "transaction_id": "TXN123456789"
  },
  "remark": "Order #123",
  "merchant_reference_id": "order_123",
  "expires_at": "2024-01-15T11:00:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:32:15Z",
  "metadata": {
    "order_id": "order_123",
    "customer_id": "cust_456"
  }
}
```

### Example
```js
const paymentId = 'pay_1234567890';
const response = await fetch(`https://api.zwitch.io/v1/payments/${paymentId}`, {
  headers: {
    'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`
  }
});

const payment = await response.json();
console.log('Payment Status:', payment.status);
console.log('Amount:', payment.amount);
if (payment.status === 'completed') {
  console.log('Completed At:', payment.completed_at);
}
```

## Payment Webhooks

Zwitch sends webhook events for payment status changes. Configure webhooks in your dashboard to receive real-time notifications. See [Webhooks documentation](./10_webhooks.md) for details.

## Create Payment Token (for Layer.js)

**POST** `/v1/pg/payment_token` (Production)  
**POST** `/v1/pg/sandbox/payment_token` (Sandbox)

> **Note**: Payment token creation uses the Payment Gateway (`/v1/pg/`) namespace, not `/v1/payments/`

### What this API does

Creates a payment token for use with Layer.js payment gateway integration. This token is used to initialize the Layer.js payment UI on your frontend, which supports 150+ payment methods (cards, UPI, net banking, wallets).

### When to use this API

- ✅ You need multiple payment methods (cards, UPI, net banking, wallets)
- ✅ You're integrating Layer.js for web payments
- ✅ You want a comprehensive payment gateway solution
- ✅ Customer is on checkout page and ready to pay
- ✅ You need payment gateway features (recurring payments, payment links, etc.)

### When NOT to use this API

- ❌ You only need UPI payments → Use UPI Collect API instead (simpler)
- ❌ Customer hasn't reached checkout → Don't create tokens prematurely
- ❌ You're calling from frontend → This API requires secret key, must be backend-only
- ❌ You need mobile SDK integration → Use mobile SDKs (Android/iOS/Flutter) instead
- ❌ You're in sandbox but using production endpoint → Use `/v1/pg/sandbox/payment_token` for testing

### Required inputs

- `amount` (float, required): Payment amount in Indian Rupees (minimum: ₹1.00)
- `currency` (string, required): Currency code (always `INR` for Indian Rupees)
- `mtx` (string, required): Merchant transaction ID - unique reference ID for the transaction (min: 7, max: 40 characters, only alphabets and numbers)
- `contact_number` (string, required): Actual customer mobile number (10 digits, Indian format, e.g., `9876543210`)
  - ⚠️ **Important**: Pass the actual customer mobile number. Hardcoded values might lead to transactions appearing with hardcoded names and numbers.
- `email_id` (string, required): Customer email address
- `udf` (object, optional): User Defined Fields - extra parameters you need in response (max 5 key-value pairs, each value max 256 characters)
- `sub_accounts_id` (string, optional): Sub account ID for split settlements

### Common mistakes

1. **Calling from frontend** - This API requires secret key, must be called from backend only (see [Frontend vs Backend Calls](../decisions/frontend_vs_backend_calls.md))
2. **Creating tokens too early** - Don't create payment tokens before customer is ready to pay
3. **Not verifying payment status** - Always verify payment status server-side after Layer.js callback
4. **Reusing expired tokens** - Payment tokens expire, create new token if expired
5. **Not storing payment_id** - Store the payment_id returned from Layer.js callback
6. **Using production endpoint in sandbox** - Use sandbox endpoint for testing

### Production recommendation

- **Always call from backend** - Never expose secret keys in frontend (critical security requirement)
- **Create token when customer is ready** - Don't create tokens before checkout page
- **Verify payment server-side** - After Layer.js callback, verify payment status via API
- **Handle token expiry** - Create new token if customer takes too long
- **Use webhooks** - Set up webhooks as primary source of truth (see [Polling vs Webhooks](../decisions/polling_vs_webhooks.md))
- **Store payment_id** - Link payment_id to your order_id for reconciliation
- **Implement idempotency** - Use order_id to prevent duplicate token creation

Creates a payment token for use with Layer.js payment gateway integration. This API must be called from your server-side code.

### Request Body
```json
{
  "amount": 10.00,
  "currency": "INR",
  "mtx": "ORDER_2024_01_15_001",
  "contact_number": "9876543210",
  "email_id": "customer@example.com",
  "udf": {
    "key_1": "order_id",
    "key_2": "customer_id"
  },
  "sub_accounts_id": "sa_da4f9f84ac6d"
}
```

### Request Parameters
- `amount` (float, required): The amount of transaction in Indian Rupees (minimum: ₹1.00)
- `currency` (string, required): Currency code (always `INR` for Indian Rupees)
- `mtx` (string, required): Reference ID for the transaction (should be unique for each transaction, min: 7, max: 40 characters, only alphabets and numbers)
- `contact_number` (string, required): Actual customer mobile number (10 digits, Indian format, e.g., `9876543210`)
  - ⚠️ **Important**: Pass the actual customer mobile number. Hardcoded values might lead to transactions appearing with hardcoded names and numbers.
- `email_id` (string, required): Customer email address (e.g., `customer@example.com`)
- `udf` (object, optional): User Defined Fields - allows merchants to pass extra parameters in the request which they require in the response
  - Each pair cannot exceed 256 characters
  - Maximum 5 key-value pairs
  - Example: `{"key_1": "DD", "key_2": "XOF"}`
- `sub_accounts_id` (string, optional): Sub account ID for split settlements

### Response
```json
{
  "amount": "10.00",
  "currency": "INR",
  "mtx": "ORDER_2024_01_15_001",
  "attempts": 0,
  "sub_accounts_id": "sa_da4f9f84ac6d",
  "users_id": 366411705,
  "created_at": "2025-12-05 16:22:52",
  "id": "pt_676932b984f1203",
  "entity": "payment_token",
  "status": "created",
  "customer": {
    "contact_number": "9876543210",
    "email_id": "customer@example.com",
    "id": "cs_d86932b740dfDa6",
    "entity": "customer"
  }
}
```

### Response Fields
- `id`: Payment token ID (format: `pt_...`) - Use this in Layer.checkout()
- `entity`: API object type (always "payment_token")
- `status`: Payment token status (typically "created")
- `amount`: Transaction amount in Indian Rupees
- `currency`: Currency code (always "INR")
- `mtx`: Your merchant reference ID
- `customer`: Customer object with contact_number, email_id, and customer ID
- `created_at`: Timestamp when payment token was created
- `attempts`: Number of payment attempts (starts at 0)
- `sub_accounts_id`: Sub account ID (if provided)

> ⚠️ **Important**: This API must be called from your server-side code, never from client-side JavaScript. See [Layer.js documentation](./15_layer_js.md) for complete integration guide.

## Status Check API (for Layer.js)

**GET** `/v1/payments/token/{payment_token_id}/status`

Check the payment status using the payment token ID. This should be called after receiving a `captured` event from Layer.js to verify the payment status.

> **Note**: The status check endpoint uses `/v1/payments/token/` path, not `/v1/pg/payment_token/`

### Path Parameters
- `payment_token_id` (string, required): Payment token ID from Layer.js callback

### Response
```json
{
  "payment_token_id": "token_1234567890abcdef",
  "payment_id": "pay_1234567890",
  "status": "captured",
  "amount": 1000.00,
  "currency": "INR",
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:32:15Z"
}
```

## Best Practices

1. **Store Payment IDs**: Always store the payment ID returned when creating a payment request
2. **Use Webhooks**: Set up webhooks to receive real-time payment status updates instead of polling
3. **Handle Expiry**: Monitor payment expiry and allow customers to create new payment requests if expired
4. **Validate Amounts**: Ensure amounts meet minimum requirements before creating payment requests
5. **Use Metadata**: Store order IDs, customer IDs, or other references in metadata for easy reconciliation
6. **Layer.js Integration**: For payment gateway integration, use Layer.js. See [Layer.js documentation](./15_layer_js.md) for details
7. **Verify Payment Status**: Always verify payment status server-side after receiving Layer.js callbacks

