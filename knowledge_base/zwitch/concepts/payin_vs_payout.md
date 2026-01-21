# Payin vs Payout: Understanding Money Flow

## Simple Explanation

Think of your Zwitch virtual account as a wallet:
- **Payin**: Money coming **INTO** your wallet (customers paying you)
- **Payout**: Money going **OUT OF** your wallet (you paying others)

## Payin (Money In)

**Payin** is when you **collect money from customers**. This is also called "collections" or "payments."

### Examples:
- Customer buys a product → Payin
- User subscribes to your service → Payin
- Marketplace receives commission → Payin
- Freelancer receives payment from client → Payin

### How Payin Works:
1. Customer initiates payment (via UPI, card, etc.)
2. Money flows **from customer's account** → **to your Zwitch virtual account**
3. Your account balance increases
4. You receive a webhook: `payment.completed`

### APIs Used:
- **UPI Collect**: `/v1/accounts/{account_id}/payments/upi/collect`
- **Payment Gateway (Layer.js)**: `/v1/pg/payment_token`

## Payout (Money Out)

**Payout** is when you **send money to others**. This is also called "transfers" or "disbursements."

### Examples:
- Paying salaries to employees → Payout
- Sending refunds to customers → Payout
- Paying vendors/suppliers → Payout
- Marketplace paying sellers → Payout

### How Payout Works:
1. You initiate a transfer from your virtual account
2. Money flows **from your Zwitch virtual account** → **to beneficiary's bank account**
3. Your account balance decreases
4. You receive a webhook: `transfer.completed`

### APIs Used:
- **Transfers**: `/v1/transfers`
- **Bulk Transfers**: `/v1/transfers/bulk`

## Visual Flow

```
PAYIN (Money Coming In)
┌─────────────┐         ┌──────────────┐
│  Customer   │ ──₹──> │ Your Virtual │
│   Account   │        │   Account    │
└─────────────┘        └──────────────┘
                              ↑
                              │ Balance Increases

PAYOUT (Money Going Out)
┌──────────────┐         ┌─────────────┐
│ Your Virtual │ ──₹──> │ Beneficiary │
│   Account    │        │   Account   │
└──────────────┘        └─────────────┘
       ↓
Balance Decreases
```

## Key Differences

| Aspect | Payin | Payout |
|--------|-------|--------|
| **Direction** | Into your account | Out of your account |
| **Who initiates** | Customer | You (merchant) |
| **Destination** | Your virtual account | Beneficiary's bank account |
| **Balance effect** | Increases | Decreases |
| **API namespace** | `/v1/payments/` or `/v1/pg/` | `/v1/transfers/` |
| **Webhook event** | `payment.completed` | `transfer.completed` |

## Common Use Cases

### E-commerce Platform
- **Payin**: Customers pay for products
- **Payout**: Refunds to customers, payments to sellers

### SaaS Subscription
- **Payin**: Monthly subscription fees
- **Payout**: Rare (maybe refunds)

### Marketplace
- **Payin**: Commission from transactions
- **Payout**: Payments to sellers after commission deduction

### Payroll Service
- **Payin**: Company deposits salary pool
- **Payout**: Salaries to employees

## Important Notes

### Payin Considerations:
- Customer controls the payment (they choose payment method)
- Payment can fail, expire, or be cancelled
- You must handle payment status webhooks
- Payment methods vary (UPI, card, net banking, etc.)

### Payout Considerations:
- You control the transfer (you initiate it)
- Requires beneficiary to be created first
- Transfer can fail (wrong account, insufficient balance, etc.)
- You must handle transfer status webhooks
- Fees may apply (check your pricing)

## What NOT to Confuse

❌ **Wrong**: "Payout is the same as refund"
- Refund is a **type** of payout, but payout is broader (salaries, vendor payments, etc.)

❌ **Wrong**: "Payin and payout use the same API"
- They use different APIs: payments vs transfers

✅ **Correct**: Payin = collections, Payout = disbursements

## Summary

- **Payin**: Money coming in (customers → you)
- **Payout**: Money going out (you → others)
- Both are essential for a complete financial flow
- Use different APIs and handle different webhooks
- Both affect your virtual account balance (in opposite directions)

