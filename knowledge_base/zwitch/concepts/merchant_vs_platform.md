# Merchant vs Platform: Understanding Your Role

## Simple Explanation

When using Zwitch, you need to understand whether you are:
- **Merchant**: You're selling directly to end customers
- **Platform**: You're enabling others to sell (marketplace, SaaS, etc.)

This distinction affects how you structure your accounts, handle payments, and comply with regulations.

## What is a Merchant?

A **merchant** is a business that sells products or services **directly to end customers**.

### Characteristics:
- You own the products/services
- You receive payments directly from customers
- You handle customer support
- You're responsible for refunds, returns, disputes

### Examples:
- E-commerce store selling your own products
- SaaS company selling subscriptions
- Service provider (consulting, design, etc.)
- Restaurant with online ordering

### Zwitch Setup:
- Usually **one main virtual account**
- All customer payments go to your account
- You handle all payouts (refunds, vendor payments, etc.)

## What is a Platform?

A **platform** is a business that **enables other businesses or individuals to sell** through your service.

### Characteristics:
- You facilitate transactions between buyers and sellers
- You may take a commission
- You handle escrow, settlements, payouts to sellers
- You're responsible for platform operations, not individual products

### Examples:
- Marketplace (like Amazon, Flipkart model)
- Gig economy platform (freelancers, drivers, etc.)
- Crowdfunding platform
- Multi-vendor e-commerce platform
- Payment aggregator

### Zwitch Setup:
- **Multiple virtual accounts** (one per seller, or one main + sub-accounts)
- Payments may go to escrow first
- You handle settlements to sellers
- More complex reconciliation needed

## Key Differences

| Aspect | Merchant | Platform |
|--------|----------|----------|
| **Customer relationship** | Direct | Indirect (via sellers) |
| **Account structure** | Usually single account | Multiple accounts or escrow |
| **Settlement** | Not applicable | Must settle with sellers |
| **Compliance** | Standard merchant KYC | May need platform-specific compliance |
| **Refund handling** | Direct to customer | May involve seller approval |
| **Revenue model** | Product/service sales | Commission, fees, subscriptions |

## Real-World Analogy

**Merchant**: You own a bakery. Customers buy bread directly from you. You keep all the money.

**Platform**: You own a food delivery app. Restaurants list their food. Customers order. You take a commission and pay the restaurant the rest.

## Zwitch Account Strategy

### For Merchants:
```
Single Virtual Account
  ├── Receives all customer payments
  ├── Holds your balance
  └── Used for refunds, vendor payments
```

### For Platforms:
```
Option 1: Escrow Model
  Main Account (Escrow)
    ├── Receives all customer payments
    ├── Holds funds temporarily
    └── Transfers to seller accounts on settlement

Option 2: Direct Model
  Seller Virtual Accounts
    ├── Each seller has their own account
    ├── Customer pays directly to seller account
    └── Platform takes commission via separate transfer
```

## Compliance Considerations

### Merchant:
- Standard KYC requirements
- Direct tax liability on sales
- Standard refund/dispute policies

### Platform:
- May need additional licenses (depending on business model)
- Must handle seller KYC (or ensure sellers are KYC'd)
- Escrow regulations may apply
- Settlement reporting requirements
- May need to handle GST for sellers

## Common Mistakes

### ❌ Merchant Mistake:
- Creating multiple virtual accounts when one would suffice
- Over-complicating the setup

### ❌ Platform Mistake:
- Using a single account for all transactions (makes reconciliation impossible)
- Not handling escrow properly
- Not settling with sellers in time
- Not maintaining proper audit trails

## How to Decide

Ask yourself:
1. **Do I own the products/services?** → Merchant
2. **Do I facilitate others to sell?** → Platform
3. **Do I take a commission?** → Platform
4. **Do I need to settle funds with others?** → Platform

## Hybrid Models

Some businesses are both:
- **Example**: A company that sells its own products AND allows third-party sellers
- **Solution**: Use separate virtual accounts for merchant vs platform operations

## Best Practices

### For Merchants:
- Keep it simple: one main account
- Use metadata to track orders/customers
- Handle refunds directly

### For Platforms:
- Use separate accounts for escrow vs settlements
- Implement proper settlement cycles
- Maintain detailed audit logs
- Handle seller onboarding/KYC properly
- Implement reconciliation processes

## Summary

- **Merchant**: You sell directly → Simple account structure
- **Platform**: You enable others to sell → Complex account structure, settlements required
- Choose your account strategy based on your business model
- Compliance requirements differ
- Platform models require more careful design

If you're unsure, start simple (merchant model) and evolve to platform model as needed.

