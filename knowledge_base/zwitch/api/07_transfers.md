# Zwitch API — Transfers

Transfers allow you to send funds from a virtual account to bank accounts via beneficiaries. You must create a beneficiary before initiating a transfer.

## Transfer Funds
**POST** `/v1/transfers`

### What this API does

Transfers funds from your Zwitch virtual account to a beneficiary's bank account. This is used for payouts, refunds, settlements, and any money movement out of your account.

### When to use this API

- ✅ You need to send money to a bank account (payouts, refunds, settlements)
- ✅ Beneficiary is already created and verified (if verification required)
- ✅ You have sufficient balance in your virtual account
- ✅ You're processing refunds to customers
- ✅ You're settling payments to sellers (marketplaces)
- ✅ You're paying salaries, vendors, or suppliers

### When NOT to use this API

- ❌ Beneficiary doesn't exist → Create beneficiary first using `/v1/beneficiaries/bank-account`
- ❌ Beneficiary not verified → Verify beneficiary first (if verification required)
- ❌ Insufficient balance → Check account balance and add funds first
- ❌ You're collecting money (payin) → Use Payments API instead
- ❌ You're testing without real account → Use sandbox environment
- ❌ You need to transfer to UPI ID only → Check if beneficiary supports UPI or use appropriate method

### Required inputs

- `debit_account_id` (required): Your Zwitch virtual account ID from which money will be debited (format: `va_...`)
- `beneficiary_id` (required): Beneficiary ID to which money will be transferred (must be created first via `/v1/accounts/{account_id}/beneficiaries`, format: `vab_...`)
- `amount` (required): Transfer amount in Indian Rupees (minimum: ₹1.00)
- `payment_remark` (optional): Payment remark shown in bank statement (max: 40 characters, only alphabets, numbers, and spaces)
- `merchant_reference_id` (optional): Your unique reference ID for tracking (min: 7, max: 40 characters, only alphabets and numbers)
- `metadata` (optional): Custom metadata key-value pairs (max 5 pairs, each value max 256 characters)

### Common mistakes

1. **Transferring without beneficiary** - Always create beneficiary first using `/v1/accounts/{account_id}/beneficiaries`
2. **Not checking balance** - Verify sufficient balance in virtual account before transferring
3. **Not verifying beneficiary** - Check beneficiary verification status (if required)
4. **Using wrong field names** - Use `debit_account_id` (not `account_id`), `payment_remark` (not `remark`), `merchant_reference_id` (not `reference_id`)
5. **Marking as completed on `pending`** - Only mark as completed when status is `success` (see [Transfer Status Lifecycle](../states/transfer_status_lifecycle.md))
6. **Not handling failures** - Implement retry logic for transient failures, handle permanent failures
7. **Calling from frontend** - This API requires secret key, must be called from backend only
8. **Not storing transfer_id** - Always store transfer ID for tracking and reconciliation
9. **Using wrong currency** - Always use INR (Indian Rupees) - Zwitch only supports Indian payments
10. **Using crypto/examples** - NEVER use cryptocurrency, Bitcoin, or international currencies - Zwitch is an Indian fintech company

### Production recommendation

- **Always call from backend** - Never expose secret keys in frontend code
- **Verify beneficiary first** - Check beneficiary exists and is verified (if required)
- **Check balance** - Verify sufficient balance in virtual account before initiating transfer
- **Use correct field names** - Use `debit_account_id`, `payment_remark`, `merchant_reference_id` as per API documentation
- **Use webhooks** - Set up webhooks for transfer status updates (see [Polling vs Webhooks](../decisions/polling_vs_webhooks.md))
- **Handle all statuses** - Implement handlers for `initiated`, `pending`, `success`, `failed` states
- **Implement retry logic** - Retry transient failures, don't retry permanent failures (see [Retries and Idempotency](../decisions/retries_and_idempotency.md))
- **Store transfer_id** - Link transfer_id to your internal records (refund_id, settlement_id, etc.)
- **Monitor failures** - Alert on transfer failures, investigate and resolve
- **Use metadata** - Store references (order_id, refund_id, etc.) in metadata for reconciliation
- **Indian context only** - Always use INR currency, Indian banks, IFSC codes, Indian payment methods (UPI, NEFT, IMPS, RTGS)
- **Never use crypto** - Zwitch does NOT support cryptocurrencies - use Indian payment methods only

Transfers funds from a virtual account to a beneficiary's bank account.

### Request Body
```json
{
  "debit_account_id": "va_3Zk64YDxnBtyvkzWoIVUOIWHu",
  "beneficiary_id": "vab_g4U5sHgLA2awuLUBoXvhTp8TR",
  "amount": 1000.00,
  "payment_remark": "Salary payment for January 2024",
  "merchant_reference_id": "SALARY_2024_01_001",
  "metadata": {
    "employee_id": "EMP_456",
    "payroll_id": "PAYROLL_789",
    "department": "Engineering"
  }
}
```

### Request Parameters
- `debit_account_id` (string, required): Your Zwitch virtual account ID from which money will be debited (format: `va_...`)
- `beneficiary_id` (string, required): Beneficiary ID to which money will be transferred (must be created first via `/v1/accounts/{account_id}/beneficiaries`, format: `vab_...`)
- `amount` (number, required): Transfer amount in Indian Rupees (minimum: ₹1.00)
- `payment_remark` (string, optional): Payment remark shown in bank statement (max: 40 characters, only alphabets, numbers, and spaces allowed)
- `merchant_reference_id` (string, optional): Your unique reference ID for tracking (min: 7, max: 40 characters, only alphabets and numbers)
- `metadata` (object, optional): Custom metadata key-value pairs (max 5 pairs, each value max 256 characters)

### Response
```json
{
  "id": "tr_pE33t80XLanGc14F017rRQi6w",
  "object": "transfer",
  "type": "account_number",
  "amount": 1000.00,
  "debit_account_id": "va_3Zk64YDxnBtyvkzWoIVUOIWHu",
  "beneficiary_id": "vab_g4U5sHgLA2awuLUBoXvhTp8TR",
  "status": "success",
  "bank_reference_number": "214568825005",
  "currency_code": "inr",
  "message": "Transaction success",
  "payment_mode": "upi",
  "payment_remark": "Salary payment for January 2024",
  "paid_to": "5010001010101",
  "beneficiary_name": "Sunil Reddy",
  "beneficiary_ifsc": "HDFC0000123",
  "merchant_reference_id": "SALARY_2024_01_001",
  "metadata": {
    "employee_id": "EMP_456",
    "payroll_id": "PAYROLL_789",
    "department": "Engineering"
  },
  "transacted_at": 1653472639,
  "created_at": 1653472637,
  "is_sandbox": false
}
```

### Transfer Status
- `initiated`: Transfer request was successfully created and added to the transfer queue (only when async=true). Money has been debited from the debit account, but the transfer has not yet been sent to the bank for processing.
- `pending`: Transfer request is successful, but money has not been credited to the beneficiary yet. The transfer is being processed by the bank.
- `success`: The transfer has been successfully processed and money has been credited to the beneficiary.
- `failed`: The transfer could not be processed. This could be because of multiple reasons such as insufficient balance, invalid beneficiary details, or bank rejection.

### Response Fields
- `id`: Unique transfer identifier (format: `tr_...`)
- `object`: API object type (always "transfer")
- `type`: Account type to which transfer was made (`account_number`, `vpa`, or `wallet`)
- `amount`: Transfer amount in Indian Rupees
- `debit_account_id`: Virtual account ID from which money was debited
- `beneficiary_id`: Beneficiary ID to which money was transferred
- `status`: Transfer status (`initiated`, `pending`, `success`, `failed`)
- `bank_reference_number`: Unique reference number sent by the bank
- `currency_code`: Currency code (always "inr" for Indian Rupees)
- `message`: Success message or reason for failure/pending
- `payment_mode`: Payment method used (`upi`, `neft`, `imps`, `rtgs`, `ift`)
- `payment_remark`: Payment remark shown in bank statement
- `paid_to`: Account number or VPA handle to which money was transferred
- `beneficiary_name`: Beneficiary's name
- `beneficiary_ifsc`: Beneficiary bank IFSC code (only for account_number type)
- `merchant_reference_id`: Your unique reference ID
- `metadata`: Custom metadata you provided
- `transacted_at`: Unix timestamp when transfer was successfully processed
- `created_at`: Unix timestamp when transfer request was received
- `is_sandbox`: Whether API was called in sandbox mode (true/false)

### Example (Node.js)
```js
const response = await fetch('https://api.zwitch.io/v1/transfers', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    debit_account_id: 'va_3Zk64YDxnBtyvkzWoIVUOIWHu',
    beneficiary_id: 'vab_g4U5sHgLA2awuLUBoXvhTp8TR',
    amount: 1000.00,
    payment_remark: 'Salary payment for January 2024',
    merchant_reference_id: 'SALARY_2024_01_001',
    metadata: {
      employee_id: 'EMP_456',
      payroll_id: 'PAYROLL_789',
      department: 'Engineering'
    }
  })
});

const transfer = await response.json();
console.log('Transfer ID:', transfer.id);
console.log('Status:', transfer.status);
console.log('Bank Reference:', transfer.bank_reference_number);
console.log('Payment Mode:', transfer.payment_mode); // upi, neft, imps, rtgs
console.log('Beneficiary:', transfer.beneficiary_name);
```

### Example (Python)
```python
import requests

url = 'https://api.zwitch.io/v1/transfers'
headers = {
    'Authorization': f'Bearer {ACCESS_KEY}:{SECRET_KEY}',
    'Content-Type': 'application/json'
}
payload = {
    'debit_account_id': 'va_3Zk64YDxnBtyvkzWoIVUOIWHu',
    'beneficiary_id': 'vab_g4U5sHgLA2awuLUBoXvhTp8TR',
    'amount': 1000.00,
    'payment_remark': 'Salary payment for January 2024',
    'merchant_reference_id': 'SALARY_2024_01_001',
    'metadata': {
        'employee_id': 'EMP_456',
        'payroll_id': 'PAYROLL_789',
        'department': 'Engineering'
    }
}

response = requests.post(url, json=payload, headers=headers)
transfer = response.json()
print(f"Transfer ID: {transfer['id']}")
print(f"Status: {transfer['status']}")
print(f"Bank Reference: {transfer['bank_reference_number']}")
print(f"Payment Mode: {transfer['payment_mode']}")  # upi, neft, imps, rtgs
print(f"Beneficiary: {transfer['beneficiary_name']}")
```

## Get Transfer by ID
**GET** `/v1/transfers/{id}`

Returns detailed information for a specific transfer.

### Path Parameters
- `id` (string, required): Transfer ID

### Response
```json
{
  "id": "tr_pE33t80XLanGc14F017rRQi6w",
  "object": "transfer",
  "type": "account_number",
  "amount": 1000.00,
  "debit_account_id": "va_3Zk64YDxnBtyvkzWoIVUOIWHu",
  "beneficiary_id": "vab_g4U5sHgLA2awuLUBoXvhTp8TR",
  "status": "success",
  "bank_reference_number": "214568825005",
  "currency_code": "inr",
  "message": "Transaction success",
  "payment_mode": "upi",
  "payment_remark": "Salary payment for January 2024",
  "paid_to": "5010001010101",
  "beneficiary_name": "Sunil Reddy",
  "beneficiary_ifsc": "HDFC0000123",
  "merchant_reference_id": "SALARY_2024_01_001",
  "metadata": {
    "employee_id": "EMP_456",
    "payroll_id": "PAYROLL_789",
    "department": "Engineering"
  },
  "transacted_at": 1653472639,
  "created_at": 1653472637,
  "is_sandbox": false
}
```

### Response Fields
- `bank_reference_number`: Unique reference number sent by the bank for the transfer
- `beneficiary_name`: Name of the beneficiary account holder
- `beneficiary_ifsc`: IFSC code of the beneficiary bank (only for account_number type)
- `paid_to`: Account number or VPA handle to which money was transferred

### Example
```js
const transferId = 'tr_pE33t80XLanGc14F017rRQi6w';
const response = await fetch(`https://api.zwitch.io/v1/transfers/${transferId}`, {
  headers: {
    'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`
  }
});

const transfer = await response.json();
console.log('Transfer Status:', transfer.status);
console.log('Bank Reference:', transfer.bank_reference_number);
console.log('Payment Mode:', transfer.payment_mode); // upi, neft, imps, rtgs
console.log('Beneficiary:', transfer.beneficiary_name);
console.log('IFSC:', transfer.beneficiary_ifsc);
```

## Bulk Transfers
**POST** `/v1/transfers/bulk`

Creates multiple transfers in a single request. Useful for payroll, vendor payments, or bulk payouts.

### Request Body
```json
{
  "debit_account_id": "va_3Zk64YDxnBtyvkzWoIVUOIWHu",
  "transfers": [
    {
      "beneficiary_id": "vab_g4U5sHgLA2awuLUBoXvhTp8TR",
      "amount": 1000.00,
      "payment_remark": "Salary payment - Employee 1",
      "merchant_reference_id": "SALARY_2024_01_001"
    },
    {
      "beneficiary_id": "vab_bj7y4CkSxKWRqCDq7ACBfwahz",
      "amount": 2000.00,
      "payment_remark": "Salary payment - Employee 2",
      "merchant_reference_id": "SALARY_2024_01_002"
    }
  ]
}
```

### Request Parameters
- `debit_account_id` (string, required): Source virtual account ID from which money will be debited (format: `va_...`)
- `transfers` (array, required): Array of transfer objects (max: 100 transfers per request)
  - `beneficiary_id` (string, required): Beneficiary ID (format: `vab_...`)
  - `amount` (number, required): Transfer amount in Indian Rupees
  - `payment_remark` (string, optional): Payment remark shown in bank statement (max: 40 characters)
  - `merchant_reference_id` (string, optional): Unique reference ID for tracking (min: 7, max: 40 characters)

### Response
```json
{
  "id": "bulk_tr_1RXhgvAsznx9zgA0PJ7QzpWCi",
  "object": "bulk_transfer",
  "debit_account_id": "va_3Zk64YDxnBtyvkzWoIVUOIWHu",
  "status": "processing",
  "total_transfers": 2,
  "total_amount": 3000.00,
  "transfers": [
    {
      "id": "tr_pE33t80XLanGc14F017rRQi6w",
      "beneficiary_id": "vab_g4U5sHgLA2awuLUBoXvhTp8TR",
      "amount": 1000.00,
      "status": "success",
      "bank_reference_number": "214568825005",
      "payment_mode": "upi",
      "merchant_reference_id": "SALARY_2024_01_001"
    },
    {
      "id": "tr_RR66dJIg95bhPP7YUHA6hBMVx",
      "beneficiary_id": "vab_bj7y4CkSxKWRqCDq7ACBfwahz",
      "amount": 2000.00,
      "status": "pending",
      "bank_reference_number": "N179221309296093",
      "payment_mode": "neft",
      "merchant_reference_id": "SALARY_2024_01_002"
    }
  ],
  "created_at": 1653472637
}
```

### Example
```js
const response = await fetch('https://api.zwitch.io/v1/transfers/bulk', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    debit_account_id: 'va_3Zk64YDxnBtyvkzWoIVUOIWHu',
    transfers: [
      {
        beneficiary_id: 'vab_g4U5sHgLA2awuLUBoXvhTp8TR',
        amount: 1000.00,
        payment_remark: 'Salary payment - Employee 1',
        merchant_reference_id: 'SALARY_2024_01_001'
      },
      {
        beneficiary_id: 'vab_bj7y4CkSxKWRqCDq7ACBfwahz',
        amount: 2000.00,
        payment_remark: 'Salary payment - Employee 2',
        merchant_reference_id: 'SALARY_2024_01_002'
      }
    ]
  })
});

const bulkTransfer = await response.json();
console.log(`Bulk Transfer ID: ${bulkTransfer.id}`);
console.log(`Total Amount: ₹${bulkTransfer.total_amount}`);
bulkTransfer.transfers.forEach(transfer => {
  console.log(`Transfer ${transfer.id}: ${transfer.status} (${transfer.payment_mode})`);
  console.log(`  Bank Reference: ${transfer.bank_reference_number}`);
});
```

## List All Transfers
**GET** `/v1/transfers`

Returns a paginated list of all transfers.

### Query Parameters
- `page` (integer, optional): Page number (default: 1)
- `limit` (integer, optional): Number of results per page (default: 20, max: 100)
- `status` (string, optional): Filter by status
- `account_id` (string, optional): Filter by account ID
- `from_date` (string, optional): Start date in `YYYY-MM-DD` format
- `to_date` (string, optional): End date in `YYYY-MM-DD` format

### Response
```json
{
  "object": "list",
  "has_more": false,
  "data": [
    {
      "id": "tr_pE33t80XLanGc14F017rRQi6w",
      "object": "transfer",
      "type": "account_number",
      "amount": 1000.00,
      "debit_account_id": "va_3Zk64YDxnBtyvkzWoIVUOIWHu",
      "beneficiary_id": "vab_g4U5sHgLA2awuLUBoXvhTp8TR",
      "status": "success",
      "bank_reference_number": "214568825005",
      "currency_code": "inr",
      "payment_mode": "upi",
      "payment_remark": "Salary payment for January 2024",
      "beneficiary_name": "Sunil Reddy",
      "beneficiary_ifsc": "HDFC0000123",
      "merchant_reference_id": "SALARY_2024_01_001",
      "transacted_at": 1653472639,
      "created_at": 1653472637,
      "is_sandbox": false
    }
  ]
}
```

## Transfer Webhooks

Zwitch sends webhook events for transfer status changes. Configure webhooks to receive real-time notifications. See [Webhooks documentation](./10_webhooks.md) for details.

## Best Practices

1. **Create Beneficiaries First**: Always create beneficiaries before initiating transfers
2. **Verify Account Balance**: Check account balance before initiating transfers
3. **Handle Fees**: Account for transfer fees when calculating amounts
4. **Use Reference IDs**: Use unique reference IDs for easy tracking and reconciliation
5. **Monitor Status**: Use webhooks or polling to monitor transfer status
6. **Bulk Transfers**: Use bulk transfers API for multiple payouts to reduce API calls
7. **Store UTR**: Store UTR numbers for bank reconciliation

