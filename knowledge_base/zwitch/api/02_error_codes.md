# Zwitch API — Error Codes

ZWITCH APIs return:
- **2XX** on success
- **4XX** for client errors
- **5XX** for server/provider errors

## Error Response Format

All error responses follow this structure:

```json
{
  "error": {
    "type": "error_type",
    "message": "Human-readable error message",
    "code": "ERROR_CODE",
    "details": {
      "field": "Additional error details if available"
    }
  }
}
```

## HTTP Status Codes

### Success Codes (2XX)
- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **202 Accepted**: Request accepted for processing

### Client Errors (4XX)
- **400 Bad Request**: Invalid request parameters or malformed request
- **401 Unauthorized**: Authentication failed or missing credentials
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict (e.g., duplicate entry)
- **422 Unprocessable Entity**: Validation error
- **429 Too Many Requests**: Rate limit exceeded

### Server Errors (5XX)
- **500 Internal Server Error**: Unexpected server error
- **502 Bad Gateway**: Upstream service error
- **503 Service Unavailable**: Service temporarily unavailable
- **504 Gateway Timeout**: Request timeout

## Common Error Types

### Authentication Errors
```json
{
  "error": {
    "type": "authentication_error",
    "message": "Invalid secret key.",
    "code": "AUTH_FAILED"
  }
}
```

**Common causes:**
- Missing Authorization header
- Invalid Access Key or Secret Key
- Expired API keys
- Malformed Authorization header format

### Invalid Request Errors
```json
{
  "error": {
    "type": "invalid_request_error",
    "message": "Invalid amount. Amount must be greater than 0.",
    "code": "INVALID_AMOUNT",
    "details": {
      "field": "amount",
      "value": -100
    }
  }
}
```

**Common causes:**
- Missing required fields
- Invalid field values
- Invalid data types
- Out of range values

### Validation Errors
```json
{
  "error": {
    "type": "validation_error",
    "message": "IFSC code is invalid.",
    "code": "INVALID_IFSC",
    "details": {
      "field": "ifsc",
      "value": "INVALID123"
    }
  }
}
```

**Common causes:**
- Invalid IFSC code format
- Invalid UPI ID format
- Invalid account number
- Invalid PAN format

### Service Provider Errors
```json
{
  "error": {
    "type": "service_provider_error",
    "message": "Bank service temporarily unavailable.",
    "code": "BANK_UNAVAILABLE"
  }
}
```

**Common causes:**
- Partner bank service down
- Network issues with banking partner
- Banking partner rate limits

### Resource Not Found Errors
```json
{
  "error": {
    "type": "not_found_error",
    "message": "Account not found.",
    "code": "ACCOUNT_NOT_FOUND"
  }
}
```

### Rate Limit Errors
```json
{
  "error": {
    "type": "rate_limit_error",
    "message": "Too many requests. Please try again later.",
    "code": "RATE_LIMIT_EXCEEDED",
    "details": {
      "retry_after": 60
    }
  }
}
```

## Error Handling Best Practices

### 1. Always Check Response Status
```js
const response = await fetch(url, options);
if (!response.ok) {
  const error = await response.json();
  // Handle error
}
```

### 2. Implement Retry Logic
```js
async function makeRequestWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.ok) return await response.json();
      
      // Don't retry on 4XX errors (except 429)
      if (response.status >= 400 && response.status < 500 && response.status !== 429) {
        throw new Error(await response.json());
      }
      
      // Retry on 5XX and 429
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
    } catch (error) {
      if (i === maxRetries - 1) throw error;
    }
  }
}
```

### 3. Handle Specific Error Types
```python
try:
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    error_data = e.response.json()
    error_type = error_data.get('error', {}).get('type')
    
    if error_type == 'authentication_error':
        # Re-authenticate or refresh keys
        pass
    elif error_type == 'rate_limit_error':
        # Wait and retry
        retry_after = error_data.get('error', {}).get('details', {}).get('retry_after', 60)
        time.sleep(retry_after)
    elif error_type == 'validation_error':
        # Fix validation issues
        pass
```

## Error Code Reference

| Error Type | HTTP Status | Description |
|------------|-------------|-------------|
| `authentication_error` | 401 | Authentication failed |
| `invalid_request_error` | 400 | Invalid request parameters |
| `validation_error` | 422 | Validation failed |
| `not_found_error` | 404 | Resource not found |
| `rate_limit_error` | 429 | Rate limit exceeded |
| `service_provider_error` | 502/503 | Banking partner error |
| `internal_error` | 500 | Internal server error |

