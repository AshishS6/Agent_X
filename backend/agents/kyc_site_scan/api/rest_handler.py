"""
REST API Handler for KYC Site Scan
Synchronous API endpoint for KYC screening

Endpoint: POST /kyc/scan
- Accepts MerchantKYCInput
- Returns KYCDecisionOutput
- Processing time: < 5 minutes per application
"""

import logging
import time
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    from ..models.input_schema import MerchantKYCInput
    from ..models.output_schema import KYCDecisionOutput, KYCDecisionEnum
    from ..kyc_engine import KYCDecisionEngine
except ImportError:
    from models.input_schema import MerchantKYCInput
    from models.output_schema import KYCDecisionOutput, KYCDecisionEnum
    from kyc_engine import KYCDecisionEngine

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/kyc", tags=["KYC Site Scan"])


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: str


class ScanStatusResponse(BaseModel):
    """Scan status response for async queries"""
    scan_id: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    decision: Optional[str] = None
    message: Optional[str] = None


# In-memory scan status store (replace with Redis/DB in production)
_scan_status_store: dict = {}


def get_kyc_engine() -> KYCDecisionEngine:
    """Dependency injection for KYC engine"""
    return KYCDecisionEngine(logger=logger)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Service health status
    """
    return HealthResponse(
        status="healthy",
        version=KYCDecisionEngine.VERSION,
        timestamp=datetime.now().isoformat()
    )


@router.post("/scan", response_model=KYCDecisionOutput)
async def scan_merchant(
    input_data: MerchantKYCInput,
    engine: KYCDecisionEngine = Depends(get_kyc_engine)
) -> KYCDecisionOutput:
    """
    Perform synchronous KYC website screening.
    
    This endpoint performs a comprehensive website scan and returns
    a KYC decision (PASS/FAIL/ESCALATE) within 5 minutes.
    
    Args:
        input_data: Merchant KYC input data
        
    Returns:
        KYCDecisionOutput with decision, reason codes, and audit trail
        
    Raises:
        HTTPException: If scan fails or times out
    """
    start_time = time.monotonic()
    
    logger.info(f"[REST] Received KYC scan request for: {input_data.website_url}")
    
    try:
        # Run the KYC scan
        result = await engine.process(input_data)
        
        duration = time.monotonic() - start_time
        logger.info(
            f"[REST] KYC scan completed: {result.decision.value} "
            f"(duration: {duration:.2f}s)"
        )
        
        return result
        
    except Exception as e:
        duration = time.monotonic() - start_time
        logger.error(f"[REST] KYC scan failed after {duration:.2f}s: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "KYC scan failed",
                "message": str(e),
                "duration_seconds": duration
            }
        )


@router.post("/scan/validate", response_model=dict)
async def validate_input(input_data: MerchantKYCInput):
    """
    Validate merchant input data without performing scan.
    
    Useful for pre-validation before submitting full scan request.
    
    Args:
        input_data: Merchant KYC input data to validate
        
    Returns:
        Validation result with any warnings
    """
    warnings = []
    
    # Check URL accessibility hints
    url = input_data.website_url
    if not url.startswith('https://'):
        warnings.append({
            "field": "website_url",
            "message": "URL should use HTTPS for security"
        })
    
    # Check business type
    known_types = ['E-commerce', 'SaaS', 'Fintech', 'Retail', 'Services', 'Content']
    if input_data.declared_business_type not in known_types:
        warnings.append({
            "field": "declared_business_type",
            "message": f"Business type '{input_data.declared_business_type}' is not in standard list"
        })
    
    # Check product count
    if len(input_data.declared_products_services) > 20:
        warnings.append({
            "field": "declared_products_services",
            "message": "Large number of products may affect matching accuracy"
        })
    
    return {
        "valid": True,
        "warnings": warnings,
        "input_summary": {
            "merchant_name": input_data.merchant_legal_name,
            "website_url": input_data.website_url,
            "business_type": input_data.declared_business_type,
            "products_count": len(input_data.declared_products_services)
        }
    }


@router.get("/scan/{scan_id}/status", response_model=ScanStatusResponse)
async def get_scan_status(scan_id: str):
    """
    Get status of a KYC scan.
    
    Primarily used for async scans, but can also retrieve
    status of recently completed sync scans.
    
    Args:
        scan_id: Unique scan identifier
        
    Returns:
        Current scan status
        
    Raises:
        HTTPException: If scan_id not found
    """
    if scan_id not in _scan_status_store:
        raise HTTPException(
            status_code=404,
            detail={"error": "Scan not found", "scan_id": scan_id}
        )
    
    return _scan_status_store[scan_id]


@router.get("/decisions/summary")
async def get_decision_summary():
    """
    Get summary of KYC decision rules.
    
    Returns documentation of what triggers PASS/FAIL/ESCALATE.
    Useful for API consumers to understand decision logic.
    """
    return {
        "version": KYCDecisionEngine.VERSION,
        "decisions": {
            "PASS": {
                "description": "All mandatory compliance checks satisfied",
                "conditions": [
                    "Website is accessible",
                    "Privacy Policy present",
                    "Terms & Conditions present",
                    "No high-risk content detected",
                    "Legal entity matches (or unable to verify)"
                ]
            },
            "FAIL": {
                "description": "Critical compliance violation detected",
                "conditions": [
                    "Website unreachable or parked",
                    "Missing Privacy Policy (mandatory)",
                    "Missing Terms & Conditions (mandatory)",
                    "High-risk content detected (gambling, adult, weapons, drugs)",
                    "All checkout CTAs non-functional",
                    "SSL certificate error"
                ]
            },
            "ESCALATE": {
                "description": "Manual review required",
                "conditions": [
                    "Product/service mismatch",
                    "No checkout flow detected",
                    "Legal entity name mismatch",
                    "Medium-risk content detected",
                    "Missing refund policy (e-commerce)",
                    "Domain less than 6 months old",
                    "No contact information found"
                ]
            }
        },
        "note": "Deterministic rules cannot be overridden by AI interpretation"
    }


def update_scan_status(
    scan_id: str,
    status: str,
    decision: Optional[str] = None,
    message: Optional[str] = None
):
    """
    Update scan status in store.
    
    Called internally to track scan progress.
    """
    if scan_id not in _scan_status_store:
        _scan_status_store[scan_id] = ScanStatusResponse(
            scan_id=scan_id,
            status=status,
            started_at=datetime.now().isoformat()
        )
    else:
        _scan_status_store[scan_id].status = status
        
    if decision:
        _scan_status_store[scan_id].decision = decision
    if message:
        _scan_status_store[scan_id].message = message
    if status in ["completed", "failed"]:
        _scan_status_store[scan_id].completed_at = datetime.now().isoformat()

