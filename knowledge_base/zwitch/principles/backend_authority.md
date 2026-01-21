# Backend Authority: Server-Side Financial Control

## Absolute Rule

**All critical payment and financial decisions must be made server-side. Frontend calls must never mark payments as final or authorize financial operations.**

This is a **security and reliability requirement**, not a recommendation.

## Backend Owns Financial Operations

### What Backend Must Control

1. **Payment Status Verification**
   - Backend processes webhooks
   - Backend verifies payment status via API
   - Backend marks payments as completed
   - Frontend displays what backend determines

2. **Transfer Authorization**
   - Backend creates transfers
   - Backend verifies balance
   - Backend checks beneficiary status
   - Frontend cannot initiate transfers

3. **Idempotency Enforcement**
   - Backend checks idempotency keys
   - Backend prevents duplicate processing
   - Frontend cannot bypass idempotency

4. **Retry Logic**
   - Backend implements retry strategies
   - Backend handles transient failures
   - Frontend cannot retry financial operations

5. **Reconciliation**
   - Backend runs reconciliation jobs
   - Backend detects discrepancies
   - Backend resolves issues
   - Frontend has no reconciliation role

## Frontend Limitations

### What Frontend Cannot Do

**Frontend must never:**
- ❌ Call Zwitch APIs that require secret keys
- ❌ Mark payments as completed based on frontend state
- ❌ Authorize order fulfillment
- ❌ Create payment tokens (must be backend)
- ❌ Create transfers (must be backend)
- ❌ Process webhooks (must be backend)
- ❌ Make financial decisions

### What Frontend Can Do

**Frontend is allowed to:**
- ✅ Display payment status (from backend)
- ✅ Show loading states
- ✅ Handle user interactions
- ✅ Call your backend APIs (not Zwitch APIs)
- ✅ Initialize Layer.js with token (provided by backend)
- ✅ Display payment UI

## Security Implications

### Why Backend Authority Is Required

1. **Secret Key Protection**
   - Secret keys must never be exposed to frontend
   - Frontend code is visible to users
   - Secret keys in frontend = security breach

2. **Fraud Prevention**
   - Frontend can be manipulated
   - Users can modify frontend code
   - Backend validation prevents fraud

3. **Data Integrity**
   - Frontend state can be stale
   - Network issues can cause inconsistencies
   - Backend is single source of truth

4. **Audit Trail**
   - Backend logs all financial operations
   - Frontend actions cannot be fully audited
   - Compliance requires backend control

## Implementation Pattern

### Correct Architecture

```
Frontend                    Backend                    Zwitch
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
   │                           │                           │
   │ 6. Customer pays          │                           │
   │                           │                           │
   │ 7. Payment callback       │                           │
   │──────────────────────────>│                           │
   │                           │ 8. Verify payment status  │
   │                           │──────────────────────────>│
   │                           │ 9. Payment confirmed      │
   │                           │<──────────────────────────│
   │                           │ 10. Mark order as paid    │
   │                           │     (backend decision)    │
   │ 11. Show success          │                           │
   │<──────────────────────────│                           │
```

### Backend Responsibilities

1. **API Proxy**
   - Frontend calls your backend
   - Backend calls Zwitch APIs
   - Backend never exposes secret keys

2. **Status Verification**
   - Backend processes webhooks
   - Backend verifies payment status
   - Backend updates database
   - Backend notifies frontend

3. **Business Logic**
   - Backend enforces business rules
   - Backend handles edge cases
   - Backend implements idempotency
   - Backend manages retries

## Common Mistakes

### ❌ Mistake 1: Frontend Calls Zwitch APIs

```javascript
// WRONG - Secret key exposed in frontend
const response = await fetch('https://api.zwitch.io/v1/pg/payment_token', {
  headers: {
    'Authorization': `Bearer ${SECRET_KEY}`  // ❌ Exposed!
  }
});
```

### ✅ Correct: Backend Proxy

```javascript
// CORRECT - Frontend calls your backend
const response = await fetch('/api/create-payment-token', {
  method: 'POST',
  body: JSON.stringify({ amount, orderId })
});

// Backend calls Zwitch
app.post('/api/create-payment-token', async (req, res) => {
  const token = await zwitch.createPaymentToken(...);  // Secret key in env
  res.json({ token });
});
```

### ❌ Mistake 2: Frontend Marks Payment Complete

```javascript
// WRONG - Frontend makes financial decision
if (layerCallback.status === 'captured') {
  markOrderAsPaid(orderId);  // ❌ Frontend decision!
}
```

### ✅ Correct: Backend Verifies

```javascript
// CORRECT - Frontend notifies backend
if (layerCallback.status === 'captured') {
  await fetch('/api/verify-payment', {
    method: 'POST',
    body: JSON.stringify({ paymentId: layerCallback.payment_id })
  });
}

// Backend verifies and decides
app.post('/api/verify-payment', async (req, res) => {
  const payment = await zwitch.getPayment(req.body.paymentId);
  if (payment.status === 'completed') {
    markOrderAsPaid(req.body.orderId);  // ✅ Backend decision
  }
});
```

## Override Authority

This principle **cannot be overridden** by:
- API documentation
- Best practices
- Decisions
- Concepts

This is a **foundational security principle** that applies to all layers.

## Related Documentation

- [Frontend vs Backend Calls](../decisions/frontend_vs_backend_calls.md) — Detailed guidance
- [Source of Truth](./source_of_truth.md) — Webhook authority
- [Idempotency](./idempotency.md) — Backend idempotency enforcement

