# Compliance Boundaries: What You're Responsible For

## Important Disclaimer

**This document provides general guidance only. It does not constitute legal, financial, or compliance advice. Always consult with legal and compliance experts for your specific situation.**

## Overview

When using Zwitch's APIs, you have **compliance responsibilities** that Zwitch cannot handle for you. Understanding these boundaries is critical for operating legally and safely.

## What Zwitch Handles

**Zwitch is responsible for:**
- Payment processing infrastructure
- Banking partner relationships
- Regulatory compliance for payment processing
- KYC/AML for their direct operations
- PCI DSS compliance (for payment data handling)

**Note:** This is a general statement. Verify current responsibilities with Zwitch's terms of service and agreements.

## What You're Responsible For

### 1. Customer KYC/AML

**Your responsibility:**
- Know Your Customer (KYC) verification
- Anti-Money Laundering (AML) checks
- Customer due diligence
- Ongoing monitoring

**When required:**
- Before allowing high-value transactions
- For certain business models (marketplaces, platforms)
- As per regulatory requirements in your jurisdiction

**What to do:**
- Implement KYC verification (use Zwitch's verification APIs if available)
- Store KYC documents securely
- Monitor transactions for suspicious activity
- Report suspicious transactions to authorities

**What NOT to do:**
- Don't skip KYC for high-risk customers
- Don't store KYC data insecurely
- Don't ignore suspicious activity

### 2. Data Privacy and Security

**Your responsibility:**
- Protecting customer data (PII, payment data)
- GDPR compliance (if applicable)
- Data breach notification
- Secure data storage and transmission

**Requirements:**
- Encrypt sensitive data at rest and in transit
- Implement access controls
- Regular security audits
- Data breach response plan

**What to do:**
- Use HTTPS for all API calls
- Encrypt sensitive data in database
- Implement proper access controls
- Regular security assessments
- Have incident response plan

**What NOT to do:**
- Don't store payment data unnecessarily (use tokens)
- Don't log sensitive data (card numbers, etc.)
- Don't expose customer data in APIs
- Don't skip security measures

### 3. Tax Compliance

**Your responsibility:**
- GST/VAT collection and remittance
- Income tax on your revenue
- TDS (Tax Deducted at Source) if applicable
- Tax reporting and filing

**Note:** Zwitch processes payments, but you're responsible for tax obligations on your revenue.

**What to do:**
- Consult with tax advisor
- Understand tax obligations for your business model
- Collect and remit taxes as required
- Maintain proper records
- File tax returns on time

**What NOT to do:**
- Don't assume Zwitch handles your taxes
- Don't ignore tax obligations
- Don't skip tax reporting

### 4. Business Licenses and Permits

**Your responsibility:**
- Obtaining required business licenses
- Regulatory approvals (if needed)
- Industry-specific permits

**Examples:**
- E-commerce license
- Money service business license (if applicable)
- Industry-specific licenses

**What to do:**
- Research license requirements for your business
- Obtain necessary licenses before operating
- Renew licenses on time
- Comply with license conditions

### 5. Terms of Service and User Agreements

**Your responsibility:**
- Creating and maintaining terms of service
- Privacy policy
- Refund policy
- User agreements

**What to do:**
- Have clear terms of service
- Define refund policy
- Specify dispute resolution process
- Update policies as needed

### 6. Fraud Prevention

**Your responsibility:**
- Detecting and preventing fraud on your platform
- Monitoring for suspicious transactions
- Implementing fraud prevention measures
- Reporting fraud to authorities

**What to do:**
- Monitor transactions for suspicious patterns
- Implement fraud detection (velocity checks, etc.)
- Verify customer identity
- Report fraud to authorities

**What NOT to do:**
- Don't ignore suspicious transactions
- Don't skip fraud checks
- Don't delay fraud reporting

### 7. Record Keeping and Audits

**Your responsibility:**
- Maintaining transaction records
- Audit trails
- Financial records
- Compliance documentation

**Requirements:**
- Keep records for required period (varies by jurisdiction)
- Maintain audit trail of all transactions
- Document compliance activities
- Prepare for audits

**What to do:**
- Store all transaction records
- Log all API calls and webhooks
- Maintain audit trail
- Regular record reviews

## Boundaries: What Zwitch Cannot Do For You

### ❌ Zwitch Cannot:

1. **Handle your tax obligations**
   - You're responsible for your own taxes
   - Zwitch processes payments, not your tax compliance

2. **Provide legal advice**
   - Zwitch provides technical infrastructure
   - Consult lawyers for legal matters

3. **Guarantee compliance**
   - Zwitch ensures their compliance
   - You must ensure your compliance

4. **Handle customer disputes**
   - You handle disputes with your customers
   - Zwitch handles payment processing issues

5. **Provide compliance guarantees**
   - Zwitch complies with payment regulations
   - You must comply with your business regulations

## Best Practices

### ✅ Do:
1. **Consult experts** (lawyers, accountants, compliance officers)
2. **Understand your obligations** (research, ask questions)
3. **Implement compliance measures** (KYC, security, etc.)
4. **Maintain records** (audit trail, documentation)
5. **Monitor compliance** (regular reviews, updates)
6. **Stay informed** (regulatory changes, updates)

### ❌ Don't:
1. **Don't assume Zwitch handles everything** (you have responsibilities)
2. **Don't skip compliance** (legal and financial risks)
3. **Don't ignore regulations** (can lead to penalties)
4. **Don't store data insecurely** (privacy and security risks)
5. **Don't skip expert advice** (compliance is complex)

## Risk Mitigation

### For High-Risk Scenarios:

**Marketplaces/Platforms:**
- Additional KYC requirements
- Escrow compliance
- Seller verification
- Settlement regulations

**High-Value Transactions:**
- Enhanced KYC
- AML monitoring
- Regulatory reporting

**International Operations:**
- Cross-border regulations
- Currency compliance
- Tax implications

## Documentation Requirements

**Maintain documentation for:**
- KYC records
- Transaction logs
- Compliance activities
- Security measures
- Audit trails

**Retention periods:**
- Varies by jurisdiction and record type
- Typically 5-7 years for financial records
- Consult legal advisor for specifics

## Summary

- **You have compliance responsibilities** that Zwitch cannot handle
- **Consult experts** (lawyers, accountants, compliance officers)
- **Implement compliance measures** (KYC, security, record keeping)
- **Maintain records** (audit trail, documentation)
- **Stay informed** (regulatory changes)
- **This is not legal advice** (consult experts for your situation)

**Bottom line:** Zwitch provides payment infrastructure, but you're responsible for your business compliance. Don't assume Zwitch handles everything—understand your obligations and implement appropriate measures.

## Related Documentation

- [Verification API](../api/08_verification.md) - KYC verification tools
- [Logging and Audits](../best_practices/logging_and_audits.md) - Record keeping
- [Production Checklist](../best_practices/production_checklist.md) - Compliance checklist

