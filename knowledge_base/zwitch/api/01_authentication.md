# Zwitch API — Authentication & Authorization

ZWITCH uses **Bearer tokens** combining an `Access Key` and `Secret Key`.  
Every API call must include:

```
Authorization: Bearer <ACCESS_KEY>:<SECRET_KEY>
```

## Getting Your API Keys

1. Log in to your [Zwitch Dashboard](https://dashboard.zwitch.io)
2. Navigate to **Developers → API Keys**
3. Click **Generate New Key** to create a new API key pair
4. Copy both the **Access Key** and **Secret Key** immediately (Secret Key is shown only once)

## Security Best Practices

⚠️ **Critical Security Guidelines:**

- **Never expose Secret Keys** in frontend code, client-side applications, or public repositories
- **Store keys securely** using environment variables or secure key management systems
- **Rotate keys regularly** for enhanced security
- **Use different keys** for development, staging, and production environments
- **Revoke compromised keys** immediately from the dashboard

## Authentication Header Format

The Authorization header must be formatted as:
```
Authorization: Bearer ACCESS_KEY:SECRET_KEY
```

Note: There is a colon (`:`) between the Access Key and Secret Key, with no spaces.

## Code Examples

### Node.js / JavaScript
```js
const ACCESS_KEY = process.env.ZWITCH_ACCESS_KEY;
const SECRET_KEY = process.env.ZWITCH_SECRET_KEY;

fetch("https://api.zwitch.io/v1/accounts", {
  headers: {
    "Authorization": `Bearer ${ACCESS_KEY}:${SECRET_KEY}`,
    "Content-Type": "application/json"
  }
})
.then(res => res.json())
.then(data => console.log(data));
```

### Python
```python
import os
import requests

ACCESS_KEY = os.getenv('ZWITCH_ACCESS_KEY')
SECRET_KEY = os.getenv('ZWITCH_SECRET_KEY')

headers = {
    'Authorization': f'Bearer {ACCESS_KEY}:{SECRET_KEY}',
    'Content-Type': 'application/json'
}

response = requests.get('https://api.zwitch.io/v1/accounts', headers=headers)
print(response.json())
```

### cURL
```bash
curl -X GET "https://api.zwitch.io/v1/accounts" \
  -H "Authorization: Bearer ACCESS_KEY:SECRET_KEY" \
  -H "Content-Type: application/json"
```

## Environment Variables Setup

### .env file (Node.js/Python)
```env
ZWITCH_ACCESS_KEY=your_access_key_here
ZWITCH_SECRET_KEY=your_secret_key_here
ZWITCH_API_BASE_URL=https://api.zwitch.io/v1
```

## Error Responses

If authentication fails, you'll receive a `401 Unauthorized` response:

```json
{
  "error": {
    "type": "authentication_error",
    "message": "Invalid secret key."
  }
}
```

Common authentication errors:
- `authentication_error`: Invalid or missing credentials
- `invalid_request_error`: Malformed Authorization header

## Key Management

- **Multiple Keys**: You can create multiple API key pairs for different applications
- **Key Permissions**: Keys inherit permissions from your account role
- **Key Rotation**: Generate new keys and update your applications, then revoke old keys
- **Key Expiration**: Check your dashboard for key expiration policies

