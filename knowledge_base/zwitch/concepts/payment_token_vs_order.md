# Payment Token vs Order: Understanding the Difference

## What is a Payment Token?

A **payment token** is a temporary, secure identifier created by Zwitch's Payment Gateway API (`/v1/pg/payment_token`). Think of it like a movie ticket—it grants access to a specific payment session but expires after a set time.

### Key Characteristics:
- **Temporary**: Expires after a configured time period
- **Single-use intent**: Designed for one payment attempt
- **Frontend-facing**: Used with Layer.js to initialize the payment UI
- **Server-generated**: Must be created on your backend, never in client-side code

## What is an Order?

An **order** is a business concept in your system—it represents a customer's purchase intent. An order is what you create in your database when a customer wants to buy something.

### Key Characteristics:
- **Persistent**: Lives in your database
- **Business logic**: Contains product details, pricing, customer info
- **Your responsibility**: Managed entirely by your application
- **Multiple payment attempts**: One order can have multiple payment tokens over time

## The Relationship

```
Order (Your System)
  └── Payment Token 1 (Failed/Expired)
  └── Payment Token 2 (Success) → Payment ID (Zwitch)
```

**One order can have multiple payment tokens**, but **one payment token should only be used for one order**.

## Real-World Analogy

Imagine ordering food online:
- **Order**: "I want 2 pizzas, 1 coke, total ₹500" (your order system)
- **Payment Token**: The QR code or payment link you show to collect payment (Zwitch)
- **Payment**: The actual money transfer that happens when the customer pays

## Common Confusion Points

### ❌ Wrong Understanding
- "Payment token is the same as order ID"
- "I should create one payment token per order and reuse it"

### ✅ Correct Understanding
- Payment tokens are temporary session identifiers
- Orders are your business records
- You may need multiple payment tokens if the first one expires or fails

## When to Create a Payment Token

Create a payment token when:
1. Customer clicks "Pay Now" on your checkout page
2. You need to initialize Layer.js payment UI
3. Previous payment token expired or failed

## What NOT to Do

- ❌ Don't create payment tokens in frontend JavaScript
- ❌ Don't reuse expired payment tokens
- ❌ Don't store payment tokens as permanent order identifiers
- ❌ Don't create payment tokens before the customer is ready to pay

## Best Practice

1. Create your **order** in your database first
2. When customer is ready to pay, create a **payment token** server-side
3. Use the payment token to initialize Layer.js
4. Store the resulting **payment ID** (from webhook/callback) linked to your order
5. If payment fails or expires, create a new payment token for the same order

## Summary

- **Payment Token**: Temporary Zwitch identifier for a payment session (like a movie ticket)
- **Order**: Your business record of what the customer wants to buy (like a shopping cart)
- **Payment ID**: Permanent Zwitch identifier for a completed payment (like a receipt)

Keep them separate in your system, and you'll avoid confusion.

