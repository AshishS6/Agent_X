# Zwitch API — Verification Suite

## Verify VPA (UPI ID)
**POST** `/v1/verifications/vpa`

Sample request/response in docs; verifies if a UPI ID is valid.

## Verify Bank Account (Pennyless)
**POST** `/v1/verifications/bank-account/pennyless`  
Verify bank account + IFSC without transfers.

Other verification endpoints include PAN/Name verification.

