# Citation Filtering Fix - Internal KB Files Removed

## Problem

Internal Knowledge Base (KB) markdown files were being shown in citations on the frontend. URLs like `https://api.zwitch.io/v1/api/00_introduction.md` were appearing in the "SOURCES" section, which are internal file references, not public documentation URLs.

## Solution

Strengthened URL validation in `backend/knowledge/retrieval/url_mapping.py` to:

1. **Filter out any URL containing `.md`** - Markdown files are internal KB files
2. **Filter out file path patterns** - URLs like `/api/00_introduction.md` or `/api/15_layer_js.md`
3. **Only return public documentation URLs** - Websites, documentation portals, dashboards

## Changes Made

### 1. Enhanced `_is_valid_public_url()` method

- **Strict `.md` filtering**: Any URL containing `.md` is immediately rejected
- **File path pattern detection**: Regex patterns to detect internal file paths like `/api/00_introduction.md`
- **API path validation**: Allows `/api/` in documentation URLs (e.g., `developers.zwitch.io/docs/api/...`) but blocks internal API file paths

### 2. Enhanced `extract_and_validate_urls()` method

- **Double filtering**: Final pass to remove any `.md` URLs that might have slipped through
- **Pattern-based exclusion**: Multiple regex patterns to catch file path variations
- **Validation on mapped URLs**: Ensures source path mappings also produce valid public URLs

## Validation Results

✅ **Rejected (Internal KB files):**
- `https://api.zwitch.io/v1/api/00_introduction.md` ❌
- `https://api.zwitch.io/v1/api/15_layer_js.md` ❌

✅ **Accepted (Public URLs):**
- `https://developers.zwitch.io/docs/overview` ✅
- `https://www.zwitch.io/` ✅
- `https://developers.zwitch.io/reference/layerjs` ✅
- `https://developers.zwitch.io/docs/api/overview` ✅

## Impact

- **Frontend**: Only public documentation URLs will appear in the "SOURCES" section
- **Backend**: Internal KB file paths are mapped to public URLs via `URLMapper.get_url_for_source_path()`
- **User Experience**: Citations are now meaningful public links users can actually visit

## Testing

Run validation tests:
```bash
cd backend
python3 -c "from knowledge.retrieval.url_mapping import URLMapper; test_urls = ['https://api.zwitch.io/v1/api/00_introduction.md', 'https://developers.zwitch.io/docs/overview']; [print(f'{url}: {URLMapper._is_valid_public_url(url)}') for url in test_urls]"
```

Expected output:
- `.md` URLs: `False`
- Public documentation URLs: `True`

---

**Status**: ✅ Internal KB markdown files are now filtered out. Only public URLs appear in citations.
