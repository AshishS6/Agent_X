# Zwitch API — Constants

## Overview

Zwitch provides several constants endpoints that return lookup tables and reference data commonly used in API requests. These endpoints help you populate dropdowns, validate inputs, and ensure compliance with Indian banking and business regulations.

## Base Endpoint

All constants endpoints are available under:
```
GET /v1/constants/{constant-type}
```

## Available Constants Endpoints

### 1. Bank IFSC Codes

**Endpoint:** `GET /v1/constants/bank-ifsc`

**Description:** Returns a list of all Indian bank IFSC (Indian Financial System Code) codes with associated bank information.

**Use Cases:**
- Populate bank selection dropdowns
- Validate IFSC codes before creating beneficiaries
- Display bank names for user selection
- Verify bank details for payouts

**Response Format:**
```json
{
  "data": [
    {
      "ifsc": "HDFC0000001",
      "bank_name": "HDFC Bank",
      "branch": "Mumbai",
      "address": "...",
      "city": "Mumbai",
      "state": "Maharashtra",
      "pincode": "400001"
    }
  ]
}
```

**Example Request:**
```bash
curl -X GET https://api.zwitch.io/v1/constants/bank-ifsc \
  -H "Authorization: Bearer ACCESS_KEY:SECRET_KEY"
```

---

### 2. Business Categories

**Endpoint:** `GET /v1/constants/business-categories`

**Description:** Returns a list of standard business categories used for merchant onboarding, KYC, and compliance purposes.

**Use Cases:**
- Onboarding forms requiring business category selection
- KYC documentation
- Compliance reporting
- Business type classification

**Response Format:**
```json
{
  "data": [
    {
      "code": "RETAIL",
      "name": "Retail",
      "description": "Retail and e-commerce businesses"
    },
    {
      "code": "SAAS",
      "name": "Software as a Service",
      "description": "SaaS and software businesses"
    }
  ]
}
```

**Example Request:**
```bash
curl -X GET https://api.zwitch.io/v1/constants/business-categories \
  -H "Authorization: Bearer ACCESS_KEY:SECRET_KEY"
```

---

### 3. Business Types

**Endpoint:** `GET /v1/constants/business-types`

**Description:** Returns a list of legal business entity types (e.g., Private Limited, LLP, Partnership, etc.) used for business registration and compliance.

**Use Cases:**
- Business registration forms
- KYC documentation
- Legal entity type selection
- Compliance verification

**Response Format:**
```json
{
  "data": [
    {
      "code": "PVT_LTD",
      "name": "Private Limited Company",
      "description": "Private limited company registered under Companies Act"
    },
    {
      "code": "LLP",
      "name": "Limited Liability Partnership",
      "description": "LLP registered under LLP Act"
    },
    {
      "code": "PARTNERSHIP",
      "name": "Partnership Firm",
      "description": "Partnership firm registered under Partnership Act"
    }
  ]
}
```

**Example Request:**
```bash
curl -X GET https://api.zwitch.io/v1/constants/business-types \
  -H "Authorization: Bearer ACCESS_KEY:SECRET_KEY"
```

---

### 4. State Codes

**Endpoint:** `GET /v1/constants/state-codes`

**Description:** Returns a list of Indian state and union territory codes with names, used for address validation and compliance.

**Use Cases:**
- Address forms requiring state selection
- GST registration (state codes)
- Address validation
- Compliance reporting by state

**Response Format:**
```json
{
  "data": [
    {
      "code": "MH",
      "name": "Maharashtra",
      "gst_code": "27"
    },
    {
      "code": "DL",
      "name": "Delhi",
      "gst_code": "07"
    },
    {
      "code": "KA",
      "name": "Karnataka",
      "gst_code": "29"
    }
  ]
}
```

**Example Request:**
```bash
curl -X GET https://api.zwitch.io/v1/constants/state-codes \
  -H "Authorization: Bearer ACCESS_KEY:SECRET_KEY"
```

---

## Authentication

All constants endpoints require Bearer token authentication. Include your Access Key and Secret Key in the Authorization header:

```
Authorization: Bearer ACCESS_KEY:SECRET_KEY
```

See [Authentication documentation](./01_authentication.md) for details on generating API keys.

## Response Format

All constants endpoints return JSON responses with the following structure:

**Success Response (200 OK):**
```json
{
  "data": [
    // Array of constant objects
  ]
}
```

**Error Response:**
See [Error Codes documentation](./02_error_codes.md) for error response format.

## Caching Recommendations

Constants data changes infrequently. For better performance:

1. **Cache responses locally** - Constants can be cached for 24-48 hours
2. **Update periodically** - Refresh cache daily or weekly
3. **Handle errors gracefully** - Use cached data if API is unavailable

## Best Practices

1. **Pre-fetch on app startup** - Load constants when your application starts
2. **Store locally** - Cache constants in your database or local storage
3. **Validate against constants** - Use constants to validate user inputs
4. **Display user-friendly names** - Show full names, not just codes
5. **Handle updates** - Monitor for changes in constants data

## Related Documentation

- [Authentication](./01_authentication.md) - How to authenticate API requests
- [Error Codes](./02_error_codes.md) - Understanding error responses
- [Accounts](./03_accounts.md) - Account management APIs
- [Beneficiaries](./06_beneficiaries.md) - Beneficiary management (uses IFSC codes)

## Example Usage

### Node.js Example

```javascript
const axios = require('axios');

async function getBankIFSC() {
  try {
    const response = await axios.get(
      'https://api.zwitch.io/v1/constants/bank-ifsc',
      {
        headers: {
          'Authorization': `Bearer ${ACCESS_KEY}:${SECRET_KEY}`
        }
      }
    );
    
    console.log('Bank IFSC codes:', response.data.data);
    return response.data.data;
  } catch (error) {
    console.error('Error fetching constants:', error.response.data);
    throw error;
  }
}

// Cache the results
let cachedIFSC = null;
async function getCachedIFSC() {
  if (!cachedIFSC) {
    cachedIFSC = await getBankIFSC();
    // Refresh cache after 24 hours
    setTimeout(() => { cachedIFSC = null; }, 24 * 60 * 60 * 1000);
  }
  return cachedIFSC;
}
```

### Python Example

```python
import requests
from datetime import datetime, timedelta

class ConstantsCache:
    def __init__(self):
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = timedelta(hours=24)
    
    def get_bank_ifsc(self, access_key, secret_key):
        cache_key = 'bank-ifsc'
        
        # Check cache
        if cache_key in self.cache:
            if datetime.now() - self.cache_time[cache_key] < self.cache_duration:
                return self.cache[cache_key]
        
        # Fetch from API
        response = requests.get(
            'https://api.zwitch.io/v1/constants/bank-ifsc',
            headers={
                'Authorization': f'Bearer {access_key}:{secret_key}'
            }
        )
        response.raise_for_status()
        
        data = response.json()['data']
        
        # Update cache
        self.cache[cache_key] = data
        self.cache_time[cache_key] = datetime.now()
        
        return data

# Usage
cache = ConstantsCache()
ifsc_codes = cache.get_bank_ifsc(ACCESS_KEY, SECRET_KEY)
```

---

## Notes

- Constants data is updated periodically by Zwitch
- Always validate user inputs against the latest constants
- Cache constants locally for better performance
- Use constants to ensure compliance with Indian regulations
- State codes are aligned with GST state codes where applicable

