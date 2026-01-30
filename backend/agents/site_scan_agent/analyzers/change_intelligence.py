"""
Change Intelligence Engine (Phase D)
Converts raw change detection signals into actionable business intelligence.
Assigns severity, business impact, and recommended actions.
"""

import logging
from typing import Dict, List, Any, Optional

class ChangeIntelligenceEngine:
    """
    Analyzes detected changes and enriches them with business intelligence.
    """
    
    # -------------------------------------------------------------------------
    # CONFIGURATION & RULES
    # -------------------------------------------------------------------------
    
    # Severity Levels
    SEVERITY_CRITICAL = "critical"
    SEVERITY_MODERATE = "moderate"
    SEVERITY_MINOR = "minor"
    SEVERITY_NONE = "none"

    # Canonical Change Rules
    # Maps specific change types (or patterns) to Intelligence Metadata
    CHANGE_RULES = {
        # --- Critical Changes ---
        "privacy_policy_changed": {
            "severity": SEVERITY_CRITICAL,
            "business_impact": "Legal & compliance risk exposure",
            "recommended_action": "Re-run legal compliance review immediately",
            "confidence": 1.0 # Deterministic
        },
        "terms_conditions_changed": {
            "severity": SEVERITY_CRITICAL,
            "business_impact": "Contractual terms update risk",
            "recommended_action": "Review updated terms for liability shifts",
            "confidence": 1.0
        },
        "refund_policy_changed": {
            "severity": SEVERITY_CRITICAL,
            "business_impact": "Consumer protection & regulatory impact",
            "recommended_action": "Verify alignment with consumer refund laws",
            "confidence": 0.95
        },
        "pricing_model_changed": {
            "severity": SEVERITY_CRITICAL,
            "business_impact": "Fundamental revenue model shift detected",
            "recommended_action": "Notify sales leadership & re-evaluate commercial strategy",
            "confidence": 0.95
        },
        "pricing_change": { # Mapping from ChangeDetector output
            "severity": SEVERITY_CRITICAL, 
            "business_impact": "Revenue model updated",
            "recommended_action": "Notify sales & re-evaluate onboarding",
             "confidence": 0.95
        },
        "payment_method_removed": {
            "severity": SEVERITY_CRITICAL,
            "business_impact": "Potential conversion block & business continuity risk",
            "recommended_action": "Investigate payment gateway status",
            "confidence": 0.90
        },

        # --- Moderate Changes ---
        "product_page_changed": {
             "severity": SEVERITY_MODERATE,
             "business_impact": "Core offering scope or messaging evolution",
             "recommended_action": "Review product consistency with marketing materials",
             "confidence": 0.85
        },
        "product_change": { # Mapping from ChangeDetector output
             "severity": SEVERITY_MODERATE,
             "business_impact": "Product portfolio count changed",
             "recommended_action": "Check for new product launches or discontinuations",
             "confidence": 0.90
        },
        "checkout_flow_changed": {
            "severity": SEVERITY_MODERATE,
            "business_impact": "Direct impact on conversion rates",
            "recommended_action": "Test checkout flow for friction",
            "confidence": 0.80
        },
        "seo_score_drop": {
            "severity": SEVERITY_MODERATE,
            "business_impact": "Reduced organic visibility and lead flow",
            "recommended_action": "Schedule technical SEO audit",
            "confidence": 0.85
        },
        
        # --- Minor Changes ---
        "homepage_copy_changed": {
            "severity": SEVERITY_MINOR,
            "business_impact": "Routine marketing refresh",
            "recommended_action": "No immediate action required",
            "confidence": 0.70
        },
        "metadata_update": {
            "severity": SEVERITY_MINOR,
            "business_impact": "Low-level metadata adjustment",
            "recommended_action": "Monitor for long-term SEO trend",
             "confidence": 0.60
        },
        "content_change": { # generic content change from ChangeDetector
            "severity": SEVERITY_MINOR, # Default to minor if specific type not matched
            "business_impact": "General content update",
            "recommended_action": "Review changes if convenient",
            "confidence": 0.60
        }
    }
    
    # Specific Mapping for 'content_change' based on page type if available
    PAGE_TYPE_SEVERITY_MAP = {
        "privacy_policy": "privacy_policy_changed",
        "terms_conditions": "terms_conditions_changed",
        "refund_policy": "refund_policy_changed",
        "pricing": "pricing_model_changed", # Being aggressive here as pricing page change usually matters
        "product": "product_page_changed",
        "home": "homepage_copy_changed"
    }

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def analyze_intelligence(self, change_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point: Converts a raw Change Report into an Intelligence Report.
        
        Args:
            change_report: Output from ChangeDetector.compare()
            
        Returns:
            Dict containing the 'change_intelligence' block
        """
        if not change_report or not change_report.get("since_last_scan"):
             return {
                "since_last_scan": False,
                "summary": "No significant changes detected",
                "overall_severity": self.SEVERITY_NONE,
                "changes": []
            }
            
        raw_changes = change_report.get("changes", [])
        enriched_changes = []
        severity_counts = {
            self.SEVERITY_CRITICAL: 0,
            self.SEVERITY_MODERATE: 0,
            self.SEVERITY_MINOR: 0
        }
        
        for change in raw_changes:
            enriched = self._enrich_change(change)
            enriched_changes.append(enriched)
            
            # Count severity
            sev = enriched.get("severity", self.SEVERITY_MINOR)
            if sev in severity_counts:
                severity_counts[sev] += 1
                
        # Determine Overall Severity
        overall_severity = self.SEVERITY_MINOR
        if severity_counts[self.SEVERITY_CRITICAL] > 0:
            overall_severity = self.SEVERITY_CRITICAL
        elif severity_counts[self.SEVERITY_MODERATE] > 0:
            overall_severity = self.SEVERITY_MODERATE
            
        # Generate Summary
        summary = self._generate_summary(overall_severity, severity_counts, enriched_changes)
        
        # Calculate Aggregated Confidence (Average of change confidences)
        avg_confidence = 0.0
        if enriched_changes:
            total_conf = sum(c.get("confidence", 0.0) for c in enriched_changes)
            avg_confidence = round(total_conf / len(enriched_changes), 2)
        else:
            avg_confidence = 1.0 # High confidence that nothing changed if list empty (but handled by early exit)

        return {
            "since_last_scan": True,
            "overall_severity": overall_severity,
            "summary": summary,
            "recommended_action": self._get_overall_recommendation(overall_severity, enriched_changes),
            "confidence": avg_confidence,
            "changes": enriched_changes
        }

    def _enrich_change(self, change: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply rules to a single raw change to add intelligence fields.
        """
        c_type = change.get("type")
        description = change.get("description", "")
        
        # Default Intelligence
        intelligence = {
            "severity": self.SEVERITY_MINOR,
            "business_impact": "Unclassified change detected",
            "recommended_action": "Review manually",
            "confidence": 0.5
        }
        
        # 1. Special Handling for 'content_change' to infer specific types
        if c_type == "content_change":
            matched_rule = None
            for page_key, rule_key in self.PAGE_TYPE_SEVERITY_MAP.items():
                check_str = page_key.replace('_', ' ').title()
                if check_str in description:
                    if rule_key in self.CHANGE_RULES:
                        matched_rule = self.CHANGE_RULES[rule_key]
                        break
            
            if matched_rule:
                intelligence = matched_rule.copy()
            elif c_type in self.CHANGE_RULES:
                 # Fallback to generic content change rule
                 intelligence = self.CHANGE_RULES[c_type].copy()

        # 2. Direct Type Match (for other types)
        elif c_type in self.CHANGE_RULES:
            intelligence = self.CHANGE_RULES[c_type].copy()

        # Merge intelligence into change object (preserving original fields, intelligence overwrites conflicts if any)
        # Per PRD V2.1.1: Preserve evidence fields (what_changed, where, why_it_matters, evidence)
        # We want the output to be the original change + new fields
        enriched = change.copy()
        enriched.update(intelligence)
        
        # Ensure evidence fields are preserved (from ChangeDetector)
        evidence_fields = ["what_changed", "where", "why_it_matters", "evidence", "signal_type"]
        for field in evidence_fields:
            if field in change and field not in enriched:
                enriched[field] = change[field]
        
        return enriched

    def _generate_summary(self, overall_severity: str, counts: Dict, changes: List[Dict]) -> str:
        """
        Generate human-readable summary string.
        """
        if not changes:
            return "No changes detected."
            
        count_str = []
        if counts[self.SEVERITY_CRITICAL] > 0:
            count_str.append(f"{counts[self.SEVERITY_CRITICAL]} critical")
        if counts[self.SEVERITY_MODERATE] > 0:
            count_str.append(f"{counts[self.SEVERITY_MODERATE]} moderate")
        if counts[self.SEVERITY_MINOR] > 0:
            count_str.append(f"{counts[self.SEVERITY_MINOR]} minor")
            
        counts_summary = ", ".join(count_str)
        
        # Contextual suffix
        suffix = ""
        if overall_severity == self.SEVERITY_CRITICAL:
            # Find the first critical change to mention
            crit_change = next((c for c in changes if c["severity"] == self.SEVERITY_CRITICAL), None)
            if crit_change:
                desc = crit_change.get("description", "Critical update")
                suffix = f" — dominated by {desc}"
        elif overall_severity == self.SEVERITY_MODERATE:
             mod_change = next((c for c in changes if c["severity"] == self.SEVERITY_MODERATE), None)
             if mod_change:
                desc = mod_change.get("description", "Moderate update")
                suffix = f" — notably {desc}"
                
        return f"Detected {counts_summary} changes{suffix}"

    def _get_overall_recommendation(self, overall_severity: str, changes: List[Dict]) -> str:
        """
        Top-level action based on highest severity.
        """
        if overall_severity == self.SEVERITY_CRITICAL:
            # Return the action of the first critical change
            crit = next((c for c in changes if c["severity"] == self.SEVERITY_CRITICAL), None)
            return crit.get("recommended_action", "Immediate review required")
            
        if overall_severity == self.SEVERITY_MODERATE:
            mod = next((c for c in changes if c["severity"] == self.SEVERITY_MODERATE), None)
            return mod.get("recommended_action", "Review impact on operations")
            
        return "No immediate action required"
