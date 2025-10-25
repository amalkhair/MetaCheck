import logging
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from src.backend.craap.api import analyzer

logging.basicConfig(level=logging.INFO)
app = FastAPI(
    title="MetaCheck API (Prototype)",
    description="Experimental backend for metadata extraction (PoC)",
    version="1.0.0",
)

# Open CORS for local testing; restrict later if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(analyzer.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.backend.main:app", host="0.0.0.0", port=8000, reload=True)
