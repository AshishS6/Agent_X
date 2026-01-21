# Production Checklist: Going Live with Zwitch

## Overview

This checklist ensures your Zwitch integration is **production-ready** before going live. Complete each item before processing real payments.

## Pre-Launch Checklist

### 1. API Configuration

- [ ] **API Keys Generated**
  - [ ] Production access key generated
  - [ ] Production secret key generated
  - [ ] Keys stored securely (environment variables, secret management)
  - [ ] Keys NOT committed to version control
  - [ ] Keys rotated if exposed

- [ ] **Environment Setup**
  - [ ] Production environment configured
  - [ ] Sandbox/testing environment separate
  - [ ] Environment variables properly set
  - [ ] No hardcoded credentials

- [ ] **Base URL**
  - [ ] Using production URL: `https://api.zwitch.io/v1`
  - [ ] Not using sandbox URL in production

### 2. Webhook Configuration

- [ ] **Webhook Endpoint**
  - [ ] Webhook URL configured in dashboard
  - [ ] Webhook URL uses HTTPS (required)
  - [ ] Webhook endpoint is publicly accessible
  - [ ] Webhook endpoint responds within 5 seconds

- [ ] **Webhook Security**
  - [ ] Signature verification implemented
  - [ ] Webhook secret stored securely
  - [ ] Invalid signatures rejected (return 401)
  - [ ] Signature verification tested

- [ ] **Webhook Events**
  - [ ] Required events subscribed (payment.completed, transfer.completed, etc.)
  - [ ] Webhook handler processes all subscribed events
  - [ ] Webhook handler is idempotent
  - [ ] Webhook failures handled gracefully

- [ ] **Webhook Testing**
  - [ ] Tested with Zwitch test webhooks
  - [ ] Tested webhook retry logic
  - [ ] Tested webhook failure scenarios

### 3. Payment Processing

- [ ] **Payment Creation**
  - [ ] Payment creation only from backend (not frontend)
  - [ ] Payment IDs stored in database
  - [ ] Payment metadata includes order references
  - [ ] Payment expiry handled properly

- [ ] **Payment Status Handling**
  - [ ] Only mark as paid when status is `completed` (not `processing`)
  - [ ] Payment status webhooks processed
  - [ ] Payment status reconciliation implemented
  - [ ] Failed/expired payments handled

- [ ] **Idempotency**
  - [ ] Idempotency checks implemented
  - [ ] Duplicate webhook processing prevented
  - [ ] Idempotency keys stored in database
  - [ ] Idempotency tested

### 4. Transfer/Payout Processing

- [ ] **Beneficiary Management**
  - [ ] Beneficiaries created before transfers
  - [ ] Beneficiary verification checked (if required)
  - [ ] Beneficiary details stored securely
  - [ ] Invalid beneficiaries rejected

- [ ] **Transfer Creation**
  - [ ] Transfers only from backend
  - [ ] Transfer IDs stored in database
  - [ ] Transfer metadata includes references
  - [ ] Sufficient balance checked before transfer

- [ ] **Transfer Status Handling**
  - [ ] Transfer status webhooks processed
  - [ ] Transfer failures handled
  - [ ] Transfer retry logic implemented (if appropriate)
  - [ ] Failed transfers logged and alerted

### 5. Security

- [ ] **API Key Security**
  - [ ] Secret keys never exposed in frontend
  - [ ] Secret keys stored securely
  - [ ] Secret keys not logged
  - [ ] Secret keys rotated periodically

- [ ] **Webhook Security**
  - [ ] Webhook signatures verified
  - [ ] Invalid webhooks rejected
  - [ ] Webhook endpoint rate limited
  - [ ] Webhook endpoint monitored

- [ ] **Data Security**
  - [ ] Sensitive data encrypted at rest
  - [ ] Sensitive data encrypted in transit (HTTPS)
  - [ ] Payment data not logged unnecessarily
  - [ ] Access controls implemented

- [ ] **Authentication**
  - [ ] Your API requires authentication
  - [ ] User permissions checked
  - [ ] Admin operations require additional auth

### 6. Error Handling

- [ ] **API Error Handling**
  - [ ] All API errors handled gracefully
  - [ ] Error messages logged (without secrets)
  - [ ] Transient errors retried (with backoff)
  - [ ] Permanent errors not retried

- [ ] **Webhook Error Handling**
  - [ ] Webhook processing errors handled
  - [ ] Failed webhooks logged
  - [ ] Webhook retry logic implemented
  - [ ] Dead letter queue for failed webhooks

- [ ] **User-Facing Errors**
  - [ ] User-friendly error messages
  - [ ] Technical errors not exposed to users
  - [ ] Error recovery options provided

### 7. Database

- [ ] **Schema**
  - [ ] Database schema implemented
  - [ ] Indexes added (performance)
  - [ ] Constraints added (data integrity)
  - [ ] Foreign keys defined

- [ ] **Data Integrity**
  - [ ] Transactions used for related operations
  - [ ] Idempotency enforced (unique constraints)
  - [ ] Data validation implemented
  - [ ] Backup strategy in place

- [ ] **Performance**
  - [ ] Database queries optimized
  - [ ] Slow queries identified and fixed
  - [ ] Connection pooling configured
  - [ ] Database monitoring in place

### 8. Monitoring and Logging

- [ ] **Logging**
  - [ ] All API calls logged
  - [ ] All webhooks logged
  - [ ] Payment/transfer status changes logged
  - [ ] Errors logged with context
  - [ ] Sensitive data not logged

- [ ] **Monitoring**
  - [ ] Payment success rate monitored
  - [ ] Transfer success rate monitored
  - [ ] Webhook delivery rate monitored
  - [ ] API error rate monitored
  - [ ] System health monitored

- [ ] **Alerting**
  - [ ] High error rate alerts configured
  - [ ] Failed webhook alerts configured
  - [ ] Payment/transfer failure alerts configured
  - [ ] System downtime alerts configured

### 9. Reconciliation

- [ ] **Reconciliation Process**
  - [ ] Reconciliation job implemented
  - [ ] Reconciliation runs regularly (hourly/daily)
  - [ ] Discrepancies detected and logged
  - [ ] Discrepancies resolved automatically (when safe)
  - [ ] Manual review process for risky discrepancies

- [ ] **Reconciliation Testing**
  - [ ] Reconciliation tested with test data
  - [ ] Discrepancy detection tested
  - [ ] Resolution process tested

### 10. Testing

- [ ] **Unit Tests**
  - [ ] Payment creation tested
  - [ ] Webhook processing tested
  - [ ] Idempotency tested
  - [ ] Error handling tested

- [ ] **Integration Tests**
  - [ ] End-to-end payment flow tested
  - [ ] Webhook delivery tested
  - [ ] Transfer flow tested
  - [ ] Reconciliation tested

- [ ] **Security Tests**
  - [ ] Webhook signature verification tested
  - [ ] API key security tested
  - [ ] Input validation tested

- [ ] **Load Tests**
  - [ ] System handles expected load
  - [ ] Rate limits understood
  - [ ] Performance acceptable

### 11. Documentation

- [ ] **Internal Documentation**
  - [ ] Integration documented
  - [ ] API usage documented
  - [ ] Webhook handling documented
  - [ ] Error handling documented
  - [ ] Runbooks for common issues

- [ ] **Team Knowledge**
  - [ ] Team trained on Zwitch integration
  - [ ] Support team knows how to troubleshoot
  - [ ] Escalation process defined

### 12. Compliance

- [ ] **Legal/Compliance**
  - [ ] Terms of service updated
  - [ ] Privacy policy updated
  - [ ] Refund policy defined
  - [ ] Compliance requirements understood
  - [ ] Legal review completed (if needed)

- [ ] **Data Privacy**
  - [ ] Customer data handled per privacy policy
  - [ ] Data retention policy defined
  - [ ] Data deletion process defined
  - [ ] GDPR compliance (if applicable)

### 13. Rollback Plan

- [ ] **Rollback Strategy**
  - [ ] Rollback plan documented
  - [ ] Rollback tested
  - [ ] Feature flags implemented (if needed)
  - [ ] Can disable Zwitch integration quickly

### 14. Support

- [ ] **Support Setup**
  - [ ] Zwitch support contact known
  - [ ] Support escalation process defined
  - [ ] Support documentation accessible
  - [ ] Support team trained

## Post-Launch Monitoring

### First 24 Hours

- [ ] Monitor payment success rate
- [ ] Monitor webhook delivery
- [ ] Monitor error rates
- [ ] Check reconciliation results
- [ ] Review logs for issues
- [ ] Customer support ready

### First Week

- [ ] Daily reconciliation review
- [ ] Error rate trending
- [ ] Performance monitoring
- [ ] Customer feedback review
- [ ] Support ticket analysis

### Ongoing

- [ ] Regular reconciliation (hourly/daily)
- [ ] Monitor metrics (success rate, error rate)
- [ ] Review and optimize
- [ ] Stay updated on Zwitch changes
- [ ] Periodic security reviews

## Common Issues to Watch

- **Webhook delivery failures:** Check endpoint availability, signature verification
- **Payment status mismatches:** Check webhook processing, reconciliation
- **Transfer failures:** Check balance, beneficiary verification
- **High error rates:** Check API configuration, error handling
- **Performance issues:** Check database queries, API rate limits

## Summary

- **Complete all checklist items** before going live
- **Test thoroughly** in sandbox first
- **Monitor closely** after launch
- **Have rollback plan** ready
- **Keep documentation updated**

**Bottom line:** Don't go live until all critical items are checked. Financial systems require careful preparation and testing.

## Related Documentation

- [Recommended DB Schema](./recommended_db_schema.md) - Database setup
- [Logging and Audits](./logging_and_audits.md) - Monitoring setup
- [Webhook Signature Verification](../risks/webhook_signature_verification.md) - Security

