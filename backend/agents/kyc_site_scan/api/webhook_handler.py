"""
Webhook API Handler for KYC Site Scan
Asynchronous API with webhook callbacks

Endpoint: POST /kyc/scan/async
- Accepts MerchantKYCInput + callback_url
- Returns job_id immediately
- Sends webhook callback with results when complete
"""

import asyncio
import logging
import time
import uuid
import httpx
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl, Field

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
router = APIRouter(prefix="/kyc", tags=["KYC Site Scan Async"])


class JobStatus(str, Enum):
    """Job status enumeration"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CALLBACK_SENT = "callback_sent"
    CALLBACK_FAILED = "callback_failed"


class AsyncScanRequest(BaseModel):
    """Request model for async scan"""
    merchant_data: MerchantKYCInput
    callback_url: str = Field(
        ...,
        description="URL to receive webhook callback with results"
    )
    callback_headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional headers to include in callback request"
    )
    reference_id: Optional[str] = Field(
        default=None,
        description="Client's reference ID to include in callback"
    )


class AsyncScanResponse(BaseModel):
    """Response model for async scan submission"""
    job_id: str
    status: JobStatus
    message: str
    submitted_at: str
    callback_url: str
    estimated_completion_seconds: int = Field(
        default=300,
        description="Estimated time to completion"
    )


class JobStatusResponse(BaseModel):
    """Response model for job status query"""
    job_id: str
    status: JobStatus
    submitted_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    decision: Optional[str] = None
    callback_status: Optional[str] = None
    callback_attempts: int = 0
    error_message: Optional[str] = None


class WebhookPayload(BaseModel):
    """Payload sent to callback URL"""
    job_id: str
    reference_id: Optional[str] = None
    status: str
    completed_at: str
    duration_seconds: float
    result: Optional[KYCDecisionOutput] = None
    error: Optional[str] = None


class WebhookManager:
    """
    Manages async scan jobs and webhook callbacks.
    
    In production, replace with Redis/Celery for distributed processing.
    """
    
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._engine = KYCDecisionEngine(logger=logger)
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for webhooks"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
    
    async def submit_job(
        self,
        merchant_data: MerchantKYCInput,
        callback_url: str,
        callback_headers: Optional[Dict[str, str]] = None,
        reference_id: Optional[str] = None,
    ) -> str:
        """
        Submit a new async scan job.
        
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        
        self._jobs[job_id] = {
            "status": JobStatus.QUEUED,
            "submitted_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "merchant_data": merchant_data,
            "callback_url": callback_url,
            "callback_headers": callback_headers or {},
            "reference_id": reference_id,
            "result": None,
            "error": None,
            "callback_status": None,
            "callback_attempts": 0,
        }
        
        logger.info(f"[WEBHOOK] Job {job_id} queued for {merchant_data.website_url}")
        return job_id
    
    async def process_job(self, job_id: str) -> None:
        """
        Process a queued job and send webhook callback.
        """
        if job_id not in self._jobs:
            logger.error(f"[WEBHOOK] Job {job_id} not found")
            return
        
        job = self._jobs[job_id]
        job["status"] = JobStatus.PROCESSING
        job["started_at"] = datetime.now().isoformat()
        
        start_time = time.monotonic()
        
        try:
            logger.info(f"[WEBHOOK] Processing job {job_id}")
            
            # Run KYC scan
            result = await self._engine.process(job["merchant_data"])
            
            duration = time.monotonic() - start_time
            
            job["status"] = JobStatus.COMPLETED
            job["completed_at"] = datetime.now().isoformat()
            job["result"] = result
            job["duration_seconds"] = duration
            
            logger.info(
                f"[WEBHOOK] Job {job_id} completed: {result.decision.value} "
                f"(duration: {duration:.2f}s)"
            )
            
            # Send webhook callback
            await self._send_callback(job_id)
            
        except Exception as e:
            duration = time.monotonic() - start_time
            
            job["status"] = JobStatus.FAILED
            job["completed_at"] = datetime.now().isoformat()
            job["error"] = str(e)
            job["duration_seconds"] = duration
            
            logger.error(f"[WEBHOOK] Job {job_id} failed: {e}", exc_info=True)
            
            # Send error callback
            await self._send_callback(job_id, error=str(e))
    
    async def _send_callback(
        self,
        job_id: str,
        error: Optional[str] = None,
        retry_count: int = 3
    ) -> bool:
        """
        Send webhook callback to the registered URL.
        
        Implements retry logic with exponential backoff.
        """
        if job_id not in self._jobs:
            return False
        
        job = self._jobs[job_id]
        callback_url = job["callback_url"]
        
        # Build payload
        payload = WebhookPayload(
            job_id=job_id,
            reference_id=job.get("reference_id"),
            status="completed" if not error else "failed",
            completed_at=job.get("completed_at", datetime.now().isoformat()),
            duration_seconds=job.get("duration_seconds", 0),
            result=job.get("result") if not error else None,
            error=error,
        )
        
        headers = {
            "Content-Type": "application/json",
            "X-KYC-Job-ID": job_id,
            "X-KYC-Webhook-Version": "1.0",
            **job.get("callback_headers", {})
        }
        
        client = await self._get_http_client()
        
        for attempt in range(retry_count):
            try:
                job["callback_attempts"] += 1
                
                logger.info(
                    f"[WEBHOOK] Sending callback for job {job_id} "
                    f"(attempt {attempt + 1}/{retry_count})"
                )
                
                response = await client.post(
                    callback_url,
                    json=payload.model_dump(mode='json'),
                    headers=headers,
                )
                
                if response.status_code in [200, 201, 202, 204]:
                    job["callback_status"] = "success"
                    job["status"] = JobStatus.CALLBACK_SENT
                    logger.info(f"[WEBHOOK] Callback sent successfully for job {job_id}")
                    return True
                else:
                    logger.warning(
                        f"[WEBHOOK] Callback failed for job {job_id}: "
                        f"status {response.status_code}"
                    )
                    
            except Exception as e:
                logger.warning(
                    f"[WEBHOOK] Callback error for job {job_id} "
                    f"(attempt {attempt + 1}): {e}"
                )
            
            # Exponential backoff
            if attempt < retry_count - 1:
                await asyncio.sleep(2 ** attempt)
        
        job["callback_status"] = "failed"
        job["status"] = JobStatus.CALLBACK_FAILED
        logger.error(f"[WEBHOOK] All callback attempts failed for job {job_id}")
        return False
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current job status"""
        return self._jobs.get(job_id)
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Clean up old completed jobs.
        
        Returns:
            Number of jobs cleaned up
        """
        # In production, implement proper cleanup
        # This is a placeholder for memory management
        return 0


# Global webhook manager instance
webhook_manager = WebhookManager()


@router.post("/scan/async", response_model=AsyncScanResponse)
async def submit_async_scan(
    request: AsyncScanRequest,
    background_tasks: BackgroundTasks
) -> AsyncScanResponse:
    """
    Submit asynchronous KYC scan job.
    
    The scan runs in the background and results are delivered
    via webhook callback to the specified URL.
    
    Args:
        request: Async scan request with merchant data and callback URL
        
    Returns:
        Job submission confirmation with job_id
    """
    logger.info(f"[WEBHOOK] Async scan request for: {request.merchant_data.website_url}")
    
    # Validate callback URL (basic check)
    if not request.callback_url.startswith(('http://', 'https://')):
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid callback URL", "message": "URL must start with http:// or https://"}
        )
    
    # Submit job
    job_id = await webhook_manager.submit_job(
        merchant_data=request.merchant_data,
        callback_url=request.callback_url,
        callback_headers=request.callback_headers,
        reference_id=request.reference_id,
    )
    
    # Queue background processing
    background_tasks.add_task(webhook_manager.process_job, job_id)
    
    return AsyncScanResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        message="KYC scan job queued successfully",
        submitted_at=datetime.now().isoformat(),
        callback_url=request.callback_url,
        estimated_completion_seconds=300,
    )


@router.get("/scan/async/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get status of an async scan job.
    
    Args:
        job_id: Job identifier returned from submit endpoint
        
    Returns:
        Current job status
        
    Raises:
        HTTPException: If job not found
    """
    job = webhook_manager.get_job_status(job_id)
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"error": "Job not found", "job_id": job_id}
        )
    
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        submitted_at=job["submitted_at"],
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        decision=job["result"].decision.value if job.get("result") else None,
        callback_status=job.get("callback_status"),
        callback_attempts=job.get("callback_attempts", 0),
        error_message=job.get("error"),
    )


@router.post("/scan/async/{job_id}/retry-callback")
async def retry_callback(job_id: str) -> dict:
    """
    Manually retry webhook callback for a completed job.
    
    Useful if the original callback failed and the system
    has since been fixed.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Retry status
    """
    job = webhook_manager.get_job_status(job_id)
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"error": "Job not found", "job_id": job_id}
        )
    
    if job["status"] not in [JobStatus.COMPLETED, JobStatus.CALLBACK_FAILED]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Cannot retry callback",
                "message": f"Job status is {job['status']}, must be completed or callback_failed"
            }
        )
    
    success = await webhook_manager._send_callback(job_id)
    
    return {
        "job_id": job_id,
        "retry_status": "success" if success else "failed",
        "callback_attempts": job.get("callback_attempts", 0)
    }


@router.get("/scan/async/{job_id}/result", response_model=KYCDecisionOutput)
async def get_job_result(job_id: str) -> KYCDecisionOutput:
    """
    Get full result of a completed async scan job.
    
    Alternative to webhook - allows polling for results.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Full KYC decision output
        
    Raises:
        HTTPException: If job not found or not completed
    """
    job = webhook_manager.get_job_status(job_id)
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"error": "Job not found", "job_id": job_id}
        )
    
    if job["status"] not in [JobStatus.COMPLETED, JobStatus.CALLBACK_SENT, JobStatus.CALLBACK_FAILED]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Job not completed",
                "status": job["status"],
                "message": "Please wait for job to complete"
            }
        )
    
    if not job.get("result"):
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Result not available",
                "message": job.get("error", "Unknown error")
            }
        )
    
    return job["result"]

