# Backend Authority: Frontend Is Informational Only

## Absolute Rule

**Frontend and dashboard state is never authoritative for financial operations. All financial decisions must be made on the backend.**

This is not a recommendation—it is a **mandatory architectural principle** for fintech systems.

## Frontend Cannot Be Trusted

### Why Frontend Is Not Authoritative

1. **Client-side manipulation** — Frontend code can be modified by users
2. **Network issues** — Frontend may not receive updates
3. **Race conditions** — Frontend state may be stale
4. **Security** — Frontend is exposed to users
5. **Caching** — Frontend may show cached data
6. **Browser state** — Frontend state is ephemeral

### Dashboard Is Informational Only

- Dashboard status is a derived view, not a source of truth
- Dashboard success does NOT confirm payment finality
- Dashboard failure does NOT confirm payment failure
- Dashboard must never be used to resolve discrepancies
- Dashboard balance does NOT confirm bank balance

## Backend Authority

**All financial decisions must be made on the backend:**

- Backend processes webhooks
- Backend verifies payment status
- Backend updates database
- Backend authorizes operations
- Backend reconciles transactions
- Frontend displays what backend tells it

## What Frontend Can Do

- ✅ Display payment status to users
- ✅ Show loading states
- ✅ Handle UI interactions
- ✅ Call backend APIs (not payment rails directly)
- ✅ Display derived analytics
- ✅ Show reconciliation status

## What Frontend Cannot Do

- ❌ Mark payments as completed
- ❌ Authorize financial operations
- ❌ Trust its own state for critical decisions
- ❌ Call payment rail APIs with secret keys
- ❌ Override backend decisions
- ❌ Confirm financial finality

## Implementation Requirements

### Backend Must:

1. **Process all webhooks** — Backend receives and processes payment status updates
2. **Verify all statuses** — Backend verifies payment status with payment rails
3. **Update database** — Backend updates database with authoritative state
4. **Authorize operations** — Backend authorizes all financial operations
5. **Reconcile transactions** — Backend reconciles with bank statements
6. **Provide API** — Backend provides API for frontend to query state

### Frontend Must:

1. **Never make financial decisions** — Only display status
2. **Always verify with backend** — Don't trust frontend state
3. **Never call payment rails directly** — Always go through backend
4. **Display backend state** — Show what backend tells it
5. **Handle errors gracefully** — Don't assume state is correct

## Common Mistakes

### ❌ Mistake 1: Frontend Marks Payment Complete

**Wrong:**
```javascript
// Frontend code
if (payment.status === 'completed') {
  markOrderAsPaid(); // ❌ Frontend making financial decision
}
```

**Correct:**
```javascript
// Frontend code
if (payment.status === 'completed') {
  showSuccessMessage(); // ✅ Display only
  // Backend already marked order as paid via webhook
}
```

### ❌ Mistake 2: Trusting Dashboard Balance

**Wrong:**
```javascript
// Frontend code
if (dashboardBalance >= orderAmount) {
  allowPayment(); // ❌ Trusting dashboard balance
}
```

**Correct:**
```javascript
// Frontend code
// Backend checks actual bank balance before authorizing
callBackendAPI('/check-balance', { amount: orderAmount });
// Backend responds with authorization
```

### ❌ Mistake 3: Frontend Calls Payment API

**Wrong:**
```javascript
// Frontend code
const response = await fetch('https://payment-rail.com/api/payments', {
  headers: { 'Authorization': `Bearer ${API_KEY}` } // ❌ Exposing secret
});
```

**Correct:**
```javascript
// Frontend code
const response = await fetch('/api/payments', {
  // Backend calls payment rail
});
```

## Decision Flow

**Correct flow:**
```
Frontend → Backend API → Payment Rail
                ↓
         Backend Database
                ↓
         Frontend Display
```

**Wrong flow:**
```
Frontend → Payment Rail (❌ Never)
Frontend → Financial Decision (❌ Never)
```

## Override Authority

This principle **cannot be overridden** by:
- API documentation
- Best practices
- Decisions
- Concepts
- Modules

This is a **foundational architectural principle** that applies to all layers.

## Related Documentation

- [Reconciliation Is Not Optional](./reconciliation_is_not_optional.md) — Reconciliation requirement
- [Financial Finality Rules](./financial_finality_rules.md) — When money is final
- [Dashboard Misinterpretation](../risks/dashboard_misinterpretation.md) — Dashboard risks

