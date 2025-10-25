from fastapi import APIRouter, HTTPException, Body
import aiohttp
from src.backend.craap.processing.extractor import MetaTagExtractor

router = APIRouter()

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)

@router.post("/analyze/url")
async def analyze_url(url: str):
    """
    POST body shape: {"url": "https://example.com"}
    Returns: {"url": "...", "metadata": {...}}
    """
    headers = {"User-Agent": USER_AGENT}
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        try:
            async with session.get(url, allow_redirects=True, ssl=False) as resp:
                # many sites require a UA; ssl=False helps on some corp proxies (okay for PoC)
                if resp.status != 200:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to fetch URL (HTTP {resp.status})"
                    )
                html = await resp.text()
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=400, detail=f"Network error: {e}")

    extractor = MetaTagExtractor()
    meta = await extractor.extract(html, url)
    return {"url": url, "metadata": extractor.convert_to_json(meta)}
