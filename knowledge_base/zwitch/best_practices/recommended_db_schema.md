# Recommended Database Schema: Logical Design

## Overview

This document provides **logical database schema recommendations** for integrating with Zwitch. The schema is vendor-agnostic and can be adapted to your specific database (PostgreSQL, MySQL, MongoDB, etc.).

## Core Tables

### 1. Orders Table

**Purpose:** Store customer orders

```sql
CREATE TABLE orders (
  order_id VARCHAR(255) PRIMARY KEY,
  customer_id VARCHAR(255) NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'INR',
  status VARCHAR(50) NOT NULL,  -- pending_payment, payment_initiated, paid, fulfilled, cancelled, refunded
  
  -- Payment linkage
  payment_id VARCHAR(255),  -- Links to payments table
  
  -- Timestamps
  created_at TIMESTAMP NOT NULL,
  paid_at TIMESTAMP,
  fulfilled_at TIMESTAMP,
  cancelled_at TIMESTAMP,
  refunded_at TIMESTAMP,
  
  -- Metadata
  metadata JSONB,  -- Store order details, customer info, etc.
  
  -- Indexes
  INDEX idx_customer (customer_id),
  INDEX idx_status (status),
  INDEX idx_payment (payment_id),
  INDEX idx_created (created_at)
);
```

### 2. Payments Table

**Purpose:** Store Zwitch payment records

```sql
CREATE TABLE payments (
  payment_id VARCHAR(255) PRIMARY KEY,  -- Zwitch payment ID
  order_id VARCHAR(255) NOT NULL,
  account_id VARCHAR(255) NOT NULL,  -- Your Zwitch virtual account
  
  -- Amounts
  amount DECIMAL(10, 2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'INR',
  
  -- Status
  status VARCHAR(50) NOT NULL,  -- pending, processing, completed, failed, expired, cancelled
  
  -- Payment details
  payment_method VARCHAR(50),  -- upi, card, net_banking, etc.
  merchant_reference_id VARCHAR(255),  -- Your order ID
  
  -- Timestamps
  created_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP,
  failed_at TIMESTAMP,
  expired_at TIMESTAMP,
  cancelled_at TIMESTAMP,
  
  -- Webhook tracking
  webhook_received_at TIMESTAMP,
  last_webhook_event VARCHAR(100),
  
  -- Metadata
  metadata JSONB,
  
  -- Foreign keys
  FOREIGN KEY (order_id) REFERENCES orders(order_id),
  
  -- Indexes
  INDEX idx_order (order_id),
  INDEX idx_status (status),
  INDEX idx_merchant_ref (merchant_reference_id),
  INDEX idx_created (created_at),
  INDEX idx_account (account_id)
);
```

### 3. Transfers Table

**Purpose:** Store payout/transfer records (refunds, settlements, etc.)

```sql
CREATE TABLE transfers (
  transfer_id VARCHAR(255) PRIMARY KEY,  -- Zwitch transfer ID
  account_id VARCHAR(255) NOT NULL,
  beneficiary_id VARCHAR(255) NOT NULL,
  
  -- Amounts
  amount DECIMAL(10, 2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'INR',
  fees DECIMAL(10, 2),
  
  -- Status
  status VARCHAR(50) NOT NULL,  -- pending, processing, completed, failed, cancelled
  failure_reason VARCHAR(255),
  
  -- Transfer details
  remark VARCHAR(255),
  reference_id VARCHAR(255),  -- Your reference ID
  
  -- Timestamps
  created_at TIMESTAMP NOT NULL,
  processing_started_at TIMESTAMP,
  completed_at TIMESTAMP,
  failed_at TIMESTAMP,
  cancelled_at TIMESTAMP,
  
  -- Webhook tracking
  webhook_received_at TIMESTAMP,
  
  -- Metadata
  metadata JSONB,  -- Store transfer type (refund, settlement, etc.)
  
  -- Indexes
  INDEX idx_account (account_id),
  INDEX idx_beneficiary (beneficiary_id),
  INDEX idx_status (status),
  INDEX idx_reference (reference_id),
  INDEX idx_created (created_at)
);
```

### 4. Beneficiaries Table

**Purpose:** Store bank account beneficiaries

```sql
CREATE TABLE beneficiaries (
  beneficiary_id VARCHAR(255) PRIMARY KEY,  -- Zwitch beneficiary ID
  name VARCHAR(255) NOT NULL,
  account_number VARCHAR(50) NOT NULL,
  ifsc VARCHAR(11) NOT NULL,
  account_type VARCHAR(50),  -- savings, current, salary
  
  -- Bank details
  bank_name VARCHAR(255),
  branch VARCHAR(255),
  
  -- Contact
  email VARCHAR(255),
  phone VARCHAR(20),
  
  -- Status
  status VARCHAR(50) DEFAULT 'active',  -- active, inactive
  verification_status VARCHAR(50),  -- pending, verified, failed, not_required
  failure_reason VARCHAR(255),
  
  -- Timestamps
  created_at TIMESTAMP NOT NULL,
  verified_at TIMESTAMP,
  verification_failed_at TIMESTAMP,
  
  -- Metadata
  metadata JSONB,
  
  -- Indexes
  INDEX idx_verification (verification_status),
  INDEX idx_status (status),
  INDEX idx_account_ifsc (account_number, ifsc)
);
```

### 5. Webhook Events Table

**Purpose:** Track processed webhooks (idempotency)

```sql
CREATE TABLE webhook_events (
  idempotency_key VARCHAR(255) PRIMARY KEY,  -- payment_id:event_type or transfer_id:event_type
  payment_id VARCHAR(255),
  transfer_id VARCHAR(255),
  event_type VARCHAR(100) NOT NULL,  -- payment.completed, transfer.completed, etc.
  
  -- Payload
  payload JSONB NOT NULL,
  
  -- Processing
  processed BOOLEAN DEFAULT FALSE,
  processed_at TIMESTAMP,
  processing_error TEXT,
  
  -- Timestamps
  received_at TIMESTAMP NOT NULL,
  
  -- Indexes
  INDEX idx_payment (payment_id),
  INDEX idx_transfer (transfer_id),
  INDEX idx_event_type (event_type),
  INDEX idx_processed (processed),
  INDEX idx_received (received_at)
);
```

### 6. Refunds Table

**Purpose:** Track refunds (if using transfers for refunds)

```sql
CREATE TABLE refunds (
  refund_id VARCHAR(255) PRIMARY KEY,  -- Use transfer_id
  original_payment_id VARCHAR(255) NOT NULL,
  order_id VARCHAR(255) NOT NULL,
  transfer_id VARCHAR(255) NOT NULL,  -- Links to transfers table
  
  -- Amounts
  amount DECIMAL(10, 2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'INR',
  refund_type VARCHAR(50),  -- full, partial
  
  -- Status
  status VARCHAR(50) NOT NULL,  -- processing, completed, failed, cancelled
  failure_reason VARCHAR(255),
  refund_reason VARCHAR(255),
  
  -- Timestamps
  created_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP,
  failed_at TIMESTAMP,
  
  -- Metadata
  metadata JSONB,
  
  -- Foreign keys
  FOREIGN KEY (original_payment_id) REFERENCES payments(payment_id),
  FOREIGN KEY (order_id) REFERENCES orders(order_id),
  FOREIGN KEY (transfer_id) REFERENCES transfers(transfer_id),
  
  -- Indexes
  INDEX idx_payment (original_payment_id),
  INDEX idx_order (order_id),
  INDEX idx_status (status)
);
```

### 7. Settlements Table (for Platforms)

**Purpose:** Track settlements to sellers (marketplaces, platforms)

```sql
CREATE TABLE settlements (
  settlement_id VARCHAR(255) PRIMARY KEY,
  order_id VARCHAR(255) NOT NULL,
  payment_id VARCHAR(255) NOT NULL,
  seller_id VARCHAR(255) NOT NULL,
  transfer_id VARCHAR(255),  -- Links to transfers table
  
  -- Amounts
  order_amount DECIMAL(10, 2) NOT NULL,
  commission_rate DECIMAL(5, 4),  -- e.g., 0.1000 for 10%
  commission_amount DECIMAL(10, 2),
  platform_fee DECIMAL(10, 2),
  seller_payout DECIMAL(10, 2) NOT NULL,
  transfer_fee DECIMAL(10, 2),
  
  -- Status
  status VARCHAR(50) NOT NULL,  -- pending, processing, completed, failed, reversed
  
  -- Timestamps
  created_at TIMESTAMP NOT NULL,
  transfer_initiated_at TIMESTAMP,
  completed_at TIMESTAMP,
  failed_at TIMESTAMP,
  
  -- Metadata
  metadata JSONB,
  
  -- Foreign keys
  FOREIGN KEY (order_id) REFERENCES orders(order_id),
  FOREIGN KEY (payment_id) REFERENCES payments(payment_id),
  FOREIGN KEY (transfer_id) REFERENCES transfers(transfer_id),
  
  -- Indexes
  INDEX idx_seller (seller_id),
  INDEX idx_order (order_id),
  INDEX idx_status (status),
  INDEX idx_created (created_at)
);
```

### 8. Accounts Table

**Purpose:** Store your Zwitch virtual accounts

```sql
CREATE TABLE accounts (
  account_id VARCHAR(255) PRIMARY KEY,  -- Zwitch account ID
  account_type VARCHAR(50) DEFAULT 'virtual_account',
  name VARCHAR(255),
  status VARCHAR(50) DEFAULT 'active',  -- active, inactive, suspended
  
  -- Account details
  account_number VARCHAR(50),
  ifsc VARCHAR(11),
  upi_id VARCHAR(255),
  
  -- Balance (cached, update from API)
  balance_available DECIMAL(10, 2) DEFAULT 0,
  balance_currency VARCHAR(3) DEFAULT 'INR',
  balance_last_updated TIMESTAMP,
  
  -- Timestamps
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP,
  
  -- Metadata
  metadata JSONB,
  
  -- Indexes
  INDEX idx_status (status),
  INDEX idx_type (account_type)
);
```

## Relationships

```
orders (1) ──< (many) payments
payments (1) ──< (many) refunds (via transfers)
orders (1) ──< (many) settlements (for platforms)
settlements (1) ──> (1) transfers
refunds (1) ──> (1) transfers
transfers (many) ──> (1) beneficiaries
transfers (many) ──> (1) accounts
payments (many) ──> (1) accounts
```

## Indexing Strategy

**Index on:**
- Foreign keys (for joins)
- Status fields (for filtering)
- Timestamps (for date range queries)
- Reference IDs (for lookups)
- Composite indexes for common queries

## Data Types

**Use appropriate types:**
- `DECIMAL(10, 2)` for money (precision important)
- `VARCHAR(255)` for IDs and strings
- `TIMESTAMP` for dates/times
- `JSONB` for metadata (PostgreSQL) or `JSON` (MySQL 5.7+)
- `BOOLEAN` for flags

## Constraints

**Add constraints:**
- Primary keys (unique identifiers)
- Foreign keys (referential integrity)
- NOT NULL (required fields)
- CHECK constraints (status values, amounts > 0)
- UNIQUE constraints (idempotency keys)

## Best Practices

### ✅ Do:
1. **Use transactions** for related operations
2. **Add indexes** on frequently queried fields
3. **Use appropriate data types** (DECIMAL for money)
4. **Add constraints** (foreign keys, NOT NULL)
5. **Store metadata** in JSONB/JSON (flexible)
6. **Track timestamps** (audit trail)
7. **Normalize** where appropriate (beneficiaries, accounts)

### ❌ Don't:
1. **Don't store secrets** in database (use environment variables)
2. **Don't skip indexes** (performance impact)
3. **Don't use FLOAT** for money (precision issues)
4. **Don't skip constraints** (data integrity)
5. **Don't over-normalize** (balance performance vs complexity)

## Migration Strategy

**When implementing:**
1. Start with core tables (orders, payments)
2. Add related tables as needed (refunds, settlements)
3. Add indexes after data load
4. Add constraints carefully (may fail on existing data)
5. Test with sample data first

## Summary

- **Core tables:** orders, payments, transfers, beneficiaries
- **Optional tables:** refunds, settlements, accounts, webhook_events
- **Use appropriate types:** DECIMAL for money, TIMESTAMP for dates
- **Add indexes:** Foreign keys, status, timestamps
- **Add constraints:** Primary keys, foreign keys, NOT NULL
- **Store metadata:** JSONB/JSON for flexibility

This schema provides a solid foundation for Zwitch integration. Adapt to your specific needs and database system.

## Related Documentation

- [Payin Happy Path](../flows/payin_happy_path.md) - Using these tables
- [Settlement Flow](../flows/settlement_flow.md) - Settlements table usage
- [Refund Flow](../flows/refund_flow.md) - Refunds table usage

