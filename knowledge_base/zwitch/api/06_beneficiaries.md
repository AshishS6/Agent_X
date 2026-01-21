# Zwitch API — Beneficiaries

Beneficiaries are bank account details that you register with Zwitch to enable transfers. You must create a beneficiary before initiating a transfer to that bank account.

## Create Bank Account Beneficiary
**POST** `/v1/beneficiaries/bank-account`

Creates a new bank account beneficiary for transfers.

### Request Body
```json
{
  "name": "John Doe",
  "account_number": "1234567890",
  "ifsc": "HDFC0001234",
  "account_type": "savings",
  "email": "john@example.com",
  "phone": "+919876543210",
  "metadata": {
    "employee_id": "emp_123",
    "vendor_id": "ven_456"
  }
}
```

### Request Parameters
- `name` (string, required): Beneficiary name (as per bank records)
- `account_number` (string, required): Bank account number
- `ifsc` (string, required): IFSC code of the bank branch
- `account_type` (string, optional): Account type (`savings`, `current`, `salary`) - default: `savings`
- `email` (string, optional): Beneficiary email
- `phone` (string, optional): Beneficiary phone number
- `metadata` (object, optional): Custom metadata key-value pairs

### Response
```json
{
  "id": "ben_1234567890",
  "name": "John Doe",
  "account_number": "1234567890",
  "ifsc": "HDFC0001234",
  "account_type": "savings",
  "bank_name": "HDFC Bank",
  "status": "active",
  "verification_status": "pending",
  "email": "john@example.com",
  "phone": "+919876543210",
  "created_at": "2024-01-15T10:30:00Z",
  "metadata": {
    "employee_id": "emp_123",
    "vendor_id": "ven_456"
  }
}
```

### Verification Status
- `pending`: Beneficiary created, verification pending
- `verified`: Beneficiary verified successfully
- `failed`: Beneficiary verification failed
- `not_required`: Verification not required

### Example (Node.js)
```js
const response = await fetch('https://api.zwitch.io/v1/beneficiaries/bank-account', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'John Doe',
    account_number: '1234567890',
    ifsc: 'HDFC0001234',
    account_type: 'savings',
    email: 'john@example.com',
    phone: '+919876543210',
    metadata: {
      employee_id: 'emp_123'
    }
  })
});

const beneficiary = await response.json();
console.log('Beneficiary ID:', beneficiary.id);
console.log('Bank Name:', beneficiary.bank_name);
console.log('Verification Status:', beneficiary.verification_status);
```

### Example (Python)
```python
import requests

url = 'https://api.zwitch.io/v1/beneficiaries/bank-account'
headers = {
    'Authorization': f'Bearer {ACCESS_KEY}:{SECRET_KEY}',
    'Content-Type': 'application/json'
}
payload = {
    'name': 'John Doe',
    'account_number': '1234567890',
    'ifsc': 'HDFC0001234',
    'account_type': 'savings',
    'email': 'john@example.com',
    'phone': '+919876543210',
    'metadata': {
        'employee_id': 'emp_123'
    }
}

response = requests.post(url, json=payload, headers=headers)
beneficiary = response.json()
print(f"Beneficiary ID: {beneficiary['id']}")
print(f"Bank Name: {beneficiary['bank_name']}")
```

## List Beneficiaries
**GET** `/v1/beneficiaries`

Returns a paginated list of all beneficiaries.

### Query Parameters
- `page` (integer, optional): Page number (default: 1)
- `limit` (integer, optional): Number of results per page (default: 20, max: 100)
- `status` (string, optional): Filter by status (`active`, `inactive`)
- `verification_status` (string, optional): Filter by verification status

### Response
```json
{
  "data": [
    {
      "id": "ben_1234567890",
      "name": "John Doe",
      "account_number": "1234567890",
      "ifsc": "HDFC0001234",
      "bank_name": "HDFC Bank",
      "status": "active",
      "verification_status": "verified",
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
const url = 'https://api.zwitch.io/v1/beneficiaries?page=1&limit=20';
const response = await fetch(url, {
  headers: {
    'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`
  }
});

const data = await response.json();
data.data.forEach(beneficiary => {
  console.log(`${beneficiary.name} - ${beneficiary.bank_name} (${beneficiary.verification_status})`);
});
```

## Get Beneficiary by ID
**GET** `/v1/beneficiaries/{id}`

Returns detailed information for a specific beneficiary.

### Path Parameters
- `id` (string, required): Beneficiary ID

### Response
```json
{
  "id": "ben_1234567890",
  "name": "John Doe",
  "account_number": "1234567890",
  "ifsc": "HDFC0001234",
  "account_type": "savings",
  "bank_name": "HDFC Bank",
  "branch": "Mumbai Main Branch",
  "status": "active",
  "verification_status": "verified",
  "email": "john@example.com",
  "phone": "+919876543210",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "metadata": {
    "employee_id": "emp_123",
    "vendor_id": "ven_456"
  }
}
```

### Example
```js
const beneficiaryId = 'ben_1234567890';
const response = await fetch(`https://api.zwitch.io/v1/beneficiaries/${beneficiaryId}`, {
  headers: {
    'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`
  }
});

const beneficiary = await response.json();
console.log('Beneficiary Name:', beneficiary.name);
console.log('Account Number:', beneficiary.account_number);
console.log('Verification Status:', beneficiary.verification_status);
```

## Update Beneficiary
**PUT** `/v1/beneficiaries/{id}`

Updates beneficiary information. Note: Some fields like account_number and IFSC may not be updatable after verification.

### Path Parameters
- `id` (string, required): Beneficiary ID

### Request Body
```json
{
  "name": "John Doe Updated",
  "email": "john.updated@example.com",
  "phone": "+919876543211",
  "metadata": {
    "employee_id": "emp_123",
    "department": "Engineering"
  }
}
```

### Response
Returns the updated beneficiary object.

### Example
```js
const beneficiaryId = 'ben_1234567890';
const response = await fetch(`https://api.zwitch.io/v1/beneficiaries/${beneficiaryId}`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'john.updated@example.com',
    phone: '+919876543211'
  })
});

const updatedBeneficiary = await response.json();
console.log('Updated:', updatedBeneficiary);
```

## Delete Beneficiary
**DELETE** `/v1/beneficiaries/{id}`

Deletes a beneficiary. Note: Beneficiaries with active transfers may not be deletable.

### Path Parameters
- `id` (string, required): Beneficiary ID

### Response
```json
{
  "id": "ben_1234567890",
  "deleted": true,
  "deleted_at": "2024-01-15T10:30:00Z"
}
```

### Example
```js
const beneficiaryId = 'ben_1234567890';
const response = await fetch(`https://api.zwitch.io/v1/beneficiaries/${beneficiaryId}`, {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`
  }
});

const result = await response.json();
console.log('Deleted:', result.deleted);
```

## Beneficiary Verification

After creating a beneficiary, Zwitch may automatically verify the account details. You can also manually trigger verification using the Verification API. See [Verification documentation](./08_verification.md) for details.

## Best Practices

1. **Verify Before Transfer**: Ensure beneficiaries are verified before initiating transfers
2. **Store Beneficiary IDs**: Store beneficiary IDs for reuse in multiple transfers
3. **Validate IFSC**: Use the Constants API to validate IFSC codes before creating beneficiaries
4. **Use Metadata**: Store employee IDs, vendor IDs, or other references in metadata
5. **Handle Verification**: Monitor verification status and handle failed verifications appropriately
6. **Update Contact Info**: Keep email and phone numbers updated for notifications

