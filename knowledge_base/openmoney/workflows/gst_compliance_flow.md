# GST Compliance Flow

## Overview

This document describes the **complete system-level flow** for GST compliance operations in Open Money. This covers e-Invoice generation, IRN (Invoice Reference Number) creation, and e-Way Bill generation.

## Flow Diagram

```
Document Creation → GST Validation → IRP Submission → IRN Generation → e-Way Bill (if applicable) → Compliance Confirmation
```

## Step-by-Step Flow

### Step 1: Document Creation

**What happens:**
- Invoice or bill is created in Open Money
- Document details are stored
- GST details are included

**GST details:**
- GSTIN (GST Identification Number)
- Tax rates
- Tax amounts
- HSN/SAC codes

**What you do:**
- Create document with GST details
- Verify GST information
- Prepare for IRP submission

**What to store:**
- Document ID
- GST details
- Document status
- GST compliance status

---

### Step 2: GST Validation

**What happens:**
- GST details are validated
- Document is checked for compliance
- Validation errors are identified

**Validation checks:**
- GSTIN format
- Tax rate accuracy
- Tax amount calculation
- HSN/SAC code validity

**What you do:**
- Validate GST details
- Fix validation errors
- Verify compliance

**What to store:**
- Validation status
- Validation errors (if any)
- Validation timestamp

---

### Step 3: IRP Submission

**What happens:**
- Document is submitted to IRP (Invoice Registration Portal)
- IRP validates document
- IRP processes submission

**IRP submission:**
- Document is sent to government IRP
- IRP validates GST details
- IRP processes invoice

**What you do:**
- Submit document to IRP
- Monitor submission status
- Wait for IRP response

**What to store:**
- IRP submission status
- IRP transaction ID
- Submission timestamp

---

### Step 4: IRN Generation

**What happens:**
- IRP generates IRN (Invoice Reference Number)
- IRN is unique identifier
- IRN is linked to document

**IRN generation:**
- IRP creates unique IRN
- IRN is returned to Open Money
- IRN is stored with document

**What you do:**
- Receive IRN from IRP
- Store IRN with document
- Update document status

**What to store:**
- IRN
- IRN generation timestamp
- IRP confirmation
- Document status: `irn_generated`

---

### Step 5: e-Way Bill Generation (If Applicable)

**What happens:**
- e-Way Bill is generated if required
- e-Way Bill is linked to document
- e-Way Bill details are stored

**e-Way Bill requirements:**
- Required for goods movement
- Required for certain transaction values
- Required for certain distances

**What you do:**
- Generate e-Way Bill if required
- Store e-Way Bill details
- Update document status

**What to store:**
- e-Way Bill number
- e-Way Bill generation timestamp
- e-Way Bill details
- Document status: `eway_bill_generated`

---

### Step 6: Compliance Confirmation

**What happens:**
- GST compliance is confirmed
- All requirements are met
- Document is compliant

**Compliance confirmation:**
- IRN is generated
- e-Way Bill is generated (if required)
- All GST requirements are met
- Document is compliant

**What you do:**
- Confirm compliance
- Update document status
- Store compliance records

**What to store:**
- Compliance status: `compliant`
- Compliance confirmation timestamp
- Compliance records

---

## GST Compliance States

### `non_compliant`

**Meaning:** Document is not GST compliant.

**What it means:**
- GST details are missing or invalid
- IRN is not generated
- Compliance requirements are not met

### `pending_irn`

**Meaning:** IRN generation is pending.

**What it means:**
- Document is submitted to IRP
- IRN generation is in progress
- Compliance is not yet confirmed

### `irn_generated`

**Meaning:** IRN is generated.

**What it means:**
- IRN is created by IRP
- Document has IRN
- Basic compliance is met

### `eway_bill_pending`

**Meaning:** e-Way Bill generation is pending.

**What it means:**
- IRN is generated
- e-Way Bill is required
- e-Way Bill generation is pending

### `compliant`

**Meaning:** Document is fully GST compliant.

**What it means:**
- IRN is generated
- e-Way Bill is generated (if required)
- All compliance requirements are met

## Critical Checkpoints

### ✅ Must Do:

1. **Validate GST details** — Ensure all GST information is correct
2. **Submit to IRP** — Submit document to IRP for IRN generation
3. **Store IRN** — Store IRN with document
4. **Generate e-Way Bill** — Generate e-Way Bill if required
5. **Confirm compliance** — Verify all requirements are met

### ❌ Must NOT Do:

1. **Don't skip GST validation** — Validation is required
2. **Don't skip IRP submission** — IRN is mandatory for compliance
3. **Don't assume compliance** — Verify all requirements are met
4. **Don't ignore e-Way Bill** — Generate if required
5. **Don't trust dashboard alone** — Verify against IRP

## Common Failure Points

### Failure Point 1: GST Validation Failure

**What happens:**
- GST details are invalid
- Validation fails
- Document cannot be submitted to IRP

**What to do:**
- Review GST details
- Fix validation errors
- Resubmit for validation
- Verify compliance

### Failure Point 2: IRP Submission Failure

**What happens:**
- IRP rejects submission
- IRN generation fails
- Document is not compliant

**What to do:**
- Investigate rejection reason
- Fix document details
- Resubmit to IRP
- Verify IRN generation

### Failure Point 3: e-Way Bill Generation Failure

**What happens:**
- e-Way Bill generation fails
- e-Way Bill is required
- Document is not fully compliant

**What to do:**
- Investigate failure reason
- Fix e-Way Bill details
- Regenerate e-Way Bill
- Verify compliance

## GST Authority

**GST compliance data is owned by:**
- Government (IRP) — IRN generation
- Government (e-Way Bill portal) — e-Way Bill generation
- Tax authorities — Compliance verification

**Open Money does NOT own GST compliance data. It facilitates compliance but does not guarantee it.**

## Reconciliation with GST

GST compliance must be reconciled with:
- Document details
- Payment records
- Bank entries
- Tax filings

**GST compliance does not replace reconciliation. Both are required.**

## Related Documentation

- [Compliance Module](../modules/compliance.md) — Compliance module
- [GST Compliance Risks](../risks/gst_compliance_risks.md) — Compliance risks
- [Reconciliation Flow](./reconciliation_flow.md) — Reconciliation process

