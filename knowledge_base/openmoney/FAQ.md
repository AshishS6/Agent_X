# Open Money — Frequently Asked Questions

## What Is Open Money?

**Open Money is a fintech operating platform** that provides a **web dashboard and mobile app** for businesses to manage their finances. It is a **platform/dashboard interface**, not an API provider.

Open Money helps businesses:
- Collect money (invoices, payment links)
- Pay money (vendor bills, payouts)
- Track money (cashflow, receivables, payables)
- Reconcile money (automatic reconciliation with accounting software)
- Stay compliant (GST compliance, tax filing)

**Important:** Open Money is a **user-facing platform** (dashboard/app), not an API provider. APIs for payment processing and banking services are provided by **Zwitch**, not Open Money.

---

## What Products Does Open Money Offer?

Open Money offers **10 main products/features** accessible through its platform:

1. **Connected Banking**: Connect current accounts from ICICI, SBI, Axis, Yes Bank
2. **Pay Vendors**: Bill management and direct account-to-account payments
3. **Get Paid**: GST-compliant invoices, payment links, multiple payment modes
4. **Auto-Reconciliation**: Two-way sync with accounting software (Tally, Zoho Books, NetSuite, Dynamics)
5. **GST Compliance**: Invoicing, tax filing, compliance workflows
6. **Expense Management & Corporate Cards**: VISA-powered corporate cards, expense tracking
7. **Payroll Management (Open Payroll)**: HR and payroll management, 100% statutory compliant
8. **Banking Solutions for Banks**: White-label platform solutions for banks
9. **Platform Access**: Web dashboard and mobile app for accessing all features
10. **Lending & Credit Solutions**: Anchor-based financing, revenue-based financing, working capital loans

For detailed information, see [Products Overview](./products_overview.md).

---

## Does Open Money Provide APIs?

**NO. Open Money does NOT provide APIs directly.**

**Open Money is a platform/dashboard/app** for businesses to access financial management features through a user interface (web dashboard and mobile app).

**APIs are provided by Zwitch**, not Open Money. If you need API access for:
- Payment processing
- Banking integration
- Transaction processing
- Beneficiary management
- Account connectivity

**Please use Zwitch APIs** - Zwitch provides comprehensive developer APIs for these capabilities.

Open Money is designed as a **user-facing platform** for business owners, finance teams, and accountants, not as an API provider for developers.

See [Platform Access](./products/api_solutions.md) for more details.

---

## How Reliable Are Open Money Transaction Statuses?

**Open Money is a Payment Aggregator (PA) licensed by RBI and is liable for settlements.** Transaction statuses shown in Open Money are accurate and reliable:

### Transaction Statuses:

- **Success Status**: When Open Money shows a transaction as "success", it means the transaction has been successfully processed and settled by Open Money. You can trust this status - it indicates the transaction is complete and settled.

- **Failed Status**: When Open Money shows a transaction as "failed", it means the transaction has failed. This status is accurate and reliable.

- **Pending Status**: When a transaction shows as "pending", it means the transaction is still being processed. In this case, it's best to cross-check with your bank for the latest status, as Open Money's status is updated based on callbacks from the respective bank.

### Settlement Responsibility:

- **Open Money is responsible for settlements** as a licensed Payment Aggregator (PA) under RBI regulations.
- Settlements are processed by Open Money, not by banks directly.
- In cases where a transaction goes to a pending status, Open Money depends on the bank to provide callbacks or status updates to update the transaction status accordingly.

### Key Points:

- Open Money is **liable for settlements** as a licensed Payment Aggregator
- Success and failed statuses are **accurate and reliable**
- Pending statuses require **cross-checking with your bank** as updates depend on bank callbacks
- Open Money provides **real-time status updates** based on bank callbacks

---

## What Banks Does Open Money Support?

Open Money supports **Connected Banking** with the following banks:

- **ICICI Bank**: ICICI Connected Banking
- **State Bank of India (SBI)**: SBI Connected Banking
- **Axis Bank**: Axis Bank Connected Banking
- **Yes Bank**: Yes Bank Connected Banking

**15 out of 20 top Indian banks** use Open Money for powering business payments.

### Features:
- Connect multiple current accounts from supported banks
- Real-time balance visibility
- Transaction history sync
- Direct account-to-account payments
- Multi-bank account management in one dashboard

See [Connected Banking](./products_overview.md#1-connected-banking) for details.

---

## How Does Open Money Reconciliation Work?

Open Money provides **automatic reconciliation** of payments with bills, invoices, and bank transactions.

### Reconciliation Process:

1. **Data Gathering**: Open Money gathers data from:
   - Financial documents (invoices, bills)
   - Payment records
   - Bank transactions (from connected accounts)
   - Accounting software records

2. **Automatic Matching**: 
   - Match documents to payments automatically
   - Match payments to bank entries
   - Verify amounts and confirm reconciliation

3. **Reconciliation Status**:
   - `pending`: Not yet reconciled
   - `reconciled`: Successfully matched
   - `discrepancy`: Mismatch detected

4. **Accounting Software Sync**:
   - Two-way sync with Tally, Zoho Books, Oracle NetSuite, Microsoft Dynamics
   - Automatic synchronization of bills and payments
   - Real-time data sync

### Benefits:
- Save 500+ hours annually on reconciliation
- 25% reduction in reconciliation efforts
- Reduce errors and discrepancies
- Maintain accurate financial records

### Reconciliation Frequency:
- Daily reconciliation for high-volume businesses
- Weekly reconciliation for moderate activity
- Monthly reconciliation for low activity

**Important:** Reconciliation is **mandatory, not optional**. It is required for financial accuracy and compliance.

See [Reconciliation Flow](./workflows/reconciliation_flow.md) for detailed process.

---

## What Accounting Software Does Open Money Integrate With?

Open Money integrates with **leading accounting software** through built-in two-way sync:

- **Tally**: Full integration with Tally accounting software
- **Zoho Books**: Seamless sync with Zoho Books
- **Oracle NetSuite**: Enterprise-level integration
- **Microsoft Dynamics**: Microsoft Dynamics integration

### Integration Features:
- **Two-Way Sync**: Automatic synchronization of bills and payments
- **Real-Time Updates**: Maintain live, accurate financial records
- **Manual Data Entry Elimination**: Reduce reconciliation efforts significantly
- **Error Reduction**: Minimize manual entry errors through automated syncing

**No API required** - integration is built into the Open Money platform.

See [Auto-Reconciliation](./products_overview.md#4-auto-reconciliation) for details.

---

## How Do I Get Started with Open Money?

1. **Sign Up**: Visit [open.money](https://open.money/) and create an account
2. **Connect Your Bank Account**: Connect your current account from ICICI, SBI, Axis, or Yes Bank
3. **Set Up Accounting Software Sync**: Connect your accounting software (Tally, Zoho Books, etc.)
4. **Start Creating Invoices or Bills**: Create invoices to get paid or bills to pay vendors
5. **Make Payments and Get Paid**: Process payments directly from your connected accounts

### Getting Started Checklist:
- ✅ Create Open Money account
- ✅ Connect bank account(s)
- ✅ Set up accounting software integration
- ✅ Create your first invoice or bill
- ✅ Process your first payment

---

## What Payment Methods Does Open Money Support for Collections?

Open Money supports **multiple payment methods** for receiving payments:

- **Net Banking**: Direct bank transfers
- **UPI (Unified Payments Interface)**: UPI payments
- **Credit Cards**: Credit card payments
- **Debit Cards**: Debit card payments
- **Payment Links**: Shareable payment links for easy collection

### Features:
- Instant settlement directly into bank account
- Support for split payments
- Adjustments against credit notes
- Payment reminders and follow-ups

See [Get Paid](./products_overview.md#3-get-paid) for details.

---

## What Is Open Payroll?

**Open Payroll** is Open Money's comprehensive HR and payroll management system.

### Features:
- **Automated Payroll Calculation**: Automatic salary and TDS calculations
- **100% Statutory Compliant Payslips**: Auto-generate compliant payslips
- **One-Click Processing**: Run monthly payroll in a single click
- **Form 16 Generation**: Automatic Form 16 preparation for tax filing
- **Leave Management**: Digital leave request and approval system
- **Income Tax Planning**: Employee self-service for tax declaration
- **E-GST Filing**: Automated electronic GST filing
- **Employee Self-Service Portal**: Employees can view payslips, submit leaves, update tax info

### Benefits:
- Save 500+ hours annually on payroll processing
- 100% statutory compliance automatically
- Reduce HR and payroll processing costs
- Better employee lifecycle management

See [Payroll Management](./products/payroll_management.md) for details.

---

## What Are Open Money's Corporate Cards?

Open Money offers **VISA-powered corporate cards** for expense management:

### Card Types:
- **Standard Corporate Cards**: For general business expenses
- **Prepaid Expense Cards**: Physical cards for offline purchases
- **Travel & Entertainment Cards**: For business travel and dining
- **Project-Based Cards**: Cards with specific spending limits for projects

### Features:
- **Smart Controls**: Set spending limits and approve transactions in real-time
- **Expense Tracking**: Comprehensive tracking of all employee spending
- **Real-Time Approval**: Managers can approve or reject expenses instantly
- **Automatic Reconciliation**: Card expenses automatically synced with accounting software
- **No Receipt Requirements**: Prepaid cards eliminate receipt saving burden

See [Expense Management](./products/expense_management.md) for details.

---

## What Is the Difference Between Open Money and Zwitch?

### Open Money (Platform/Dashboard)
- **Purpose**: User-facing platform for business financial management
- **Access**: Web dashboard and mobile app
- **Users**: Business owners, finance teams, accountants
- **Features**: All accessible through dashboard/app interface
- **Integration**: Built-in integrations with accounting software and banks
- **APIs**: Does NOT provide APIs

### Zwitch (API Provider)
- **Purpose**: API infrastructure for developers
- **Access**: REST APIs, Webhooks, SDKs
- **Users**: Developers, technical teams
- **Features**: API access to payment, banking, and financial services
- **Integration**: Custom integration through APIs
- **APIs**: Provides comprehensive developer APIs

**Key Distinction:** Open Money is a **platform/dashboard** for businesses. Zwitch is an **API provider** for developers.

See [What is Open Money](./concepts/what_is_open_money.md) for more details.

---

## What Are Open Money's Platform Statistics?

- **3.5 Million+** businesses using Open Money
- **$35 Billion+** transactions processed annually
- **65,000+** tax practitioners
- **15 out of 20** top banks use Open
- **35,000** new SMEs and startups join monthly
- **600+** employees ("Openers")

### Business Impact:
- **80% reduction** in manual payment tasks
- **500 hours saved** annually on reconciliation
- **25% improvement** in reconciliation efforts

---

## How Does Open Money Handle GST Compliance?

Open Money provides built-in **GST compliance** features:

### GST Features:
- **GST-Compliant Invoicing**: All invoices automatically include GST split-up
- **Automated GST Filing**: Automatic e-GST return filing (Form GSTR-1, GSTR-3B, etc.)
- **Tax Calculation**: Automatic tax calculations on invoices and payments
- **Compliance Tracking**: Real-time compliance with GST regulations
- **IRP Integration**: Invoice Registration Portal (IRP) integration for e-invoicing

### Benefits:
- Stay compliant with GST regulations
- Reduce compliance errors
- Automated tax calculations
- Easy tax filing process

See [GST Compliance](./products_overview.md#5-gst-compliance) for details.

---

## What Lending Products Does Open Money Offer?

Open Money offers **alternative lending products** leveraging transactional data:

1. **Anchor-Based Financing**: Financing for businesses with anchor company relationships
2. **Revenue-Based Financing**: Financing based on business revenue and cash flows
3. **Early Settlement Programs**: Options to get paid early by suppliers for a discount
4. **Working Capital Loans**: Short-term loans for operational needs
5. **Business Credit Cards**: Specialized credit cards for SME business needs

### Benefits:
- Faster approval based on transaction data
- Competitive interest rates
- Flexible repayment terms
- Minimal paperwork

See [Lending Solutions](./products/lending_solutions.md) for details.

---

## Who Founded Open Money and When?

Open Money was **founded in 2017** by:

- **Anish Achuthan** — Co-founder
- **Mabel Chacko** — Co-founder
- **Ajeesh Achuthan** — Co-founder
- **Deena Jacob** — Co-founder

**Headquarters:** Bengaluru, Karnataka, India

**Mission:** To automate business finances, simplify payments, and improve cash flow management for SMEs and startups across India.

See [History and Foundation](./company/history_and_foundation.md) for details.

---

## What Investors Back Open Money?

Open Money is backed by **marquee investors**:

- **Tiger Global**
- **Temasek**
- **3one4 Capital**
- **IIFL (India Infoline Finance Limited)**

These investors serve as **strategic partners**, helping drive local partnerships with banks, financial institutions, and fintech/solution providers globally.

See [Funding and Investors](./company/funding_and_investors.md) for details.

---

## How Do I Access Open Money?

Open Money can be accessed through:

### Web Dashboard
- Comprehensive dashboard for all financial management features
- Access at [open.money](https://open.money/)
- All features accessible through web interface

### Mobile App (Android)
- Available on Google Play Store
- Features include:
  - Billing on the go
  - Mobile bill management
  - Get paid faster
  - Real-time notifications
  - Quick payment processing
  - Dashboard access

**No API access required** - all features are accessible through the platform interface.

---

## Need Help?

- **Website**: [open.money](https://open.money/)
- **Sign Up**: [open.money](https://open.money/)
- **Products Overview**: [Products Overview](./products_overview.md)
- **Company Overview**: [Company Overview](./company_overview.md)
- **What is Open Money**: [What is Open Money](./concepts/what_is_open_money.md)

---

## Related Documentation

- [Products Overview](./products_overview.md) - Complete product information
- [Company Overview](./company_overview.md) - Company information
- [What is Open Money](./concepts/what_is_open_money.md) - Platform overview
- [Reconciliation Flow](./workflows/reconciliation_flow.md) - Reconciliation process
- [Invoice to Collection](./workflows/invoice_to_collection.md) - Invoice flow
- [Bill to Payout](./workflows/bill_to_payout.md) - Bill payment flow
