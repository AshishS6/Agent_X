# Webhook Signature Verification: Security Requirement

## Critical Security Rule

**Always verify webhook signatures before processing. Never process webhooks without signature verification.**

This is a security requirement, not optional. Processing unverified webhooks can lead to financial fraud.

## Why Signature Verification Matters

### Security Risks Without Verification:

1. **Fraudulent Webhooks**
   - Attackers can send fake webhooks to your server
   - Fake `payment.completed` events
   - Your system marks orders as paid without actual payment
   - **Result:** Financial loss, product shipped without payment

2. **Replay Attacks**
   - Attackers capture legitimate webhook
   - Replay it multiple times
   - Your system processes it multiple times
   - **Result:** Duplicate processing, double credits

3. **Man-in-the-Middle Attacks**
   - Attackers intercept webhooks
   - Modify webhook data
   - Forward modified webhook to your server
   - **Result:** Incorrect data processing

## How Signature Verification Works

### Process:

1. **Zwitch signs webhook:**
   - Uses your webhook secret (shared secret)
   - Computes HMAC SHA256 of webhook payload
   - Sends signature in `X-Zwitch-Signature` header

2. **You verify signature:**
   - Get webhook secret (from dashboard, stored securely)
   - Compute HMAC SHA256 of received payload
   - Compare computed signature with received signature
   - If match: Webhook is authentic
   - If mismatch: Reject webhook (potential fraud)

### Signature Format:

```
X-Zwitch-Signature: sha256=abc123def456...
```

**Format:** `sha256={hex_signature}`

## Implementation

### Node.js Example:

```javascript
const crypto = require('crypto');

function verifyWebhookSignature(payload, signature, secret) {
  // Extract signature from header
  const receivedSignature = signature.replace('sha256=', '');
  
  // Compute expected signature
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(JSON.stringify(payload))
    .digest('hex');
  
  // Compare signatures (use timing-safe comparison)
  return crypto.timingSafeEqual(
    Buffer.from(expectedSignature),
    Buffer.from(receivedSignature)
  );
}

// Express.js webhook handler
app.post('/webhook', express.raw({ type: 'application/json' }), (req, res) => {
  const signature = req.headers['x-zwitch-signature'];
  const webhookSecret = process.env.ZWITCH_WEBHOOK_SECRET;
  
  // Verify signature
  if (!verifyWebhookSignature(req.body, signature, webhookSecret)) {
    return res.status(401).send('Invalid signature');
  }
  
  // Parse and process webhook
  const event = JSON.parse(req.body);
  processWebhook(event);
  
  res.status(200).send('OK');
});
```

### Python Example:

```python
import hmac
import hashlib
import json
from flask import Flask, request

app = Flask(__name__)

def verify_webhook_signature(payload, signature, secret):
    # Extract signature from header
    received_signature = signature.replace('sha256=', '')
    
    # Compute expected signature
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures (use timing-safe comparison)
    return hmac.compare_digest(expected_signature, received_signature)

@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Zwitch-Signature')
    webhook_secret = os.getenv('ZWITCH_WEBHOOK_SECRET')
    
    # Verify signature
    if not verify_webhook_signature(request.data, signature, webhook_secret):
        return 'Invalid signature', 401
    
    # Parse and process webhook
    event = json.loads(request.data)
    process_webhook(event)
    
    return 'OK', 200
```

## Important Implementation Details

### 1. Use Raw Request Body

**Critical:** You must verify the **raw request body**, not the parsed JSON.

**Why:**
- JSON parsing can change formatting (whitespace, key order)
- Signature is computed on raw body
- Parsed JSON may not match original

**Correct:**
```javascript
// ✅ CORRECT - Use raw body
app.use('/webhook', express.raw({ type: 'application/json' }));
app.post('/webhook', (req, res) => {
  const signature = verifyWebhookSignature(req.body, ...);  // Raw body
  const event = JSON.parse(req.body);  // Parse after verification
});
```

**Wrong:**
```javascript
// ❌ WRONG - Don't use parsed JSON
app.use(express.json());
app.post('/webhook', (req, res) => {
  const signature = verifyWebhookSignature(JSON.stringify(req.body), ...);  // May not match!
});
```

### 2. Timing-Safe Comparison

**Critical:** Use timing-safe comparison to prevent timing attacks.

**Why:**
- Regular string comparison leaks information via timing
- Attackers can infer signature by measuring response time
- Timing-safe comparison prevents this

**Correct:**
```javascript
// ✅ CORRECT - Timing-safe comparison
crypto.timingSafeEqual(
  Buffer.from(expectedSignature),
  Buffer.from(receivedSignature)
);
```

**Wrong:**
```javascript
// ❌ WRONG - Regular comparison (vulnerable to timing attacks)
expectedSignature === receivedSignature;
```

### 3. Store Secret Securely

**Critical:** Store webhook secret securely.

**Do:**
- Store in environment variables
- Never commit to version control
- Use secret management service (AWS Secrets Manager, etc.)
- Rotate secrets periodically

**Don't:**
- Hardcode in source code
- Commit to git
- Expose in logs or error messages
- Share via insecure channels

## Common Mistakes

### ❌ Mistake 1: No Signature Verification
```python
# ❌ WRONG - No verification
@app.route('/webhook', methods=['POST'])
def webhook():
    event = json.loads(request.data)
    process_webhook(event)  # ❌ No verification!
    return 'OK', 200
```

### ✅ Correct: Verify Signature
```python
# ✅ CORRECT - Verify signature
@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Zwitch-Signature')
    if not verify_signature(request.data, signature):
        return 'Invalid signature', 401  # ✅ Reject if invalid
    
    event = json.loads(request.data)
    process_webhook(event)
    return 'OK', 200
```

### ❌ Mistake 2: Using Parsed JSON for Verification
```javascript
// ❌ WRONG - Verifying parsed JSON
app.use(express.json());
app.post('/webhook', (req, res) => {
  const signature = verify(JSON.stringify(req.body), ...);  // May not match!
});
```

### ✅ Correct: Use Raw Body
```javascript
// ✅ CORRECT - Verify raw body
app.use('/webhook', express.raw({ type: 'application/json' }));
app.post('/webhook', (req, res) => {
  const signature = verify(req.body, ...);  // Raw body
  const event = JSON.parse(req.body);
});
```

### ❌ Mistake 3: Regular String Comparison
```python
# ❌ WRONG - Regular comparison (timing attack)
if expected_signature == received_signature:
    process_webhook()
```

### ✅ Correct: Timing-Safe Comparison
```python
# ✅ CORRECT - Timing-safe comparison
if hmac.compare_digest(expected_signature, received_signature):
    process_webhook()
```

## Testing

### Test Signature Verification:

```python
def test_webhook_signature_verification():
    secret = 'test_secret'
    payload = b'{"event": "payment.completed", "data": {...}}'
    
    # Compute signature
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    header_signature = f'sha256={signature}'
    
    # Verify (should pass)
    assert verify_webhook_signature(payload, header_signature, secret) == True
    
    # Verify with wrong secret (should fail)
    assert verify_webhook_signature(payload, header_signature, 'wrong_secret') == False
    
    # Verify with wrong signature (should fail)
    wrong_signature = 'sha256=wrong_signature'
    assert verify_webhook_signature(payload, wrong_signature, secret) == False
```

## Best Practices

### ✅ Do:
1. **Always verify signatures** before processing
2. **Use raw request body** for verification
3. **Use timing-safe comparison**
4. **Store secrets securely** (environment variables, secret management)
5. **Log verification failures** (security monitoring)
6. **Reject invalid signatures** (return 401)
7. **Test signature verification** in development

### ❌ Don't:
1. **Don't skip signature verification** (even in development)
2. **Don't use parsed JSON** for verification
3. **Don't use regular string comparison**
4. **Don't expose secrets** in logs or errors
5. **Don't commit secrets** to version control
6. **Don't process unverified webhooks**

## Monitoring

**Monitor signature verification failures:**

```python
def verify_webhook_signature(payload, signature, secret):
    is_valid = hmac.compare_digest(...)
    
    if not is_valid:
        # Log security event
        log_security_event('webhook_signature_failed', {
            'signature': signature,
            'payload_hash': hashlib.sha256(payload).hexdigest()
        })
        # Alert security team if multiple failures
        alert_if_suspicious()
    
    return is_valid
```

## Summary

- **Signature verification is mandatory** (not optional)
- **Always verify before processing** webhooks
- **Use raw request body** for verification
- **Use timing-safe comparison**
- **Store secrets securely**
- **Reject invalid signatures** (return 401)
- **Monitor verification failures**

**Bottom line:** Never process webhooks without signature verification. This is a critical security requirement for financial systems.

## Related Documentation

- [Webhooks API](../api/10_webhooks.md) - Webhook setup
- [Double Credit Risk](./double_credit_risk.md) - Preventing fraud
- [Retries and Idempotency](../decisions/retries_and_idempotency.md) - Webhook processing

