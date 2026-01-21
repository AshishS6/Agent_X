# Zwitch API — Python Examples

## Create UPI Collect
```python
import requests

def create_upi_collect(va_id, amount):
    url = f"https://api.zwitch.io/v1/accounts/{va_id}/payments/upi/collect"
    headers = {"Authorization": "Bearer ACCESS_KEY:SECRET_KEY"}
    payload = {"remitter_vpa_handle":"payer@upi","amount":amount}
    return requests.post(url,json=payload).json()
```

