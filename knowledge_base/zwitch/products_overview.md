# Zwitch Products Overview

## Main Product Categories

Zwitch offers four main product categories for businesses to integrate financial services:

---

## 1. Payment Gateway

**Description:** Full-featured payment gateway solution for accepting online payments with comprehensive payment options and developer-friendly integration.

### Features:
- **150+ Payment Methods**: Support for credit/debit cards, UPI, net banking, digital wallets, and more
- **Payment Links**: Generate shareable payment links for easy checkout without embedding payment forms
- **Instant Refunds**: Process refunds instantly to customer accounts
- **Recurring Payments**: Set up subscription and recurring payment flows for SaaS and subscription businesses
- **Native SDKs & Plugins**:
  - Layer.js for web applications
  - Android SDK for native Android apps
  - iOS SDK for native iOS apps
  - Flutter SDK for cross-platform mobile apps

### Integration Methods:
1. **Layer.js Payment Gateway** (Recommended for Web)
   - JavaScript library for frontend integration
   - Hosted payment page
   - Endpoint: `POST /v1/pg/payment_token`
   - [Documentation →](./api/15_layer_js.md)

2. **UPI Collect**
   - UPI-only payment collection
   - QR codes and payment links
   - Endpoint: `POST /v1/accounts/{account_id}/payments/upi/collect`
   - [Documentation →](./api/05_payments.md)

3. **Mobile SDKs**
   - Native Android, iOS, and Flutter SDKs
   - Seamless mobile payment integration

### Use Cases:
- E-commerce checkout
- SaaS subscription payments
- Marketplace transactions
- Service payments
- Donation collection

---

## 2. Payouts

**Description:** Instant account-to-account transfers supported by 150+ banks through Connected Banking infrastructure.

### Features:
- **Connected Banking**: Direct integration with 150+ banks for instant transfers
- **Instant Transfers**: Real-time account-to-account money movement
- **Payment Methods**: NEFT, RTGS, IMPS, UPI
- **Escrow Payments**: Secure escrow services for marketplace transactions
- **Payouts API**: Comprehensive API for single and bulk payouts
- **Beneficiary Management**: Create, verify, and manage beneficiaries

### Integration:
- Single transfers: `POST /v1/transfers`
- Bulk transfers: `POST /v1/transfers/bulk`
- Beneficiary management: `POST /v1/beneficiaries`
- [Documentation →](./api/07_transfers.md)

### Use Cases:
- Salary payments
- Vendor payouts
- Affiliate commissions
- Refund processing
- Marketplace settlements
- Escrow releases

---

## 3. Zwitch Bill Connect

**Description:** Interoperable bill payments connecting 1000+ ERPs, billers, and banks using NPCI's Bharat Connect Network.

### Features:
- **ERP Integration**: Connect with 1000+ ERPs including Zoho, Happay, and major banking platforms
- **150+ Connected Payment Methods**: Support for multiple payment options
- **Instant Bill Discounting API**: Real-time bill discounting capabilities
- **API Marketplace**: Access to additional financial services and integrations
- **NPCI Bharat Connect Network**: Powered by NPCI's Bharat Connect for interoperability
- **Real-Time Tracking**: Monitor invoice statuses and payments in real-time

### Capabilities:
- **Connect to ERPs**: Enable invoicing between your ERP and thousands of other platforms
- **Embed B2B Payments**: Enable bill payments by connecting 150+ bank accounts directly from your app
- **Real-Time Tracking**: Monitor invoice statuses and payments for accurate reconciliation
- **Generate Additional Revenue**: Facilitate interoperable bill payments and reconciliation within your existing app

### Integration:
- Business onboarding: `/v1/bharat-connect/onboarding/`
- Invoice management: `/v1/bharat-connect/invoice/`
- Payment requests: `/v1/bharat-connect/payment`
- [Documentation →](./api/09_bharat_connect.md)

### Use Cases:
- B2B invoice payments
- ERP-to-ERP invoicing
- Bill discounting
- Supply chain finance
- Vendor payment automation

---

## 4. Verification Suite

**Description:** Comprehensive verification, compliance, and onboarding APIs for identity and financial verification.

### Features:
- **Verification APIs**:
  - VPA (Virtual Payment Address) verification
  - Bank account verification (pennyless)
  - PAN (Permanent Account Number) verification
  - Name verification
- **Compliance APIs**: Regulatory compliance verification and checks
- **Onboarding APIs**: Customer onboarding and KYC workflows

### Integration:
- VPA verification: `/v1/verifications/vpa`
- Bank account verification: `/v1/verifications/bank-account/pennyless`
- PAN verification: `/v1/verifications/pan`
- Name verification: `/v1/verifications/name`
- [Documentation →](./api/08_verification.md)

### Use Cases:
- Customer onboarding
- KYC verification
- Payment method validation
- Compliance checks
- Identity verification
- Account verification before payouts

---

## Additional Services

### Connected Banking
- Account linking with 150+ banks
- Transaction history retrieval
- Balance inquiries
- Real-time account data
- [Documentation →](./api/12_connected_banking.md)

### Accounts & Virtual Accounts
- Create and manage virtual accounts
- Account balance and statements
- Account details and information
- [Documentation →](./api/03_accounts.md)

### Webhooks
- Real-time event notifications
- Payment status updates
- Transfer confirmations
- Webhook signature verification
- [Documentation →](./api/10_webhooks.md)

---

## Platform Statistics

- **4 Million+** businesses powered
- **150+** payment methods supported
- **$35 Billion+** in transactions processed
- **1000+** ERPs and banks connected (Bill Connect)
- **150+** banks supported for payouts

---

## Getting Started

1. **Sign up** at [zwitch.io](https://www.zwitch.io/)
2. **Generate API keys** from the dashboard
3. **Choose your integration method**:
   - Web: Use Layer.js (see [Layer.js documentation](./api/15_layer_js.md))
   - Mobile: Use native SDKs (Android/iOS/Flutter)
   - UPI Only: Use UPI Collect API
4. **Follow the integration guides** in the API documentation

---

## Related Documentation

- [Company Overview](./company_overview.md)
- [FAQ](./FAQ.md)
- [Payment Gateway Confirmation](./PAYMENT_GATEWAY.md)
- [API Introduction](./api/00_introduction.md)
- [Best Practices](./best_practices/production_checklist.md)

---

## Source Notes

This document is derived from publicly available information on the official Zwitch website and API documentation. All product features and capabilities are confirmed and documented in the respective API documentation files.
