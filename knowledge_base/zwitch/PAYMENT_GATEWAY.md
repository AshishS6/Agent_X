# Zwitch Payment Gateway - Direct Answer

## Does Zwitch Offer Payment Gateway Services?

**YES. Zwitch offers a full Payment Gateway solution.**

Zwitch provides Payment Gateway services as one of its four main product categories. This is explicitly stated on their website and in their documentation.

## Quick Facts

- **Product Category**: Payment Gateway is listed as Product #1 on zwitch.io
- **150+ Payment Methods**: Cards, UPI, Net Banking, Wallets
- **Integration Methods**: Layer.js (web), Android SDK, iOS SDK, Flutter SDK
- **Features**: Payment Links, Instant Refunds, Recurring Payments
- **API Endpoint**: `/v1/pg/payment_token` (Payment Gateway namespace)

## Direct Quote from Zwitch Website

From zwitch.io homepage:
> "Payment Gateway: 150+ Payment Options, Payment Links, Instant Refunds, Recurring Payments, Native SDKs & Plugins"

## Integration Options

1. **Layer.js Payment Gateway** - For web applications
   - Endpoint: `POST /v1/pg/payment_token`
   - Documentation: See [Layer.js guide](./api/15_layer_js.md)

2. **Mobile SDKs** - For native mobile apps
   - Android, iOS, Flutter SDKs available

3. **UPI Collect** - For UPI-only payments
   - Endpoint: `POST /v1/accounts/{account_id}/payments/upi/collect`

## Conclusion

**Zwitch absolutely offers Payment Gateway services.** It is a core product offering, not an implied or suggested feature. The Payment Gateway is explicitly listed on their website, has dedicated API endpoints under the `/v1/pg/` namespace, and includes comprehensive documentation and SDKs.

For integration, see:
- [Payment Gateway Introduction](./api/00_introduction.md#1-payment-gateway)
- [Layer.js Integration Guide](./api/15_layer_js.md)
- [FAQ](./FAQ.md)

