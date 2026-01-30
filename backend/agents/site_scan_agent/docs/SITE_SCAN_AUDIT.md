# Site Scan & Crawl System Audit

**Date:** 2026-01-01
**Version:** Audit for V2.1 Scan Engine
**Scope:** End-to-end analysis of backend crawl logic, data extraction, and frontend visualization.

---

## 1️⃣ Crawl & Site Scan Architecture Overview

The site scan system follows a **modular, orchestrator-based architecture**. It separates the "fetching" concern from the "analysis" concern, joined by a unified Page Graph.

### **Execution Flow**

1.  **Entry Point**: `ModularScanEngine.comprehensive_site_scan(url)` is the main driver.
2.  **Crawl Phase**:
    *   Calls `CrawlOrchestrator.crawl(url)`.
    *   **Orchestrator** initializes `NormalizedPageGraph`.
    *   **Phase 1 (Robots)**: Checks `robots.txt` first.
    *   **Phase 2 (Seed)**: Fetches Homepage. Parsing happens immediately to find Sitemaps/Nav.
    *   **Phase 3 (Discovery)**: Extracts links via `SitemapParser` (high priority) and `NavigationDiscovery` (heuristics for header/footer links).
    *   **Phase 4 (Parallel Fetch)**: `asyncio.gather` with `aiohttp` to fetch pages up to `MAX_PAGES` (budget: 20).
    *   **Early Exit**: Stops if "Required Pages" (Privacy, Terms) AND "High Value Pages" (About, Pricing) are found.
    *   **Output**: A populated `NormalizedPageGraph` containing HTML, status codes, and metadata.
3.  **Analysis Phase** (`scan_engine.py`):
    *   Iterates through the `PageGraph`.
    *   **Policy Detection**: Maps discovered URLs to policy types (Privacy, Terms, Returns).
    *   **Tech Stack**: Runs `TechDetector` on the homepage HTML/Headers.
    *   **Business Metadata**: Extracts Name, Email, Address, Socials using `MetadataExtractor`. Uses "About Us" page from graph if available.
    *   **Product/Pricing**: Heuristic scanning for product cards and pricing models.
    *   **MCC Classification**: Keyword matching against a local MCC dictionary.
    *   **Data Enrichment**: Performs real-time RDAP lookup for domain age.
4.  **Reporting Phase**:
    *   Aggregates all data into a JSON structure via `SiteScanReportBuilder`.
    *   **Change Detection**: Compares current calculated signals/hashes against the **previous snapshot stored in Postgres** (`site_scan_snapshots`).
    *   Saves the new snapshot.
5.  **Persistence**: The final JSON report is returned to the caller (likely saved to `tasks` table), and the snapshot is saved to `site_scan_snapshots`.

### **Key Decision Points**
*   **Page Budget**: Strict cap of 20 pages prevents runaway crawls on large sites.
*   **Fallback Fetching**: If `CrawlOrchestrator` missed a key page (e.g. Pricing) but `PolicyDetector` found a link to it, the `scan_engine` performs a **synchronous fallback fetch** (blocking) to ensure coverage.
*   **Compliance Logic**: Purely existence-based (e.g., "Is there a Returns page?").

---

## 2️⃣ Data Inventory

| Data Point | Source | Collected | Stored | Used in UI | Used in Logic | Notes |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Domain Usage** | Input URL | ✅ | ✅ | ✅ | ✅ | Basis for scan |
| **Domain Vintage** | RDAP (Online Lookup) | ✅ | ✅ | ✅ (Compliance Tab) | ✅ | Flags "Low Vintage" (<1yr) |
| **SSL Status** | Socket Connection | ✅ | ✅ | ✅ (Compliance Tab) | ✅ | Flags non-HTTPS |
| **Robots.txt** | `RobotsTxtParser` | ✅ | ✅ (Metadata) | ❌ | ✅ | Used to block bad crawls |
| **Sitemap** | `SitemapParser` | ✅ | ✅ (Metadata) | ❌ | ✅ | Used for discovery priority |
| **Page Links** | `LinkExtractor` | ✅ | Transient | ❌ | ✅ | Used to find Policies |
| **Policy Pages** | `PolicyDetector` | ✅ | ✅ | ✅ (Policy Tab) | ✅ | Drives Payment Terms compliance |
| **Compliance Signals** | `scan_engine` (Logic) | ✅ | ✅ | ✅ (Compliance Tab) | ✅ | "Pass/Fail" booleans |
| **MCC Codes** | `_classify_mcc` (Text) | ✅ | ✅ | ✅ (MCC Tab) | ❌ | Suggestion only; no blocking logic |
| **Tech Stack** | `TechDetector` | ✅ | ✅ | ✅ (V2 Only) | ❌ | Informational |
| **SEO Analysis** | `SEOAnalyzer` | ✅ | ✅ | ✅ (V2 Only) | ❌ | Informational |
| **Business Name** | `MetadataExtractor` | ✅ | ✅ | ✅ (Business Tab) | ❌ | |
| **Contact Info** | Regex (Email/Phone) | ✅ | ✅ | ✅ (Business Tab) | ❌ | |
| **Content Risk** | `ContentAnalyzer` | ✅ | ✅ | **❌ (MISSING)** | ❌ | **Computed but hidden from user** |
| **Product List** | HTML Heuristics | ✅ | ✅ | ✅ (Product Tab) | ✅ | Used for Change Detection |
| **Pricing Model** | Keyword Heuristics | ✅ | ✅ | ✅ (Product Tab) | ✅ | Used for Change Detection |
| **Change Signals** | `ChangeDetector` | ✅ | ✅ (DB) | ✅ (Changes Tab) | ✅ | Drives "Severity" rating |

**Critical Observation:** `Content Risk` (gambling/adult keywords) is analyzed in the backend but **completely absent** from `MarketResearchAgent.tsx`.

---

## 3️⃣ Frontend Usage Analysis

The Frontend (`MarketResearchAgent.tsx`) is rich but has specific blind spots.

*   **Supported Tabs**:
    1.  **Compliance**: Renders General & Payment Terms checks clearly. Good visualization of alerts.
    2.  **Policies**: Lists found/missing pages with "Preview" buttons.
    3.  **MCC**: Shows System Suggestions + Manual Override flow.
    4.  **Product**: Shows Pricing Model, Audience, and extracted items.
    5.  **Business**: Shows Name, Summary, Mission, Contact Info.
    6.  **Changes**: Diff view for change detection.
*   **V2 Features**: `TechStackCard` and `SEOHealthCard` are gated behind `FEATURES.ENABLE_MARKET_RESEARCH_V2_UI`.
*   **Blind Spots**:
    *   **Content Risk**: As noted, risk data is in the JSON but not rendered.
    *   **Crawl Stats**: The user doesn't see "Pages Scanned" or "Sitemap Found" status. The scan feels like a "black box".
    *   **Raw Data Fallback**: If the complicated parsing fails, it dumps raw JSON, which is a poor experience.

---

## 4️⃣ Efficiency & Performance Evaluation

*   **Concurrency**: Excellent. `CrawlOrchestrator` uses `asyncio.Semaphore(10)` to parallelize fetches. This is significantly faster than sequential crawling.
*   **Caching**: `CrawlCache` is implemented (memory/file based?). If it's effectively persistant, it saves massive time.
*   **Early Exit**: The logic to stop after finding "Required Pages" is efficient for *compliance* checks but might be detrimental for *comprehensive* product discovery (e.g., stopping before finding a deep product catalogue).
*   **Redundancy**:
    *   **Risk**: The `scan_engine` fallback logic (lines 228, 308, 324) initiates *new* sync `requests` fetches if pages aren't in the graph. If `CrawlOrchestrator` missed them (due to budget), this is good. If they were missed due to bugs, this masks the bug with a performance penalty.
*   **Bottlenecks**:
    *   **RDAP**: Synchronous blocking HTTP call. If RDAP hangs (timeout 5s), the whole scan hangs for 5s.
    *   **SSL Check**: Synchronous blocking socket call.

---

## 5️⃣ Correctness & Coverage Assessment

*   **Targeting**: `NavigationDiscovery` is smart (Primary vs Secondary nav). It focuses on high-value links. **Verdict: Good.**
*   **False Negatives**:
    *   **SPA/JS Sites**: The crawler uses `aiohttp` + `BeautifulSoup`. It **CANNOT** execute JavaScript.
    *   **Impact**: React/Vue sites that load content dynamically will likely return empty bodies or just `<div id="root"></div>`. This is a **major correctness gap** for modern web apps. The "Tech Stack" detector might find "React", but the "Content Analyzer" will see empty text.
*   **Compliance Logic**:
    *   Checks for *existence* of a "Refund Policy" link. It does **not** validate if the policy text actually *contains* a refund offer. A blank page titled "Refunds" passes.
    *   **Verdict**: Acceptable for V1/MVP, but naive for high-risk operations.
*   **MCC Classification**:
    *   Relies entirely on matching keywords in `page_text`. Use of generic terms ("services", "consulting") can lead to noisy "Professional Services" classification.

---

## 6️⃣ Gaps & Opportunities

### **Low-Risk Improvements (Quick Wins)**
1.  **Visualize Content Risk**: Add a "Risk Analysis" section to the Compliance or Business tab in UI.
2.  **Expose Crawl Metadata**: Show "Pages Scanned: 15/20", "Sitemap: Found" in the UI header to build user trust.
3.  **Async RDAP/SSL**: Move synchronous checks into async wrappers to run parallel with the crawl, saving ~3-5 seconds per scan.

### **Medium-Risk Improvements**
1.  **JS Rendering Service**: Integrate a headless browser (Puppeteer/Playwright) service for the `CrawlOrchestrator` to handle SPAs. This is critical for coverage.
2.  **Smart Compliance**: Instead of just checking if the page *exists*, use LLM or Keyword density on the *content* of the policy page to verify it's legitimate.

### **Out-of-Scope (Future)**
*   **Full Site Archiving**: Storing the full HTML of every scan version (storage cost).
*   **Login-based Crawling**: Handling auth walls.

---

## 7️⃣ Final Verdict

| Metric | Rating | Rationale |
| :--- | :---: | :--- |
| **Architecture** | **9/10** | Modular, async, well-separated concerns. |
| **Code Quality** | **8/10** | Clean, typed, documented. Good error handling. |
| **Performance** | **8/10** | Parallel fetching is great. RDAP blocking is a minor drag. |
| **Coverage** | **6/10** | **Critical Weakness:** No JS execution means massive blind spot for modern apps. |
| **UI Integration** | **7/10** | Good visual polish, but missing "Risk" data and operational stats. |

**Overall Maturity: 7.5/10**

**Conclusion:**
The system is **production-ready for static/SSR websites** and effectively automates standard compliance checks (KYB). It mimics a Senior Analyst quickly clicking through a site. However, it is **not reliable for single-page applications (SPAs)** due to the lack of JS execution.

**Recommendation:**
Trust it for "L1 Sifting" (filtering out obvious passes/fails). For "Deep Diligence" on high-risk merchants, manual review or a headless-browser upgrade is required.
