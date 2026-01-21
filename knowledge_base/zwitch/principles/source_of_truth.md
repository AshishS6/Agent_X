# Source of Truth: Webhooks Are Primary

## Absolute Rule

**Webhooks are the primary source of truth for payment and transfer status updates. Status APIs are fallback and reconciliation tools only.**

This is not a recommendation—it is a **mandatory architectural principle** for fintech systems.

## Missing Webhook Rule (Critical)

**If a webhook has not been received, the payment or transfer state MUST be treated as unresolved.**

- Absence of a webhook does NOT imply failure
- Absence of a webhook does NOT imply success
- Until a verified webhook or reconciliation confirms the state, the system must keep the transaction in a pending or unresolved state

This rule prevents false success, false failure, and financial inconsistencies.

## Primary Source: Webhooks

### Why Webhooks Are Primary

1. **Real-time accuracy** — Webhooks are sent immediately when status changes
2. **Event-driven** — No polling delay or missed updates
3. **Authoritative** — Zwitch sends webhooks when status is confirmed
4. **Efficient** — One HTTP request per event, not constant polling

### Webhook Authority

- Webhook events (`payment.completed`, `transfer.completed`) are **authoritative**
- Webhook payloads contain the **current state** at the time of the event
- Webhook signatures verify **authenticity** (see [Webhook Signature Verification](../risks/webhook_signature_verification.md))

### When a Webhook Can Be Treated as Authoritative

- ❗ A webhook that does not exist cannot be trusted
- ✅ Webhook signature is verified
- ✅ Webhook is processed with idempotency checks
- ✅ Webhook event matches expected state transition
- ✅ Webhook is from Zwitch (verified via signature)

## Fallback: Status APIs

### When to Use Status APIs

Status APIs (`GET /v1/payments/{id}`, `GET /v1/transfers/{id}`) are **fallback tools** for:

1. **Reconciliation** — Periodic checks to catch missed webhooks
2. **Initial verification** — One-time check after creating payment/transfer
3. **Webhook failure recovery** — When webhook delivery failed
4. **Development/testing** — When webhooks are hard to test locally

### Status APIs Are NOT Primary

- ❌ Do not use status APIs as primary method for status updates
- ❌ Do not poll status APIs continuously in production
- ❌ Do not replace webhooks with polling
- ❌ Trust status APIs over webhooks when both are available
- ❌ Do not treat a single status API response as final confirmation without reconciliation


### Reconciliation Pattern

**Correct approach:**
```
Primary: Process webhook → Update database
Fallback: Reconciliation job (hourly/daily) → Check status API → Update if missed
```

**Wrong approach:**
```
Primary: Poll status API every 5 seconds → Update database
```

## Frontend State Is Never Authoritative

### Critical Rule

**Frontend state is never authoritative for financial operations.**

### Dashboard Is Informational Only

- Dashboard status is a derived view, not a source of truth
- Dashboard success does NOT confirm payment finality
- Dashboard failure does NOT confirm payment failure
- Dashboard must never be used to resolve discrepancies

### Why Frontend Cannot Be Trusted

1. **Client-side manipulation** — Frontend code can be modified by users
2. **Network issues** — Frontend may not receive updates
3. **Race conditions** — Frontend state may be stale
4. **Security** — Frontend is exposed to users

### What Frontend Can Do

- ✅ Display payment status to users
- ✅ Show loading states
- ✅ Handle UI interactions
- ✅ Call backend APIs (not Zwitch APIs directly)

### What Frontend Cannot Do

- ❌ Mark payments as completed
- ❌ Authorize financial operations
- ❌ Trust its own state for critical decisions
- ❌ Call Zwitch APIs with secret keys

### Backend Authority

**All financial decisions must be made on the backend:**

- Backend processes webhooks
- Backend verifies payment status
- Backend updates database
- Backend authorizes order fulfillment
- Frontend displays what backend tells it

## Implementation Requirements

### Webhook Handler Must:

1. **Verify signature** — Always verify webhook signature before processing
2. **Check idempotency** — Prevent duplicate processing
3. **Update database** — Store status change with timestamp
4. **Respond quickly** — Return 200 OK within 5 seconds
5. **Process asynchronously** — Don't block webhook response

### Status API Usage Must:

1. **Be reconciliation only** — Not primary status source
2. **Run periodically** — Hourly for recent, daily for older
3. **Check idempotency** — Don't process if already processed
4. **Log discrepancies** — Alert if status mismatch found

### Frontend Must:

1. **Never make financial decisions** — Only display status
2. **Always verify with backend** — Don't trust frontend state
3. **Never call Zwitch APIs directly** — Always go through backend

## Decision Outcomes Summary

| Situation | Action |
|---------|-------|
| Webhook received and verified | Treat state as authoritative |
| Webhook missing | Treat state as unresolved |
| Dashboard shows success only | Ignore for finality |
| Status API used alone | Use only for reconciliation |
| Conflicting signals | Reconcile before final decision |

## Override Authority

This principle **cannot be overridden** by:
- API documentation
- Best practices
- Decisions
- Concepts

This is a **foundational architectural principle** that applies to all layers.

## Related Documentation

- [Polling vs Webhooks](../decisions/polling_vs_webhooks.md) — Detailed comparison
- [Webhook Signature Verification](../risks/webhook_signature_verification.md) — Security requirement
- [Backend Authority](./backend_authority.md) — Backend ownership
- [Payment Status Lifecycle](../states/payment_status_lifecycle.md) — State definitions

