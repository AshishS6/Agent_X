# Logging and Audits: Maintaining Records

## Overview

**Comprehensive logging and audit trails are essential** for fintech systems. This document outlines what to log, how to log, and how to maintain audit records.

## What to Log

### 1. API Calls

**Log all Zwitch API calls:**

```python
def log_api_call(endpoint, method, request_data, response_data, status_code, duration):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'type': 'api_call',
        'endpoint': endpoint,
        'method': method,
        'request_data': sanitize_data(request_data),  # Remove secrets
        'response_status': status_code,
        'response_data': sanitize_data(response_data),
        'duration_ms': duration,
        'success': status_code < 400
    }
    logger.info(json.dumps(log_entry))
```

**What to include:**
- Endpoint called
- HTTP method
- Request data (sanitized - no secrets)
- Response status
- Response data (sanitized)
- Duration
- Timestamp

**What NOT to log:**
- Secret keys
- Full payment card numbers (if any)
- Complete request/response bodies (may contain sensitive data)

### 2. Webhook Events

**Log all webhook events:**

```python
def log_webhook_event(event_type, payload, signature, verified, processed):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'type': 'webhook',
        'event_type': event_type,
        'payment_id': payload.get('data', {}).get('id'),
        'signature_verified': verified,
        'processed': processed,
        'payload_hash': hashlib.sha256(json.dumps(payload).encode()).hexdigest()  # Hash, not full payload
    }
    logger.info(json.dumps(log_entry))
```

**What to include:**
- Event type
- Payment/transfer ID
- Signature verification status
- Processing status
- Payload hash (for verification, not full payload)
- Timestamp

### 3. Payment Status Changes

**Log all payment status changes:**

```python
def log_payment_status_change(payment_id, old_status, new_status, source, metadata):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'type': 'payment_status_change',
        'payment_id': payment_id,
        'old_status': old_status,
        'new_status': new_status,
        'source': source,  # 'webhook', 'reconciliation', 'api', 'manual'
        'metadata': metadata
    }
    logger.info(json.dumps(log_entry))
```

**What to include:**
- Payment ID
- Old status
- New status
- Source of change (webhook, reconciliation, etc.)
- Timestamp
- Any relevant metadata

### 4. Transfer Status Changes

**Log all transfer status changes:**

```python
def log_transfer_status_change(transfer_id, old_status, new_status, source, metadata):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'type': 'transfer_status_change',
        'transfer_id': transfer_id,
        'old_status': old_status,
        'new_status': new_status,
        'source': source,
        'metadata': metadata
    }
    logger.info(json.dumps(log_entry))
```

### 5. Business Logic Events

**Log important business events:**

```python
def log_business_event(event_type, order_id, payment_id, details):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'type': 'business_event',
        'event_type': event_type,  # 'order_fulfilled', 'refund_issued', etc.
        'order_id': order_id,
        'payment_id': payment_id,
        'details': details
    }
    logger.info(json.dumps(log_entry))
```

**Examples:**
- Order marked as paid
- Order fulfilled
- Refund issued
- Settlement processed
- Reconciliation discrepancies

### 6. Errors and Failures

**Log all errors with context:**

```python
def log_error(error_type, error_message, context, stack_trace=None):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'type': 'error',
        'error_type': error_type,
        'error_message': error_message,
        'context': context,  # Payment ID, order ID, etc.
        'stack_trace': stack_trace  # For debugging
    }
    logger.error(json.dumps(log_entry))
```

**What to include:**
- Error type
- Error message
- Context (payment ID, order ID, etc.)
- Stack trace (for debugging)
- Timestamp

### 7. Security Events

**Log security-related events:**

```python
def log_security_event(event_type, details):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'type': 'security_event',
        'event_type': event_type,  # 'webhook_signature_failed', 'unauthorized_access', etc.
        'details': details
    }
    logger.warning(json.dumps(log_entry))  # Use warning level for security events
```

**Examples:**
- Webhook signature verification failures
- Unauthorized API access attempts
- Suspicious activity patterns
- Failed authentication attempts

## Logging Best Practices

### ✅ Do:

1. **Log at appropriate levels**
   - INFO: Normal operations
   - WARNING: Issues that need attention
   - ERROR: Errors that need investigation
   - CRITICAL: System failures

2. **Use structured logging**
   - JSON format (easy to parse)
   - Consistent fields
   - Machine-readable

3. **Include context**
   - Payment ID, order ID, user ID
   - Request IDs for tracing
   - Timestamps (UTC)

4. **Sanitize sensitive data**
   - Remove secret keys
   - Hash sensitive fields
   - Don't log full payment details

5. **Log asynchronously**
   - Don't block main operations
   - Use background workers
   - Batch logs if needed

6. **Retain logs appropriately**
   - Financial logs: 5-7 years (check regulations)
   - General logs: 30-90 days
   - Security logs: Longer retention

### ❌ Don't:

1. **Don't log secrets**
   - API keys, secret keys
   - Passwords, tokens
   - Full payment card numbers

2. **Don't log excessively**
   - Avoid logging in tight loops
   - Don't log every database query
   - Focus on important events

3. **Don't log PII unnecessarily**
   - Customer names, emails (if not needed)
   - Full addresses
   - Phone numbers (unless required)

4. **Don't block on logging**
   - Use async logging
   - Don't let logging slow down operations
   - Handle logging failures gracefully

## Audit Trail Requirements

### Financial Transactions

**Must log:**
- All payment creations
- All payment status changes
- All transfer creations
- All transfer status changes
- All refunds
- All settlements

**Retention:** 5-7 years (check local regulations)

### Security Events

**Must log:**
- Authentication attempts
- Authorization failures
- Webhook signature failures
- Unusual access patterns

**Retention:** 1-2 years (or per policy)

### Business Events

**Must log:**
- Order status changes
- Fulfillment events
- Customer actions
- Admin actions

**Retention:** 1-2 years (or per policy)

## Database Audit Tables

**Create audit tables for critical operations:**

```sql
-- Payment audit trail
CREATE TABLE payment_audit (
  audit_id BIGSERIAL PRIMARY KEY,
  payment_id VARCHAR(255) NOT NULL,
  action VARCHAR(50) NOT NULL,  -- 'created', 'status_changed', 'processed'
  old_value JSONB,
  new_value JSONB,
  changed_by VARCHAR(255),  -- 'system', 'user_id', 'webhook', etc.
  changed_at TIMESTAMP NOT NULL,
  metadata JSONB,
  INDEX idx_payment (payment_id),
  INDEX idx_changed_at (changed_at)
);

-- Transfer audit trail
CREATE TABLE transfer_audit (
  audit_id BIGSERIAL PRIMARY KEY,
  transfer_id VARCHAR(255) NOT NULL,
  action VARCHAR(50) NOT NULL,
  old_value JSONB,
  new_value JSONB,
  changed_by VARCHAR(255),
  changed_at TIMESTAMP NOT NULL,
  metadata JSONB,
  INDEX idx_transfer (transfer_id),
  INDEX idx_changed_at (changed_at)
);
```

## Log Storage

### Options:

1. **File-based logging**
   - Simple, local storage
   - Good for small scale
   - Requires log rotation

2. **Centralized logging**
   - ELK stack (Elasticsearch, Logstash, Kibana)
   - Cloud logging (AWS CloudWatch, Google Cloud Logging)
   - Better for distributed systems

3. **Database logging**
   - Store logs in database
   - Easy to query
   - May impact performance

### Recommendations:

- **Development:** File-based or database
- **Production:** Centralized logging service
- **Compliance:** Ensure logs are tamper-proof

## Log Analysis

### Key Metrics to Track:

1. **Payment success rate**
   - Successful payments / Total payments
   - Track over time

2. **Webhook delivery rate**
   - Delivered webhooks / Sent webhooks
   - Identify delivery issues

3. **Error rate**
   - Errors / Total operations
   - Alert on high error rates

4. **Processing time**
   - Average API call duration
   - Average webhook processing time
   - Identify performance issues

### Queries:

```sql
-- Payment success rate (last 24 hours)
SELECT 
  COUNT(*) FILTER (WHERE status = 'completed') * 100.0 / COUNT(*) as success_rate
FROM payments
WHERE created_at > NOW() - INTERVAL '24 hours';

-- Webhook delivery rate
SELECT 
  COUNT(*) FILTER (WHERE processed = true) * 100.0 / COUNT(*) as delivery_rate
FROM webhook_events
WHERE received_at > NOW() - INTERVAL '24 hours';

-- Error rate
SELECT 
  COUNT(*) FILTER (WHERE level = 'ERROR') * 100.0 / COUNT(*) as error_rate
FROM logs
WHERE timestamp > NOW() - INTERVAL '24 hours';
```

## Compliance Considerations

### Regulatory Requirements:

- **Financial records:** 5-7 years retention (check local regulations)
- **Audit trail:** Immutable, tamper-proof
- **Access controls:** Limit who can view/modify logs
- **Data privacy:** Don't log unnecessary PII

### Best Practices:

- Encrypt logs at rest
- Control access to logs
- Regular log reviews
- Compliance audits

## Summary

- **Log all important events:** API calls, webhooks, status changes, errors
- **Use structured logging:** JSON format, consistent fields
- **Sanitize sensitive data:** Remove secrets, hash sensitive fields
- **Maintain audit trails:** Financial transactions, security events
- **Retain appropriately:** 5-7 years for financial, 1-2 years for others
- **Monitor and analyze:** Track metrics, identify issues

**Bottom line:** Comprehensive logging is essential for debugging, compliance, and security. Log everything important, but do it securely and efficiently.

## Related Documentation

- [Recommended DB Schema](./recommended_db_schema.md) - Audit table schemas
- [Production Checklist](./production_checklist.md) - Logging requirements
- [Reconciliation Failures](../risks/reconciliation_failures.md) - Using logs for reconciliation

