#!/usr/bin/env python3
"""
Simple test script for KYC Site Scan
Run from the kyc_site_scan directory:
    python3 test_scan.py https://example.com "Company Name"
"""

import sys
import os
import asyncio
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.input_schema import MerchantKYCInput
from kyc_engine import KYCDecisionEngine


async def run_test(url: str, company_name: str):
    """Run a KYC scan test"""
    
    print(f"\n{'='*60}")
    print("KYC Site Scan v2 - Test Mode")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Company: {company_name}")
    print(f"{'='*60}\n")
    
    # Create input
    input_data = MerchantKYCInput(
        merchant_legal_name=company_name,
        registered_address="Test Address, City 12345",
        declared_business_type="E-commerce",
        declared_products_services=["Products", "Services"],
        website_url=url,
        merchant_display_name=company_name.split()[0] if ' ' in company_name else company_name,
    )
    
    # Run scan
    print("Starting scan...")
    engine = KYCDecisionEngine()
    result = await engine.process(input_data)
    
    # Display results
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    
    decision_emoji = {"PASS": "✅", "FAIL": "❌", "ESCALATE": "⚠️"}
    print(f"\n{decision_emoji.get(result.decision.value, '?')} DECISION: {result.decision.value}")
    print(f"Confidence: {result.confidence_score:.0%}")
    print(f"\nSummary: {result.summary}")
    
    if result.reason_codes:
        print(f"\nReason Codes ({len(result.reason_codes)}):")
        for rc in result.reason_codes:
            icon = "❌" if rc.is_auto_fail else "⚠️" if rc.is_auto_escalate else "ℹ️"
            print(f"  {icon} [{rc.code}] {rc.message}")
    
    if result.compliance_score:
        print(f"\nCompliance Score: {result.compliance_score.overall_score}/100")
    
    print(f"\nAudit:")
    print(f"  - Scan ID: {result.audit_trail.scan_id}")
    print(f"  - Duration: {result.audit_trail.scan_duration_seconds:.2f}s")
    print(f"  - Pages Scanned: {result.audit_trail.pages_scanned}")
    
    # Save JSON
    output_file = f"/tmp/kyc_scan_{result.audit_trail.scan_id}.json"
    with open(output_file, 'w') as f:
        json.dump(result.model_dump(mode='json'), f, indent=2, default=str)
    print(f"\nFull results saved to: {output_file}")
    
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_scan.py <url> [company_name]")
        print("\nExamples:")
        print('  python3 test_scan.py https://shopify.com "Shopify Inc"')
        print('  python3 test_scan.py https://razorpay.com "Razorpay Pvt Ltd"')
        print('  python3 test_scan.py https://stripe.com "Stripe Inc"')
        sys.exit(1)
    
    url = sys.argv[1]
    company = sys.argv[2] if len(sys.argv) > 2 else "Test Company"
    
    asyncio.run(run_test(url, company))


if __name__ == "__main__":
    main()

