#!/usr/bin/env python3
"""
KYC Site Scan CLI
Command-line interface for testing KYC scans

Usage:
    python cli.py scan --url https://example.com --name "Company Name"
    python cli.py scan --input merchant_data.json
    python cli.py validate --url https://example.com
"""

import argparse
import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kyc_site_scan.models.input_schema import MerchantKYCInput
from kyc_site_scan.kyc_engine import KYCDecisionEngine


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )


async def run_scan(
    url: str,
    merchant_name: str,
    business_type: str = "E-commerce",
    products: list = None,
    address: str = "Address not provided",
    display_name: str = None,
    output_file: str = None,
):
    """Run a KYC scan"""
    
    # Build input
    input_data = MerchantKYCInput(
        merchant_legal_name=merchant_name,
        registered_address=address,
        declared_business_type=business_type,
        declared_products_services=products or ["Products/Services"],
        website_url=url,
        merchant_display_name=display_name or merchant_name.split()[0],
    )
    
    print(f"\n{'='*60}")
    print("KYC Site Scan v2.0")
    print(f"{'='*60}")
    print(f"Target URL: {url}")
    print(f"Merchant: {merchant_name}")
    print(f"Business Type: {business_type}")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")
    
    # Run scan
    engine = KYCDecisionEngine()
    result = await engine.process(input_data)
    
    # Display results
    print(f"\n{'='*60}")
    print("SCAN RESULTS")
    print(f"{'='*60}")
    print(f"\nDECISION: {result.decision.value}")
    print(f"Confidence: {result.confidence_score:.2%}")
    print(f"\nSummary: {result.summary}")
    
    if result.reason_codes:
        print(f"\nReason Codes ({len(result.reason_codes)}):")
        for rc in result.reason_codes:
            status = "❌" if rc.is_auto_fail else "⚠️" if rc.is_auto_escalate else "ℹ️"
            print(f"  {status} [{rc.code}] {rc.message}")
    
    if result.compliance_score:
        print(f"\nCompliance Score: {result.compliance_score.overall_score}/100 ({result.compliance_score.rating})")
        print(f"  - Technical: {result.compliance_score.technical_score}/30")
        print(f"  - Policy: {result.compliance_score.policy_score}/40")
        print(f"  - Trust: {result.compliance_score.trust_score}/30")
    
    if result.policy_checks:
        print(f"\nPolicy Pages:")
        for pc in result.policy_checks:
            status = "✅" if pc.found else "❌"
            print(f"  {status} {pc.policy_type}: {pc.url or 'Not found'}")
    
    if result.entity_match:
        print(f"\nEntity Match:")
        print(f"  Declared: {result.entity_match.declared_name}")
        print(f"  Best Match: {result.entity_match.best_match or 'None'}")
        print(f"  Score: {result.entity_match.match_score:.1f}%")
        print(f"  Status: {result.entity_match.match_status}")
    
    print(f"\nAudit Trail:")
    print(f"  Scan ID: {result.audit_trail.scan_id}")
    print(f"  Duration: {result.audit_trail.scan_duration_seconds:.2f}s")
    print(f"  Pages Scanned: {result.audit_trail.pages_scanned}")
    print(f"  Checks Performed: {len(result.audit_trail.checks_performed)}")
    
    print(f"\n{'='*60}\n")
    
    # Save to file if requested
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(result.model_dump(mode='json'), f, indent=2, default=str)
        print(f"Results saved to: {output_file}")
    
    return result


async def run_scan_from_file(input_file: str, output_file: str = None):
    """Run scan from JSON input file"""
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    input_data = MerchantKYCInput(**data)
    
    engine = KYCDecisionEngine()
    result = await engine.process(input_data)
    
    # Display and save
    print(json.dumps(result.model_dump(mode='json'), indent=2, default=str))
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(result.model_dump(mode='json'), f, indent=2, default=str)


def main():
    parser = argparse.ArgumentParser(
        description="KYC Site Scan v2 - Automated Website Screening"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Run KYC website scan')
    scan_parser.add_argument('--url', '-u', required=True, help='Website URL')
    scan_parser.add_argument('--name', '-n', required=True, help='Merchant legal name')
    scan_parser.add_argument('--type', '-t', default='E-commerce', help='Business type')
    scan_parser.add_argument('--products', '-p', nargs='+', help='Products/services list')
    scan_parser.add_argument('--address', '-a', default='Address not provided', help='Registered address')
    scan_parser.add_argument('--display', '-d', help='Display name')
    scan_parser.add_argument('--output', '-o', help='Output file (JSON)')
    
    # Scan from file command
    file_parser = subparsers.add_parser('scan-file', help='Run scan from JSON file')
    file_parser.add_argument('--input', '-i', required=True, help='Input JSON file')
    file_parser.add_argument('--output', '-o', help='Output file (JSON)')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate input data')
    validate_parser.add_argument('--url', '-u', required=True, help='Website URL')
    validate_parser.add_argument('--name', '-n', default='Test Company', help='Merchant name')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    setup_logging(args.verbose)
    
    if args.command == 'scan':
        asyncio.run(run_scan(
            url=args.url,
            merchant_name=args.name,
            business_type=args.type,
            products=args.products,
            address=args.address,
            display_name=args.display,
            output_file=args.output,
        ))
    
    elif args.command == 'scan-file':
        asyncio.run(run_scan_from_file(
            input_file=args.input,
            output_file=args.output,
        ))
    
    elif args.command == 'validate':
        # Quick validation
        try:
            input_data = MerchantKYCInput(
                merchant_legal_name=args.name,
                registered_address="Test Address 12345",
                declared_business_type="E-commerce",
                declared_products_services=["Test"],
                website_url=args.url,
                merchant_display_name="Test",
            )
            print(f"✅ Input validation passed")
            print(f"   URL: {input_data.website_url}")
            print(f"   Name: {input_data.merchant_legal_name}")
        except Exception as e:
            print(f"❌ Input validation failed: {e}")


if __name__ == "__main__":
    main()

