import json
import hashlib
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _stable_hash(obj: Any) -> str:
    """
    Best-effort determinism check:
    hash only stable fields; ignore timestamps and transient metadata.
    """
    dumped = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def _get_scan_payload(scan_json: Dict[str, Any]) -> Dict[str, Any]:
    return scan_json.get("comprehensive_site_scan", scan_json)


def _extract_policy_found(scan: Dict[str, Any], policy_key: str) -> Optional[bool]:
    policies = scan.get("policy_details", {}) or {}
    item = policies.get(policy_key, {}) if isinstance(policies, dict) else {}
    if "found" in item:
        return bool(item.get("found"))
    return None


def _extract_mcc_primary(scan: Dict[str, Any]) -> Tuple[Optional[str], float]:
    mcc = scan.get("mcc_codes", {}) or {}
    primary = mcc.get("primary_mcc") or {}
    if not isinstance(primary, dict):
        return None, 0.0
    return primary.get("mcc_code") or primary.get("code"), float(primary.get("confidence") or 0.0)


def _extract_content_risk(scan: Dict[str, Any]) -> List[Dict[str, Any]]:
    cr = scan.get("content_risk", {}) or {}
    items = cr.get("restricted_keywords_found", []) or []
    return items if isinstance(items, list) else []


def _count_critical_flags(items: List[Dict[str, Any]]) -> int:
    critical = 0
    for it in items:
        ev = it.get("evidence", {}) if isinstance(it.get("evidence"), dict) else {}
        if ev.get("severity") == "critical":
            critical += 1
    return critical


def main():
    import os
    from pathlib import Path

    # Ensure repo root is on sys.path so `backend.*` imports work when run as a script
    repo_root = Path(__file__).resolve().parents[4]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    # Local import to avoid forcing scan deps when just reading files
    from backend.agents.market_research_agent.scan_engine import ModularScanEngine  # type: ignore

    here = Path(__file__).parent
    gold_path = here / "goldset.json"
    gold = json.loads(gold_path.read_text(encoding="utf-8"))

    sites = gold.get("sites", [])
    if not sites:
        print("No sites in goldset.json")
        return

    engine = ModularScanEngine(logger=None)

    policy_total = 0
    policy_correct = 0
    mcc_total = 0
    mcc_correct = 0
    risk_total = 0
    risk_fp_ok = 0
    determinism_total = 0
    determinism_ok = 0

    for site in sites:
        url = site.get("url")
        business_name = site.get("business_name", "") or ""
        expect = site.get("expect", {}) or {}

        if not url:
            continue

        print(f"\n=== Scanning: {url} ===")
        out1 = engine.comprehensive_site_scan(url, business_name, task_id=None)
        scan1 = json.loads(out1)
        payload1 = _get_scan_payload(scan1)

        # Determinism check (run twice)
        out2 = engine.comprehensive_site_scan(url, business_name, task_id=None)
        scan2 = json.loads(out2)
        payload2 = _get_scan_payload(scan2)

        # Hash stable sub-sections
        stable1 = {
            "policy_details": payload1.get("policy_details"),
            "mcc_codes": payload1.get("mcc_codes"),
            "content_risk": payload1.get("content_risk"),
            "crawl_summary": payload1.get("crawl_summary"),
        }
        stable2 = {
            "policy_details": payload2.get("policy_details"),
            "mcc_codes": payload2.get("mcc_codes"),
            "content_risk": payload2.get("content_risk"),
            "crawl_summary": payload2.get("crawl_summary"),
        }
        determinism_total += 1
        if _stable_hash(stable1) == _stable_hash(stable2):
            determinism_ok += 1

        # Policy accuracy
        exp_policies = (expect.get("policies") or {})
        for policy_key, exp_val in exp_policies.items():
            if exp_val not in (True, False):
                continue
            policy_total += 1
            got = _extract_policy_found(payload1, policy_key)
            if got is not None and got == exp_val:
                policy_correct += 1

        # MCC primary (very simple)
        exp_mcc = expect.get("mcc_primary") or {}
        exp_code = exp_mcc.get("code")
        exp_min_conf = float(exp_mcc.get("min_confidence") or 0.0)
        if exp_code and exp_code != "unknown":
            mcc_total += 1
            got_code, got_conf = _extract_mcc_primary(payload1)
            if got_code == exp_code and got_conf >= exp_min_conf:
                mcc_correct += 1

        # Content risk FP guardrail for critical categories
        exp_cr = expect.get("content_risk") or {}
        max_crit_fp = exp_cr.get("critical_false_positive_categories_max")
        if isinstance(max_crit_fp, int):
            risk_total += 1
            items = _extract_content_risk(payload1)
            crit = _count_critical_flags(items)
            if crit <= max_crit_fp:
                risk_fp_ok += 1

    # Report
    print("\n=== Gold Set Summary ===")
    if policy_total:
        print(f"Policy presence accuracy: {policy_correct}/{policy_total} ({policy_correct/policy_total:.2%})")
    else:
        print("Policy presence accuracy: n/a (no labeled policies)")

    if mcc_total:
        print(f"MCC primary match rate: {mcc_correct}/{mcc_total} ({mcc_correct/mcc_total:.2%})")
    else:
        print("MCC primary match rate: n/a (no labeled MCCs)")

    if risk_total:
        print(f"Content risk critical FP guardrail pass: {risk_fp_ok}/{risk_total} ({risk_fp_ok/risk_total:.2%})")
    else:
        print("Content risk critical FP guardrail: n/a (no labeled thresholds)")

    print(f"Determinism (stable sections): {determinism_ok}/{determinism_total} ({determinism_ok/determinism_total:.2%})")


if __name__ == "__main__":
    main()

