# V2 Promotion Readiness Guide

**Status**: ✅ READY FOR SOFT ROLLOUT  
**Recommended Path**: `v1` → `dual` (24hrs) → `v2`  
**Default Engine**: Keep as `v1` for now

---

## Current State

✅ V2 fully implemented and tested  
✅ 100% backward compatible  
✅ All validation tests passed (5/5 sites)  
✅ Frontend compatibility verified  
✅ Instant rollback available  
✅ Documentation complete

---

## When to Promote to V2

### ✅ Safe to Enable V2 When:

1. **Dual mode runs cleanly for 24-48 hours**
   - No comparison errors logged
   - No missing required fields
   - No unexpected type mismatches

2. **Production metrics are stable**
   - Error rate < 1%
   - Average scan time ≤ V1 baseline
   - No worker crashes

3. **Frontend handles new fields gracefully**
   - UI displays correctly with V2 responses
   - No console errors
   - New fields either displayed or ignored

4. **Rollback procedure tested**
   - Confirmed switching back to v1 works
   - Worker restarts successfully
   - No data corruption

---

## Promotion Steps

### Phase 1: Dual Mode Monitoring (Current → +24hrs)

```bash
# Enable dual mode
export MARKET_SCAN_ENGINE=dual

# Restart worker_v2.py
# (or update environment in deployment)
```

**Monitor**:
- Worker logs for `[DUAL]`, `[COMPARE]`, `[V2_WARN]` tags
- Comparison results (should show compatible=true)
- Any missing fields or unexpected nulls
- Performance metrics (scan duration)

**Success Criteria**:
- 95%+ scans show "compatible=true"
- No critical errors for 24+ hours
- Performance within acceptable range

---

### Phase 2: Soft V2 Rollout (+24hrs → +72hrs)

```bash
# Switch to V2-only mode
export MARKET_SCAN_ENGINE=v2

# Restart worker_v2.py
```

**Monitor**:
- Error rates (should be ≤ V1 baseline)
- Frontend user reports
- Missing field warnings  
- Performance improvements

**Success Criteria**:
- Error rate < 1%
- No user complaints about missing data
- Scan times 10-20% faster than V1

---

### Phase 3: Make V2 Default (+72hrs → production)

**Update Default in Code**:

```python
# In worker_v2.py (line ~50)
SCAN_ENGINE_MODE = os.getenv("MARKET_SCAN_ENGINE", "v2").lower()  # Changed from "v1"
```

**Or in deployment config**:
```yaml
# docker-compose.yml or deployment manifest
environment:
  - MARKET_SCAN_ENGINE=v2
```

**Success Criteria**:
- V2 stable for 1 week+
- No major issues reported
- Team confident in V2 reliability

---

## Red Flags (DO NOT PROMOTE)

### 🚨 Stop Promotion If:

❌ **Comparison shows incompatible results**
   - Missing required fields in V2
   - Type mismatches
   - Core logic differences

❌ **Error rate increases**
   - > 5% scans failing
   - Worker crashes
   - Database errors

❌ **Frontend breaks**
   - UI rendering errors
   - Null reference exceptions
   - Missing data displays

❌ **Performance degrades**
   - Scan times > 2x slower
   - Memory leaks
   - Timeout increases

---

## Rollback Procedure

If issues arise at any phase:

### Immediate Rollback

```bash
# Instant switch back to V1
export MARKET_SCAN_ENGINE=v1

# Restart worker (automatic in some deployments)
# Worker will use legacy engine immediately
```

**Verify**:
- Check logs show `[V1]` tags
- Confirm scans completing successfully
- Monitor for ~1 hour

### Emergency Rollback

If worker won't start with V2:

1. **Switch to V1-only worker**:
   ```bash
   # Use original worker.py
   python3 agents/market_research_agent/worker.py
   ```

2. **Investigate offline**:
   - Check logs for errors
   - Run validation tests
   - Fix issues before re-enabling V2

---

## Monitoring Dashboard

### Key Metrics to Track

| Metric | V1 Baseline | V2 Target | Alert If |
|--------|-------------|-----------|----------|
| Success Rate | 98%+ | ≥ 98% | < 95% |
| Avg Scan Time | 5.0s | ≤ 5.0s | > 6.0s |
| Error Rate | < 2% | < 2% | > 5% |
| Missing Fields | 0 | 0 | > 0 |
| Worker Uptime | 99%+ | 99%+ | < 99% |

### Log Patterns to Watch

**Good Signs** ✅:
```
[V2_OK] All required fields present
[V2_OK] No unexpected nulls
[V2_OK] Feature 'tech_stack' detected
[COMPARE] compatible=True
```

**Warning Signs** ⚠️:
```
[V2_WARN] Missing required fields: [...]
[V2_WARN] Unexpected nulls in: [...]
[COMPARE] compatible=False
```

**Critical Issues** 🚨:
```
[ERROR] V2 scan failed: ...
[ERROR] Comparison failed: ...
CRITICAL ERROR processing task
```

---

## Checklist Before Promoting

### Before Enabling Dual Mode

- [ ] worker_v2.py tested locally
- [ ] Validation script passed (5/5 sites)
- [ ] Documentation reviewed
- [ ] Team notified of dual mode start
- [ ] Rollback procedure confirmed

### Before Enabling V2-Only

- [ ] Dual mode ran for 24+ hours
- [ ] No compatibility warnings
- [ ] Performance metrics acceptable
- [ ] Frontend tested with V2 responses
- [ ] Stakeholders informed

### Before Making V2 Default

- [ ] V2-only ran for 72+ hours
- [ ] No user complaints
- [ ] Error rate within target
- [ ] New features working as expected
- [ ] Team trained on V2 features

---

## Communication Plan

### Who to Notify

1. **Engineering Team**: Before each phase
2. **Product Team**: After dual mode, before V2-only
3. **Support Team**: After V2-only stable
4. **Users**: After V2 default (release notes)

### Message Templates

**Phase 1 (Dual Mode)**:
> We're testing an upgraded scanning engine alongside the current system. No user-facing changes expected. Monitoring for 24-48 hours.

**Phase 2 (V2-Only)**:
> Scanning engine upgraded to V2. New features include tech stack detection and SEO analysis. Please report any issues.

**Phase 3 (V2 Default)**:
> V2 engine is now the default. Benefits: 20% faster scans, enhanced data. Rollback available if needed.

---

## Success Definition

V2 is considered **production-ready** when:

✅ Dual mode compatibility: 95%+ for 24 hours  
✅ V2-only error rate: < 2% for 72 hours  
✅ Frontend reports: No critical bugs  
✅ Performance: ≤ V1 baseline  
✅ Team confidence: Comfortable with rollback procedure

---

## Timeline Estimate

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Dual Mode | 24-48 hours | 2 days |
| V2-Only Test | 48-72 hours | 5 days |
| Observation | 7+ days | 12 days |
| **Total** | **~2 weeks** | **Safe rollout** |

Faster rollout possible if metrics are excellent, but **2 weeks recommended** for production safety.

---

## Current Recommendation

### Next Action: **Enable Dual Mode**

```bash
# In your deployment environment
export MARKET_SCAN_ENGINE=dual

# Then restart worker_v2.py
```

### Wait Condition: **24-48 hours of clean dual mode**

### Then: **Re-evaluate for V2-only promotion**

---

## Questions?

- **Technical**: Review [frontend_compatibility.md](frontend_compatibility.md)
- **Validation**: Check [validation_results.json](../validation_results.json)
- **Contract**: See [v2_output_contract.md](v2_output_contract.md)
- **Setup**: Read [V2_README.md](../V2_README.md)

---

**Last Updated**: 2025-12-28  
**Promotion Status**: Awaiting dual mode validation  
**Default Engine**: v1 (safe, keep until dual mode validates)
