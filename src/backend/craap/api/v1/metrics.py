# File: `api/health.py`
import logging
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """Check API health status"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )
@router.get("/")
async def root():
    return {
        "message": "MetaCheck API",
        "version": "1.0.0",
        "endpoints": {
            "analyze_url": "POST /analyze/url",
            "analyze_html": "POST /analyze/html",
            "health": "GET /health",
            "metrics": "GET /metrics"
        }
    }