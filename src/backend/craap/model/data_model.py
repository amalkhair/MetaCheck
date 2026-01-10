from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pydantic import BaseModel
from pydantic.types import Json


class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    results: Dict[str, Any]
    confidence: float
    processed_at: str
    raw_meta_tags: Optional[Json[Dict[str, Any]]] = None

@dataclass
class MetaTagData:
    """Structured representation of HTML meta tag data"""
    publication_date: Optional[str] = None
    last_modification_date: Optional[str] = None
    author: Optional[str] = None
    authors: List[str] = None
    description: Optional[str] = None
    keywords: List[str] = None
    publisher: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    language: Optional[str] = None
    content_type: Optional[str] = None
    generator: Optional[str] = None
    viewport: Optional[str] = None
    robots: Optional[str] = None
    refresh: Optional[str] = None
    reputation: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None # Primary resolved IP address for the URL (first from resolve_ips), optional

    def __post_init__(self):
        if self.authors is None:
            self.authors = []
        if self.keywords is None:
            self.keywords = []
        if self.author and not self.authors:
            self.authors = [self.author]
