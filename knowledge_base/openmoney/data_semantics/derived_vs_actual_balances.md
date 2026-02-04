# Derived vs Actual Balances

## Critical Distinction

**Balances shown in Open Money may be derived from the last bank sync plus known transactions; the bank remains the source of truth for the actual balance.**

## What Is Actual Balance

Actual balance is:
- Balance shown in bank statement
- Balance from bank API
- Balance in passbook
- Balance confirmed by bank
- Authoritative balance

**Actual balance is owned by the bank, not Open Money (connected banks).**

## What Is Derived Balance

Derived balance is:
- Based on last bank sync
- Based on known transactions
- Based on pending transactions

**Derived balance is calculated by Open Money, not owned by bank.**

## How Derived Balance Is Calculated

Derived balance is calculated from:
- Last known bank balance (from sync)


To verify balance accuracy:

1. **Check last sync timestamp** — When was balance last updated?
2. **Check bank statement** — What is actual bank balance?
3. **Reconcile transactions** — Do all transactions match?
4. **Verify pending transactions** — Are pending transactions accounted for?
5. **Compare amounts** — Does derived balance match actual balance?

**Only after verification can you trust derived balance for non-critical decisions.**

## Related Documentation

- [Banking Module](../modules/banking.md) — Banking module
- [Stale Bank Data](../risks/stale_bank_data.md) — Bank sync risks
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Reconciliation Logic](./reconciliation_logic.md) — Reconciliation meaning
- [Open Money vs Bank](../concepts/open_money_vs_bank.md) — Platform comparison

