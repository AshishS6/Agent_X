"""
Compliance Intelligence Engine
Calculates unified Compliance Score and Risk Flags based on technical, policy, and content signals.
Phase E.1: Context-Aware Complinace
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from analyzers.context_classifier import BusinessContextClassifier

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
            tech_breakdown.append({"item": "SSL Certificate", "score": 15, "max": 15, "status": "pass"})
        else:
            tech_breakdown.append({"item": "SSL Certificate", "score": 0, "max": 15, "status": "fail", "reason": "No valid HTTPS detected"})

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
            policy_breakdown.append({
                "item": name,
                "score": item_score,
                "max": 10,
                "status": status_label,
                "expectation": expectation,
                "notes": ", ".join(reasons)
            })
            
        
        # 3. Trust & Risk (Max 30) - Context Conditioned
        trust_score = 30
        risk_flags = []
        
        restricted = content_risk.get('restricted_keywords_found', [])
        for item in restricted:
            cat = item.get('category')
            penalty = 0
            
            # Context Logic for Crypto
            if cat == 'crypto':
                if context_type in [BusinessContextClassifier.CONTEXT_BLOCKCHAIN, BusinessContextClassifier.CONTEXT_FINTECH]:
                    penalty = 0 # Neutral / Informational
                    # Add info flag instead of penalty?
                    risk_flags.append({
                         "type": "contextual_info",
                         "severity": "info",
                         "message": f"Crypto content detected (Expected for {context_type})",
                         "penalty": 0
                    })
                else:
                    penalty = 5 # Standard penalty for others (e.g. Ecom)
            elif cat == 'gambling': penalty = 15
            elif cat == 'adult': penalty = 20
            elif cat == 'pharmacy': penalty = 10
            
            if penalty > 0:
                trust_score -= penalty
                risk_flags.append({
                    "type": "restricted_content",
                    "severity": "critical" if penalty >= 15 else "moderate",
                    "message": f"Detected {cat} related specific keywords ({item.get('keyword')})",
                    "penalty": penalty
                })
        
        if content_risk.get('dummy_words_detected'):
            trust_score -= 10
            risk_flags.append({
                "type": "quality_risk",
                "severity": "moderate",
                "message": "Lorem ipsum / dummy text detected",
                "penalty": 10
            })
            
        trust_score = max(0, min(30, trust_score))
        
        # Calculate Final
        total_score = tech_score + policy_score + trust_score
        
        if total_score >= 80: rating = "Good"
        elif total_score >= 50: rating = "Fair"
        else: rating = "Poor"
        
        return {
            "score": total_score,
            "rating": rating,
            "context": context_type,
            "breakdown": {
                "technical": {"score": tech_score, "max": 30, "details": tech_breakdown},
                "policy": {"score": policy_score, "max": 40, "details": policy_breakdown},
                "trust": {"score": trust_score, "max": 30, "details": risk_flags}
            },
            "risk_flags": risk_flags
        }
