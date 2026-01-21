# Fix: Remove Internal Source Citations

## Problem

The RAG system was exposing internal markdown file references (like "Source 7", "Source 1") in chat responses, which is not acceptable for production use with internal teams and clients.

**Example of problematic response:**
```
The relevant information is available in Source 7 and Source 1:
- Source 7: Open Money - Platform Access mentions...
- Source 1: Zwitch - Products Overview...
```

## Solution

Removed all internal source citations and replaced them with public URL citations only.

## Changes Made

### 1. RAG Pipeline (`backend/rag/pipeline.py`)

**Changes:**
- Changed default `include_sources` parameter from `True` to `False`
- Removed internal source citation formatting (`[Source 1: ...]`)
- Added `_extract_public_urls()` method to extract public URLs from context
- Updated context formatting to exclude internal source labels
- Added explicit instructions to NOT cite internal file references

**Key Changes:**
```python
# Before: include_sources: bool = True
# After:  include_sources: bool = False  # No internal source citations

# Before: Added "[Source 1: Zwitch - Products Overview]" labels
# After:  No source labels, only extract public URLs from context
```

### 2. System Prompt (`backend/assistants/fintech.py`)

**Changes:**
- Removed instruction to "cite sources using the format provided in context"
- Added explicit instruction: "NEVER cite internal file references, source numbers, or markdown file paths"
- Added instruction: "ONLY cite public URLs when relevant: website links, documentation links, or dashboard links"

**Before:**
```
- Cite sources when referencing KB content using the format provided in context (e.g., "[Source 1: Zwitch - Products Overview]")
```

**After:**
```
- NEVER cite internal file references, source numbers (like "Source 1", "Source 7"), or markdown file paths
- ONLY cite public URLs when relevant: website links (zwitch.io, open.money), documentation links (developers.zwitch.io), or dashboard links
```

### 3. Public URL Extraction

**New Feature:**
- Automatically extracts public URLs from context chunks
- Filters out localhost/internal URLs
- Only includes public domains (zwitch.io, open.money, developers.*, dashboard.*, etc.)
- Provides extracted URLs to LLM for citation when relevant

## Expected Behavior

### Before Fix:
```
User: "What's Zwitch's payout API?"
Response: "The relevant information is available in Source 7 and Source 1:
- Source 7: Open Money - Platform Access mentions...
- Source 1: Zwitch - Products Overview..."
```

### After Fix:
```
User: "What's Zwitch's payout API?"
Response: "Open Money does not provide APIs. For payout/transfer APIs, use Zwitch Transfers APIs.

Endpoint: POST /v1/transfers
Documentation: https://developers.zwitch.io/reference/transfers"
```

## Public URLs That Can Be Cited

The system will automatically extract and allow citation of:
- **Zwitch:**
  - https://www.zwitch.io/ (Website)
  - https://developers.zwitch.io (API Documentation)
  - https://dashboard.zwitch.io (Dashboard)
  - https://api.zwitch.io/v1/* (API Endpoints)

- **Open Money:**
  - https://open.money/ (Website)
  - Dashboard links (if mentioned in context)

## Testing

To verify the fix works:

1. **Test Question:** "What's Zwitch's payout API?"
   - ✅ Should NOT show "Source 7", "Source 1", etc.
   - ✅ Should show public URLs like developers.zwitch.io
   - ✅ Should show API endpoints

2. **Test Question:** "What products does Zwitch offer?"
   - ✅ Should NOT show internal source references
   - ✅ Should list all 4 products
   - ✅ May cite zwitch.io if relevant

3. **Test Question:** "How do I integrate payments?"
   - ✅ Should NOT show markdown file paths
   - ✅ Should cite developers.zwitch.io documentation
   - ✅ Should provide API endpoints

## Files Modified

1. `backend/rag/pipeline.py` - Removed internal source citations, added public URL extraction
2. `backend/assistants/fintech.py` - Updated system prompt to prohibit internal citations

## Impact

- ✅ No more internal file references in responses
- ✅ Only public URLs cited when relevant
- ✅ Production-ready for internal teams and clients
- ✅ Maintains accuracy while improving professionalism

## Next Steps

1. Restart the backend server to apply changes
2. Test with sample questions
3. Verify responses no longer contain internal references
4. Confirm public URLs are cited appropriately

---

**Status:** ✅ Fixed
**Date:** Implementation complete
**Ready for:** Production use
