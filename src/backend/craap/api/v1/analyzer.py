from typing import Optional

from fastapi import APIRouter, Form, Request, Response
import logging as logger

from src.backend.craap.model.data_model import AnalysisResponse
from datetime import datetime

from fastapi import HTTPException
import aiohttp
import asyncio
from src.backend.craap.processing.extractor import MetaTagExtractor
from urllib.parse import urlparse


def normalize_and_validate_url(raw_url: Optional[str]) -> str:
    """
    Normalize and validate a user-supplied URL.
    - Strips whitespace
    - If scheme is missing, assumes http://
    - Ensures scheme is http or https and netloc is present
    Raises HTTPException(status_code=422) when invalid.
    Returns the normalized URL string.
    """
    if not raw_url:
        raise HTTPException(status_code=422, detail=[{
            "type": "missing",
            "loc": ["body", "url"],
            "msg": "Field required",
            "input": None
        }])

    if not isinstance(raw_url, str):
        raise HTTPException(status_code=422, detail="URL must be a string")

    url = raw_url.strip()
    if url == "":
        raise HTTPException(status_code=422, detail="URL is empty")

    # If scheme is missing, assume http
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "http://" + url
        parsed = urlparse(url)

    # Validate scheme and netloc
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        raise HTTPException(status_code=422, detail=f"Invalid URL: {raw_url}")

    return url

router = APIRouter()


@router.options("/analyze/url")
async def analyze_url_options(response: Response):
    # Respond to CORS preflight requests
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return Response(status_code=204, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    })


async def fetch_html_content(url: str) -> str:
    """
    Fetch HTML content from a URL with proper headers and error handling
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=30) as response:
                if response.status  in [200, 201, 202]:
                    return await response.text()
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to fetch URL: HTTP {response.status}"
                    )
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=400, detail=f"Network error: {str(e)}")
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timeout")


@router.post("/analyze/url", response_model=AnalysisResponse)
async def analyze_url(request: Request, response: Response, url: Optional[str] = Form(None)):
    """
    Analyze a webpage by URL - accepts url from form-data, JSON body, or query param.
    """
    # Try form field first (used by the HTML form)
    resolved_url = url

    # If not provided via form, try JSON body (browser extension)
    if not resolved_url:
        try:
            payload = await request.json()
            if isinstance(payload, dict):
                resolved_url = payload.get("url")
        except Exception:
            # ignore JSON parse errors, we'll try query params next
            resolved_url = resolved_url

    # If still not found, try query params
    if not resolved_url:
        resolved_url = request.query_params.get("url")

    # Normalize and validate the resolved URL (raises HTTPException on failure)
    try:
        resolved_url = normalize_and_validate_url(resolved_url)
    except HTTPException:
        # re-raise to preserve status/detail
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid URL: {str(e)}")

    if not resolved_url:
        raise HTTPException(status_code=422, detail=[{
            "type": "missing",
            "loc": ["body", "url"],
            "msg": "Field required",
            "input": None
        }])

    # add fallback CORS headers on the actual response (in case global CORS middleware isn't active)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    logger.info(f"Analyzing URL: {resolved_url}")
    html_content = await fetch_html_content(resolved_url)

    extractor = MetaTagExtractor()
    meta_tags = await extractor.extract(html_content, resolved_url)

    # call the instance method instead of the standalone function
    print(extractor.convert_to_json(meta_tags))

    results = {"analysis_id": "placeholder_id", "confidence": 0.95, "status": "completed", "results": {}}
    return AnalysisResponse(
        analysis_id=results["analysis_id"],
        status=results["status"],
        results=results["results"],
        confidence=results["confidence"],
        processed_at=datetime.utcnow().isoformat(),
        raw_meta_tags= extractor.convert_to_json(meta_tags)
    )