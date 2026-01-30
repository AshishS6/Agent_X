"""
Signal Classifier Module
Classifies all SiteScan signals according to PRD V2.1.1 classification framework.
Every signal must be classified as: Authoritative, Advisory, or Informational.
"""

from typing import Dict, Any, Optional


class SignalClassifier:
    """
    Classifies signals according to PRD V2.1.1 mandatory classification table.
    
    Signal Types:
    - Authoritative: Deterministic, objective, verifiable (Pass/Fail allowed)
    - Advisory: Heuristic, probabilistic, contextual (Suggestions, confidence scores)
    - Informational: Context-only, non-decision (Read-only metadata)
    """
    
    # PRD V2.1.1 Mandatory Classification Table
    SIGNAL_CLASSIFICATIONS = {
        # Authoritative signals
        "website_liveness": "authoritative",
        "ssl_https_presence": "authoritative",
        "excessive_redirects": "authoritative",
        "policy_page_presence": "authoritative",  # Presence only, not validity
        
        # Advisory signals
        "policy_validity": "advisory",
        "compliance_score": "advisory",
        "mcc_classification": "advisory",
        "content_risk_detection": "advisory",
        
        # Informational signals
        "domain_age": "informational",
        "seo_score": "informational",
        "business_metadata_extraction": "informational",
        "change_detection": "informational",
    }
    
    @staticmethod
    def classify_signal(signal_name: str) -> str:
        """
        Classify a signal by name.
        
        Args:
            signal_name: Name of the signal (e.g., "website_liveness", "mcc_classification")
            
        Returns:
            Signal type: "authoritative", "advisory", or "informational"
        """
        return SignalClassifier.SIGNAL_CLASSIFICATIONS.get(
            signal_name.lower(),
            "advisory"  # Default to advisory if unknown (safe default)
        )
    
    @staticmethod
    def get_signal_metadata(signal_name: str, 
                           value: Any = None,
                           confidence: Optional[float] = None,
                           evidence: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get complete signal metadata with classification.
        
        Args:
            signal_name: Name of the signal
            value: Signal value (optional)
            confidence: Confidence score 0-100 (optional, for advisory signals)
            evidence: Evidence dictionary (optional)
            
        Returns:
            Dictionary with signal_type, value, confidence, and evidence
        """
        signal_type = SignalClassifier.classify_signal(signal_name)
        
        metadata = {
            "signal_name": signal_name,
            "signal_type": signal_type,
            "value": value
        }
        
        # Add confidence for advisory signals
        if signal_type == "advisory" and confidence is not None:
            metadata["confidence"] = confidence
        
        # Add evidence if provided
        if evidence:
            metadata["evidence"] = evidence
        
        return metadata
    
    @staticmethod
    def is_authoritative(signal_name: str) -> bool:
        """Check if signal is authoritative"""
        return SignalClassifier.classify_signal(signal_name) == "authoritative"
    
    @staticmethod
    def is_advisory(signal_name: str) -> bool:
        """Check if signal is advisory"""
        return SignalClassifier.classify_signal(signal_name) == "advisory"
    
    @staticmethod
    def is_informational(signal_name: str) -> bool:
        """Check if signal is informational"""
        return SignalClassifier.classify_signal(signal_name) == "informational"
    
    @staticmethod
    def can_use_pass_fail(signal_name: str) -> bool:
        """
        Check if signal can use pass/fail UI treatment.
        Only authoritative signals can use pass/fail.
        """
        return SignalClassifier.is_authoritative(signal_name)
    
    @staticmethod
    def requires_confidence(signal_name: str) -> bool:
        """
        Check if signal requires confidence score.
        Advisory signals should have confidence scores.
        """
        return SignalClassifier.is_advisory(signal_name)

