# URL Mapping System for Public Citations

## Overview

This system ensures that only valid public URLs are cited in chat responses, never internal file references or invalid URLs.

## Problem Solved

**Before:** Responses could cite invalid URLs like:
- `https://api.zwitch.io/v1/api/11_api_constants.md` ❌ (doesn't exist)
- Internal file paths ❌
- Source numbers like "Source 7" ❌

**After:** Only valid public URLs are cited:
- `https://developers.zwitch.io/reference/transfers-bulk` ✅
- `https://www.zwitch.io/` ✅
- `https://open.money/` ✅

## How It Works

### 1. URL Mapping (`backend/rag/url_mapping.py`)

**Source Path Mapping:**
- Maps KB file paths to public URLs
- Example: `zwitch/api/07_transfers.md` → `https://developers.zwitch.io/reference/transfers-bulk`

**API Endpoint Mapping:**
- Maps API endpoints to documentation URLs
- Example: `POST /v1/transfers` → `https://developers.zwitch.io/reference/transfers-bulk`

**URL Validation:**
- Filters out invalid URLs (localhost, .md files, invalid API paths)
- Only allows public domains (zwitch.io, open.money, developers.*, etc.)

### 2. RAG Pipeline Integration

The RAG pipeline:
1. Retrieves context chunks with metadata (including source_path)
2. Extracts public URLs from:
   - URLs found in context text
   - Source path mappings
   - API endpoint mappings
3. Validates all URLs (filters invalid ones)
4. Provides only valid public URLs to LLM for citation

## URL Mappings

### Zwitch URLs

**Base URLs:**
- Website: `https://www.zwitch.io/`
- Documentation: `https://developers.zwitch.io/`
- Dashboard: `https://dashboard.zwitch.io/`

**API Documentation:**
- Transfers: `https://developers.zwitch.io/reference/transfers-bulk`
- Payments: `https://developers.zwitch.io/docs/payment`
- Layer.js: `https://developers.zwitch.io/docs/layer`
- Authentication: `https://developers.zwitch.io/reference/authorization`
- Webhooks: `https://developers.zwitch.io/docs/webhook-setup`
- Verification: `https://developers.zwitch.io/reference/verifications-bank-account`
- Connected Banking: `https://developers.zwitch.io/reference/connected-banking-apis`
- Beneficiaries: `https://developers.zwitch.io/docs/beneficiary-integration-flow`

### Open Money URLs

**Base URLs:**
- Website: `https://open.money/`
- Dashboard: `https://dashboard.open.money/` (if available)

**Note:** Open Money is a platform, not an API provider, so most references point to the main website.

## Invalid URL Patterns (Filtered Out)

The system automatically filters out:
- ❌ `localhost` URLs
- ❌ Internal IPs (192.168.*, 10.0.*, 172.16.*)
- ❌ URLs ending in `.md` (markdown files)
- ❌ Invalid API paths like `api.zwitch.io/v1/api/`
- ❌ Source numbers like "Source 7", "Source 1"

## Example Mappings

### KB File → Public URL

| KB File | Public URL |
|---------|-----------|
| `zwitch/api/07_transfers.md` | `https://developers.zwitch.io/reference/transfers-bulk` |
| `zwitch/api/11_api_constants.md` | `https://developers.zwitch.io/reference` |
| `zwitch/products_overview.md` | `https://www.zwitch.io/` |
| `openmoney/products_overview.md` | `https://open.money/` |
| `zwitch/api/05_payments.md` | `https://developers.zwitch.io/docs/payment` |

### API Endpoint → Documentation URL

| API Endpoint | Documentation URL |
|--------------|-------------------|
| `POST /v1/transfers` | `https://developers.zwitch.io/reference/transfers-bulk` |
| `POST /v1/pg/payment_token` | `https://developers.zwitch.io/docs/layer` |
| `GET /v1/constants/bank-ifsc` | `https://developers.zwitch.io/reference` |
| `POST /v1/accounts/{account_id}/payments/upi/collect` | `https://developers.zwitch.io/docs/payment` |

## Testing

The URL mapping system has been tested and verified:

```bash
# Test URL mapping
python3 -c "from backend.rag.url_mapping import URLMapper; print(URLMapper.get_url_for_source_path('zwitch/api/07_transfers.md'))"
# Output: https://developers.zwitch.io/reference/transfers-bulk

# Test invalid URL filtering
python3 -c "from backend.rag.url_mapping import URLMapper; print(URLMapper._is_valid_public_url('https://api.zwitch.io/v1/api/11_api_constants.md'))"
# Output: False
```

## Usage in RAG Pipeline

The URL mapper is automatically used by the RAG pipeline:

1. **Context Retrieval:** Gets source paths from metadata
2. **URL Extraction:** Extracts URLs from context text and maps source paths
3. **Validation:** Filters out invalid URLs
4. **Citation:** Provides only valid public URLs to LLM

## Adding New Mappings

To add new URL mappings, edit `backend/rag/url_mapping.py`:

```python
# Add to URL_MAPPING dict
URL_MAPPING = {
    "zwitch/new_file.md": "https://developers.zwitch.io/docs/new-feature",
    # ...
}

# Add to API_ENDPOINT_MAPPING dict
API_ENDPOINT_MAPPING = {
    "POST /v1/new-endpoint": "https://developers.zwitch.io/reference/new-endpoint",
    # ...
}
```

## Verification

After changes, verify mappings work:

```bash
cd /Users/ashish/local-ai-chat
python3 -c "from backend.rag.url_mapping import URLMapper; print(URLMapper.get_url_for_source_path('zwitch/api/07_transfers.md'))"
```

## Status

✅ **Complete and Verified**
- URL mapping system implemented
- Invalid URL filtering working
- RAG pipeline integrated
- All test cases passing

---

**Last Updated:** Based on website crawling and documentation review
**Status:** Production-ready
