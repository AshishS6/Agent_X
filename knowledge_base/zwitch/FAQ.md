# Zwitch API — Frequently Asked Questions

## Does Zwitch Offer Payment Gateway (PG) Services?

**YES. Zwitch offers Payment Gateway services. This is a core product offering, explicitly listed on their website as one of four main product categories.**

Zwitch provides a comprehensive Payment Gateway solution that includes:

Zwitch provides a full-featured Payment Gateway service that includes:

### Payment Gateway Features
- **150+ Payment Options**: Support for credit/debit cards, UPI, net banking, wallets, and more
- **Payment Links**: Generate shareable payment links for easy checkout
- **Instant Refunds**: Process refunds instantly
- **Recurring Payments**: Set up subscription and recurring payment flows
- **Native SDKs & Plugins**: 
  - Layer.js for web integration
  - Android SDK
  - iOS SDK
  - Flutter SDK

### Payment Gateway Integration Methods

1. **Layer.js Payment Gateway** (Recommended for Web)
   - JavaScript library for frontend integration
   - Hosted payment page
   - Supports multiple payment methods
   - Endpoint: `POST /v1/pg/payment_token`
   - [Documentation →](./api/15_layer_js.md)

2. **UPI Collect**
   - Request payments via UPI
   - QR codes and payment links
   - Endpoint: `POST /v1/accounts/{account_id}/payments/upi/collect`
   - [Documentation →](./api/05_payments.md)

3. **Mobile SDKs**
   - Native Android, iOS, and Flutter SDKs
   - Seamless mobile payment integration

### Key Statistics
- **4 Million+** businesses powered
- **150+** payment methods supported
- **$35 Billion+** in transactions processed

### Getting Started with Payment Gateway

1. Sign up at [zwitch.io](https://www.zwitch.io/)
2. Generate API keys from the dashboard
3. Choose your integration method:
   - **Web**: Use Layer.js (see [Layer.js documentation](./api/15_layer_js.md))
   - **Mobile**: Use native SDKs (Android/iOS/Flutter)
   - **UPI Only**: Use UPI Collect API
4. Follow the integration guides in the API documentation

### Related Documentation
- [Payment Gateway Introduction](./api/00_introduction.md#1-payment-gateway)
- [Layer.js Integration Guide](./api/15_layer_js.md)
- [Payments API Documentation](./api/05_payments.md)

---

## What Payment Methods Does Zwitch Support?

Zwitch supports **150+ payment methods** including:
- Credit and Debit Cards
- UPI (Unified Payments Interface)
- Net Banking
- Digital Wallets
- And many more payment options

---

## How Do I Integrate Zwitch Payment Gateway?

### For Web Applications:
Use **Layer.js** - Zwitch's JavaScript payment library:
1. Create a payment token server-side: `POST /v1/pg/payment_token`
2. Initialize Layer.js on your frontend
3. Handle payment callbacks

See [Layer.js Integration Guide](./api/15_layer_js.md) for complete steps.

### For Mobile Applications:
Use Zwitch's native SDKs:
- Android SDK
- iOS SDK
- Flutter SDK

### For UPI-Only Integration:
Use UPI Collect API: `POST /v1/accounts/{account_id}/payments/upi/collect`

---

## What's the Difference Between Payment Gateway and UPI Collect?

- **Payment Gateway (Layer.js)**: Full-featured payment solution supporting 150+ payment methods (cards, UPI, net banking, wallets). Best for comprehensive checkout experiences.

- **UPI Collect**: UPI-only payment collection. Simpler integration, QR codes and payment links. Best for UPI-focused use cases.

Both are part of Zwitch's Payment Gateway product category.

---

## Where Can I Find Payment Gateway Documentation?

- **Main Introduction**: [API Introduction](./api/00_introduction.md#1-payment-gateway)
- **Layer.js Guide**: [Layer.js Payment Gateway](./api/15_layer_js.md)
- **Payments API**: [Payments Documentation](./api/05_payments.md)
- **Official Docs**: [developers.zwitch.io](https://developers.zwitch.io)

---

---

## What Products Does Zwitch Offer?

Zwitch offers **four main product categories**:

1. **Payment Gateway**
   - 150+ payment methods
   - Payment links, instant refunds, recurring payments
   - Native SDKs (Android, iOS, Flutter) and Layer.js for web
   - See [Products Overview](./products_overview.md) for details

2. **Payouts**
   - Connected Banking with 150+ banks
   - Instant account-to-account transfers
   - NEFT/RTGS/IMPS/UPI support
   - Escrow payments
   - See [Products Overview](./products_overview.md) for details

3. **Zwitch Bill Connect**
   - Connected with 1000+ ERPs and Banks
   - 150+ Connected Payment Methods
   - Instant Bill Discounting API
   - API Marketplace
   - NPCI Bharat Connect Network
   - See [Products Overview](./products_overview.md) for details

4. **Verification Suite**
   - Verification APIs (VPA, Bank Account, PAN, Name)
   - Compliance APIs
   - Onboarding APIs
   - See [Products Overview](./products_overview.md) for details

For comprehensive product information, see [Products Overview](./products_overview.md).

---

## What Are Zwitch's Platform Statistics?

- **4 Million+** businesses powered
- **150+** payment methods supported
- **$35 Billion+** in transactions processed
- **1000+** ERPs and banks connected (via Bill Connect)
- **150+** banks supported for payouts

---

## How Do I Get Started with Zwitch?

1. **Sign Up**: Visit [zwitch.io](https://www.zwitch.io/) and create an account
2. **Generate API Keys**: Get your API keys from the dashboard
3. **Choose Integration Method**:
   - **Web**: Use Layer.js (see [Layer.js documentation](./api/15_layer_js.md))
   - **Mobile**: Use native SDKs (Android/iOS/Flutter)
   - **UPI Only**: Use UPI Collect API
4. **Follow Documentation**: See [API Introduction](./api/00_introduction.md) for detailed guides
5. **Test in Sandbox**: Use test credentials to test your integration
6. **Go Live**: Once tested, switch to production credentials

---

## What Is the Base URL for Zwitch APIs?

**Base URL:** `https://api.zwitch.io/v1`

All API endpoints are prefixed with this base URL. For example:
- Payment Gateway: `POST https://api.zwitch.io/v1/pg/payment_token`
- UPI Collect: `POST https://api.zwitch.io/v1/accounts/{account_id}/payments/upi/collect`
- Transfers: `POST https://api.zwitch.io/v1/transfers`

---

## How Does Zwitch Authentication Work?

Zwitch uses **Bearer token authentication**:

- **Format**: `Bearer ACCESS_KEY:SECRET_KEY`
- **Header**: `Authorization: Bearer ACCESS_KEY:SECRET_KEY`
- **Generation**: API keys are generated from the Zwitch dashboard
- **Security**: Keep your API keys secure and never expose them in client-side code

See [Authentication Documentation](./api/01_authentication.md) for details.

---

## What Is the Difference Between Payment Gateway and Payouts?

- **Payment Gateway (Payin)**: Money coming IN - Accept payments from customers
  - Customer pays you
  - Use cases: E-commerce, SaaS subscriptions, service payments
  - Endpoint: `POST /v1/pg/payment_token` or `POST /v1/accounts/{account_id}/payments/upi/collect`

- **Payouts**: Money going OUT - Send money to vendors, employees, partners
  - You pay others
  - Use cases: Vendor payments, salary payments, affiliate commissions, refunds
  - Endpoint: `POST /v1/transfers` or `POST /v1/transfers/bulk`

Both are separate product categories with different use cases and APIs.

---

## Does Zwitch Support Webhooks?

**YES.** Zwitch supports webhooks for real-time event notifications.

### Webhook Features:
- Real-time payment status updates
- Transfer confirmations
- Event notifications
- Secure webhook signature verification
- Automatic retry for failed deliveries

### Webhook Events:
- Payment status changes
- Transfer status updates
- Account updates
- And more

See [Webhooks Documentation](./api/10_webhooks.md) for setup and configuration.

---

## What Is Zwitch Bill Connect?

**Zwitch Bill Connect** is Zwitch's interoperable bill payment solution that connects 1000+ ERPs, billers, and banks using NPCI's Bharat Connect Network.

### Features:
- Connect to 1000+ ERPs and Banks
- 150+ Connected Payment Methods
- Instant Bill Discounting API
- API Marketplace
- Real-time invoice and payment tracking

### Use Cases:
- B2B invoice payments
- ERP-to-ERP invoicing
- Bill discounting
- Supply chain finance

See [Bharat Connect Documentation](./api/09_bharat_connect.md) for details.

---

## What Verification Services Does Zwitch Offer?

Zwitch Verification Suite provides:

- **VPA Verification**: Verify UPI Virtual Payment Addresses
- **Bank Account Verification**: Pennyless bank account verification
- **PAN Verification**: Verify Permanent Account Numbers
- **Name Verification**: Verify names against documents

See [Verification API Documentation](./api/08_verification.md) for details.

---

## Need Help?

- **Dashboard**: [dashboard.zwitch.io](https://dashboard.zwitch.io)
- **API Documentation**: [developers.zwitch.io](https://developers.zwitch.io)
- **Support**: Contact support through your dashboard
- **Website**: [zwitch.io](https://www.zwitch.io/)
- **Products Overview**: [Products Overview](./products_overview.md)
- **Company Overview**: [Company Overview](./company_overview.md)

