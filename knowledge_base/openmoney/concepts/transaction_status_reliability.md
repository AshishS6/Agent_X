# Transaction Status Reliability (Open Money)

## Why this matters
Open Money shows payment and payout **statuses** (for example: `pending`, `processing`, `completed`, `failed`). Users often treat these as “final truth”, but financial decisions still require **reconciliation** against bank entries.

This document is the canonical guide for **what to trust** vs **what to verify**.

## What statuses mean (practical)
- **`completed` / `success`**: The payment rail reports the transaction as successful. This is strong evidence the transaction succeeded on the rail.
- **`failed`**: The payment rail reports the transaction failed.
- **`pending` / `processing`**: The transaction is still in-flight and may change.

## What is reliable vs what needs verification
### Reliable enough for operational workflow
- Treat `success/completed` and `failed` as reliable for **workflow state** (e.g., stop retrying, mark invoice collection attempt outcome).

### Still verify for financial finality
Even if a payment shows `success/completed`, you should verify via:
- **Bank statement / bank transaction entries**
- **Reconciliation** (match documents → payments/payouts → bank entries)

Reason: “Success on the rail” is not the same as “I can prove the final bank credit/debit entry is present and reconciled.”

## When you must cross-check with the bank
- Any `pending` / `processing` status
- Any large-value or business-critical decision
- When bank sync is stale or `sync_failed`
- When reconciliation shows discrepancies or missing bank entries

## If the KB conflicts
If you find KB content that says both “statuses are always final” and “statuses are not reliable”, treat that as a KB inconsistency and prefer:
- `principles/` and `states/` + `workflows/` over `concepts/` and marketing-style text
- reconciliation rules as the final arbiter of financial truth

## Related documentation
- [Dashboard Misinterpretation Risk](../risks/dashboard_misinterpretation.md)
- [Reconciliation Is Not Optional](../principles/reconciliation_is_not_optional.md)
- [Financial Finality Rules](../principles/financial_finality_rules.md)
- [Reconciliation Flow](../workflows/reconciliation_flow.md)

