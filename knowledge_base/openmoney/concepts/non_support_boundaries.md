# What Open Money Does NOT Support (Boundaries)

This is a canonical boundaries doc. If a question falls outside these boundaries and the retrieved context does not explicitly confirm support, the assistant should say the KB is insufficient rather than guessing.

## No API surface for developers (platform-first)
Open Money is primarily a **business platform (dashboard + mobile app)**. If asked for Open Money API endpoints, request/response schemas, or webhooks, only answer if the retrieved context explicitly documents such APIs. Otherwise:
- state that the KB does not confirm an Open Money developer API surface
- suggest using the platform workflows instead

## Not a bank (no account ownership)
Open Money does not “own” a business bank account. The bank remains the source of truth for:
- account balance
- statement entries
- bank-side finality

## Not a full accounting-system replacement
Open Money can sync and assist with reconciliation, but accounting truth lives in:
- the accounting system (e.g., Tally, Zoho Books) and
- bank statements

## Not crypto / not international payments (unless explicitly stated)
Unless the retrieved context explicitly says otherwise, assume:
- no cryptocurrency support
- no international payments / FX

## Derived metrics are not bank truth
Cashflow, overdue, and derived balances are computed and must be interpreted with their limitations.

## Related documentation
- [Company Overview](../company_overview.md)
- [Data Ownership and Limitations](./data_ownership_and_limitations.md)
- [Derived vs Actual Balances](../data_semantics/derived_vs_actual_balances.md)

