# Site Scan — Complete Documentation

## What is Site Scan?

**Site Scan** is an automated website analysis tool that performs comprehensive due diligence on any website. It extracts business intelligence, compliance status, technical infrastructure, and SEO health in a single scan.

Think of it as a **digital investigator** that visits a website, reads its pages, and produces a structured report covering everything from legal policies to payment systems.

---

## Why Use Site Scan?

### Primary Use Cases

| Use Case | Who Benefits |
|----------|--------------|
| **Merchant Onboarding** | Payment processors, acquirers |
| **Partner Due Diligence** | Business development teams |
| **Competitor Analysis** | Product & marketing teams |
| **Compliance Audits** | Risk & legal teams |
| **Investment Research** | VCs, analysts |

### Key Benefits

- ⚡ **Speed**: Complete analysis in ~2 minutes vs hours of manual research
- 🎯 **Consistency**: Same 50+ data points checked for every website
- 📊 **Structured Output**: Machine-readable JSON for integration
- 🔍 **Deep Extraction**: Finds data humans often miss (hidden policies, tech stack)

---

## How It Works

### Scan Flow

```
URL Input → Crawl → Extract → Analyze → Report
```

### Step-by-Step Process

#### 1. **URL Crawling**
- Fetches home page HTML
- Follows internal links to find key pages
- Respects robots.txt

#### 2. **Page Discovery**
Automatically locates:
- Home page
- About Us
- Contact Us
- Privacy Policy
- Terms & Conditions
- Refund/Returns Policy
- Pricing page
- Product pages

#### 3. **Data Extraction**
Parses HTML to extract:
- Business name & description
- Contact information (email, phone, address)
- Social media links
- Policy content
- Product listings

#### 4. **Technical Analysis**
Detects:
- CMS (WordPress, Shopify, Custom)
- Frameworks (React, Angular, Vue)
- Analytics tools (Google Analytics, Mixpanel)
- Payment processors (Stripe, PayPal, Razorpay)
- Hosting infrastructure

#### 5. **SEO Analysis**
Checks:
- Title tag presence & length
- Meta description
- H1 count
- Canonical URLs
- Indexability
- Sitemap & robots.txt

#### 6. **Compliance Checks**
Validates:
- Website is live (HTTP 200)
- SSL certificate valid
- Domain vintage (age)
- Required policies present
- No suspicious redirects

#### 7. **MCC Classification**
Uses LLM to determine:
- Merchant Category Code (MCC)
- Business category & subcategory
- Confidence score

---

## What You Get Out of It

### Scan Report Sections

#### 📋 Compliance Checks
| Check | What It Means |
|-------|---------------|
| **Liveness** | Website responds with HTTP 200 |
| **SSL Valid** | HTTPS certificate is properly configured |
| **Domain Vintage** | Domain registered for 2+ years |
| **No Redirects** | URL goes directly to content |

#### 📄 Policy Details
- **Privacy Policy**: Found / Not Found + URL
- **Terms & Conditions**: Found / Not Found + URL
- **Refund Policy**: Found / Not Found + URL
- **Contact Page**: Found / Not Found + URL

#### 💳 MCC Codes
- Primary MCC number
- Secondary MCC (if applicable)
- Category description
- Confidence score (%)

#### 🛍️ Product Details
- Pricing model (subscription, one-time, freemium)
- Target audience
- Key products/services list
- Checkout detection
- E-commerce indicators

#### 🏢 Business Details
- Business name
- Company summary
- Mission & vision
- Key offerings
- Contact information
- Social media presence

#### 🔧 Tech Stack Intelligence (V2)
- CMS: WordPress, Shopify, Custom, etc.
- Frameworks: React, Angular, Vue, Next.js
- Analytics: Google Analytics, Mixpanel, Segment
- Payments: Stripe, PayPal, Razorpay
- Hosting: AWS, Cloudflare, Vercel

#### 📈 SEO Health Report (V2)
- **SEO Score**: 0-100 rating
- Title tag status
- Meta description status
- H1 tag count
- Canonical URL presence
- Indexability
- Sitemap found
- Robots.txt found

---

## Sample Output Structure

```json
{
  "comprehensive_site_scan": {
    "url": "https://example.com",
    "business_name": "Example Corp",
    "scan_timestamp": "2025-12-29T20:00:00Z",
    
    "compliance_checks": {
      "liveness": { "status": "pass", "message": "Website is live" },
      "ssl": { "status": "pass", "message": "Valid HTTPS certificate" },
      "vintage": { "status": "pass", "message": "Domain 5+ years old" }
    },
    
    "policy_details": {
      "privacy_policy": { "found": true, "url": "https://..." },
      "terms_conditions": { "found": true, "url": "https://..." }
    },
    
    "mcc_codes": {
      "primary": { "code": "5411", "confidence": 85 },
      "category": "Grocery Stores"
    },
    
    "tech_stack": {
      "cms": "Shopify",
      "frameworks": ["React"],
      "analytics": ["Google Analytics"],
      "payments": ["Stripe"]
    },
    
    "seo_analysis": {
      "seo_score": 85,
      "title": { "present": true, "length": 55 },
      "indexable": true
    }
  }
}
```

---

## How to Run a Site Scan

### From the UI

1. Go to **Market Research** in the sidebar
2. Click **+ New Research Report**
3. Select **Site Scan** from dropdown
4. Enter the website URL
5. Click **Start Research**
6. Wait ~2 minutes for results

### From API

```bash
POST /api/agents/market_research/execute
{
  "action": "site_scan",
  "input": {
    "topic": "https://example.com"
  }
}
```

---

## Best Practices

### URLs to Scan
✅ Use the main domain (e.g., `https://stripe.com`)  
✅ Include country-specific domains (e.g., `https://stripe.com/in`)  
❌ Don't scan internal/admin pages  
❌ Don't scan localhost or private IPs  

### Interpreting Results
- **MCC Confidence < 50%**: Manual review recommended
- **Missing Policies**: Flag for compliance review
- **SEO Score < 50**: Website has significant issues
- **"Not Found" fields**: May indicate thin content or poor structure

### Limitations
- **JavaScript-heavy sites**: Some content may not extract
- **Login-protected content**: Cannot access authenticated pages
- **Rate limits**: Some sites may block repeated scans
- **Dynamic content**: Single snapshot, not real-time monitoring

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Site Scan Engine                     │
├─────────────────────────────────────────────────────────┤
│  Scanners           │  Extractors        │  Analyzers   │
│  ─────────          │  ──────────        │  ─────────   │
│  • Site Crawler     │  • Link Extractor  │  • SEO       │
│  • Policy Scanner   │  • Metadata        │  • Tech      │
│  • WHOIS Lookup     │  • Policy Detector │  • Content   │
│                     │  • Business Info   │              │
├─────────────────────────────────────────────────────────┤
│                    Report Builder                       │
│  Combines all data into structured JSON output          │
└─────────────────────────────────────────────────────────┘
```

---

## Related Documentation

- [V2 Output Contract](./docs/v2_output_contract.md) — Detailed field specifications
- [Frontend Compatibility](./docs/frontend_compatibility.md) — UI field mapping
- [Promotion Readiness](./docs/promotion_readiness.md) — V2 rollout guide
