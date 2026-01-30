"""
Compliance Intelligence Engine
Calculates unified Compliance Score and Risk Flags based on technical, policy, and content signals.
Phase E.1: Context-Aware Complinace
Per PRD V2.1.1: Compliance score is Advisory, must show breakdown, each penalty references specific signal.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from analyzers.context_classifier import BusinessContextClassifier
from analyzers.signal_classifier import SignalClassifier

class ComplianceIntelligence:
    """
    Analyzes site data to produce a 0-100 Compliance Score and Risk Report.
    Adheres to context-specific expectations.
    
    Scoring Model (Total 100):
    - Technical (Max 30): SSL, Domain Age
    - Policies (Max 40): Privacy, Terms, Refund, Contact (Graded based on Context)
    - Trust & Risk (Max 30): Penalty-based model starting at 30 (Context conditioned)
    """
    
    def __init__(self, logger=None):
        self.logger = logger
        self.classifier = BusinessContextClassifier()
        
    def analyze(self, 
                compliance_checks: Dict[str, Any],
                policy_details: Dict[str, Any], 
                content_risk: Dict[str, Any],
                domain_vintage_days: Optional[int] = None,
                business_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze all signals and compute score with context awareness.
        """
        
        context_type = business_context.get('primary', 'UNKNOWN') if business_context else 'UNKNOWN'
        context_status = business_context.get('status', BusinessContextClassifier.STATUS_DETERMINED) if business_context else BusinessContextClassifier.STATUS_DETERMINED
        
        # 1. Technical Score (Max 30) - Unchanged by Context
        tech_score = 0
        tech_breakdown = []
        
        # SSL
        alerts = compliance_checks.get('general', {}).get('alerts', [])
        ssl_issues = [a for a in alerts if a.get('code') in ['NO_HTTPS', 'SSL_ERROR']]
        if not ssl_issues:
            tech_score += 15
            tech_breakdown.append({
                "item": "SSL Certificate",
                "score": 15,
                "max": 15,
                "status": "pass",
                "signal_reference": "ssl_https_presence",
                "signal_type": SignalClassifier.classify_signal("ssl_https_presence")
            })
        else:
            ssl_alert = ssl_issues[0]
            tech_breakdown.append({
                "item": "SSL Certificate",
                "score": 0,
                "max": 15,
                "status": "fail",
                "reason": "No valid HTTPS detected",
                "signal_reference": "ssl_https_presence",
                "signal_type": SignalClassifier.classify_signal("ssl_https_presence"),
                "triggering_alert": ssl_alert.get('code', 'NO_HTTPS')
            })

        # Domain Age
        age_score = 0
        age_status = "unknown"
        if domain_vintage_days is not None:
            if domain_vintage_days < 180: age_score, age_status = 0, "Critical (< 6mo)"
            elif domain_vintage_days < 365: age_score, age_status = 5, "Low (6-12mo)"
            elif domain_vintage_days < 1095: age_score, age_status = 10, "Moderate (1-3yr)"
            else: age_score, age_status = 15, "Good (> 3yr)"
        else:
            age_score, age_status = 0, "Unknown (RDAP failed)"
            
        tech_score += age_score
        tech_breakdown.append({"item": "Domain Age", "score": age_score, "max": 15, "status": age_status})
        
        
        # 2. Policy Completeness (Max 40) - Context Aware
        # Define expectations
        # Start with Strict (Ecom default)
        expectations = {
            "privacy_policy": "required",
            "terms_condition": "required",
            "returns_refund": "required",
            "contact_us": "required"
        }
        
        # Adjust based on context
        if context_status == BusinessContextClassifier.STATUS_UNDETERMINED:
             # Safety: If context is undetermined (scan blocked or empty), do not penalize.
             # Mark all as optional or n/a to prevent false fails.
             for k in expectations:
                 expectations[k] = "optional"
        
        elif context_type == BusinessContextClassifier.CONTEXT_SAAS:
            expectations["returns_refund"] = "optional"
            
        elif context_type == BusinessContextClassifier.CONTEXT_FINTECH:
            expectations["returns_refund"] = "n/a"
            
        elif context_type == BusinessContextClassifier.CONTEXT_BLOCKCHAIN:
            expectations["returns_refund"] = "n/a"
            expectations["contact_us"] = "optional"
            
        elif context_type == BusinessContextClassifier.CONTEXT_CONTENT:
            expectations["returns_refund"] = "n/a"
            expectations["contact_us"] = "optional"
            expectations["terms_condition"] = "optional"
            
        # Low Confidence Safety: Check overrides?
        if context_status == BusinessContextClassifier.STATUS_LOW_CONFIDENCE:
            # If uncertain, relax Refund Policy to Optional to avoid harsh penalties
            if expectations["returns_refund"] == "required":
                expectations["returns_refund"] = "optional"

        policy_score = 0
        policy_breakdown = []
        policy_map = {
            "privacy_policy": "Privacy Policy",
            "terms_condition": "Terms of Service",
            "returns_refund": "Refund Policy",
            "contact_us": "Contact Page"
        }
        
        for key, name in policy_map.items():
            p_data = policy_details.get(key, {})
            expectation = expectations.get(key, "required")
            
            # Base Score per item is 10
            item_score = 0
            reasons = []
            status_label = "Missing"
            
            if p_data.get('found'):
                status_label = "Found"
                # Scored logic
                content_len = p_data.get('content_length', 0)
                
                # Base 6 pts
                item_score = 6
                if content_len > 500: item_score += 2
                if p_data.get('has_specific_keywords'): item_score += 2
                
                # Boost simple found to 10 if we lack depth (MVP parity)
                if item_score == 6: item_score = 10
                
            else:
                # Not Found Logic
                if expectation == "required":
                    item_score = 0
                    reasons.append("Required but missing")
                    status_label = "Missing (Required)"
                elif expectation == "optional":
                    item_score = 10 # Passthrough
                    status_label = "Missing (Optional)"
                    reasons.append("Optional for this context")
                elif expectation == "n/a":
                    item_score = 10
                    status_label = "N/A"
                    reasons.append("Not applicable")

            policy_score += item_score
            
            # Add signal reference and evidence if available
            # Per PRD V2.1.1: Policy detection must show expectation state (Required/Optional/N/A)
            breakdown_item = {
                "item": name,
                "score": item_score,
                "max": 10,
                "status": status_label,
                "expectation": expectation,  # Required/Optional/Not Applicable
                "expectation_state": expectation,  # Per PRD: Explicit expectation state
                "notes": ", ".join(reasons),
                "signal_reference": "policy_page_presence",
                "signal_type": SignalClassifier.classify_signal("policy_page_presence"),
                # Per PRD: Show detection status and source URL if detected
                "detection_status": "detected" if p_data.get('found') else "not_detected",
                "source_url": p_data.get('url', '') if p_data.get('found') else None
            }
            
            # Add evidence if policy was found
            if p_data.get('found') and p_data.get('evidence'):
                breakdown_item["evidence"] = p_data.get('evidence')
            
            policy_breakdown.append(breakdown_item)
            
        
        # 3. Trust & Risk (Max 30) - Context Conditioned with Intent Awareness
        trust_score = 30
        risk_flags = []
        
        # Policy page types where prohibitive intent reduces penalties
        policy_page_types = ['privacy_policy', 'terms_conditions', 'terms_condition', 
                            'refund_policy', 'returns_refund', 'acceptable_use']
        
        restricted = content_risk.get('restricted_keywords_found', [])
        for item in restricted:
            cat = item.get('category')
            keyword = item.get('keyword', 'unknown')
            intent = item.get('intent', 'neutral')  # NEW: Intent classification
            page_type = item.get('page_type', 'unknown')  # NEW: Page type context
            penalty = 0
            penalty_adjustment_reason = ""
            business_context_applied = ""
            
            # NEW: Check if this is prohibitive intent on a policy page
            # These are informational mentions (e.g., "we do not allow gambling")
            is_policy_page = page_type in policy_page_types
            if is_policy_page and intent == "prohibitive":
                # Prohibitive intent on policy pages = informational only, no penalty
                penalty = 0
                penalty_adjustment_reason = f"Prohibitive intent detected on {page_type} (legal boilerplate, not actual risk)"
                business_context_applied = context_type or "UNKNOWN"
                
                # Add as informational flag, not a penalty
                risk_flags.append({
                    "type": "policy_mention",
                    "severity": "info",
                    "message": f"Policy page mentions {cat} in prohibitive context ('{keyword}')",
                    "penalty": 0,
                    "penalty_adjustment_reason": penalty_adjustment_reason,
                    "business_context_applied": business_context_applied,
                    "signal_reference": "content_risk_detection",
                    "signal_type": SignalClassifier.classify_signal("content_risk_detection"),
                    "triggering_keyword": keyword,
                    "triggering_category": cat,
                    "intent": intent,
                    "page_type": page_type,
                    "source_url": item.get('evidence', {}).get('source_url', 'unknown') if isinstance(item.get('evidence'), dict) else 'unknown',
                    "evidence_snippet": item.get('intent_context', '') or (item.get('evidence', {}).get('evidence_snippet', '') if isinstance(item.get('evidence'), dict) else '')
                })
                continue  # Skip normal penalty processing
            
            # Context Logic for Crypto
            if cat == 'crypto':
                if context_type in [BusinessContextClassifier.CONTEXT_BLOCKCHAIN, BusinessContextClassifier.CONTEXT_FINTECH]:
                    penalty = 0 # Neutral / Informational
                    penalty_adjustment_reason = f"Reduced due to {context_type} context (crypto content is expected)"
                    business_context_applied = context_type
                    # Add info flag instead of penalty
                    risk_flags.append({
                         "type": "contextual_info",
                         "severity": "info",
                         "message": f"Crypto content detected (Expected for {context_type})",
                         "penalty": 0,
                         "penalty_adjustment_reason": penalty_adjustment_reason,
                         "business_context_applied": business_context_applied,
                         "signal_reference": "content_risk_detection",
                         "signal_type": SignalClassifier.classify_signal("content_risk_detection"),
                         "triggering_keyword": keyword,
                         "triggering_category": cat,
                         "intent": intent,
                         "page_type": page_type
                    })
                else:
                    penalty = 5 # Standard penalty for others (e.g. Ecom)
                    penalty_adjustment_reason = "Standard penalty for crypto content in non-crypto context"
                    business_context_applied = context_type or "UNKNOWN"
            # Context Logic for Forex - Fintech companies naturally deal with currency/forex
            elif cat == 'forex':
                if context_type == BusinessContextClassifier.CONTEXT_FINTECH:
                    penalty = 0 # Neutral / Informational for payment/fintech companies
                    penalty_adjustment_reason = f"Reduced due to {context_type} context (forex/currency content is expected)"
                    business_context_applied = context_type
                    # Add info flag instead of penalty
                    risk_flags.append({
                         "type": "contextual_info",
                         "severity": "info",
                         "message": f"Forex/currency content detected (Expected for {context_type})",
                         "penalty": 0,
                         "penalty_adjustment_reason": penalty_adjustment_reason,
                         "business_context_applied": business_context_applied,
                         "signal_reference": "content_risk_detection",
                         "signal_type": SignalClassifier.classify_signal("content_risk_detection"),
                         "triggering_keyword": keyword,
                         "triggering_category": cat,
                         "intent": intent,
                         "page_type": page_type
                    })
                else:
                    penalty = 5 # Standard penalty for forex in non-fintech contexts
                    penalty_adjustment_reason = "Standard penalty for forex content in non-fintech context"
                    business_context_applied = context_type or "UNKNOWN"
            # Context Logic for Securities/Money Transfer - also expected for fintech
            elif cat in ['securities', 'money_transfer', 'money_changer', 'digital_lending']:
                if context_type == BusinessContextClassifier.CONTEXT_FINTECH:
                    penalty = 0 # Neutral / Informational for payment/fintech companies
                    penalty_adjustment_reason = f"Reduced due to {context_type} context ({cat} content is expected)"
                    business_context_applied = context_type
                    risk_flags.append({
                         "type": "contextual_info",
                         "severity": "info",
                         "message": f"{cat.replace('_', ' ').title()} content detected (Expected for {context_type})",
                         "penalty": 0,
                         "penalty_adjustment_reason": penalty_adjustment_reason,
                         "business_context_applied": business_context_applied,
                         "signal_reference": "content_risk_detection",
                         "signal_type": SignalClassifier.classify_signal("content_risk_detection"),
                         "triggering_keyword": keyword,
                         "triggering_category": cat,
                         "intent": intent,
                         "page_type": page_type
                    })
                else:
                    penalty = 5 # Standard penalty for financial content in non-fintech contexts
                    penalty_adjustment_reason = f"Standard penalty for {cat} content in non-fintech context"
                    business_context_applied = context_type or "UNKNOWN"
            elif cat == 'gambling': 
                penalty = 15
                penalty_adjustment_reason = "Standard penalty for gambling content"
                business_context_applied = context_type or "UNKNOWN"
            elif cat == 'adult': 
                penalty = 20
                penalty_adjustment_reason = "Standard penalty for adult content"
                business_context_applied = context_type or "UNKNOWN"
            elif cat == 'pharmacy': 
                penalty = 10
                penalty_adjustment_reason = "Standard penalty for pharmacy content"
                business_context_applied = context_type or "UNKNOWN"
            # Default: Low-risk categories with no specific handling
            # These include: alcohol, tobacco, mlm, etc. - advisory but low penalty
            elif cat in ['alcohol', 'tobacco']:
                penalty = 3 # Lower penalty for age-restricted but legal products
                penalty_adjustment_reason = f"Low penalty for {cat} (age-restricted but legal)"
                business_context_applied = context_type or "UNKNOWN"
            
            if penalty > 0:
                trust_score -= penalty
                # Per PRD V2.1.1: Content risk must never auto-fail compliance
                # Severity must downgrade if context reduces relevance
                risk_flags.append({
                    "type": "restricted_content",
                    "severity": "critical" if penalty >= 15 else "moderate",
                    "message": f"Detected {cat} related specific keywords ({keyword})",
                    "penalty": penalty,
                    "penalty_adjustment_reason": penalty_adjustment_reason,  # Per PRD
                    "business_context_applied": business_context_applied,  # Per PRD
                    "signal_reference": "content_risk_detection",
                    "signal_type": SignalClassifier.classify_signal("content_risk_detection"),
                    "triggering_keyword": keyword,
                    "triggering_category": cat,
                    "intent": intent,  # NEW: Include intent for transparency
                    "page_type": page_type,  # NEW: Include page type for transparency
                    # Per PRD: Include source URL and snippet from content_risk evidence
                    "source_url": item.get('evidence', {}).get('source_url', 'unknown') if isinstance(item.get('evidence'), dict) else 'unknown',
                    "evidence_snippet": item.get('evidence', {}).get('evidence_snippet', '') if isinstance(item.get('evidence'), dict) else ''
                })
        
        if content_risk.get('dummy_words_detected'):
            trust_score -= 10
            dummy_evidence = content_risk.get('dummy_words_evidence', [])
            source_url = dummy_evidence[0].get('page_url', 'unknown') if dummy_evidence else 'unknown'
            evidence_snippet = dummy_evidence[0].get('evidence_snippet', '') if dummy_evidence else ''
            
            risk_flags.append({
                "type": "quality_risk",
                "severity": "moderate",
                "message": "Lorem ipsum / dummy text detected",
                "penalty": 10,
                "penalty_adjustment_reason": "Standard penalty for placeholder/dummy content",
                "business_context_applied": context_type or "UNKNOWN",
                "signal_reference": "content_risk_detection",
                "signal_type": SignalClassifier.classify_signal("content_risk_detection"),
                "triggering_rule": "Dummy text pattern matching",
                "source_url": source_url,
                "evidence_snippet": evidence_snippet
            })
            
        trust_score = max(0, min(30, trust_score))
        
        # Calculate Final
        total_score = tech_score + policy_score + trust_score
        
        if total_score >= 80: rating = "Good"
        elif total_score >= 50: rating = "Fair"
        else: rating = "Poor"
        
        # Per PRD V2.1.1: Compliance score is Advisory, must be labeled as such
        # Add static disclaimer and component breakdown with evidence
        return {
            "score": total_score,
            "advisory_score": total_score,  # Explicit advisory label per PRD
            "rating": rating,
            "context": context_type,
            "signal_type": SignalClassifier.classify_signal("compliance_score"),
            "label": "Advisory Score",  # Per PRD: must display as "Advisory Score"
            # Per PRD V2.1.1: Static disclaimer under score
            "disclaimer": "Advisory score based on publicly visible signals. Requires human review.",
            "breakdown": {
                "technical": {
                    "score": tech_score,
                    "max": 30,
                    "details": tech_breakdown,
                    "label": "Technical Compliance",
                    # Per PRD: Each component must expose signals contributing, points added/deducted, reason
                    "components": [
                        {
                            "name": item.get("item", "Unknown"),
                            "points": item.get("score", 0),
                            "max_points": item.get("max", 0),
                            "status": item.get("status", "unknown"),
                            "reason": item.get("reason", item.get("notes", "")),
                            "signal_reference": item.get("signal_reference", "unknown"),
                            "signal_type": item.get("signal_type", "advisory")
                        }
                        for item in tech_breakdown
                    ]
                },
                "policy": {
                    "score": policy_score,
                    "max": 40,
                    "details": policy_breakdown,
                    "label": "Policy Compliance",
                    # Per PRD: Each component must expose signals contributing, points added/deducted, reason
                    "components": [
                        {
                            "name": item.get("item", "Unknown"),
                            "points": item.get("score", 0),
                            "max_points": item.get("max", 0),
                            "status": item.get("status", "unknown"),
                            "expectation": item.get("expectation", "required"),  # Per PRD: Required/Optional/N/A
                            "reason": item.get("notes", ""),
                            "signal_reference": item.get("signal_reference", "unknown"),
                            "signal_type": item.get("signal_type", "advisory"),
                            "evidence": item.get("evidence")  # Include evidence if available
                        }
                        for item in policy_breakdown
                    ]
                },
                "trust": {
                    "score": trust_score,
                    "max": 30,
                    "details": risk_flags,
                    "label": "Trust & Risk",
                    # Per PRD: Each risk flag must show penalty adjustment reason
                    "components": [
                        {
                            "name": flag.get("type", "unknown").replace("_", " ").title(),
                            "severity": flag.get("severity", "info"),
                            "penalty": flag.get("penalty", 0),
                            "message": flag.get("message", ""),
                            "penalty_adjustment_reason": flag.get("penalty_adjustment_reason", ""),  # Per PRD
                            "business_context_applied": flag.get("business_context_applied", ""),  # Per PRD
                            "signal_reference": flag.get("signal_reference", "unknown"),
                            "signal_type": flag.get("signal_type", "advisory"),
                            "triggering_keyword": flag.get("triggering_keyword"),
                            "triggering_category": flag.get("triggering_category")
                        }
                        for flag in risk_flags
                    ]
                }
            },
            "risk_flags": risk_flags,
            # Per PRD: Score breakdown must be visible, each penalty references specific signal
            "breakdown_visible": True,
            "penalties_referenced": True
        }
