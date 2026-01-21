# Zwitch API — Introduction

## Overview

Zwitch is India's leading online payment API solution, providing an all-in-one platform to accept online payments, process payouts, and seamlessly onboard clients. 

**Payment Gateway Services: YES, Zwitch offers Payment Gateway as a core product.** Zwitch provides a comprehensive Payment Gateway solution with 150+ payment methods, along with enterprise-grade APIs for payouts, verifications, compliance, collections, and payments, helping businesses automate financial operations with speed and scale.

**Platform Statistics:**
- **4 Million+** businesses powered
- **150+** payment methods supported
- **$35 Billion+** in transactions processed

**Payment Gateway Services:**
✅ **YES, Zwitch offers Payment Gateway (PG) services** including:
- Full-featured payment gateway with 150+ payment options
- Layer.js for web integration
- Native mobile SDKs (Android, iOS, Flutter)
- Payment links, instant refunds, recurring payments
- UPI Collect for UPI-only payments

The API follows REST principles and uses JSON for request and response payloads. Built for developers and trusted by businesses, Zwitch APIs power seamless money movement, secure identity verification, and regulatory compliance.

**Source**: [zwitch.io](https://www.zwitch.io/)

## Base URL

All API requests should be made to:
```
https://api.zwitch.io/v1
```

## API Versioning

The current API version is **v1**. All endpoints are prefixed with `/v1/`.

## Authentication

Zwitch uses Bearer token authentication. Every API request must include an `Authorization` header with your Access Key and Secret Key. See the [Authentication documentation](./01_authentication.md) for details.

## Rate Limits

API rate limits are applied per account. Check your dashboard or contact support for specific rate limit information for your account tier.

## Request Format

- **Content-Type**: `application/json`
- **Method**: Standard HTTP methods (GET, POST, PUT, DELETE)
- **Encoding**: UTF-8

## Response Format

All successful API responses return JSON with a `2XX` status code. Error responses follow a consistent error format. See [Error Codes documentation](./02_error_codes.md) for details.

## Core Product Categories

Zwitch offers four main product categories, each with comprehensive API support:

### 1. Payment Gateway
Accept online payments with streamlined checkout and higher success rates.

**Features:**
- **150+ Payment Options**: Support for cards, UPI, net banking, wallets, and more
- **Payment Links**: Generate shareable payment links
- **Instant Refunds**: Process refunds instantly
- **Recurring Payments**: Set up subscription and recurring payment flows
- **Native SDKs & Plugins**: Android, iOS, Flutter SDKs, and Layer.js for web

**API Endpoints:**
- UPI Collect: `/v1/accounts/{account_id}/payments/upi/collect`
- Payment Gateway (Layer.js): `/v1/pg/payment_token`
- [Learn more →](./05_payments.md)
- [Layer.js Integration →](./15_layer_js.md)

> **Note**: Collections are handled through UPI Collect API, not a separate `/v1/collections` endpoint

### 2. Payouts
Instant account-to-account transfers supported by 150+ banks through Connected Banking.

**Features:**
- **Connected Banking**: Direct integration with 150+ banks
- **Payouts API**: Programmatic fund transfers
- **Escrow Payments**: Secure escrow services
- **Multiple Transfer Methods**: NEFT, RTGS, IMPS, UPI

**API Endpoints:**
- Transfers: `/v1/transfers`
- Bulk Transfers: `/v1/transfers/bulk`
- Connected Banking: See [Connected Banking documentation](./12_connected_banking.md)
- [Learn more →](./07_transfers.md)

### 3. Zwitch Bill Connect
Embed interoperable bill payments by connecting with 1000+ ERPs, billers, and banks using NPCI's Bharat Connect Network.

**Features:**
- **ERP Integration**: Connect to 1000+ ERPs and banking platforms (Zoho, Happay, HDFC Bank, ICICI Bank, etc.)
- **150+ Connected Payment Methods**: Multiple payment options
- **Instant Bill Discounting**: Real-time bill discounting capabilities
- **B2B Payments**: Enable real-time B2B payments from current accounts

**API Endpoints:**
- Business Onboarding: `/v1/bharat-connect/onboarding/`
- Invoice Management: `/v1/bharat-connect/invoice/`
- Payment Requests: `/v1/bharat-connect/payment`
- [Learn more →](./09_bharat_connect.md)

### 4. Verification Suite
Enhance compliance and verification with powerful APIs.

**Features:**
- **Verification APIs**: VPA, bank account, PAN, name verification
- **Compliance APIs**: Regulatory compliance tools
- **Onboarding APIs**: Streamlined customer onboarding

**API Endpoints:**
- VPA Verification: `/v1/verifications/vpa`
- Bank Account Verification: `/v1/verifications/bank-account/pennyless`
- PAN Verification: `/v1/verifications/pan`
- Name Verification: `/v1/verifications/name`
- [Learn more →](./08_verification.md)

## Additional API Services

### Accounts Management
- Create and manage virtual accounts
- Retrieve account balances and statements
- [Learn more →](./03_accounts.md)

### Beneficiaries
- Manage bank account beneficiaries
- Beneficiary verification
- [Learn more →](./06_beneficiaries.md)

### Connected Banking
- Account linking with 150+ banks
- Transaction history
- Balance inquiries
- [Learn more →](./12_connected_banking.md)

### Webhooks
- Real-time event notifications
- Payment and transfer status updates
- [Learn more →](./10_webhooks.md)

## Getting Started

1. **Sign up** for a Zwitch account at [zwitch.io](https://zwitch.io)
2. **Generate API keys** in the dashboard under **Developers → API Keys**
3. **Set up webhooks** (optional) for real-time event notifications
4. **Make your first API call** using the authentication credentials

## SDKs and Libraries

While Zwitch provides REST APIs that can be called from any language, you can also use:
- **Layer.js**: JavaScript payment library for frontend integration ([Documentation →](./15_layer_js.md))
- **Mobile SDKs**: Android, iOS, and Flutter SDKs for native mobile apps
- Custom SDKs: Check Zwitch documentation for official SDKs

## Support and Resources

- **Website**: [zwitch.io](https://www.zwitch.io/)
- **API Documentation**: This knowledge base
- **Developer Portal**: [developers.zwitch.io](https://developers.zwitch.io)
- **Dashboard**: [dashboard.zwitch.io](https://dashboard.zwitch.io)
- **Support**: Contact support through your dashboard
- **Blog**: [zwitch.io/blog](https://zwitch.io/blog)

## Best Practices

1. **Never expose Secret Keys** in frontend code or client-side applications
2. **Use webhooks** for real-time status updates instead of polling
3. **Handle errors gracefully** and implement retry logic for transient failures
4. **Verify webhook signatures** to ensure authenticity
5. **Store API keys securely** using environment variables or secure key management

## Next Steps

- Read the [Authentication guide](./01_authentication.md) to get started
- Review [Error Codes](./02_error_codes.md) to understand error handling
- Check out [Code Examples](./13_examples_node.md) for Node.js or [Python Examples](./14_examples_python.md)

