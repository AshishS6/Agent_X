# Frontend vs Backend API Calls: Security and Architecture

## Critical Rule

**Never call Zwitch APIs that require secret keys from frontend code. Always call them from your backend.**

This is a security requirement, not a preference.

## What Must Be Backend-Only

### ❌ Never Call from Frontend:

1. **Payment Token Creation**
   - `POST /v1/pg/payment_token`
   - **Why:** Requires secret key (must be kept secret)

2. **Payment Creation (UPI Collect)**
   - `POST /v1/accounts/{account_id}/payments/upi/collect`
   - **Why:** Requires secret key, creates payment requests

3. **Transfers**
   - `POST /v1/transfers`
   - **Why:** Requires secret key, moves money

4. **Account Management**
   - `GET /v1/accounts`, `POST /v1/accounts`
   - **Why:** Requires secret key, sensitive account data

5. **Beneficiary Management**
   - `POST /v1/beneficiaries/*`
   - **Why:** Requires secret key

6. **Any API requiring authentication**
   - All APIs that need `Authorization: Bearer {ACCESS_KEY}:{SECRET_KEY}`
   - **Why:** Secret keys must never be exposed

### ✅ Can Be Called from Frontend (with caution):

1. **Public Payment Links**
   - If Zwitch provides public payment links (no auth required)
   - **Use case:** Displaying payment links to customers

2. **Layer.js Integration**
   - Layer.js is designed for frontend use
   - **But:** Payment token creation must be backend

3. **Status Checks (if public)**
   - Only if Zwitch provides public status endpoints (unlikely)
   - **Better:** Always verify status via backend

## Why This Matters

### Security Risks of Frontend API Calls:

1. **Secret Key Exposure**
   ```javascript
   // ❌ WRONG - Never do this
   const response = await fetch('https://api.zwitch.io/v1/pg/payment_token', {
     headers: {
       'Authorization': `Bearer ${SECRET_KEY}`  // ❌ Exposed in browser!
     }
   });
   ```
   - Secret keys in frontend code are visible to anyone
   - Attackers can extract keys from browser DevTools
   - Keys can be stolen and misused

2. **Unauthorized Actions**
   - Attackers can create payments, transfers, etc.
   - Financial fraud risk
   - Account compromise

3. **Rate Limiting Bypass**
   - Frontend calls can be manipulated
   - Harder to enforce rate limits
   - API abuse risk

## Correct Architecture

### Payment Flow (Correct):

```
Frontend                    Backend                    Zwitch API
   │                           │                           │
   │ 1. User clicks "Pay"      │                           │
   │──────────────────────────>│                           │
   │                           │ 2. Create payment token   │
   │                           │──────────────────────────>│
   │                           │ 3. Payment token          │
   │                           │<──────────────────────────│
   │ 4. Payment token          │                           │
   │<──────────────────────────│                           │
   │ 5. Initialize Layer.js    │                           │
   │    (with token)           │                           │
   │──────────────────────────>│                           │
   │                           │                           │
   │ 6. Customer pays          │                           │
   │                           │                           │
   │ 7. Payment callback       │                           │
   │──────────────────────────>│                           │
   │                           │ 8. Verify payment status  │
   │                           │──────────────────────────>│
   │                           │ 9. Payment confirmed      │
   │                           │<──────────────────────────│
   │ 10. Show success          │                           │
   │<──────────────────────────│                           │
```

### Implementation Example:

**Backend (Node.js/Express):**
```javascript
// ✅ CORRECT - Backend endpoint
app.post('/api/create-payment', async (req, res) => {
  // Validate request (user auth, order validation, etc.)
  const { amount, orderId } = req.body;
  
  // Call Zwitch API (secret key in environment variable)
  const response = await fetch('https://api.zwitch.io/v1/pg/payment_token', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.ZWITCH_ACCESS_KEY}:${process.env.ZWITCH_SECRET_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      amount: amount,
      order_id: orderId,
      // ... other params
    })
  });
  
  const paymentToken = await response.json();
  
  // Return payment token to frontend (safe - token is temporary)
  res.json({ paymentToken: paymentToken.payment_token });
});
```

**Frontend:**
```javascript
// ✅ CORRECT - Frontend calls your backend
async function createPayment(orderId, amount) {
  // Call YOUR backend, not Zwitch directly
  const response = await fetch('/api/create-payment', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${userToken}`  // Your app's auth, not Zwitch
    },
    body: JSON.stringify({ orderId, amount })
  });
  
  const { paymentToken } = await response.json();
  
  // Use payment token with Layer.js (safe - token is temporary)
  initializeLayerJS(paymentToken);
}
```

## Layer.js Integration

**Layer.js is designed for frontend use, but:**

1. **Payment token creation:** Must be backend
2. **Layer.js initialization:** Can be frontend (uses token, not secret key)
3. **Payment callbacks:** Should be verified via backend

**Example:**
```javascript
// Backend: Create payment token
app.post('/api/create-payment-token', async (req, res) => {
  const token = await createPaymentToken(req.body);  // Backend call
  res.json({ paymentToken: token });
});

// Frontend: Use token with Layer.js
const { paymentToken } = await fetch('/api/create-payment-token', {...});
Layer.checkout({
  token: paymentToken,  // ✅ Safe - token is temporary
  onSuccess: (data) => {
    // Verify payment via backend
    verifyPaymentOnBackend(data.payment_id);
  }
});
```

## What About Public APIs?

**If Zwitch provides public APIs (no auth required):**
- These may be safe for frontend use
- **But:** Verify with Zwitch documentation
- **Best practice:** Still route through backend for:
  - Rate limiting
  - Logging
  - Business logic
  - Security controls

## Common Mistakes

### ❌ Mistake 1: Secret Key in Frontend
```javascript
// ❌ WRONG - Never do this
const SECRET_KEY = 'sk_live_abc123...';  // Exposed!
fetch('https://api.zwitch.io/v1/pg/payment_token', {
  headers: {
    'Authorization': `Bearer ${SECRET_KEY}`
  }
});
```

### ✅ Correct: Backend Proxy
```javascript
// ✅ CORRECT - Frontend calls backend
fetch('/api/create-payment', { ... });  // Your backend

// Backend calls Zwitch
app.post('/api/create-payment', async (req, res) => {
  const token = await zwitch.createPaymentToken(...);  // Secret key in env
  res.json({ token });
});
```

### ❌ Mistake 2: Environment Variables in Frontend
```javascript
// ❌ WRONG - Frontend env vars are public
const key = import.meta.env.VITE_ZWITCH_SECRET_KEY;  // Visible in browser!
```

### ✅ Correct: Backend Environment Variables
```javascript
// ✅ CORRECT - Backend env vars are private
const key = process.env.ZWITCH_SECRET_KEY;  // Server-side only
```

## Security Best Practices

### ✅ Do:
1. **Store secret keys** in backend environment variables
2. **Never commit** secret keys to version control
3. **Use backend proxy** for all Zwitch API calls
4. **Validate requests** on backend (auth, authorization, business rules)
5. **Log API calls** on backend (audit trail)
6. **Rate limit** on backend (prevent abuse)

### ❌ Don't:
1. **Don't expose** secret keys in frontend code
2. **Don't use** frontend environment variables for secrets
3. **Don't call** Zwitch APIs directly from frontend
4. **Don't trust** frontend-only validation
5. **Don't skip** backend validation

## Architecture Pattern

**Recommended pattern:**

```
Frontend (React/Vue/etc.)
  ↓ (calls your backend API)
Backend API (Node.js/Python/etc.)
  ↓ (calls Zwitch API with secret key)
Zwitch API
  ↓ (sends webhooks)
Backend Webhook Handler
  ↓ (updates database)
Database
```

**Benefits:**
- Secret keys stay secure
- Centralized business logic
- Better error handling
- Audit trail
- Rate limiting
- Security controls

## Summary

- **Never call Zwitch APIs requiring secret keys from frontend**
- **Always use backend proxy** for API calls
- **Layer.js is frontend-safe** (uses tokens, not secret keys)
- **Payment token creation must be backend**
- **Webhooks must be handled on backend**
- **Security is non-negotiable** in fintech

**Bottom line:** If an API requires authentication, it must be called from your backend. Frontend should only interact with your backend API, never directly with Zwitch APIs that require secret keys.

## Related Documentation

- [Layer.js Integration](../api/15_layer_js.md) - Frontend-safe payment integration
- [Authentication](../api/01_authentication.md) - API authentication
- [Webhook Signature Verification](../risks/webhook_signature_verification.md) - Webhook security

