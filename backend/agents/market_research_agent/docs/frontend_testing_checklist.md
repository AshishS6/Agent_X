# Frontend Testing Checklist

**Purpose**: Verify V2 backend compatibility with existing frontend (zero visual changes expected)

**Mode**: Dual (V1 output, V2 logging)  
**Risk Level**: Minimal (V1 responses unchanged)

---

## Pre-Flight Check

- [ ] Current worker.py is running (will be replaced)
- [ ] Backend is running (`npm run dev`)
- [ ] Frontend is running (`npm run dev`)
- [ ] Can access Market Research UI

---

## Step 1: Enable Dual Mode Worker

### Kill Current Worker

```bash
# Find current worker process
ps aux | grep "worker.py"

# Kill it (or use the terminal where it's running)
# Ctrl+C in the worker terminal
```

### Start V2 Worker in Dual Mode

```bash
# Set dual mode
export MARKET_SCAN_ENGINE=dual

# Start worker_v2.py
cd /Users/ashish/Agent_X
python3 agents/market_research_agent/worker_v2.py
```

### Verify Startup

Look for in logs:
```
✅ Market Research Agent Worker V2 started
✅ 🔧 Scan Engine Mode: dual
✅ V2 Modular Engine initialized
✅ Scan Comparator initialized for dual mode
```

---

## Step 2: Test Existing Reports

### Navigate to Market Research Dashboard

1. Open frontend: `http://localhost:3000` (or your port)
2. Go to Market Research section
3. View existing scan reports

### Check:

- [ ] Existing reports display correctly
- [ ] No console errors
- [ ] All sections render (compliance, policies, MCC, etc.)
- [ ] No "undefined" or "null" errors

**Expected**: Everything looks normal ✅

---

## Step 3: Trigger New Scan (Critical Test)

### Start a New Scan

1. Click "New Site Scan" or equivalent
2. Enter test URL: `https://www.shopify.com`
3. Submit scan
4. Wait for completion

### Monitor:

**Backend Logs** (worker_v2.py terminal):
- [ ] See `[DUAL] Running V1 engine`
- [ ] See `[DUAL] Running V2 engine`
- [ ] See `[COMPARE] Comparison: compatible=True`
- [ ] No `[V2_WARN]` messages

**Frontend**:
- [ ] Scan completes successfully
- [ ] Results display normally
- [ ] **No visual differences** from before
- [ ] No console errors

---

## Step 4: Network Inspection (Proof of Compatibility)

### Open DevTools

1. F12 or right-click → Inspect
2. Go to Network tab
3. Filter: `XHR` or `Fetch`

### Trigger New Scan

Scan: `https://www.stripe.com`

### Find API Response

Look for request to backend API (e.g., `/api/tasks/...` or similar)

### Verify Response Structure

Check JSON response:

```json
{
  "comprehensive_site_scan": {
    "url": "...",
    "compliance": { ... },
    "policy_details": { ... },
    "tech_stack": { ... },      // ← NEW (V2-only)
    "seo_analysis": { ... }      // ← NEW (V2-only)
  }
}
```

#### Checklist:

- [ ] Root key is `comprehensive_site_scan`
- [ ] All original fields present
- [ ] New fields (`tech_stack`, `seo_analysis`) present
- [ ] No fields are undefined/null unexpectedly

**Expected**: Old + new fields coexist ✅

---

## Step 5: Console Check (No Errors)

### Open Console Tab

1. DevTools → Console
2. Clear console
3. Trigger another scan: `https://www.google.com`

### Watch For:

❌ **Red errors** (fail)  
⚠️ **Yellow warnings** about missing fields (fail)  
✅ **Clean or normal logs** (pass)

#### Checklist:

- [ ] No "Cannot read property of undefined"
- [ ] No "Missing required field" errors
- [ ] No rendering failures
- [ ] UI updates smoothly

---

## Step 6: Edge Cases

### Test Multiple Scans

Run 3 scans back-to-back:
1. `https://www.amazon.com`
2. `https://www.opencapital.co.in`
3. `https://example.com`

### Verify:

- [ ] All complete successfully
- [ ] All display correctly
- [ ] Worker logs show dual mode for each
- [ ] No memory leaks (check DevTools Memory tab)

---

## Step 7: Review Backend Logs

### Check Worker Terminal

Look for comparison summaries:

```
[DUAL] Comparison: compatible=True, differences=0
[COMPARE] ✅ V2 is backward compatible with V1
[COMPARE] ✅ Core fields match perfectly
[COMPARE] ✨ V2 feature 'tech_stack' detected
[COMPARE] ✨ V2 feature 'seo_analysis' detected
```

### Red Flags (Should NOT see):

❌ `[V2_WARN] Missing required fields`  
❌ `[COMPARE] compatible=False`  
❌ `[ERROR]` messages

---

## Step 8: Optional Safety Assertion

### Add Frontend Validation (Optional)

**File**: Where you handle scan results (e.g., `SiteScanResults.tsx`)

**Add before rendering**:

```typescript
// Non-blocking safety check
if (!data?.comprehensive_site_scan) {
  console.warn('[V2-Safety] Unexpected scan format', data);
  // Continue rendering anyway (don't break UI)
}
```

**Purpose**: Early warning if format changes  
**Risk**: Zero (doesn't block rendering)

---

## Pass Criteria

Frontend testing is **COMPLETE** when:

✅ **All checklist items passed**  
✅ **No console errors during scans**  
✅ **No visual regressions**  
✅ **Network shows V2 fields present**  
✅ **Backend logs show clean comparisons**  
✅ **Worker runs for 1+ hours without issues**

---

## If Something Fails

### Immediate Rollback

```bash
# Kill worker_v2.py
# Ctrl+C in terminal

# Restart original worker
python3 agents/market_research_agent/worker.py
```

**Recovery time**: < 30 seconds

### Report Issue

Document:
- What action triggered it
- Console error message
- Backend log snippet
- Network response (if relevant)

---

## After Testing Complete

### If All Tests Pass:

1. **Leave dual mode running** for 24-48 hours
2. Monitor backend logs periodically
3. Check for any user reports
4. After 48 hours → evaluate v2-only promotion

### If Any Test Fails:

1. **Rollback to worker.py immediately**
2. Document failure
3. Fix issue in V2
4. Re-run validation tests
5. Don't proceed until 100% pass rate

---

## Timeline

- **Now**: Start dual mode worker
- **+15 min**: Manual testing (this checklist)
- **+1 hour**: Verify stability
- **+24 hours**: Check logs for issues
- **+48 hours**: Evaluate v2-only promotion

---

## Questions?

- **Backend not starting?** Check Redis is running
- **Frontend errors?** Check browser console
- **Comparison fails?** Check backend logs for details
- **Unsure?** Rollback and investigate

---

**Testing started**: [Record timestamp when you begin]  
**Testing completed**: [Record timestamp when done]  
**Result**: [PASS / FAIL / NEEDS INVESTIGATION]
