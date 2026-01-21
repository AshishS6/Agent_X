# Zwitch API — Balance & Statement

## Get Account Balance
**GET** `/v1/accounts/{id}/balance`

Retrieves the current balance information for a virtual account.

### Path Parameters
- `id` (string, required): Account ID

### Response
```json
{
  "account_id": "acc_1234567890",
  "balance": {
    "available": 10000.50,
    "pending": 500.00,
    "currency": "INR"
  },
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### Balance Fields
- `available`: Funds available for immediate use (transfers, payouts)
- `pending`: Funds that are pending settlement (incoming payments not yet settled)
- `currency`: Currency code (typically `INR` for Indian Rupees)

### Example (Node.js)
```js
const accountId = 'acc_1234567890';
const response = await fetch(`https://api.zwitch.io/v1/accounts/${accountId}/balance`, {
  headers: {
    'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`
  }
});

const balance = await response.json();
console.log(`Available: ₹${balance.balance.available}`);
console.log(`Pending: ₹${balance.balance.pending}`);
```

### Example (Python)
```python
import requests

account_id = 'acc_1234567890'
url = f'https://api.zwitch.io/v1/accounts/{account_id}/balance'
headers = {'Authorization': f'Bearer {ACCESS_KEY}:{SECRET_KEY}'}

response = requests.get(url, headers=headers)
balance = response.json()
print(f"Available: ₹{balance['balance']['available']}")
print(f"Pending: ₹{balance['balance']['pending']}")
```

## Get Account Statement
**GET** `/v1/accounts/{id}/statement`

Retrieves transaction history (statement) for a virtual account.

### Path Parameters
- `id` (string, required): Account ID

### Query Parameters
- `from_date` (string, optional): Start date in `YYYY-MM-DD` format (default: 30 days ago)
- `to_date` (string, optional): End date in `YYYY-MM-DD` format (default: today)
- `page` (integer, optional): Page number (default: 1)
- `limit` (integer, optional): Number of transactions per page (default: 20, max: 100)
- `transaction_type` (string, optional): Filter by type (`credit`, `debit`, `all`)

### Response
```json
{
  "account_id": "acc_1234567890",
  "from_date": "2024-01-01",
  "to_date": "2024-01-15",
  "transactions": [
    {
      "id": "txn_1234567890",
      "type": "credit",
      "amount": 1000.00,
      "currency": "INR",
      "description": "Payment received via UPI",
      "reference_id": "ref_123",
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z",
      "metadata": {
        "payment_id": "pay_123",
        "customer_id": "cust_456"
      }
    },
    {
      "id": "txn_0987654321",
      "type": "debit",
      "amount": 500.00,
      "currency": "INR",
      "description": "Transfer to beneficiary",
      "reference_id": "ref_456",
      "status": "completed",
      "created_at": "2024-01-14T15:20:00Z",
      "metadata": {
        "transfer_id": "trf_789",
        "beneficiary_id": "ben_123"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 2,
    "total_pages": 1
  },
  "summary": {
    "total_credits": 1000.00,
    "total_debits": 500.00,
    "net_amount": 500.00
  }
}
```

### Transaction Types
- `credit`: Money received (incoming payments, refunds)
- `debit`: Money sent (transfers, payouts, fees)

### Transaction Status
- `pending`: Transaction is being processed
- `completed`: Transaction completed successfully
- `failed`: Transaction failed
- `cancelled`: Transaction was cancelled

### Example (Node.js)
```js
const accountId = 'acc_1234567890';
const fromDate = '2024-01-01';
const toDate = '2024-01-15';

const url = `https://api.zwitch.io/v1/accounts/${accountId}/statement?from_date=${fromDate}&to_date=${toDate}&page=1&limit=20`;

const response = await fetch(url, {
  headers: {
    'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`
  }
});

const statement = await response.json();
console.log(`Total Credits: ₹${statement.summary.total_credits}`);
console.log(`Total Debits: ₹${statement.summary.total_debits}`);
console.log(`Net Amount: ₹${statement.summary.net_amount}`);

statement.transactions.forEach(txn => {
  console.log(`${txn.type.toUpperCase()}: ₹${txn.amount} - ${txn.description}`);
});
```

### Example (Python)
```python
import requests
from datetime import datetime, timedelta

account_id = 'acc_1234567890'
to_date = datetime.now().strftime('%Y-%m-%d')
from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

url = f'https://api.zwitch.io/v1/accounts/{account_id}/statement'
headers = {'Authorization': f'Bearer {ACCESS_KEY}:{SECRET_KEY}'}
params = {
    'from_date': from_date,
    'to_date': to_date,
    'page': 1,
    'limit': 20
}

response = requests.get(url, headers=headers, params=params)
statement = response.json()

print(f"Total Credits: ₹{statement['summary']['total_credits']}")
print(f"Total Debits: ₹{statement['summary']['total_debits']}")
print(f"Net Amount: ₹{statement['summary']['net_amount']}")

for txn in statement['transactions']:
    print(f"{txn['type'].upper()}: ₹{txn['amount']} - {txn['description']}")
```

## Use Cases

1. **Balance Monitoring**: Check available balance before initiating transfers
2. **Reconciliation**: Download statements for accounting reconciliation
3. **Transaction History**: Display transaction history to end users
4. **Reporting**: Generate financial reports based on transaction data
5. **Audit Trail**: Maintain audit trail of all account activities

