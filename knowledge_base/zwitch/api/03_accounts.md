# Zwitch API — Accounts

Virtual Accounts (VAs) are the core entity in Zwitch. They act as wallets that can receive payments, hold balances, and initiate transfers.

## Create a Virtual Account
**POST** `/v1/accounts`

Create a virtual account for wallet/transfers/collections.

### Request Body
```json
{
  "account_type": "virtual_account",
  "name": "My Business Account",
  "description": "Primary account for collections",
  "metadata": {
    "customer_id": "cust_123",
    "business_unit": "sales"
  }
}
```

### Request Parameters
- `account_type` (string, optional): Type of account. Default: `virtual_account`
- `name` (string, optional): Human-readable account name
- `description` (string, optional): Account description
- `metadata` (object, optional): Custom metadata key-value pairs

### Response
```json
{
  "id": "acc_1234567890",
  "account_type": "virtual_account",
  "name": "My Business Account",
  "status": "active",
  "balance": {
    "available": 0,
    "currency": "INR"
  },
  "account_details": {
    "account_number": "1234567890123456",
    "ifsc": "ZWITCH000123",
    "upi_id": "acc_1234567890@zwitch"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Example (Node.js)
```js
const response = await fetch('https://api.zwitch.io/v1/accounts', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'My Business Account',
    description: 'Primary account for collections'
  })
});

const account = await response.json();
console.log('Account ID:', account.id);
console.log('Account Number:', account.account_details.account_number);
```

### Example (Python)
```python
import requests

url = 'https://api.zwitch.io/v1/accounts'
headers = {
    'Authorization': f'Bearer {ACCESS_KEY}:{SECRET_KEY}',
    'Content-Type': 'application/json'
}
payload = {
    'name': 'My Business Account',
    'description': 'Primary account for collections'
}

response = requests.post(url, json=payload, headers=headers)
account = response.json()
print(f"Account ID: {account['id']}")
```

## Get All Accounts
**GET** `/v1/accounts`

Returns a paginated list of all virtual accounts associated with your account.

### Query Parameters
- `page` (integer, optional): Page number (default: 1)
- `limit` (integer, optional): Number of results per page (default: 20, max: 100)
- `status` (string, optional): Filter by status (`active`, `inactive`, `suspended`)

### Response
```json
{
  "data": [
    {
      "id": "acc_1234567890",
      "account_type": "virtual_account",
      "name": "My Business Account",
      "status": "active",
      "balance": {
        "available": 10000.50,
        "currency": "INR"
      },
      "account_details": {
        "account_number": "1234567890123456",
        "ifsc": "ZWITCH000123",
        "upi_id": "acc_1234567890@zwitch"
      },
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

### Example
```js
const response = await fetch('https://api.zwitch.io/v1/accounts?page=1&limit=20', {
  headers: {
    'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`
  }
});

const data = await response.json();
console.log(`Total accounts: ${data.pagination.total}`);
data.data.forEach(account => {
  console.log(`${account.name}: ${account.balance.available} ${account.balance.currency}`);
});
```

## Get Account by ID
**GET** `/v1/accounts/{id}`

Returns detailed information for a specific virtual account.

### Path Parameters
- `id` (string, required): Account ID

### Response
```json
{
  "id": "acc_1234567890",
  "account_type": "virtual_account",
  "name": "My Business Account",
  "description": "Primary account for collections",
  "status": "active",
  "balance": {
    "available": 10000.50,
    "pending": 500.00,
    "currency": "INR"
  },
  "account_details": {
    "account_number": "1234567890123456",
    "ifsc": "ZWITCH000123",
    "upi_id": "acc_1234567890@zwitch",
    "bank_name": "Partner Bank"
  },
  "metadata": {
    "customer_id": "cust_123",
    "business_unit": "sales"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Example
```js
const accountId = 'acc_1234567890';
const response = await fetch(`https://api.zwitch.io/v1/accounts/${accountId}`, {
  headers: {
    'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`
  }
});

const account = await response.json();
console.log('Account Balance:', account.balance.available);
console.log('UPI ID:', account.account_details.upi_id);
```

## Account Status

Accounts can have the following statuses:
- `active`: Account is active and can transact
- `inactive`: Account is inactive (cannot transact)
- `suspended`: Account is suspended (usually due to compliance issues)

## Account Details

Each virtual account includes:
- **Account Number**: Unique account number for bank transfers
- **IFSC Code**: IFSC code for the virtual account
- **UPI ID**: UPI ID for receiving payments via UPI

## Use Cases

1. **Payment Collections**: Share account details or UPI ID with customers
2. **Wallet Functionality**: Hold funds in virtual accounts
3. **Payouts**: Transfer funds from virtual accounts to beneficiaries
4. **Multi-tenant**: Create separate accounts for different customers or business units

