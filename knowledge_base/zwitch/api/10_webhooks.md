# Zwitch API — Webhooks

Webhooks allow you to receive real-time notifications about events in your Zwitch account. Instead of polling the API for status updates, Zwitch will send HTTP POST requests to your configured webhook endpoints when events occur.

## Supported Events

Zwitch supports webhook event delivery for:
- **Transfers**: Transfer status changes (pending → processing → completed/failed)
- **Payments**: Payment status changes (pending → completed/failed/expired)
- **Account changes**: Account status updates
- **Beneficiary events**: Beneficiary verification status changes

## Setting Up Webhooks

### 1. Configure Webhook Endpoint

1. Log in to your [Zwitch Dashboard](https://dashboard.zwitch.io)
2. Navigate to **Developers → Webhooks**
3. Click **Add Webhook Endpoint**
4. Enter your webhook URL (must be HTTPS)
5. Select the events you want to receive
6. Save the configuration

### 2. Webhook URL Requirements

- Must use **HTTPS** (HTTP is not supported for security)
- Must be publicly accessible (not localhost)
- Should respond with `200 OK` within 5 seconds
- Should handle POST requests

## Webhook Payload Structure

All webhook payloads follow this structure:

```json
{
  "event": "transfer.completed",
  "data": {
    "id": "trf_1234567890",
    "account_id": "acc_1234567890",
    "status": "completed",
    "amount": 1000.00,
    "created_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:35:00Z"
  },
  "timestamp": "2024-01-15T10:35:00Z",
  "signature": "sha256=abc123..."
}
```

### Payload Fields
- `event`: Event type (e.g., `transfer.completed`, `payment.completed`)
- `data`: Event-specific data object
- `timestamp`: ISO 8601 timestamp of the event
- `signature`: HMAC SHA256 signature for verification

## Event Types

### Transfer Events
- `transfer.created`: Transfer initiated
- `transfer.processing`: Transfer being processed
- `transfer.completed`: Transfer completed successfully
- `transfer.failed`: Transfer failed
- `transfer.cancelled`: Transfer cancelled

### Payment Events
- `payment.created`: Payment request created
- `payment.processing`: Payment being processed
- `payment.completed`: Payment completed successfully
- `payment.failed`: Payment failed
- `payment.expired`: Payment request expired
- `payment.cancelled`: Payment cancelled

### Account Events
- `account.created`: Account created
- `account.updated`: Account updated
- `account.suspended`: Account suspended
- `account.activated`: Account activated

### Beneficiary Events
- `beneficiary.created`: Beneficiary created
- `beneficiary.verified`: Beneficiary verified
- `beneficiary.verification_failed`: Beneficiary verification failed

## Webhook Signature Verification

Zwitch signs all webhook payloads using HMAC SHA256. You must verify the signature to ensure the webhook is authentic.

### Signature Header

Zwitch sends the signature in the `X-Zwitch-Signature` header:
```
X-Zwitch-Signature: sha256=abc123def456...
```

### Verification Process

1. Get your webhook secret from the dashboard (under **Developers → Webhooks**)
2. Compute HMAC SHA256 of the raw request body using your webhook secret
3. Compare the computed signature with the signature in the header

### Example (Node.js)
```js
const crypto = require('crypto');

function verifyWebhookSignature(payload, signature, secret) {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(JSON.stringify(payload))
    .digest('hex');
  
  const receivedSignature = signature.replace('sha256=', '');
  
  return crypto.timingSafeEqual(
    Buffer.from(expectedSignature),
    Buffer.from(receivedSignature)
  );
}

// Express.js example
app.post('/webhook', express.raw({ type: 'application/json' }), (req, res) => {
  const signature = req.headers['x-zwitch-signature'];
  const webhookSecret = process.env.ZWITCH_WEBHOOK_SECRET;
  
  if (!verifyWebhookSignature(req.body, signature, webhookSecret)) {
    return res.status(401).send('Invalid signature');
  }
  
  const event = JSON.parse(req.body);
  // Process event
  console.log('Event:', event.event);
  console.log('Data:', event.data);
  
  res.status(200).send('OK');
});
```

### Example (Python)
```python
import hmac
import hashlib
import json
from flask import Flask, request

app = Flask(__name__)

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    received_signature = signature.replace('sha256=', '')
    
    return hmac.compare_digest(expected_signature, received_signature)

@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Zwitch-Signature')
    webhook_secret = os.getenv('ZWITCH_WEBHOOK_SECRET')
    
    if not verify_webhook_signature(request.data, signature, webhook_secret):
        return 'Invalid signature', 401
    
    event = json.loads(request.data)
    # Process event
    print(f"Event: {event['event']}")
    print(f"Data: {event['data']}")
    
    return 'OK', 200
```

## Webhook Retry Logic

Zwitch automatically retries failed webhook deliveries:

- **Initial attempt**: Immediate
- **Retry 1**: After 1 minute
- **Retry 2**: After 5 minutes
- **Retry 3**: After 15 minutes
- **Retry 4**: After 1 hour
- **Retry 5**: After 6 hours

If all retries fail, the webhook is marked as failed. You can view failed webhooks in your dashboard and manually retry them.

## Webhook Best Practices

1. **Verify Signatures**: Always verify webhook signatures to ensure authenticity
2. **Idempotency**: Handle duplicate events gracefully (use event IDs)
3. **Quick Response**: Respond with `200 OK` quickly, then process asynchronously
4. **Error Handling**: Log errors but return `200 OK` to prevent retries for permanent failures
5. **Event Processing**: Process events asynchronously to avoid timeouts
6. **Monitoring**: Monitor webhook delivery success rates in your dashboard

## Example Webhook Handler

### Node.js (Express)
```js
const express = require('express');
const crypto = require('crypto');
const app = express();

app.use('/webhook', express.raw({ type: 'application/json' }));

app.post('/webhook', (req, res) => {
  const signature = req.headers['x-zwitch-signature'];
  const secret = process.env.ZWITCH_WEBHOOK_SECRET;
  
  // Verify signature
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(req.body)
    .digest('hex');
  
  if (signature !== `sha256=${expectedSignature}`) {
    return res.status(401).send('Invalid signature');
  }
  
  const event = JSON.parse(req.body);
  
  // Process event asynchronously
  processEvent(event).catch(console.error);
  
  // Respond immediately
  res.status(200).send('OK');
});

async function processEvent(event) {
  switch (event.event) {
    case 'payment.completed':
      await handlePaymentCompleted(event.data);
      break;
    case 'transfer.completed':
      await handleTransferCompleted(event.data);
      break;
    // Handle other events
  }
}

async function handlePaymentCompleted(data) {
  console.log(`Payment ${data.id} completed: ₹${data.amount}`);
  // Update your database, send notifications, etc.
}
```

## Testing Webhooks

You can test webhooks using:
1. **Dashboard Test**: Use the "Test Webhook" feature in your dashboard
2. **Local Testing**: Use tools like [ngrok](https://ngrok.com) to expose local endpoints
3. **Webhook Testing Tools**: Use services like [webhook.site](https://webhook.site) for testing

## Webhook Security

- Always use HTTPS for webhook endpoints
- Verify signatures on every request
- Use webhook secrets (never expose them)
- Implement rate limiting on your webhook endpoints
- Monitor for suspicious activity

