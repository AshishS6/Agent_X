# Open Money — Platform Access and Developer Integration

## Important Clarification

**Open Money does NOT provide APIs directly.** Open Money is a **fintech operating platform** that provides a **dashboard/app interface** for businesses to access financial management features.

**APIs are provided by Zwitch**, not Open Money. If you need API access for payment processing, banking, or financial services, please refer to Zwitch's API documentation.

## What Open Money Is

Open Money is a **business finance operating platform** that provides:

- **Dashboard/App Interface**: Web and mobile app for accessing all features
- **Connected Banking**: Connect bank accounts and manage them through the dashboard
- **Invoice Management**: Create and manage invoices through the app
- **Payment Links**: Generate payment links through the dashboard
- **Bill Management**: Upload, manage, and pay bills through the platform
- **Expense Management**: Manage corporate cards and expenses through the app
- **Payroll Management**: Access Open Payroll features through the dashboard
- **Reconciliation**: View and manage reconciliation through the platform
- **GST Compliance**: Access GST features through the app

## Platform Access Methods

### Web Dashboard

Open Money provides a comprehensive web dashboard where businesses can:
- Access all financial management features
- Connect bank accounts
- Create invoices and bills
- Generate payment links
- Manage expenses and corporate cards
- Process payroll
- View reconciliation status
- Access reports and analytics

### Mobile App (Android)

Open Money provides a mobile app (Android) with features including:
- Billing on the go: Upload invoices or photograph bills
- Mobile bill management: Manage vendor bills and payments
- Get paid faster: Send invoices and track payments remotely
- Real-time notifications: Instant alerts on payment status
- Quick payment: Process payments with minimal taps
- Dashboard access: View key financial metrics anytime, anywhere

## Integration with Other Systems

While Open Money doesn't provide APIs directly, it integrates with:

### Accounting Software

- **Two-way sync** with Tally, Zoho Books, Oracle NetSuite, Microsoft Dynamics
- Automatic synchronization of bills and payments
- Real-time data sync
- No API required - integration is built into the platform

### Banking Systems

- **Connected Banking** integration with ICICI, SBI, Axis, Yes Bank
- Direct account connectivity through bank partnerships
- Real-time balance and transaction sync
- No API required - integration is handled by Open Money

### Payment Gateways

- Integration with payment gateways for collections
- Support for net banking, UPI, credit/debit cards
- Payment processing through connected payment infrastructure
- No direct API access - handled through the platform

## For Developers Needing APIs

If you are a developer and need API access for:

- Payment processing
- Banking integration
- Transaction processing
- Beneficiary management
- Account connectivity

**Please use Zwitch APIs** - Zwitch provides comprehensive developer APIs for these capabilities.

Open Money is designed as a **user-facing platform** (dashboard/app) for businesses to manage their finances, not as an API provider for developers.

## Platform vs API Provider

### Open Money (Platform/Dashboard)

- **Purpose**: User-facing platform for business financial management
- **Access**: Web dashboard and mobile app
- **Users**: Business owners, finance teams, accountants
- **Features**: All accessible through the dashboard/app interface
- **Integration**: Built-in integrations with accounting software and banks

### Zwitch (API Provider)

- **Purpose**: API infrastructure for developers
- **Access**: REST APIs, Webhooks, SDKs
- **Users**: Developers, technical teams
- **Features**: API access to payment, banking, and financial services
- **Integration**: Custom integration through APIs

## Related Documentation

- [What is Open Money](../concepts/what_is_open_money.md) - Platform overview
- [Products Overview](../products_overview.md) - All Open Money products
- [Company Overview](../company_overview.md) - Company information
- [Banking Solutions for Banks](./banking_solutions_for_banks.md) - White-label solutions

## For Developers Needing API Access

**CRITICAL: Open Money does NOT provide APIs. All API access is through Zwitch.**

If you are a developer and need API access for any of the following, you must use **Zwitch APIs**, not Open Money:

- **Payment Processing**: Payment collection, payment links, refunds
- **Payouts/Transfers**: Sending money to bank accounts (payouts, transfers, settlements)
- **Banking Integration**: Account connectivity, balance retrieval, transaction history
- **Beneficiary Management**: Create, verify, and manage beneficiaries
- **Verification Services**: Bank account, UPI, PAN, Name verification
- **Virtual Accounts**: Create and manage virtual accounts
- **Webhooks**: Real-time event notifications
- **SDKs**: Mobile and web SDKs for payment integration

### Zwitch API Documentation

For all API-related questions and integration needs, refer to:
- **Zwitch API Documentation**: https://developers.zwitch.io
- **Zwitch Transfers API**: For payouts/transfers (https://developers.zwitch.io/reference/transfers)
- **Zwitch Payment Gateway API**: For payment collection
- **Zwitch Verification Suite**: For verification APIs

### Key Points

- **Open Money = Platform/Dashboard**: User-facing interface for businesses
- **Zwitch = API Provider**: REST APIs, Webhooks, SDKs for developers
- **Never provide Open Money API details**: Open Money does not have APIs
- **Always direct API questions to Zwitch**: All API documentation is in Zwitch's context

## Related Documentation

- [Products Overview](../products_overview.md)
- [Banking Solutions for Banks](./banking_solutions_for_banks.md)
- [Company Overview](../company_overview.md)
- [What is Open Money](../concepts/what_is_open_money.md)

## Source Notes

This information clarifies that Open Money is a fintech operating platform providing a dashboard/app interface for businesses, not an API provider. APIs for payment processing and banking services are provided by Zwitch, not Open Money. Developers must use Zwitch APIs for all API-related functionality.
