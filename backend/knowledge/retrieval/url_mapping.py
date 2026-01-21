"""
URL Mapping System for Public Citations

Extracted from Local-LLM project (backend/local_llm_staging/backend/rag/url_mapping.py).

Maps internal KB content to public URLs for citation in responses.
Only public URLs (websites, documentation, dashboards) should be cited.
"""

from typing import Dict, Optional, Set
import re


class URLMapper:
    """
    Maps KB content to public URLs
    
    Extracted from Local-LLM project. Provides mapping from internal
    knowledge base file paths to public documentation URLs.
    """
    
    # Base URLs
    ZWITCH_WEBSITE = "https://www.zwitch.io/"
    ZWITCH_DOCS = "https://developers.zwitch.io/"
    ZWITCH_DASHBOARD = "https://dashboard.zwitch.io/"
    ZWITCH_API_BASE = "https://api.zwitch.io/v1"
    
    OPEN_MONEY_WEBSITE = "https://open.money/"
    OPEN_MONEY_DASHBOARD = "https://dashboard.open.money/"  # Assuming this exists
    
    # Mapping from KB file paths/patterns to public URLs
    URL_MAPPING: Dict[str, str] = {
        # Zwitch - General
        "zwitch/company_overview.md": ZWITCH_WEBSITE,
        "zwitch/products_overview.md": ZWITCH_WEBSITE,
        "zwitch/FAQ.md": ZWITCH_WEBSITE,
        "zwitch/PAYMENT_GATEWAY.md": f"{ZWITCH_WEBSITE}#payment-gateway",
        
        # Zwitch - API Documentation
        "zwitch/api/00_introduction.md": f"{ZWITCH_DOCS}docs/overview",
        "zwitch/api/01_authentication.md": f"{ZWITCH_DOCS}reference/authorization",
        "zwitch/api/02_error_codes.md": f"{ZWITCH_DOCS}reference/error-codes",
        "zwitch/api/03_accounts.md": f"{ZWITCH_DOCS}reference/virtual-accounts",
        "zwitch/api/04_account_balance_statement.md": f"{ZWITCH_DOCS}reference/virtual-accounts",
        "zwitch/api/05_payments.md": f"{ZWITCH_DOCS}docs/payment",
        "zwitch/api/06_beneficiaries.md": f"{ZWITCH_DOCS}docs/beneficiary-integration-flow",
        "zwitch/api/07_transfers.md": f"{ZWITCH_DOCS}reference/transfers-virtual-accounts-create-to-account-beneficiary",
        "zwitch/api/08_verification.md": f"{ZWITCH_DOCS}reference/verifications-bank-account",
        "zwitch/api/09_bharat_connect.md": f"{ZWITCH_WEBSITE}#zwitch-bill-connect",
        "zwitch/api/10_webhooks.md": f"{ZWITCH_DOCS}docs/webhook-setup",
        "zwitch/api/11_api_constants.md": f"{ZWITCH_DOCS}reference",  # General reference
        "zwitch/api/12_connected_banking.md": f"{ZWITCH_DOCS}reference/connected-banking-apis",
        "zwitch/api/13_examples_node.md": f"{ZWITCH_DOCS}docs",
        "zwitch/api/14_examples_python.md": f"{ZWITCH_DOCS}docs",
        "zwitch/api/15_layer_js.md": f"{ZWITCH_DOCS}reference/layerjs",
        
        # Zwitch - Concepts
        "zwitch/concepts/payin_vs_payout.md": f"{ZWITCH_DOCS}docs/overview",
        "zwitch/concepts/payment_token_vs_order.md": f"{ZWITCH_DOCS}docs/payment",
        "zwitch/concepts/merchant_vs_platform.md": ZWITCH_WEBSITE,
        "zwitch/concepts/zwitch_vs_open_money.md": ZWITCH_WEBSITE,
        
        # Zwitch - States
        "zwitch/states/payment_status_lifecycle.md": f"{ZWITCH_DOCS}docs/payment",
        "zwitch/states/transfer_status_lifecycle.md": f"{ZWITCH_DOCS}reference/transfers-bulk",
        "zwitch/states/verification_states.md": f"{ZWITCH_DOCS}reference/verifications-bank-account",
        
        # Zwitch - Flows
        "zwitch/flows/payin_happy_path.md": f"{ZWITCH_DOCS}docs/payment",
        "zwitch/flows/payin_failure_path.md": f"{ZWITCH_DOCS}docs/payment",
        "zwitch/flows/refund_flow.md": f"{ZWITCH_DOCS}docs/payment",
        "zwitch/flows/settlement_flow.md": f"{ZWITCH_DOCS}docs/payment",
        
        # Zwitch - Best Practices
        "zwitch/best_practices/recommended_db_schema.md": f"{ZWITCH_DOCS}docs",
        "zwitch/best_practices/production_checklist.md": f"{ZWITCH_DOCS}docs",
        "zwitch/best_practices/logging_and_audits.md": f"{ZWITCH_DOCS}docs",
        
        # Zwitch - Principles
        "zwitch/principles/source_of_truth.md": f"{ZWITCH_DOCS}docs/webhook-setup",
        "zwitch/principles/backend_authority.md": f"{ZWITCH_DOCS}docs",
        "zwitch/principles/idempotency.md": f"{ZWITCH_DOCS}docs",
        
        # Zwitch - Decisions
        "zwitch/decisions/polling_vs_webhooks.md": f"{ZWITCH_DOCS}docs/webhook-setup",
        "zwitch/decisions/frontend_vs_backend_calls.md": f"{ZWITCH_DOCS}docs",
        "zwitch/decisions/retries_and_idempotency.md": f"{ZWITCH_DOCS}docs",
        
        # Zwitch - Risks
        "zwitch/risks/double_credit_risk.md": f"{ZWITCH_DOCS}docs",
        "zwitch/risks/webhook_signature_verification.md": f"{ZWITCH_DOCS}docs/webhook-setup",
        "zwitch/risks/reconciliation_failures.md": f"{ZWITCH_DOCS}docs",
        "zwitch/risks/compliance_boundaries.md": ZWITCH_WEBSITE,
        
        # Open Money - General
        "openmoney/company_overview.md": OPEN_MONEY_WEBSITE,
        "openmoney/products_overview.md": OPEN_MONEY_WEBSITE,
        "openmoney/FAQ.md": OPEN_MONEY_WEBSITE,
        
        # Open Money - Products
        "openmoney/products/api_solutions.md": OPEN_MONEY_WEBSITE,
        "openmoney/products/banking_solutions_for_banks.md": OPEN_MONEY_WEBSITE,
        "openmoney/products/expense_management.md": OPEN_MONEY_WEBSITE,
        "openmoney/products/lending_solutions.md": OPEN_MONEY_WEBSITE,
        "openmoney/products/payroll_management.md": OPEN_MONEY_WEBSITE,
        
        # Open Money - Concepts
        "openmoney/concepts/what_is_open_money.md": OPEN_MONEY_WEBSITE,
        "openmoney/concepts/open_money_vs_bank.md": OPEN_MONEY_WEBSITE,
        "openmoney/concepts/open_money_vs_accounting_software.md": OPEN_MONEY_WEBSITE,
        "openmoney/concepts/open_money_product_philosophy.md": OPEN_MONEY_WEBSITE,
        "openmoney/concepts/data_ownership_and_limitations.md": OPEN_MONEY_WEBSITE,
        
        # Open Money - Modules
        "openmoney/modules/receivables.md": OPEN_MONEY_WEBSITE,
        "openmoney/modules/payables.md": OPEN_MONEY_WEBSITE,
        "openmoney/modules/banking.md": OPEN_MONEY_WEBSITE,
        "openmoney/modules/cashflow_analytics.md": OPEN_MONEY_WEBSITE,
        "openmoney/modules/payments_and_payouts.md": OPEN_MONEY_WEBSITE,
        "openmoney/modules/compliance.md": OPEN_MONEY_WEBSITE,
    }
    
    # API Endpoint mappings (for specific endpoints mentioned in context)
    API_ENDPOINT_MAPPING: Dict[str, str] = {
        "POST /v1/transfers": f"{ZWITCH_DOCS}reference/transfers-virtual-accounts-create-to-account-beneficiary",
        "POST /v1/transfers/bulk": f"{ZWITCH_DOCS}reference/transfers-bulk",
        "GET /v1/transfers": f"{ZWITCH_DOCS}docs/transfer-virtual-accounts-manage",
        "GET /v1/transfers/{id}": f"{ZWITCH_DOCS}reference/transfers-virtual-accounts-object",
        "POST /v1/pg/payment_token": f"{ZWITCH_DOCS}reference/create-payment-token",
        "POST /v1/pg/sandbox/payment_token": f"{ZWITCH_DOCS}reference/create-payment-token",
        "POST /v1/accounts/{account_id}/payments/upi/collect": f"{ZWITCH_DOCS}docs/payment",
        "POST /v1/accounts/{account_id}/beneficiaries": f"{ZWITCH_DOCS}docs/beneficiary-integration-flow",
        "POST /v1/verifications/vpa": f"{ZWITCH_DOCS}reference/verifications-bank-account",
        "POST /v1/verifications/bank-account/pennyless": f"{ZWITCH_DOCS}reference/verifications-bank-account",
        "POST /v1/verifications/pan": f"{ZWITCH_DOCS}reference/verifications-bank-account",
        "POST /v1/verifications/name": f"{ZWITCH_DOCS}reference/verifications-bank-account",
        "POST /v1/bharat-connect/onboarding/": f"{ZWITCH_WEBSITE}#zwitch-bill-connect",
        "POST /v1/bharat-connect/invoice/": f"{ZWITCH_WEBSITE}#zwitch-bill-connect",
        "POST /v1/bharat-connect/payment": f"{ZWITCH_WEBSITE}#zwitch-bill-connect",
        "GET /v1/constants/bank-ifsc": f"{ZWITCH_DOCS}reference",
        "GET /v1/constants/business-categories": f"{ZWITCH_DOCS}reference",
        "GET /v1/constants/business-types": f"{ZWITCH_DOCS}reference",
        "GET /v1/constants/state-codes": f"{ZWITCH_DOCS}reference",
    }
    
    @classmethod
    def get_url_for_source_path(cls, source_path: str) -> Optional[str]:
        """
        Get public URL for a KB source path
        
        Args:
            source_path: Internal KB path like 'zwitch/api/07_transfers.md'
            
        Returns:
            Public URL or None if not found
        """
        # Remove knowledge_base/ prefix if present
        clean_path = source_path.replace('knowledge_base/', '')
        
        # Try exact match first
        if clean_path in cls.URL_MAPPING:
            return cls.URL_MAPPING[clean_path]
        
        # Try partial match (for files in subdirectories)
        for pattern, url in cls.URL_MAPPING.items():
            if pattern in clean_path or clean_path.endswith(pattern):
                return url
        
        # Try matching by vendor and layer
        if 'zwitch' in clean_path:
            if '/api/' in clean_path:
                return cls.ZWITCH_DOCS
            elif '/flows/' in clean_path or '/states/' in clean_path:
                return cls.ZWITCH_DOCS
            else:
                return cls.ZWITCH_WEBSITE
        elif 'openmoney' in clean_path:
            return cls.OPEN_MONEY_WEBSITE
        
        return None
    
    @classmethod
    def get_url_for_api_endpoint(cls, endpoint: str) -> Optional[str]:
        """
        Get public URL for an API endpoint
        
        Args:
            endpoint: API endpoint like 'POST /v1/transfers'
            
        Returns:
            Public documentation URL or None
        """
        # Try exact match
        if endpoint in cls.API_ENDPOINT_MAPPING:
            return cls.API_ENDPOINT_MAPPING[endpoint]
        
        # Try partial match
        for pattern, url in cls.API_ENDPOINT_MAPPING.items():
            if pattern in endpoint or endpoint in pattern:
                return url
        
        # Fallback to general docs
        if '/v1/' in endpoint:
            if 'zwitch' in endpoint.lower() or 'api.zwitch.io' in endpoint.lower():
                return cls.ZWITCH_DOCS
        
        return None
    
    @classmethod
    def extract_and_validate_urls(cls, context: str, source_paths: list = None) -> Set[str]:
        """
        Extract and validate public URLs from context
        
        Args:
            context: Context text
            source_paths: List of source paths from retrieved chunks
            
        Returns:
            Set of valid public URLs
        """
        public_urls = set()
        
        # Extract URLs from text
        url_pattern = r'https?://[^\s\)\]\>]+'
        found_urls = re.findall(url_pattern, context)
        
        for url in found_urls:
            # Clean URL
            clean_url = url.rstrip('.,;:!?)')
            
            # Validate it's a public URL
            if cls._is_valid_public_url(clean_url):
                public_urls.add(clean_url)
        
        # Add URLs from source path mapping
        if source_paths:
            for source_path in source_paths:
                mapped_url = cls.get_url_for_source_path(source_path)
                if mapped_url:
                    public_urls.add(mapped_url)
        
        # Extract API endpoints and map them
        endpoint_pattern = r'(?:POST|GET|PUT|DELETE|PATCH)\s+[^\s\)\]\>]+'
        endpoints = re.findall(endpoint_pattern, context, re.IGNORECASE)
        
        for endpoint in endpoints:
            mapped_url = cls.get_url_for_api_endpoint(endpoint)
            if mapped_url:
                public_urls.add(mapped_url)
        
        return public_urls
    
    @classmethod
    def _is_valid_public_url(cls, url: str) -> bool:
        """
        Check if URL is a valid public URL (not localhost, internal, or invalid)
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid public URL
        """
        url_lower = url.lower()
        
        # Exclude invalid patterns
        invalid_patterns = [
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            '192.168.',
            '10.0.',
            '172.16.',
            '.md',  # Exclude markdown file paths
            '/api/11_api_constants.md',  # Specific invalid URL
            'api.zwitch.io/v1/api/',  # Invalid API path structure
        ]
        
        if any(pattern in url_lower for pattern in invalid_patterns):
            return False
        
        # Include valid public domains
        valid_domains = [
            'zwitch.io',
            'open.money',
            'developers.',
            'dashboard.',
            'www.',
        ]
        
        return any(domain in url_lower for domain in valid_domains)
