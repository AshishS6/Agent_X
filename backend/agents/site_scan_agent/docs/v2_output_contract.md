# V2 Output Contract - Field Annotations

**Purpose**: Defines which fields are required, optional, or V2-only for frontend integration.

---

## Field Classification

### ⚡ Required Fields
Fields that **MUST** be present and **MUST NOT** be null in every scan response.

```
comprehensive_site_scan              [object] Root wrapper (CRITICAL)
├── url                              [string] REQUIRED - Scanned URL
├── scan_timestamp                   [string] REQUIRED - ISO 8601 timestamp
├── compliance                       [object] REQUIRED
│   ├── general                      [object] REQUIRED
│   │   ├── pass                     [boolean] REQUIRED
│   │   ├── alerts                   [array] REQUIRED (may be empty)
│   │   └── actions_needed           [array] REQUIRED (may be empty)
│   └── payment_terms                [object] REQUIRED
│       ├── pass                     [boolean] REQUIRED
│       ├── alerts                   [array] REQUIRED (may be empty)
│       └── actions_needed           [array] REQUIRED (may be empty)
├── policy_details                   [object] REQUIRED
│   ├── home_page                    [object] REQUIRED
│   ├── privacy_policy               [object] REQUIRED
│   ├── terms_condition              [object] REQUIRED
│   ├── returns_refund               [object] REQUIRED
│   ├── shipping_delivery            [object] REQUIRED
│   ├── contact_us                   [object] REQUIRED
│   ├── about_us                     [object] REQUIRED
│   ├── faq                          [object] REQUIRED
│   └── product                      [object] REQUIRED
├── business_details                 [object] REQUIRED
│   └── extracted_business_name      [string] REQUIRED
├── content_risk                     [object] REQUIRED
│   ├── dummy_words_detected         [boolean] REQUIRED
│   ├── dummy_words                  [array] REQUIRED
│   ├── restricted_keywords_found    [array] REQUIRED
│   └── risk_score                   [number] REQUIRED
├── product_details                  [object] REQUIRED
│   ├── has_products                 [boolean] REQUIRED
│   ├── has_pricing                  [boolean] REQUIRED
│   ├── has_cart                     [boolean] REQUIRED
│   └── ecommerce_platform           [boolean] REQUIRED
└── mcc_codes                        [object] REQUIRED
    ├── primary_mcc                  [object|null] REQUIRED (nullable)
    ├── secondary_mcc                [object|null] REQUIRED (nullable)
    └── all_matches                  [array] REQUIRED (may be empty)
```

---

### 🆕 V2-Only Fields (New Features)
Fields introduced in V2 that **MAY** be missing in V1 responses.

```
comprehensive_site_scan
├── tech_stack                       [object] V2-ONLY
│   ├── cms                          [string] V2-ONLY - CMS platform
│   ├── analytics                    [array<string>] V2-ONLY - Analytics tools
│   ├── payments                     [array<string>] V2-ONLY - Payment gateways
│   ├── frameworks                   [array<string>] V2-ONLY - JS frameworks
│   └── hosting                      [string|null] V2-ONLY - Hosting/CDN provider
├── seo_analysis                     [object] V2-ONLY
│   ├── title                        [object] V2-ONLY
│   │   ├── present                  [boolean] V2-ONLY
│   │   ├── length                   [number] V2-ONLY
│   │   └── text                     [string] V2-ONLY
│   ├── meta_description             [object] V2-ONLY (same structure as title)
│   ├── h1_count                     [number] V2-ONLY
│   ├── canonical                    [string|null] V2-ONLY
│   ├── indexable                    [boolean] V2-ONLY
│   ├── sitemap_found                [boolean] V2-ONLY
│   ├── robots_txt_found             [boolean] V2-ONLY
│   └── seo_score                    [number] V2-ONLY - 0-100
└── business_details
    ├── contact_info                 [object] V2-ONLY (enhanced)
    │   ├── email                    [string|null] V2-ONLY
    │   ├── phone                    [string|null] V2-ONLY
    │   └── address                  [string|null] V2-ONLY
    └── social_links                 [object] V2-ONLY (enhanced)
        ├── facebook                 [string|null] V2-ONLY
        ├── twitter                  [string|null] V2-ONLY
        ├── linkedin                 [string|null] V2-ONLY
        └── instagram                [string|null] V2-ONLY
```

---

## Frontend Integration Guide

### Accessing Required Fields (Safe)

```typescript
// All these fields are GUARANTEED to exist
const scan = response.comprehensive_site_scan;

const url = scan.url;                              // ✅ Always string
const compliancePassed = scan.compliance.general.pass;  // ✅ Always boolean
const alerts = scan.compliance.general.alerts;     // ✅ Always array (may be empty)
const businessName = scan.business_details.extracted_business_name; // ✅ Always string
const riskScore = scan.content_risk.risk_score;    // ✅ Always number
```

### Accessing V2-Only Fields (Safe with Checks)

```typescript
// Check for existence before using
const scan = response.comprehensive_site_scan;

// Tech Stack (V2-only)
if (scan.tech_stack) {
  const cms = scan.tech_stack.cms;                 // ✅ Safe
  const analytics = scan.tech_stack.analytics;     // ✅ Safe
  const frameworks = scan.tech_stack.frameworks;   // ✅ Safe
}

// SEO Analysis (V2-only)
if (scan.seo_analysis) {
  const seoScore = scan.seo_analysis.seo_score;    // ✅ Safe (0-100)
  const hasTitle = scan.seo_analysis.title.present; // ✅ Safe
}

// Enhanced Business Details (V2-only)
if (scan.business_details?.contact_info) {
  const email = scan.business_details.contact_info.email; // ⚠️ May be null
}

if (scan.business_details?.social_links) {
  const facebook = scan.business_details.social_links.facebook; // ⚠️ May be null
}
```

---

## Null Safety Guide

### Fields That Can Be Null

| Field Path | Reason | How to Handle |
|------------|--------|---------------|
| `mcc_codes.primary_mcc` | No MCC match found | Check `if (primary_mcc)` before use |
| `mcc_codes.secondary_mcc` | Less than 2 matches | Check `if (secondary_mcc)` before use |
| `tech_stack.hosting` | Could not detect | Use optional chaining `?.` |
| `seo_analysis.canonical` | No canonical tag | Use optional chaining `?.` |
| `business_details.contact_info.*` | Not found on page | Check each field individually |
| `business_details.social_links.*` | No social profiles | Check each field individually |

### Fields That Are Never Null

All boolean and number fields are never null:
- `compliance.*.pass` → always `true` or `false`
- `seo_analysis.seo_score` → always `0-100`
- `content_risk.risk_score` → always a number
- `product_details.*` → always boolean

---

## Example V2 Output

See [test_v2_output.json](../test_v2_output.json) for a complete real-world example.

### Key Observations

1. **Backward Compatible**: All V1 fields present
2. **Additive Only**: V2 fields are siblings, not replacements
3. **Type Safety**: Consistent types across all scans
4. **Null Safety**: Predictable null behavior

---

## Version Detection

To detect if a response is from V2:

```typescript
function isV2Response(scan: any): boolean {
  return 'tech_stack' in scan || 'seo_analysis' in scan;
}

// Usage
if (isV2Response(scan)) {
  // Show enhanced UI with V2 features
  displayTechStack(scan.tech_stack);
  displaySEOScore(scan.seo_analysis.seo_score);
} else {
  // Fall back to V1 UI
  displayBasicInfo(scan);
}
```

---

## Migration Checklist for Frontend

### Phase 1: Prepare (No Changes)
- [ ] Verify current code handles new fields gracefully (ignores them)
- [ ] Test with V2 responses to ensure no errors
- [ ] Confirm null safety for V2-only fields

### Phase 2: Enhance (Optional)
- [ ] Add tech stack badges/display
- [ ] Add SEO score meter
- [ ] Display contact info cards
- [ ] Add social media links

### Phase 3: Optimize (Future)
- [ ] Cache V2-specific data
- [ ] Add filters for tech stack
- [ ] Create SEO insights dashboard

---

## Contact

For questions about V2 output structure:
- See [frontend_compatibility.md](frontend_compatibility.md)
- Review [validation_results.json](../validation_results.json)
- Check [test_v2_output.json](../test_v2_output.json)

---

**Last Updated**: 2025-12-28  
**Schema Version**: v2.0
