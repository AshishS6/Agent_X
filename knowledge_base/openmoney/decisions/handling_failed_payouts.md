# Handling Failed Payouts: What to Do

## Recommendation

**When a payout fails, investigate the failure reason, verify account balance and beneficiary details, and retry if appropriate. Always update records and notify relevant parties.**

This is not just a suggestion—it's a best practice for managing payout failures effectively.

## What to Do When Payout Fails

### Step 1: Investigate Failure Reason

**What to do:**
- Check payout failure reason
- Understand why payout failed
- Review error message
- Identify root cause

**Failure reasons may include:**
- Insufficient funds
- Invalid beneficiary details
- Bank rejection
- Network/system error
- Payment rail issue

**What to store:**
- Failure reason
- Error message
- Failure timestamp
- Investigation notes

### Step 2: Verify Account Balance

**What to do:**
- Check account balance
- Verify sufficient funds available
- Check for pending transactions
- Verify balance accuracy

**What to verify:**
- Current account balance
- Required payout amount
- Available balance
- Pending transactions

**What to store:**
- Account balance at failure time
- Balance verification timestamp
- Balance verification result

### Step 3: Verify Beneficiary Details

**What to do:**
- Check beneficiary account number
- Verify beneficiary IFSC/bank code
- Confirm beneficiary name
- Verify beneficiary details are correct

**What to verify:**
- Beneficiary account number
- Beneficiary IFSC/bank code
- Beneficiary name
- Beneficiary bank

**What to store:**
- Beneficiary verification result
- Verification timestamp
- Any corrections needed

### Step 4: Retry if Appropriate

**What to do:**
- Determine if retry is appropriate
- Fix issues if needed
- Create new payout if retry is appropriate
- Monitor retry status

**When to retry:**
- Temporary network/system error
- Insufficient funds (after adding funds)
- Beneficiary details corrected
- Payment rail issue resolved

**When NOT to retry:**
- Invalid beneficiary details (fix first)
- Permanent bank rejection
- Account closure
- Invalid payout amount

**What to store:**
- Retry decision
- Retry timestamp
- New payout ID (if created)
- Retry status

### Step 5: Update Records

**What to do:**
- Update payout status to failed
- Update bill status (if linked)
- Update vendor records
- Document failure and resolution

**What to store:**
- Payout status: `failed`
- Failure reason
- Resolution action
- Update timestamp

### Step 6: Notify Relevant Parties

**What to do:**
- Notify vendor (if applicable)
- Notify internal team
- Update stakeholders
- Document notifications

**What to notify:**
- Failure reason
- Resolution plan
- Expected timeline
- Next steps

## What NOT to Do

### ❌ Don't Ignore Failures

**Wrong:** "Payout failed, I'll deal with it later."

**Correct:** "Investigate failure immediately. Don't ignore payout failures."

### ❌ Don't Retry Without Investigation

**Wrong:** "I'll just retry the payout."

**Correct:** "Investigate failure reason first. Retry only if appropriate."

### ❌ Don't Skip Verification

**Wrong:** "Failure reason is clear, no need to verify."

**Correct:** "Always verify account balance and beneficiary details. Don't skip verification."

### ❌ Don't Update Records Incorrectly

**Wrong:** "I'll mark payout as completed even though it failed."

**Correct:** "Update records accurately. Mark payout as failed, not completed."

## Failure Handling Process

### Immediate Actions

1. **Investigate failure** — Check failure reason
2. **Verify details** — Check account balance and beneficiary
3. **Document failure** — Record failure details
4. **Notify parties** — Inform relevant parties

### Resolution Actions

1. **Fix issues** — Resolve identified problems
2. **Retry if appropriate** — Create new payout if retry is appropriate
3. **Update records** — Update all related records
4. **Monitor retry** — Track retry status

### Follow-up Actions

1. **Verify retry success** — Confirm retry completed successfully
2. **Reconcile payout** — Reconcile successful payout
3. **Update final status** — Mark records as final
4. **Document resolution** — Record resolution details

## Common Failure Scenarios

### Scenario 1: Insufficient Funds

**What happens:** Account balance is less than payout amount.

**What to do:**
- Verify account balance
- Add funds if needed
- Retry payout after funds are available
- Update records

### Scenario 2: Invalid Beneficiary

**What happens:** Beneficiary details are incorrect.

**What to do:**
- Verify beneficiary details
- Correct beneficiary information
- Create new payout with correct details
- Update records

### Scenario 3: Bank Rejection

**What happens:** Bank rejects payout.

**What to do:**
- Investigate rejection reason
- Verify beneficiary details
- Contact bank if needed
- Retry or create new payout

### Scenario 4: Network/System Error

**What happens:** Temporary network or system error.

**What to do:**
- Wait for error resolution
- Retry payout
- Monitor retry status
- Update records

## Retry Strategy

### When to Retry

- Temporary errors
- Network/system issues
- Resolved insufficient funds
- Corrected beneficiary details

### When NOT to Retry

- Permanent bank rejection
- Invalid beneficiary (fix first)
- Account closure
- Invalid payout amount

### How to Retry

1. **Fix issues** — Resolve identified problems
2. **Create new payout** — Don't reuse failed payout
3. **Monitor status** — Track new payout status
4. **Reconcile when successful** — Reconcile successful payout

## Summary

- **Investigate immediately** — Don't ignore failures
- **Verify details** — Check account balance and beneficiary
- **Retry if appropriate** — Only retry after fixing issues
- **Update records** — Mark payout as failed, update all records
- **Notify parties** — Inform relevant parties
- **Monitor retry** — Track retry status and reconcile when successful

**Bottom line:** Handle failures systematically. Investigate, verify, fix, retry, and update. Don't ignore or skip steps.

## Related Documentation

- [Payout State Lifecycle](../states/payout_state_lifecycle.md) — Payout states
- [Bill to Payout Workflow](../workflows/bill_to_payout.md) — Payout flow
- [Reconciliation Flow](../workflows/reconciliation_flow.md) — Reconciliation process
- [Financial Finality Rules](../principles/financial_finality_rules.md) — When money is final

