## SiteScan Gold Set Validation (V2.1.1+)

This folder provides a **lightweight, deterministic validation harness** for SiteScan.

### What it validates
- **Policy presence accuracy** (against a curated gold set you maintain)
- **MCC primary suggestion quality** (basic match/threshold checks)
- **Content risk false positives** (for critical categories)
- **Determinism**: same input + same version ⇒ same output (best-effort)

### Files
- `goldset.json`: list of sites + expected outcomes (you own the truth data here)
- `validate_goldset.py`: runs scans and prints summary metrics

### How to use
1. Add/curate sites in `goldset.json` (target ≥30 sites).
2. Ensure runtime deps are installed (including Playwright if JS rendering is enabled):
   - `pip install playwright`
   - `playwright install`
3. Run:
   - `python backend/agents/market_research_agent/validation/validate_goldset.py`

### Notes / Caveats
- This harness is intentionally simple and does not require DB access.
- Network variability can affect timing and JS-rendered pages. Determinism checks focus on **stable, evidence-based fields**.

