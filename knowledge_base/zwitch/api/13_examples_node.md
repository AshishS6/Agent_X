# Zwitch API — Node.js Examples

## Create UPI Collect
```js
import fetch from "node-fetch";

async function createUPICollect(vaId, amount) {
  const res = await fetch(`https://api.zwitch.io/v1/accounts/${vaId}/payments/upi/collect`, {
    method: "POST",
    headers: {
      Authorization: "Bearer ACCESS_KEY:SECRET_KEY",
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ remitter_vpa_handle: "payer@upi", amount })
  });
  return res.json();
}
```

