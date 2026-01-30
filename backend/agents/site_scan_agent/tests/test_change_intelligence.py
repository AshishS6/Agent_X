import unittest
from analyzers.change_intelligence import ChangeIntelligenceEngine

class TestChangeIntelligenceEngine(unittest.TestCase):
    
    def setUp(self):
        self.engine = ChangeIntelligenceEngine()
        
    def test_no_changes(self):
        report = {"since_last_scan": False}
        result = self.engine.analyze_intelligence(report)
        self.assertEqual(result["overall_severity"], "none")
        self.assertEqual(result["summary"], "No significant changes detected")

    def test_pricing_model_change(self):
        # Critical change
        change_report = {
            "since_last_scan": True,
            "changes": [
                {
                    "type": "pricing_model_changed",
                    "description": "Pricing model changed"
                }
            ]
        }
        result = self.engine.analyze_intelligence(change_report)
        
        self.assertEqual(result["overall_severity"], "critical")
        self.assertTrue("critical" in result["summary"])
        self.assertEqual(result["changes"][0]["severity"], "critical")
        self.assertEqual(result["changes"][0]["business_impact"], "Fundamental revenue model shift detected")

    def test_mixed_severity_changes(self):
        # Critical + Minor
        change_report = {
            "since_last_scan": True,
            "changes": [
                {
                    "type": "privacy_policy_changed",  # Critical
                    "description": "Privacy updated"
                },
                {
                    "type": "homepage_copy_changed",   # Minor
                    "description": "New hero text"
                }
            ]
        }
        result = self.engine.analyze_intelligence(change_report)
        
        self.assertEqual(result["overall_severity"], "critical")
        self.assertTrue("1 critical" in result["summary"])
        self.assertTrue("1 minor" in result["summary"])
        
        # Verify recommended action comes from critical change
        self.assertIn("compliance", result["recommended_action"]) # "Re-run compliance..."

    def test_content_change_inference(self):
        # Test the Page Type inference logic
        change_report = {
            "since_last_scan": True,
            "changes": [
                {
                    "type": "content_change",
                    "description": "Privacy Policy page content has changed."
                }
            ]
        }
        result = self.engine.analyze_intelligence(change_report)
        
        enriched_change = result["changes"][0]
        self.assertEqual(enriched_change["severity"], "critical") # Should be mapped to privacy_policy_changed -> critical
        self.assertEqual(enriched_change["business_impact"], "Legal & compliance risk exposure")

    def test_unknown_change_type(self):
        change_report = {
            "since_last_scan": True,
            "changes": [
                {
                    "type": "random_unknown_change",
                    "description": "Something happened"
                }
            ]
        }
        result = self.engine.analyze_intelligence(change_report)
        
        enriched_change = result["changes"][0]
        self.assertEqual(enriched_change["severity"], "minor")
        self.assertEqual(enriched_change["business_impact"], "Unclassified change detected")

if __name__ == '__main__':
    unittest.main()
