# Zwitch API — Layer.js Payment Gateway

Layer.js is a JavaScript payment library that helps you integrate Zwitch's payment gateway into your website or checkout page in two simple steps. It provides a seamless payment experience with support for multiple payment methods.

## Overview

Layer.js enables you to:
- Accept payments through a hosted payment page
- Support multiple payment methods (UPI, cards, net banking, etc.)
- Customize the payment page theme to match your brand
- Handle payment callbacks and status updates

## Getting Started

### Step 1: Create a Payment Token

A `payment_token` represents an order or purchase. The first step to open a Layer payment page is to create a `payment_token` using the Create Payment Token API.

> ⚠️ **Important**: Always call the payment token API from your **server side**!
> 
> This API contains critical information related to your order and should **never** be called directly via AJAX or from client-side code. Always generate the payment token from your server and pass it to your client-side code.

#### Create Payment Token API
**POST** `/v1/pg/payment_token` (Production)  
**POST** `/v1/pg/sandbox/payment_token` (Sandbox)

> **Note**: The endpoint uses `/v1/pg/` (Payment Gateway) namespace, not `/v1/payments/`

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
- `id`: Payment token ID (format: `pt_...`) - Use this in Layer.checkout() as the `token` parameter
- `entity`: API object type (always "payment_token")
- `status`: Payment token status (typically "created")
- `amount`: Transaction amount in Indian Rupees
- `currency`: Currency code (always "INR")
- `mtx`: Your merchant reference ID
- `customer`: Customer object with contact_number, email_id, and customer ID
- `created_at`: Timestamp when payment token was created
- `attempts`: Number of payment attempts (starts at 0)
- `sub_accounts_id`: Sub account ID (if provided)

### Example (Node.js - Server Side)
```js
// Server-side code (e.g., Express.js)
// Use /v1/pg/sandbox/payment_token for sandbox or /v1/pg/payment_token for production
app.post('/api/create-payment-token', async (req, res) => {
  const response = await fetch('https://api.zwitch.io/v1/pg/sandbox/payment_token', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`,
      'Content-Type': 'application/json',
      'accept': 'application/json'
    },
    body: JSON.stringify({
      amount: 1000.00,
      currency: 'INR',
      mtx: 'ORDER_' + Date.now(), // Unique merchant transaction ID
      contact_number: req.body.contact_number, // Actual customer mobile number (10 digits)
      email_id: req.body.email_id,
      udf: {
        key_1: req.body.order_id || 'ORDER_001',
        key_2: req.body.customer_id || 'CUST_001'
      }
    })
  });
  
  const data = await response.json();
  // Return payment_token ID (data.id) to client
  res.json({ payment_token: data.id });
});
```

### Example (Python - Server Side)
```python
# Server-side code (e.g., Flask)
import requests
from datetime import datetime

@app.route('/api/create-payment-token', methods=['POST'])
def create_payment_token():
    # Use /v1/pg/sandbox/payment_token for sandbox or /v1/pg/payment_token for production
    url = 'https://api.zwitch.io/v1/pg/sandbox/payment_token'
    headers = {
        'Authorization': f'Bearer {ACCESS_KEY}:{SECRET_KEY}',
        'Content-Type': 'application/json',
        'accept': 'application/json'
    }
    payload = {
        'amount': 1000.00,
        'currency': 'INR',
        'mtx': f'ORDER_{int(datetime.now().timestamp())}',  # Unique merchant transaction ID
        'contact_number': request.json.get('contact_number'),  # Actual customer mobile number (10 digits)
        'email_id': request.json.get('email_id'),
        'udf': {
            'key_1': request.json.get('order_id', 'ORDER_001'),
            'key_2': request.json.get('customer_id', 'CUST_001')
        }
    }
    
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    # Return payment_token ID (data['id']) to client
    return jsonify({'payment_token': data['id']})
```

### Step 2: Trigger Layer Payment Page

Once you have the `payment_token` from your server, you can trigger the Layer payment page on your website.

#### Include Layer.js Script

Add the Layer.js script to your HTML page. Choose the appropriate script based on your environment:

**For Sandbox/Testing:**
```html
<script id="context" type="text/javascript" 
  src="https://sandbox-payments.open.money/layer"></script>
```

**For Production:**
```html
<script id="context" type="text/javascript"
  src="https://payments.open.money/layer"></script>
```

#### Initialize Layer.checkout

```html
<html>
<!-- To make Layer checkout responsive on your checkout page.-->
<meta name="viewport" content="width=device-width, initial-scale=1" />

<!--Please add either of the following script to your HTML depending up on your environment-->

<!--For Sandbox--> 
<script id="context" type="text/javascript" 
src="https://sandbox-payments.open.money/layer"></script>

<!--OR-->

<!--For Production-->
<script id="context" type="text/javascript"
src="https://payments.open.money/layer"></script>

<body>
  <script>

//You can bind the Layer.checkout initialization script to a button click event.
//Binding inside a click event Zwitch Layer payment page on click of a button
//setTimeout is optional. You can replace it with any event listener such as button click.

setTimeout(() => {
  Layer.checkout({
        token: "payment_token",
        accesskey: "access_key",
        theme: {
            logo : "https://zwitch-logo.png",
            color: "#3d9080",
            error_color : "#ff2b2b"
          }
    },
    function(response) {
    
        if (response.status == "captured") {
           // response.payment_token_id
           // response.payment_id
           window.location.href = "success_redirect_url";

        } else if (response.status == "created") {


        } else if (response.status == "pending") {


        } else if (response.status == "failed") {
          window.location.href = "failure_redirect_url";

        } else if (response.status == "cancelled") {
          window.location.href = "cancel_redirect_url";
        }
    },
    function(err) {
        //integration errors
    }
);
}, 1000);
</script>
</body>
</html>
```

## Layer.checkout Parameters

### Required Parameters
- `token` (string): Payment token received from Create Payment Token API
- `accesskey` (string): Your access key from Zwitch dashboard (safe to use on client-side)

### Optional Parameters
- `theme` (object): Theme customization object (see below)

## Theme Customization

The `theme` object allows you to customize the Layer payment page appearance:

```javascript
theme: {
  logo: "https://your-logo.png",        // Your logo URL
  color: "#3d9080",                     // Main color (hex code)
  error_color: "#ff2b2b"                // Error color (hex code)
}
```

### Theme Object Properties

- **`color`** (string): Main color of Layer payment page
  - Only accepts hex code colors (e.g., `#3d9080`)
  - Default color is applied if not provided or invalid
  
- **`error_color`** (string): Color for error icons, error lines, and error messages
  - Only accepts hex code colors
  - Optional parameter
  - Default color is applied if not provided or invalid
  
- **`logo`** (string): Logo image URL
  - If image source is not available, default Zwitch logo will be used
  - Image loading time depends on image size
  - Should be a publicly accessible URL

### Example Theme Configuration
```javascript
Layer.checkout({
  token: paymentToken,
  accesskey: accessKey,
  theme: {
    logo: "https://cdn.yoursite.com/logo.png",
    color: "#1a73e8",           // Blue theme
    error_color: "#ea4335"       // Red error color
  }
}, callback, errorCallback);
```

## Callback Events

Layer.checkout provides several callback events in the `function(response) {}` block:

### `created`
- **Triggered when**: Layer payment page is opened
- **Action required**: None (informational only)

### `pending`
- **Triggered when**: Customer has been redirected to bank's login page or 3D secure page
- **Action required**: None (informational only)

### `captured`
- **Triggered when**: Transaction is successful
- **Response includes**:
  - `payment_token_id`: Payment token ID
  - `payment_id`: Payment ID
- **Important**: 
  - Use this event **only** to redirect the user to a success page
  - **Do NOT** rely solely on the `captured` event to process an order
  - Always cross-check the transaction status by calling the Status Check API with `payment_token_id` to confirm the transaction status

### `failed`
- **Triggered when**: Transaction has failed
- **Action**: Layer allows customers to retry the transaction by choosing other payment modes
- **Note**: You don't need to take action unless you want to prevent retries

### `cancelled`
- **Triggered when**: Customer clicked the cancel button without initiating payment
- **Response**: `payment_id` will be `null`
- **Action**: Show a transaction cancelled page or allow customer to re-initiate
- **Note**: You can still use the same `payment_token` to re-trigger `Layer.checkout` on click of Pay

## Status Check API

After receiving a `captured` event, always verify the payment status using the Status Check API:

**GET** `/v1/payments/token/{payment_token_id}/status`

> **Note**: The status check endpoint uses `/v1/payments/token/` path, not `/v1/pg/payment_token/`

### Example
```js
// After receiving 'captured' event
async function verifyPaymentStatus(paymentTokenId) {
  const response = await fetch(
    `https://api.zwitch.io/v1/payments/token/${paymentTokenId}/status`,
    {
      headers: {
        'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`
      }
    }
  );
  
  const status = await response.json();
  
  if (status.status === 'captured') {
    // Process order
    await processOrder(status.payment_id);
  } else {
    // Handle other statuses
    console.error('Payment not confirmed:', status.status);
  }
}
```

## Access Key

### What is an Access Key?

An `access_key` is a unique key that you can generate from your Zwitch dashboard. You can generate either a sandbox `access_key` or production `access_key` depending on your environment.

- **Access Key** is considered a **public key** and is **safe to be passed from client-side**
- You can think of `access_key` as a username
- **NEVER expose your `secret_key`** - it's sensitive like a password

### Getting Your Access Key

1. Log in to your [Zwitch Dashboard](https://dashboard.zwitch.io)
2. Navigate to **Developers → API Keys**
3. Generate a new API key pair or use an existing one
4. Copy the **Access Key** (not the Secret Key)
5. Use this Access Key in your client-side Layer.js integration

## Complete Integration Example

### Server-Side (Node.js/Express)
```js
const express = require('express');
const app = express();
app.use(express.json());

// Create payment token endpoint
app.post('/api/create-payment-token', async (req, res) => {
  try {
    // Use /v1/pg/sandbox/payment_token for sandbox or /v1/pg/payment_token for production
    const response = await fetch('https://api.zwitch.io/v1/pg/sandbox/payment_token', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.ZWITCH_ACCESS_KEY}:${process.env.ZWITCH_SECRET_KEY}`,
        'Content-Type': 'application/json',
        'accept': 'application/json'
      },
      body: JSON.stringify({
        amount: req.body.amount,
        currency: 'INR',
        mtx: req.body.mtx || `ORDER_${Date.now()}`, // Unique merchant transaction ID
        contact_number: req.body.contact_number, // Actual customer mobile number (10 digits)
        email_id: req.body.email_id,
        udf: {
          key_1: req.body.order_id || 'ORDER_001',
          key_2: req.body.customer_id || 'CUST_001'
        }
      })
    });
    
    const data = await response.json();
    // Return payment_token ID (data.id) to client
    res.json({ payment_token: data.id });
  } catch (error) {
    res.status(500).json({ error: 'Failed to create payment token' });
  }
});

// Verify payment status endpoint
app.get('/api/payment-status/:tokenId', async (req, res) => {
  try {
    const response = await fetch(
      `https://api.zwitch.io/v1/payments/token/${req.params.tokenId}/status`,
      {
        headers: {
          'Authorization': `Bearer ${process.env.ZWITCH_ACCESS_KEY}:${process.env.ZWITCH_SECRET_KEY}`
        }
      }
    );
    
    const status = await response.json();
    res.json(status);
  } catch (error) {
    res.status(500).json({ error: 'Failed to check payment status' });
  }
});

app.listen(3000);
```

### Client-Side (HTML/JavaScript)
```html
<html>
<!-- To make Layer checkout responsive on your checkout page.-->
<meta name="viewport" content="width=device-width, initial-scale=1" />

<!--Please add either of the following script to your HTML depending up on your environment-->

<!--For Sandbox--> 
<script id="context" type="text/javascript" 
src="https://sandbox-payments.open.money/layer"></script>

<!--OR-->

<!--For Production-->
<script id="context" type="text/javascript"
src="https://payments.open.money/layer"></script>

<body>
  <button id="pay-button">Pay ₹1000</button>
  
  <script>
    const ACCESS_KEY = 'your_access_key'; // Get from Zwitch dashboard
    
    document.getElementById('pay-button').addEventListener('click', async function() {
      // Step 1: Get payment token from server
      const tokenResponse = await fetch('/api/create-payment-token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: 1000.00,
          contact_number: '9876543210', // Actual customer mobile number
          email_id: 'customer@example.com',
          order_id: 'ORDER_' + Date.now()
        })
      });
      
      const { payment_token } = await tokenResponse.json();
      
      // Step 2: Initialize Layer checkout
      Layer.checkout({
        token: payment_token,
        accesskey: ACCESS_KEY,
        theme: {
          logo: "https://zwitch-logo.png",
          color: "#3d9080",
          error_color: "#ff2b2b"
        }
      },
      function(response) {
        if (response.status == "captured") {
          // response.payment_token_id
          // response.payment_id
          // IMPORTANT: Always verify payment status server-side using Status Check API
          window.location.href = "success_redirect_url";
          
        } else if (response.status == "created") {
          // Payment page opened - no action needed
          
        } else if (response.status == "pending") {
          // Customer redirected to bank's login page or 3D secure page - no action needed
          
        } else if (response.status == "failed") {
          // Payment failed - Layer allows customer to retry
          window.location.href = "failure_redirect_url";
          
        } else if (response.status == "cancelled") {
          // Customer cancelled payment - payment_id will be null
          window.location.href = "cancel_redirect_url";
        }
      },
      function(err) {
        // Integration errors
        console.error('Layer.js error:', err);
        alert('Payment initialization failed. Please try again.');
      });
    });
  </script>
</body>
</html>
```

## Best Practices

1. **Always create payment tokens server-side**: Never call the payment token API from client-side code
2. **Verify payment status**: Always verify payment status using the Status Check API after receiving `captured` event
3. **Handle all callback events**: Implement handlers for all callback events (`created`, `pending`, `captured`, `failed`, `cancelled`)
4. **Use HTTPS**: Always use HTTPS in production for security
5. **Store access keys securely**: While access keys are safe for client-side, store them securely and don't commit them to version control
6. **Test in sandbox**: Always test your integration in sandbox mode before going to production
7. **Error handling**: Implement proper error handling for both success and error callbacks
8. **Responsive design**: Ensure your checkout page is responsive for mobile devices

## Mobile SDKs

Zwitch also provides native mobile SDKs for Layer.js integration:

- **Android SDK**: For Android applications
- **iOS SDK**: For iOS applications  
- **Flutter SDK**: For Flutter applications

Refer to Zwitch documentation for mobile SDK integration details.

## Additional Resources

- **Official Documentation**: [developers.zwitch.io](https://developers.zwitch.io)
- **Dashboard**: [dashboard.zwitch.io](https://dashboard.zwitch.io)
- **Support**: Contact support through your dashboard

## Related APIs

- [Create Payment Token API](./05_payments.md#create-payment-token)
- [Status Check API](./05_payments.md#status-check)
- [Webhooks](./10_webhooks.md) - For server-side payment notifications

