# Open Money Glossary

## Payment Aggregator (PA)
An entity that enables merchants/businesses to accept payments through multiple payment modes and is responsible for processing and settlement flows as described in the KB.

## Settlement
The movement of funds that results in a final bank credit/debit entry. Operational “success” on a payment rail is not the same as proven settlement in your bank statement.

## Reconciliation
The process of matching:
- documents (bills/invoices/payment links)
- to payments/payouts
- to bank statement entries
to ensure the financial record is correct and complete.

## Connected banking
Linking business bank accounts into the Open Money platform to view balances and transaction history and initiate certain workflows.

## Actual balance
The authoritative balance as reported by the bank (bank statement / bank API).

## Derived balance
A calculated balance based on last sync and known transactions; useful for visibility but must be verified for critical decisions.

## Sync / last sync
The last successful fetch of bank/transaction data into Open Money. If sync is stale or failed, recent transactions may be missing.

## Payment status
A status reported for a payment/collection flow (e.g., `pending`, `processing`, `completed`, `failed`). Status should be interpreted alongside reconciliation and bank entries.

## Payout
An outgoing payment to a beneficiary. Like collections, payouts must be reconcilable against bank entries for finality.

