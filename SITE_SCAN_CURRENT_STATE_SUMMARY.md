# SiteScan Current State Summary
**Date:** 2026-01-XX  
**Version:** V2.1 Modular Engine  
**Purpose:** Baseline documentation for Phase-2 PRD

---

## 1. System Overview

### What SiteScan Does End-to-End
SiteScan is an automated website analysis tool that performs comprehensive due diligence on websites. It:
1. **Crawls** websites using parallel page discovery (up to 20 pages)
2. **Extracts** business metadata, policy pages, technical stack, and content
3. **Analyzes** compliance status, SEO health, content risks, and business context
4. **Classifies** Merchant Category Codes (MCC) based on content keywords
5. **Detects** changes between scans using content hashing and derived signals
6. **Generates** structured JSON reports with compliance scores and risk flags

### Primary Use Case
- **Merchant Onboarding**: Payment processors and acquirers use it for KYB (Know Your Business) checks
- **Compliance Audits**: Risk and legal teams validate policy presence and content
- **Partner Due Diligence**: Business development teams assess potential partners
- **Competitor Analysis**: Product and marketing teams gather intelligence

### Execution Model
- **Async/Background**: Tasks are queued in PostgreSQL and executed asynchronously by Go backend
- **Python CLI**: Go backend spawns Python CLI process (`cli.py`) per scan request
- **Timeout**: 10 minutes total (600 seconds) per scan
- **Non-blocking**: Snapshot persistence runs in background thread

### System Boundaries
**In Scope:**
- Static HTML websites and server-side rendered (SSR) sites
- Public pages (no authentication required)
- Policy page detection via URL patterns and link text
- Technical stack detection via HTML signatures
- Compliance scoring based on policy presence and content analysis

**Out of Scope:**
- JavaScript-rendered Single Page Applications (SPAs) - no headless browser support
- Login-protected or authenticated pages
- Real-time monitoring or continuous scanning
- Deep site crawling (limited to 20 pages, depth 2)
- Full HTML archival (only content hashes stored)

---

## 2. Scan Capabilities (As Implemented)

### 2.1 Domain Health Checks

**Liveness Detection:**
- **Method**: HTTP status code check (200 = live)
- **Output**: `scan_status.status` field with values: `SUCCESS`, `FAILED`
- **Failure Reasons**: `DNS_FAIL`, `HTTP_403`, `SSL_ERROR`, `TIMEOUT`, `HTTP_XXX`
- **Retryable Flag**: Indicates if scan can be retried

**Redirect Detection:**
- **Method**: Tracks `redirect_count` from HTTP response
- **Output**: Compliance alert if `redirect_count > 1`
- **Alert Code**: `EXCESSIVE_REDIRECTS`

**SSL Certificate Validation:**
- **Method**: Python `ssl` module with `socket.create_connection()` on port 443
- **Output**: Compliance alert if HTTPS missing or SSL handshake fails
- **Alert Codes**: `NO_HTTPS`, `SSL_ERROR`
- **Blocking**: Non-HTTPS sites fail general compliance

**Domain Age (Vintage):**
- **Method**: RDAP (Registration Data Access Protocol) lookup
  - Primary: `https://rdap.org/domain/{domain}`
  - Fallback: `https://rdap.verisign.com/com/v1/domain/{domain}` (for .com/.net)
- **Output**: `domain_vintage_days` integer
- **Compliance Logic**: Alerts if age < 365 days (`LOW_VINTAGE`)
- **Scoring**: Used in compliance intelligence (0-15 points based on age brackets)

### 2.2 Policy Page Detection

**Detection Method:**
- **Primary**: Regex pattern matching on link URLs and link text
- **Enhancement**: Page graph discovery (if orchestrator found page, use it)
- **Patterns**: Defined in `PolicyDetector.PATTERNS` dictionary
  - Privacy Policy: `privacy[-_]?policy`, `privacy`, `gdpr`, `data[-_]?protection`
  - Terms: `terms?[-_]?(and[-_]?|\&[-_]?)?conditions?`, `tos`
  - Refund: `returns?`, `refunds?`, `cancellation`
  - Shipping: `shipping`, `delivery`, `dispatch`
  - Contact: `contact[-_]?us`, `contact`, `support`
  - About: `about[-_]?us`, `about`
  - FAQ: `faq`, `frequently[-_]?asked`
  - Product: `products?`, `shop`, `store`

**Output Format:**
```json
{
  "privacy_policy": {
    "found": true/false,
    "url": "https://...",
    "status": "Privacy Policy page is available"
  }
}
```

**Compliance Logic:**
- **Payment Terms Compliance**: Requires both `returns_refund` AND `terms_condition` to pass
- **Context-Aware**: Expectations adjusted based on business context (SaaS, FinTech, Blockchain, etc.)

### 2.3 Content Checks

**Dummy Text Detection:**
- **Method**: Regex patterns for Lorem Ipsum (`lorem\s+ipsum\s+dolor`, `consectetur\s+adipiscing`, `sed\s+do\s+eiusmod`)
- **Output**: `content_risk.dummy_words_detected` boolean, `dummy_words` array
- **Penalty**: -10 points in compliance trust score

**Restricted Keywords:**
- **Method**: Keyword matching in page text (case-insensitive)
- **Categories**: 
  - `gambling`: casino, poker, betting, slots, lottery
  - `adult`: xxx, adult content, nsfw
  - `crypto`: cryptocurrency, bitcoin, ico
  - `pharmacy`: viagra, cialis, prescription drugs
- **Output**: `content_risk.restricted_keywords_found` array with category and keyword
- **Penalties**: Context-aware (crypto = 0 for blockchain/fintech, 5 for others; gambling = 15; adult = 20; pharmacy = 10)
- **Note**: Content risk data is computed but **NOT displayed in UI** (known gap)

**Product Indicators:**
- **Method**: Keyword presence in page text
- **Checks**: `has_products`, `has_pricing`, `has_cart`, `ecommerce_platform`
- **Output**: Boolean flags in `product_details`

### 2.4 MCC Classification

**Method:**
- **Keyword Matching**: Local dictionary-based classification (hardcoded in `scan_engine.py._classify_mcc()`)
- **Categories**: Retail (Fashion, Groceries, Electronics, Home & Garden), Services (Professional, Financial, Education, Health), Travel & Entertainment
- **Scoring**: Confidence = `min(matched_keywords * 15, 100)`
- **Output Format:**
```json
{
  "primary_mcc": {
    "category": "Retail",
    "subcategory": "Fashion & Clothing",
    "mcc_code": "5621",
    "description": "Women's Ready-to-Wear Stores",
    "confidence": 75,
    "keywords_matched": ["women", "dress", "fashion"]
  },
  "secondary_mcc": {...},
  "all_matches": [...] // Top 10 matches
}
```

**Limitations:**
- No LLM-based classification (despite documentation mentioning it)
- Generic keywords can cause false positives
- No blocking logic - suggestions only

### 2.5 Security & Infrastructure Checks

**SSL Check:**
- Implemented (see Domain Health section)

**DNS Check:**
- Implicit via HTTP connection failures (reported as `DNS_FAIL`)

**Robots.txt Handling:**
- **Method**: `RobotsTxtParser` fetches and parses robots.txt
- **Usage**: Blocks crawling of disallowed paths
- **Output**: Stored in `page_graph.metadata.robots_checked` (boolean)
- **Not displayed in UI**

**Sitemap Discovery:**
- **Method**: `SitemapParser` checks robots.txt sitemaps and `/sitemap.xml`
- **Usage**: Used for high-priority URL discovery
- **Output**: Stored in `page_graph.metadata.sitemap_found` (boolean)
- **Not displayed in UI**

---

## 3. Crawling & Data Collection

### 3.1 Crawl Architecture

**Engine**: `CrawlOrchestrator` (async Python with `aiohttp`)
- **Version**: V2.1 (integrated with ModularScanEngine)
- **Concurrency**: 10 parallel requests (`asyncio.Semaphore(10)`)
- **Page Budget**: 20 pages maximum (`MAX_PAGES = 20`)
- **Max Depth**: 2 levels
- **Timeouts**: 
  - Per page: 12 seconds (`PAGE_TIMEOUT`)
  - Connection: 5 seconds (`CONNECT_TIMEOUT`)
  - Total: 600 seconds (`TOTAL_TIMEOUT`)

### 3.2 Crawl Phases

**Phase 1: Robots.txt Check**
- Fetches `{base_url}/robots.txt`
- Parses rules for path-based blocking
- Non-blocking (continues if missing)

**Phase 2: Homepage Fetch**
- Fetches seed URL (homepage)
- Parses HTML immediately for sitemap/navigation discovery
- If homepage fails, scan terminates with error status

**Phase 3: Discovery**
- **Sitemap URLs**: Extracted from sitemap.xml (high priority)
- **Navigation Links**: Extracted from header/footer via `NavigationDiscovery`
  - Primary nav: `<nav>`, `<header>` links
  - Secondary nav: Footer links (if no sitemap)
- **URL Normalization**: Deduplication and filtering via `URLNormalizer`

**Phase 4: Parallel Fetch**
- Fetches discovered URLs in parallel (up to 19 pages, excluding homepage)
- Respects robots.txt rules
- Early exit if "Required Pages" (Privacy, Terms) AND "High Value Pages" (About, Pricing) found

**Phase 5: Classification**
- Classifies each page by type (home, privacy_policy, terms_conditions, product, pricing, about, contact, etc.)
- Uses URL patterns and page titles

### 3.3 JavaScript Rendering

**Status**: **NOT SUPPORTED**
- Uses `aiohttp` + `BeautifulSoup` (HTML parser only)
- Cannot execute JavaScript
- **Impact**: SPAs (React/Vue/Angular client-side rendered) return empty content
- **Workaround**: Tech stack detector can identify framework from script tags, but content extraction fails

### 3.4 Rate Limiting & Robots.txt

**Robots.txt**: Fully respected (blocks disallowed paths)
**Rate Limiting**: 
- No explicit rate limiting (relies on timeout and concurrency limits)
- Retry logic: 1 retry per page with exponential backoff (2s initial, doubles)
- User-Agent: `Agent_X_CrawlOrchestrator/1.0`

### 3.5 Content Storage

**Stored:**
- **Page Graph**: In-memory during scan (HTML, status codes, metadata)
- **Content Hashes**: Saved to `site_scan_snapshots.page_hashes` (JSONB)
- **Crawl Cache**: `crawl_page_cache` table (URL, HTML, status, expires_at)
- **Full Report**: Stored in `tasks.output` (JSONB)

**Discarded:**
- Full HTML content (after hash extraction) - not persisted long-term
- Intermediate parsing results (soup objects)
- HTTP headers (except for tech detection)

---

## 4. Data Models & Storage

### 4.1 Core Tables

**`tasks` Table:**
- **Purpose**: Stores scan execution records
- **Key Fields**:
  - `id` (UUID): Task identifier
  - `agent_id` (UUID): References `agents` table
  - `action` (VARCHAR): "site_scan" or "comprehensive_site_scan"
  - `input` (JSONB): Input parameters (URL, business_name, etc.)
  - `output` (JSONB): Full scan report JSON
  - `status` (VARCHAR): pending, processing, completed, failed
  - `started_at`, `completed_at`, `created_at` (TIMESTAMP)
- **Indexes**: `agent_id`, `status`, `created_at DESC`, `user_id`

**`site_scan_snapshots` Table:**
- **Purpose**: Stores change detection snapshots
- **Key Fields**:
  - `id` (SERIAL): Primary key
  - `task_id` (TEXT): References task UUID
  - `target_url` (TEXT): Scanned URL
  - `scan_timestamp` (TIMESTAMP): When snapshot was taken
  - `page_hashes` (JSONB): Content hashes per page type
  - `derived_signals` (JSONB): Pricing model, extracted products
- **Indexes**: `target_url, scan_timestamp DESC`

**`crawl_page_cache` Table:**
- **Purpose**: Caches crawled pages for performance
- **Key Fields**:
  - `url` (TEXT): Primary key
  - `canonical_url` (TEXT)
  - `page_type` (TEXT)
  - `content_hash` (TEXT)
  - `html` (TEXT): Full HTML (cached)
  - `status` (INTEGER): HTTP status code
  - `headers` (JSONB)
  - `expires_at` (TIMESTAMP)
- **Indexes**: `expires_at`

### 4.2 Scan Entity Structure

**Scan ID**: Generated from `task_id` or UUID (8 chars)
**Status Tracking**: Via `tasks.status` field
**Timestamps**: 
- `scan_start_timestamp`: ISO format string
- `scan_timestamp`: In report JSON
- `started_at`, `completed_at`: In tasks table

### 4.3 Scan Results Storage

**Format**: JSON wrapped in `comprehensive_site_scan` key
**Location**: `tasks.output` (JSONB column)
**Structure**: See `SiteScanReportBuilder.build()` output

**Historical Scans**: 
- **Preserved**: Yes, via `tasks` table (all completed scans)
- **Queryable**: Via `tasks` table with filters (agent_id, status, created_at)
- **Change Detection**: Compares against `site_scan_snapshots` (most recent per URL)

### 4.4 Audit Logs & Versioning

**Audit Logs**: 
- **Report Downloads**: Logged to console (not persisted) - see `logDownloadEvent()` in `tasks.go`
- **Scan Execution**: Logged to Python logger (stderr) with scan_id prefixes
- **No Database Audit Table**: Not implemented

**Versioning**:
- **Engine Version**: `ModularScanEngine.VERSION = "v2.1"`
- **Report Version**: `SiteScanReportBuilder.VERSION = "v1.0"`
- **No Schema Versioning**: Database schema changes not tracked

---

## 5. APIs & Interfaces

### 5.1 Trigger Scan API

**Endpoint**: `POST /api/agents/market_research/execute`
**Request Body**:
```json
{
  "action": "site_scan" | "comprehensive_site_scan",
  "input": {
    "topic": "https://example.com",  // or "url" field
    "business_name": "Example Inc"   // optional
  },
  "priority": "high" | "medium" | "low",  // optional
  "userId": "user123"  // optional
}
```

**Response** (Immediate):
```json
{
  "success": true,
  "data": {
    "id": "task-uuid",
    "status": "pending",
    "action": "site_scan",
    ...
  },
  "message": "Task enqueued successfully"
}
```

**Behavior**: Async (returns task immediately, execution happens in background goroutine)

### 5.2 Fetch Results API

**Endpoint**: `GET /api/tasks/:id`
**Response**:
```json
{
  "success": true,
  "data": {
    "id": "task-uuid",
    "status": "completed",
    "output": {
      "action": "site_scan",
      "response": "{...JSON string with comprehensive_site_scan...}"
    },
    ...
  }
}
```

**Note**: `output.response` is a JSON string that must be parsed to access `comprehensive_site_scan`

### 5.3 Download Report API

**Endpoint**: `GET /api/tasks/:id/report?format=pdf|json|markdown`
**Parameters**:
- `format`: Required query parameter (pdf, json, or markdown)
- Default: json if not specified

**Response**: 
- PDF: Binary PDF file (`application/pdf`)
- JSON: JSON file (`application/json`)
- Markdown: Markdown file (`text/markdown`)

**Filename Format**:
- PDF: `site_compliance_{domain}_{taskId}_{date}.pdf`
- JSON: `site_scan_{domain}_{taskId}.json`
- Markdown: `site_report_{domain}_{taskId}.md`

**Error Handling**:
- 400: Invalid format
- 404: Task not found
- 400: Task not completed
- 500: Report generation failure

### 5.4 Sync vs Async Behavior

**Scan Execution**: Fully async
- API returns task immediately
- Go backend spawns Python CLI in goroutine
- Task status updated in database as it progresses

**Report Download**: Sync (blocks until report generated)
- Calls Python CLI `download_report` action
- Returns file directly

### 5.5 Error Handling Patterns

**Scan Failures**:
- **Gating Logic**: If homepage fetch fails, returns limited report with `scan_status.status = "FAILED"`
- **Error Codes**: `DNS_FAIL`, `HTTP_403`, `SSL_ERROR`, `TIMEOUT`, `HTTP_XXX`
- **Retryable Flag**: Indicates if scan can be retried
- **Error Storage**: `tasks.error` (TEXT field)

**API Errors**:
- Standard HTTP status codes (400, 404, 500)
- Error messages in `{"success": false, "error": "..."}` format

---

## 6. UI / Dashboard Functionality

### 6.1 Available Screens

**Market Research Agent Page** (`MarketResearchAgent.tsx`):
- **Search/Input**: URL input field with "Start Research" button
- **Task History**: List of previous scans (from `tasks` table)
- **Detail View**: Tabbed interface showing scan results
- **Bulk Upload**: **Not Implemented**

### 6.2 Scan Result View Tabs

**Tab Structure** (6 tabs):
1. **Compliance Tab** (`activeTab === 'compliance'`):
   - General Compliance section: Pass/Fail, alerts, actions needed
   - Payment Terms Compliance: Pass/Fail, actions needed
   - Compliance Intelligence: Score (0-100), rating (Good/Fair/Poor), breakdown (technical, policy, trust)
   - Risk Flags: List of risk items with severity

2. **Policy Tab** (`activeTab === 'policy'`):
   - Policy Pages table: Found/Missing status, URL, "Preview" button
   - Pages shown: Privacy Policy, Terms & Conditions, Refund Policy, Shipping Policy, Contact, About, FAQ, Product

3. **MCC Tab** (`activeTab === 'mcc'`):
   - System Suggestions: Primary MCC, Secondary MCC, all matches (top 10)
   - Manual Override: **UI exists but override logic unclear from code**

4. **Product Tab** (`activeTab === 'product'`):
   - Pricing Model: Subscription, One-time, Freemium, Quote-based, Fixed Price
   - Target Audience: Enterprise/B2B, Developers, SMBs/Startups, Consumers, General
   - Extracted Products: List of product names with brief descriptions
   - Product Indicators: Has products, has pricing, has cart, ecommerce platform

5. **Business Tab** (`activeTab === 'business'`):
   - Business Name: Extracted name
   - Company Summary: Text from About page
   - Mission/Vision: Extracted statement
   - Key Offerings: Extracted offerings
   - Contact Info: Email, phone, address
   - Social Links: Facebook, Twitter, LinkedIn, Instagram, etc.
   - Source URLs: Home, About Us, Contact Us

6. **Changes Tab** (`activeTab === 'changes'`):
   - Change Detection: "Since Last Scan" indicator
   - Changes List: Type (content_change, pricing_change, product_change), severity, description
   - Last Scan Date: Timestamp of previous scan
   - **Note**: Only shows if previous snapshot exists

### 6.3 V2 Features (Gated)

**Tech Stack Card** (`TechStackCard.tsx`):
- **Gated By**: `FEATURES.ENABLE_MARKET_RESEARCH_V2_UI` flag
- **Shows**: CMS, Frameworks, Analytics, Payments, Hosting
- **Location**: Displayed in scan result view (not in a tab)

**SEO Health Card** (`SEOHealthCard.tsx`):
- **Gated By**: `FEATURES.ENABLE_MARKET_RESEARCH_V2_UI` flag
- **Shows**: SEO Score (0-100), Title, Meta Description, H1 Count, Canonical, Indexable, Sitemap, Robots.txt
- **Location**: Displayed in scan result view (not in a tab)

### 6.4 Manual Override / Custom Input

**MCC Override**: 
- UI exists (dropdown/input in MCC tab)
- **Implementation Status**: Unclear from code (may be frontend-only, not persisted)

**Custom Business Name**: 
- Supported via API input (`business_name` parameter)
- Used if provided, otherwise extracted from page

### 6.5 Download/Report Options

**Download Button** (`ReportDownloadButton.tsx`):
- **Location**: In scan result view header
- **Formats**: PDF, JSON, Markdown (dropdown menu)
- **Disabled**: If task status !== 'completed'
- **Implementation**: Calls `TaskService.downloadReport(taskId, format)`

**Report Formats**:
- **PDF**: Compliance-focused report (via `PDFBuilder`)
- **JSON**: Full scan data (via `JSONBuilder`)
- **Markdown**: Human-readable report (via `MarkdownBuilder`)

---

## 7. Scoring, Decisions & Explainability

### 7.1 Risk Scores

**Compliance Score** (0-100):
- **Calculated By**: `ComplianceIntelligence.analyze()`
- **Components**:
  - Technical (Max 30): SSL (15), Domain Age (15)
  - Policy (Max 40): Privacy (10), Terms (10), Refund (10), Contact (10)
  - Trust & Risk (Max 30): Starting at 30, penalties for restricted content, dummy text
- **Rating**: Good (≥80), Fair (≥50), Poor (<50)
- **Context-Aware**: Expectations adjusted for SaaS, FinTech, Blockchain, Content, E-commerce

**SEO Score** (0-100):
- **Calculated By**: `SEOAnalyzer.analyze_seo()`
- **Components**:
  - Title (20): Presence (10), Length 30-60 (10)
  - Meta Description (20): Presence (10), Length 120-160 (10)
  - H1 Count (15): Exactly 1 (15), >0 (5)
  - Canonical (10): Present (10)
  - Indexable (15): Not noindex (15)
  - Sitemap (10): Found (10)
  - Robots.txt (10): Found (10)

**Content Risk Score**:
- **Calculated By**: `ContentAnalyzer.analyze_content_risk()`
- **Formula**: `len(restricted_keywords) * 20 + (50 if dummy_words else 0)`
- **Note**: **Not displayed in UI** (computed but hidden)

### 7.2 Pass/Fail Logic

**General Compliance**:
- **Pass Condition**: No SSL errors, no excessive redirects
- **Fail Triggers**: `NO_HTTPS`, `SSL_ERROR`, `EXCESSIVE_REDIRECTS`
- **Stored In**: `compliance.general.pass` (boolean)

**Payment Terms Compliance**:
- **Pass Condition**: Both `returns_refund` AND `terms_condition` found
- **Fail Triggers**: Missing required policies
- **Stored In**: `compliance.payment_terms.pass` (boolean)
- **Context-Aware**: Refund policy optional for SaaS, N/A for FinTech/Blockchain

**Scan Status**:
- **Success**: Homepage returns HTTP 200, page graph populated
- **Failed**: Homepage fails (DNS, SSL, timeout, HTTP error)
- **Stored In**: `scan_status.status` ("SUCCESS" | "FAILED")

### 7.3 Explanations & Evidence

**Compliance Breakdown**:
- **Technical Breakdown**: Itemized scores (SSL, Domain Age) with status labels
- **Policy Breakdown**: Per-policy scores with expectation (required/optional/n/a) and notes
- **Trust Breakdown**: Risk flags with severity, message, penalty

**Risk Flags**:
- **Type**: `restricted_content`, `quality_risk`, `contextual_info`
- **Severity**: `critical`, `moderate`, `info`
- **Message**: Human-readable description
- **Penalty**: Points deducted from trust score

**Change Detection Explanations**:
- **Summary**: "X changes detected" or "No significant changes detected"
- **Per Change**: Type, severity, description (e.g., "Pricing model changed from Subscription to One-time")

**MCC Explanations**:
- **Confidence**: Percentage (0-100)
- **Keywords Matched**: List of matched keywords
- **Category/Subcategory**: Business classification

### 7.4 MCC Decision Making

**Method**: Keyword matching against hardcoded dictionary
**Primary MCC**: Highest confidence match
**Secondary MCC**: Second-highest confidence match
**All Matches**: Top 10 sorted by confidence

**Display**: 
- Primary and secondary shown in MCC tab
- All matches available in JSON output
- **Manual Override**: UI exists but persistence unclear

**No Blocking Logic**: MCC suggestions do not affect compliance pass/fail

---

## 8. Known Gaps & Explicit Non-Features

### 8.1 Explicitly Not Supported

**JavaScript Execution**:
- No headless browser (Puppeteer/Playwright)
- Cannot crawl SPAs (React/Vue/Angular client-side rendered)
- **Impact**: Empty content extraction for modern web apps

**Authentication**:
- Cannot access login-protected pages
- No session management or cookie handling

**Deep Crawling**:
- Limited to 20 pages maximum
- Depth limited to 2 levels
- Early exit may stop before finding all relevant pages

**Real-time Monitoring**:
- Single snapshot per scan
- No continuous monitoring or alerts
- Change detection only compares to last scan

**Full HTML Archival**:
- Only content hashes stored in snapshots
- Full HTML discarded after analysis (except in cache with TTL)

### 8.2 Partially Implemented

**Content Risk Visualization**:
- **Status**: Computed in backend (`content_risk` in report)
- **UI**: **NOT DISPLAYED** (known gap from audit)
- **Location**: Should be in Compliance or Business tab

**Crawl Metadata Display**:
- **Status**: Collected (pages_scanned, sitemap_found, robots_checked)
- **UI**: **NOT DISPLAYED**
- **Location**: Should be in scan header or metadata section

**MCC Manual Override**:
- **Status**: UI exists in MCC tab
- **Persistence**: Unclear if override is saved to database
- **API**: No explicit override endpoint found

**Audit Logging**:
- **Status**: Console logging only (not persisted)
- **Report Downloads**: Logged but not stored in database
- **Scan Execution**: Logged to stderr, not queryable

### 8.3 Logic Exists But Unused

**Crawl Cache**:
- **Status**: Implemented (`CrawlCache` class, `crawl_page_cache` table)
- **Usage**: Checked before fetching pages
- **Effectiveness**: Unclear if cache hits are common (depends on TTL and URL stability)

**Change Intelligence**:
- **Status**: `ChangeIntelligenceEngine` exists and runs
- **Output**: Stored in `change_intelligence` field
- **UI**: **NOT DISPLAYED** (only raw change detection shown)

**Business Context Classification**:
- **Status**: `BusinessContextClassifier` runs and classifies context (SaaS, FinTech, E-commerce, etc.)
- **Output**: Stored in `business_context` field
- **Usage**: Used for context-aware compliance scoring
- **UI**: **NOT DISPLAYED** (context used internally only)

---

## 9. Dependencies & External Services

### 9.1 External APIs

**RDAP (Domain Age)**:
- **Primary**: `https://rdap.org/domain/{domain}` (generic gateway)
- **Fallback**: `https://rdap.verisign.com/com/v1/domain/{domain}` (for .com)
- **Fallback**: `https://rdap.verisign.com/net/v1/domain/{domain}` (for .net)
- **Timeout**: 5 seconds
- **Failure Handling**: Swallowed (returns None, doesn't block scan)

**Sitemap/Robots.txt Checks**:
- **Method**: HTTP HEAD requests to `{base_url}/sitemap.xml` and `{base_url}/robots.txt`
- **Timeout**: 5 seconds
- **Non-blocking**: Failures don't stop scan

### 9.2 Third-Party Services

**None**: No paid third-party services (all self-hosted/open-source)

### 9.3 Internal Shared Services

**Database**:
- **PostgreSQL**: Primary data store
- **Connection**: Via `shared.db_utils.get_db_connection()` (psycopg2)

**Go Backend**:
- **Service**: `agentx-backend` (Go service on port 3001)
- **Role**: Task orchestration, API gateway, Python CLI execution
- **Communication**: Spawns Python CLI process, reads stdout JSON

**Python CLI**:
- **Location**: `backend/agents/market_research_agent/cli.py`
- **Interface**: `--input '{"action": "...", ...}'` (JSON string)
- **Output**: JSON to stdout, logs to stderr

**Shared Libraries**:
- **Base Agent**: `shared.base_agent.BaseAgent` (not used for site scans, used for other actions)
- **DB Utils**: `shared.db_utils` (PostgreSQL connection pooling)

---

## 10. Summary for Phase-2 Planning

### 10.1 What Phase-2 Must Build On Top Of

**Core Architecture**:
- ModularScanEngine V2.1 (scan_engine.py)
- CrawlOrchestrator (async parallel crawling)
- Page Graph data structure (NormalizedPageGraph)
- Report Builder (SiteScanReportBuilder)
- Change Detection (ChangeDetector with snapshots)

**Data Models**:
- `tasks` table structure (task execution tracking)
- `site_scan_snapshots` table (change detection)
- `crawl_page_cache` table (performance optimization)
- JSON report structure (`comprehensive_site_scan` wrapper)

**APIs**:
- Task execution API (`POST /api/agents/market_research/execute`)
- Task retrieval API (`GET /api/tasks/:id`)
- Report download API (`GET /api/tasks/:id/report`)

**UI Components**:
- Tabbed result view (6 tabs: Compliance, Policy, MCC, Product, Business, Changes)
- Report download button
- Task history/list view

**Analyzers**:
- Compliance Intelligence (scoring engine)
- Content Analyzer (risk detection)
- SEO Analyzer (SEO health)
- Tech Detector (stack identification)
- Business Context Classifier (context-aware logic)

### 10.2 Architectural Constraints Phase-2 Must Respect

**Execution Model**:
- Python CLI interface (`--input` JSON, stdout JSON output)
- Go backend spawns Python process (10-minute timeout)
- Async task execution (non-blocking API)

**Database Schema**:
- `tasks` table structure (cannot break existing queries)
- `site_scan_snapshots` structure (change detection depends on it)
- JSONB columns for flexibility (output, input, page_hashes, derived_signals)

**Report Structure**:
- `comprehensive_site_scan` root key (frontend expects this)
- Field names in report (UI components parse specific fields)
- Scan status structure (`scan_status.status`, `scan_status.reason`, etc.)

**Crawl Limits**:
- 20 pages maximum (hard limit in CrawlOrchestrator)
- 2 depth maximum
- Early exit logic (required + high-value pages)

**No Breaking Changes**:
- Existing scans must remain readable
- API contracts must remain backward compatible
- UI components must not break with new data

### 10.3 Known Technical Debt

**JavaScript Rendering**: Critical gap for SPAs (requires headless browser integration)
**Content Risk UI**: Data computed but not displayed
**Crawl Metadata UI**: Data collected but not shown to users
**Audit Logging**: Console-only, not persisted
**MCC Override**: UI exists but persistence unclear

---

## Appendix: Key File Locations

**Scan Engine**: `backend/agents/market_research_agent/scan_engine.py`
**Crawl Orchestrator**: `backend/agents/market_research_agent/crawlers/crawl_orchestrator.py`
**CLI Entry Point**: `backend/agents/market_research_agent/cli.py`
**Report Builder**: `backend/agents/market_research_agent/reports/site_scan_report.py`
**Analyzers**: `backend/agents/market_research_agent/analyzers/`
**Scanners**: `backend/agents/market_research_agent/scanners/`
**Frontend UI**: `src/pages/MarketResearchAgent.tsx`
**API Handlers**: `backend/internal/handlers/agents.go`, `backend/internal/handlers/tasks.go`
**Database Schema**: `database/schema.sql`

