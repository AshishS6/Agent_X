"""
Severity Classification Engine
Centralized rules for determining issue severity levels (HIGH/MEDIUM/LOW).
Context-aware rules prevent logic duplication across report builders.
"""

from typing import Dict, Any, Optional
from analyzers.context_classifier import BusinessContextClassifier


class SeverityRules:
    """
    Centralized severity classification rules.
    All report builders must use this class to ensure consistency.
    """
    
    # Severity levels
    SEVERITY_HIGH = "HIGH"
    SEVERITY_MEDIUM = "MEDIUM"
    SEVERITY_LOW = "LOW"
    
    def __init__(self):
        self.classifier = BusinessContextClassifier()
    
    def classify_issue(self,
                      issue_type: str,
                      issue_data: Dict[str, Any],
                      business_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Classify an issue and return severity, required flag, and contextual reason.
        
        Args:
            issue_type: Type of issue (e.g., 'ssl_missing', 'policy_missing', 'restricted_content')
            issue_data: Issue-specific data
            business_context: Business context from classifier
            
        Returns:
            Dict with:
            - severity: HIGH/MEDIUM/LOW
            - required: boolean (whether this is a required fix)
            - contextual_reason: string explaining why this severity/requirement
        """
        context_type = business_context.get('primary', 'UNKNOWN') if business_context else 'UNKNOWN'
        context_status = business_context.get('status', BusinessContextClassifier.STATUS_DETERMINED) if business_context else BusinessContextClassifier.STATUS_DETERMINED
        
        # SSL/TLS Issues
        if issue_type == 'ssl_missing' or issue_type == 'ssl_error':
            return {
                "severity": self.SEVERITY_HIGH,
                "required": True,
                "contextual_reason": "HTTPS is required for all payment processing sites"
            }
        
        # Domain Age Issues
        if issue_type == 'domain_age_low':
            age_days = issue_data.get('age_days', 0)
            if age_days < 180:
                return {
                    "severity": self.SEVERITY_HIGH,
                    "required": True,
                    "contextual_reason": "Domain age < 6 months indicates high risk for payment processing"
                }
            elif age_days < 365:
                return {
                    "severity": self.SEVERITY_MEDIUM,
                    "required": False,
                    "contextual_reason": "Domain age 6-12 months may require additional verification"
                }
            else:
                return {
                    "severity": self.SEVERITY_LOW,
                    "required": False,
                    "contextual_reason": "Domain age 1-3 years is acceptable but not optimal"
                }
        
        # Policy Missing Issues (Context-Aware)
        if issue_type == 'policy_missing':
            policy_name = issue_data.get('policy_name', '')
            expectation = issue_data.get('expectation', 'required')
            
            if expectation == 'required':
                return {
                    "severity": self.SEVERITY_HIGH,
                    "required": True,
                    "contextual_reason": f"{policy_name} is required for {context_type} businesses"
                }
            elif expectation == 'optional':
                return {
                    "severity": self.SEVERITY_MEDIUM,
                    "required": False,
                    "contextual_reason": f"{policy_name} is optional for {context_type} but recommended"
                }
            else:  # n/a
                return {
                    "severity": self.SEVERITY_LOW,
                    "required": False,
                    "contextual_reason": f"{policy_name} is not applicable for {context_type}"
                }
        
        # Restricted Content Issues (Context-Aware)
        if issue_type == 'restricted_content':
            category = issue_data.get('category', '')
            keyword = issue_data.get('keyword', '')
            
            # Context-aware crypto handling
            if category == 'crypto':
                if context_type in [BusinessContextClassifier.CONTEXT_BLOCKCHAIN, 
                                   BusinessContextClassifier.CONTEXT_FINTECH]:
                    return {
                        "severity": self.SEVERITY_LOW,
                        "required": False,
                        "contextual_reason": f"Crypto content is expected for {context_type} businesses"
                    }
                else:
                    return {
                        "severity": self.SEVERITY_MEDIUM,
                        "required": False,
                        "contextual_reason": f"Crypto content detected in {context_type} context may require review"
                    }
            
            # High-severity restricted content
            if category == 'gambling':
                return {
                    "severity": self.SEVERITY_HIGH,
                    "required": True,
                    "contextual_reason": "Gambling-related content requires special licensing and compliance"
                }
            
            if category == 'adult':
                return {
                    "severity": self.SEVERITY_HIGH,
                    "required": True,
                    "contextual_reason": "Adult content requires age verification and special payment processing"
                }
            
            if category == 'pharmacy':
                return {
                    "severity": self.SEVERITY_MEDIUM,
                    "required": False,
                    "contextual_reason": "Pharmacy-related content may require additional compliance verification"
                }
            
            # Generic restricted content
            return {
                "severity": self.SEVERITY_MEDIUM,
                "required": False,
                "contextual_reason": f"Restricted keyword '{keyword}' detected in {category} category"
            }
        
        # Quality Issues
        if issue_type == 'dummy_text':
            return {
                "severity": self.SEVERITY_MEDIUM,
                "required": False,
                "contextual_reason": "Dummy/placeholder text indicates incomplete site development"
            }
        
        # Compliance Check Failures
        if issue_type == 'compliance_failure':
            check_name = issue_data.get('check_name', '')
            if check_name in ['liveness', 'ssl_valid']:
                return {
                    "severity": self.SEVERITY_HIGH,
                    "required": True,
                    "contextual_reason": f"{check_name} failure prevents payment processing"
                }
            else:
                return {
                    "severity": self.SEVERITY_MEDIUM,
                    "required": False,
                    "contextual_reason": f"{check_name} failure may impact compliance"
                }
        
        # Default for unknown issue types
        return {
            "severity": self.SEVERITY_MEDIUM,
            "required": False,
            "contextual_reason": "Issue requires manual review"
        }
    
    def get_policy_expectation(self,
                              policy_key: str,
                              business_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Get policy expectation (required/optional/n/a) based on business context.
        
        Args:
            policy_key: Policy key (e.g., 'privacy_policy', 'terms_condition')
            business_context: Business context from classifier
            
        Returns:
            'required', 'optional', or 'n/a'
        """
        if not business_context:
            return 'required'  # Default to strict
        
        context_type = business_context.get('primary', 'UNKNOWN')
        context_status = business_context.get('status', BusinessContextClassifier.STATUS_DETERMINED)
        
        # If undetermined, don't penalize
        if context_status == BusinessContextClassifier.STATUS_UNDETERMINED:
            return 'optional'
        
        # Base expectations (strict for ecommerce)
        expectations = {
            "privacy_policy": "required",
            "terms_condition": "required",
            "returns_refund": "required",
            "contact_us": "required"
        }
        
        # Context-specific adjustments
        if context_type == BusinessContextClassifier.CONTEXT_SAAS:
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
        
        # Low confidence safety
        if context_status == BusinessContextClassifier.STATUS_LOW_CONFIDENCE:
            if expectations.get("returns_refund") == "required":
                expectations["returns_refund"] = "optional"
        
        return expectations.get(policy_key, "required")



