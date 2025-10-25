from dataclasses import dataclass
from typing import Optional, List

@dataclass
class MetaTagData:
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    publication_date: Optional[str] = None
    last_modification_date: Optional[str] = None
    keywords: List[str] = None
    publisher: Optional[str] = None
    language: Optional[str] = None
    url: Optional[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
