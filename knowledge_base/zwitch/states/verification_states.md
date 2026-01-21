# Verification States: Account and Beneficiary Verification

## Overview

This document defines the **verification states** for beneficiaries and accounts in Zwitch. Verification ensures that bank accounts and other details are valid before processing transfers.

## Beneficiary Verification States

### 1. `pending`
**Meaning:** Beneficiary created, verification not yet started or in progress.

**When it occurs:**
- Immediately after creating beneficiary via API
- Verification process hasn't completed yet

**What it means:**
- Beneficiary exists in system
- Verification status is unknown
- May or may not be valid

**Can transition to:**
- `verified` (verification successful)
- `failed` (verification failed)
- `not_required` (verification not needed)

**Is reversible:** Yes (can be re-verified)

**What to do:**
- Store beneficiary
- Wait for verification result
- Don't use for transfers until verified (if verification required)

---

### 2. `verified`
**Meaning:** Beneficiary verified successfully, account is valid.

**When it occurs:**
- Zwitch successfully verified bank account details
- Account number, IFSC, name match bank records
- Account is active and valid

**What it means:**
- Beneficiary is valid
- Safe to use for transfers
- This is a **terminal state** (unless re-verification needed)

**Can transition to:**
- `pending` (if re-verification triggered)
- Usually stays `verified`

**Is reversible:** Yes (can be re-verified if needed)

**What to do:**
- Mark beneficiary as verified
- Allow transfers to this beneficiary
- Store verification timestamp

---

### 3. `failed`
**Meaning:** Verification failed, account details are invalid.

**When it occurs:**
- Account number doesn't exist
- IFSC code is invalid
- Name doesn't match bank records
- Account is closed/frozen

**What it means:**
- Beneficiary details are incorrect
- Not safe to use for transfers
- Needs correction

**Can transition to:**
- `pending` (after updating details and re-verifying)
- `verified` (after fixing details and successful re-verification)

**Is reversible:** Yes (fix details and re-verify)

**What to do:**
- Mark beneficiary as failed
- Don't allow transfers to this beneficiary
- Notify user to update details
- Provide failure reason if available

**Common failure reasons:**
- `invalid_account_number`: Account doesn't exist
- `invalid_ifsc`: IFSC code is wrong
- `name_mismatch`: Name doesn't match bank records
- `account_closed`: Account is closed
- `account_frozen`: Account is frozen

---

### 4. `not_required`
**Meaning:** Verification is not required for this beneficiary.

**When it occurs:**
- Beneficiary type doesn't require verification
- Verification is optional and skipped
- System configuration allows unverified beneficiaries

**What it means:**
- Beneficiary can be used without verification
- May still be validated at transfer time

**Can transition to:**
- Usually stays `not_required`
- Can be verified if needed (→ `pending` → `verified`)

**Is reversible:** N/A (not required)

**What to do:**
- Allow transfers (if policy permits)
- May still validate at transfer time

---

## Verification State Diagram

```
                    ┌─────────┐
                    │ pending │
                    └────┬────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                 │
        ▼                ▼                 ▼
   ┌──────────┐     ┌──────────┐     ┌──────────┐
   │verified  │     │ failed   │     │not_required│
   └──────────┘     └────┬─────┘     └──────────┘
                         │
                         │ (after fixing details)
                         ▼
                    ┌─────────┐
                    │ pending │ (re-verification)
                    └─────────┘
```

## When Verification is Required

**Typically required for:**
- Bank account beneficiaries (for transfers)
- High-value transfers
- First transfer to a beneficiary
- Regulatory compliance

**May not be required for:**
- Low-value transfers (depending on policy)
- UPI-only beneficiaries
- Internal accounts

**Check Zwitch documentation** for current verification requirements.

## Verification Process

### Automatic Verification:
- Zwitch may automatically verify beneficiaries after creation
- Verification happens asynchronously
- Webhook sent when verification completes

### Manual Verification:
- You can trigger verification via API (if supported)
- Useful for re-verification after updating details

### Verification Time:
- Usually takes seconds to minutes
- May take longer for some banks
- Check verification status via API

## Webhook Events

Verification state changes trigger webhooks:

| State | Webhook Event |
|-------|---------------|
| `pending` | `beneficiary.created` |
| `verified` | `beneficiary.verified` |
| `failed` | `beneficiary.verification_failed` |

## Database Representation

```sql
CREATE TABLE beneficiaries (
  beneficiary_id VARCHAR(255) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  account_number VARCHAR(50) NOT NULL,
  ifsc VARCHAR(11) NOT NULL,
  verification_status VARCHAR(50) NOT NULL,  -- pending, verified, failed, not_required
  failure_reason VARCHAR(255),
  
  created_at TIMESTAMP,
  verified_at TIMESTAMP,     -- Only set when verification_status = 'verified'
  verification_failed_at TIMESTAMP,  -- Only set when verification_status = 'failed'
  
  -- Add constraint
  CHECK (
    (verification_status = 'verified' AND verified_at IS NOT NULL) OR
    (verification_status = 'failed' AND verification_failed_at IS NOT NULL) OR
    (verification_status IN ('pending', 'not_required'))
  )
);
```

## Using Verified Beneficiaries

### ✅ Safe to Use:
- Beneficiaries with `verification_status = 'verified'`
- Beneficiaries with `verification_status = 'not_required'` (if policy allows)

### ❌ Not Safe to Use:
- Beneficiaries with `verification_status = 'failed'`
- Beneficiaries with `verification_status = 'pending'` (if verification required)

### Best Practice:
```python
# Check verification before transfer
if beneficiary.verification_status == 'verified':
    create_transfer(beneficiary_id)
elif beneficiary.verification_status == 'not_required':
    create_transfer(beneficiary_id)  # If policy allows
else:
    raise Error("Beneficiary not verified")
```

## Handling Verification Failures

### When Verification Fails:

1. **Notify user:**
   - Show verification failure message
   - Provide failure reason (if available)
   - Guide user to update details

2. **Update beneficiary:**
   - Allow user to update account details
   - Trigger re-verification after update

3. **Don't allow transfers:**
   - Block transfers to unverified beneficiaries
   - Prevent failed transfers

### Re-verification:

1. **Update beneficiary details:**
   ```python
   # Update beneficiary
   update_beneficiary(beneficiary_id, {
     'account_number': 'correct_account_number',
     'ifsc': 'correct_ifsc'
   })
   ```

2. **Trigger re-verification:**
   - Verification may happen automatically
   - Or trigger via API (if supported)

3. **Wait for result:**
   - Monitor verification status
   - Handle webhook when verification completes

## Account Verification

**Account verification** may also apply to:
- Virtual accounts (your accounts)
- Connected banking accounts
- Other account types

**States are similar:**
- `pending`: Verification in progress
- `verified`: Account verified
- `failed`: Verification failed

**Check Zwitch documentation** for account-specific verification requirements.

## Best Practices

### ✅ Do:
1. **Verify before first transfer** (if required)
2. **Store verification status** in database
3. **Check verification status** before transfers
4. **Handle verification failures** gracefully
5. **Re-verify periodically** (compliance)
6. **Notify users** of verification status

### ❌ Don't:
1. **Don't skip verification** if required
2. **Don't allow transfers** to unverified beneficiaries (if policy requires verification)
3. **Don't ignore verification failures**
4. **Don't assume verification is instant**

## Summary

- **4 verification states:** pending, verified, failed, not_required
- **Verification ensures** account details are valid
- **Only use verified beneficiaries** for transfers (if required)
- **Handle failures** by updating details and re-verifying
- **Monitor verification status** via webhooks or API

Proper verification prevents failed transfers and ensures compliance.

## Related Documentation

- [Beneficiaries API](../api/06_beneficiaries.md) - Creating and managing beneficiaries
- [Transfers API](../api/07_transfers.md) - Using beneficiaries for transfers
- [Verification API](../api/08_verification.md) - Verification APIs

