# python
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.craap.api.v1 import analyzer, metrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MetaCheck API",
    description="Semi-automated credibility assessment tool based on CRAAP framework",
    version="1.0.0"
)

# CORS middleware for browser extension
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["chrome-extension://*", "moz-extension://*"],
    allow_origins=["*"],  # In production, restrict to your extension IDs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(metrics.router)
app.include_router(analyzer.router)


@app.get("/ping")
async def ping():
    return {"status": "ok"}


if __name__ == "__main__":
    import sys
    import uvicorn

    # If a debugger is attached, disable the reloader (it triggers the problematic path).
    debug = sys.gettrace() is not None
    # Use an import string for the app to avoid some debugger-related asyncio issues:
    uvicorn.run("src.backend.craap.main:app", host="0.0.0.0", port=10124,reload=not debug)