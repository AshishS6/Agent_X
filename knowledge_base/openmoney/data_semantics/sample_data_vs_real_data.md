# Sample Data vs Real Data

## Critical Distinction

**Sample data must never be treated as real business data. Sample data exists only for demonstration and testing purposes.**

## What Is Sample Data

Sample data is:
- Pre-populated demonstration data
- Not real business transactions
- Not real money
- Not real customers or vendors
- Not real bank accounts
- Not real compliance data

## What Is Real Data

Real data is:
- Actual business transactions
- Real money movement
- Real customers and vendors
- Real bank accounts
- Real compliance records
- Data that affects real business

## Sample Data Mode

When sample data mode is enabled:
- All data shown is sample data
- No real transactions are displayed
- No real money is involved
- No real compliance is tracked
- No real reconciliation is possible

**Sample data mode must be clearly indicated to users.**

## Why Sample Data Exists

Sample data exists for:
- Product demonstration
- User onboarding
- Testing and training
- Feature exploration
- UI/UX validation

**Sample data does NOT exist for:**
- Real business operations
- Financial decisions
- Compliance reporting
- Audit purposes
- Legal documentation

## Critical Rules

### ✅ Must Do:

1. **Clearly indicate sample data** — Users must know when data is sample
2. **Isolate sample data** — Sample data must not mix with real data
3. **Prevent sample data usage** — Sample data must not be used for real operations
4. **Warn users** — Users must be warned about sample data

### ❌ Must NOT Do:

1. **Don't treat sample data as real** — Sample data is not real
2. **Don't use sample data for decisions** — Sample data cannot inform real decisions
3. **Don't reconcile sample data** — Sample data cannot be reconciled
4. **Don't report sample data** — Sample data cannot be used for reporting
5. **Don't assume sample data accuracy** — Sample data may not be accurate

## Common Misinterpretations

### Misinterpretation 1: Sample Data = Real Data

**Wrong:** "I see ₹X in my account, so I have ₹X."

**Correct:** "If sample data mode is enabled, all data is sample. Real data is only shown when sample data mode is disabled."

### Misinterpretation 2: Sample Transactions = Real Transactions

**Wrong:** "I see transactions, so these are my real transactions."

**Correct:** "If sample data mode is enabled, all transactions are sample. Real transactions are only shown when sample data mode is disabled."

### Misinterpretation 3: Sample Compliance = Real Compliance

**Wrong:** "I see IRN, so my invoice is compliant."

**Correct:** "If sample data mode is enabled, all compliance data is sample. Real compliance is only tracked when sample data mode is disabled."

## How to Identify Sample Data

Sample data is typically:
- Clearly labeled as "Sample" or "Demo"
- Shown with sample data mode indicator
- Isolated from real data
- Not reconcilable
- Not usable for real operations

**If you're unsure whether data is sample or real, assume it's sample until verified.**

## Switching Between Sample and Real Data

When switching from sample to real data:
- All sample data is hidden
- Only real data is shown
- Real data may be empty initially
- Real operations can begin

When switching from real to sample data:
- All real data is hidden
- Only sample data is shown
- Real operations are paused
- Sample data is displayed

**Switching modes does not affect real data. Real data remains intact.**

## Data Isolation

Sample data and real data must be:
- Stored separately
- Displayed separately
- Processed separately
- Never mixed

**Mixing sample and real data can cause serious financial errors.**

## Related Documentation

- [Derived vs Actual Balances](./derived_vs_actual_balances.md) — Balance interpretation
- [Dashboard Misinterpretation](../risks/dashboard_misinterpretation.md) — Dashboard risks
- [Data Ownership and Limitations](../concepts/data_ownership_and_limitations.md) — Data boundaries

