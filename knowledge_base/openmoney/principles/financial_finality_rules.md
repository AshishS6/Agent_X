# Financial Finality Rules: When Money Movement Is Final

## Absolute Rule

**Open Money is a Payment Aggregator (PA) licensed by RBI and is liable for settlements. Transaction statuses (success/failed) shown in Open Money are accurate and reliable. However, for absolute financial finality verification, bank statements remain the authoritative source.**

This is not a guideline—it is a **mandatory principle** for financial operations.

## What Is Financial Finality

Financial finality means:
- Money has moved
- Movement is irreversible
- Movement is confirmed by authoritative source
- Movement cannot be disputed
- Movement is legally binding

## Authority Hierarchy for Finality

### 1. Bank Statement (Highest Authority)

Bank statement confirms finality when:
- Transaction appears in statement
- Transaction is cleared (not pending)
- Statement is official bank document
- Statement cannot be disputed

**Bank statement is the absolute source of truth for finality.**

### 2. Payment Rail Confirmation

Payment rail confirms finality when:
- Payment status is `completed` (from payment rail)
- Payment rail webhook confirms completion
- Payment rail API confirms completion
- Payment rail cannot reverse the transaction

**Payment rail confirmation is transactional truth, but bank statement is absolute.**

### 3. Open Money Dashboard (Settlement Status)

Open Money dashboard shows:
- Transaction statuses (success/failed/pending) from Open Money as a licensed Payment Aggregator
- Aggregated data from banks
- Computed values and metrics
- Settlement information

**Open Money transaction statuses (success/failed) are accurate and reliable as Open Money processes settlements. For absolute finality verification, bank statements remain the authoritative source.**

## When Money Movement Is Final

### Collection (Money In)

Money collection is final when:
- ✅ Bank statement shows credit
- ✅ Credit is cleared (not pending)
- ✅ Credit matches payment amount
- ✅ Credit is reconciled with invoice/payment

**Not final when:**
- ❌ Payment is processing (pending status - cross-check with bank)
- ❌ Customer confirms payment (not authoritative)
- ⚠️ Open Money shows pending (status updates depend on bank callbacks)

**Note:** Open Money success/failed statuses are reliable as Open Money processes settlements. For absolute verification, bank statement confirmation is recommended.

### Payout (Money Out)

Money payout is final when:
- ✅ Bank statement shows debit
- ✅ Debit is cleared (not pending)
- ✅ Debit matches payout amount
- ✅ Debit is reconciled with bill/payout

**Not final when:**
- ❌ Payout is processing (pending status - cross-check with bank)
- ❌ Beneficiary confirms receipt (not authoritative)
- ⚠️ Open Money shows pending (status updates depend on bank callbacks)

**Note:** Open Money success/failed statuses are reliable as Open Money processes settlements. For absolute verification, bank statement confirmation is recommended.

## States That Look Final But Are NOT

### Payment Status: "Success" in Dashboard

**Status:** Payment shows success (Open Money has processed and settled the transaction)
**For absolute verification:** Bank statement confirmation is recommended for finality verification

### Invoice Status: "Paid" in Dashboard

**Looks final:** Invoice shows paid
**Is NOT final:** Until payment is reconciled with bank entry

### Payout Status: "Completed" in Dashboard

**Looks final:** Payout shows completed
**Is NOT final:** Until bank statement confirms debit

### Balance: "₹X" in Dashboard

**Looks final:** Balance shows ₹X
**Is NOT final:** Until verified against bank statement

## Terminal States vs Finality

### Terminal States (Cannot Change Further)

- Invoice: `paid`, `cancelled`, `overdue`
- Payment: `completed`, `failed`, `expired`
- Payout: `completed`, `failed`, `cancelled`

**Terminal states mean the document/transaction cannot change further, but they do NOT confirm financial finality.**

### Financial Finality (Money Actually Moved)

- Bank statement shows transaction
- Transaction is cleared
- Transaction is reconciled
- Transaction cannot be reversed

**Financial finality means money has actually moved and is confirmed by bank.**

## Common Misinterpretations

### Misinterpretation 1: Dashboard Success = Finality

**Wrong:** "Payment shows success in Open Money, so money is final."

**Correct:** "Payment shows success in Open Money, which means Open Money (as a licensed Payment Aggregator) has processed and settled the transaction. For absolute finality verification, bank statement confirmation is recommended."

### Misinterpretation 2: Payment Rail Success = Finality

**Wrong:** "Payment rail shows completed, so money is final."

**Correct:** "Payment rail shows completed. Verify against bank statement to confirm finality. Payment rails can have reversals."

### Misinterpretation 3: Reconciliation Not Needed

**Wrong:** "Payment shows success, so reconciliation is not needed."

**Correct:** "Payment shows success, but reconciliation is mandatory to confirm finality and match with bank entry."

## Verification Process

To confirm financial finality:

1. **Check payment rail status** — Payment shows completed
2. **Check bank statement** — Transaction appears and is cleared
3. **Verify amounts match** — Payment amount = bank entry amount
4. **Reconcile records** — Link payment to bank entry
5. **Confirm no reversals** — Transaction cannot be reversed

Only after all steps are complete is money movement final.

## Reversals and Refunds

Even after "finality," reversals can occur:

- **Payment reversals** — Bank can reverse credit
- **Payout reversals** — Bank can reverse debit
- **Refunds** — Can reverse completed payments
- **Chargebacks** — Can reverse completed payments

**Finality is confirmed only when reversal is no longer possible (usually after reconciliation period).**

## Implementation Requirements

### System Must:

1. **Distinguish terminal states from finality** — States can be terminal without finality
2. **Require bank verification** — Finality requires bank confirmation
3. **Require reconciliation** — Finality requires reconciliation
4. **Track finality separately** — Finality is not the same as terminal state
5. **Warn on assumptions** — Don't assume finality from dashboard alone

### Users Must:

1. **Verify against bank** — Always check bank statement
2. **Reconcile regularly** — Don't skip reconciliation
3. **Don't assume finality** — Verify before critical decisions
4. **Understand distinction** — Terminal state ≠ financial finality
5. **Follow verification process** — Complete all verification steps

## Override Authority

This principle **cannot be overridden** by:
- Dashboard status
- Payment rail status
- User assumptions
- Other documentation

This is a **mandatory principle** for financial operations.

## Related Documentation

- [Backend Authority](./backend_authority.md) — Backend ownership
- [Reconciliation Is Not Optional](./reconciliation_is_not_optional.md) — Reconciliation requirement
- [Invoice State Lifecycle](../states/invoice_state_lifecycle.md) — Invoice states
- [Payment Link State Lifecycle](../states/payment_link_state_lifecycle.md) — Payment link states
- [Payout State Lifecycle](../states/payout_state_lifecycle.md) — Payout states

