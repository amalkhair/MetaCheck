from bs4 import BeautifulSoup
from datetime import datetime
import dataclasses, json, dateutil.parser
from typing import Optional, List, Any
from src.backend.craap.model.data_model import MetaTagData

class MetaTagExtractor:
    """Extracts metadata from HTML meta tags."""

    async def extract(self, html_content: str, url: str) -> MetaTagData:
        soup = BeautifulSoup(html_content, "html.parser")
        return MetaTagData(
            title=self.extract_title(soup),
            author=self.extract_author(soup),
            description=self.extract_description(soup),
            publication_date=self.extract_publication_date(soup),
            last_modification_date=self.extract_mod_date(soup),
            keywords=self.extract_keywords(soup),
            publisher=self.extract_publisher(soup),
            language=self.extract_language(soup),
            url=url,
        )

    def extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        el = soup.select_one('meta[property="og:title"], meta[name="twitter:title"], title')
        if el:
            if el.name == "title":
                return el.get_text(strip=True)
            return el.get("content", None)
        return None

    def extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        el = soup.select_one('meta[name="author"], meta[property="article:author"], meta[property="og:author"]')
        return el.get("content").strip() if el and el.has_attr("content") else None

    def extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        el = soup.select_one('meta[name="description"], meta[property="og:description"], meta[name="twitter:description"]')
        return el.get("content").strip() if el and el.has_attr("content") else None

    def extract_publication_date(self, soup: BeautifulSoup) -> Optional[str]:
        el = soup.select_one(
            'meta[property="article:published_time"], '
            'meta[name="publication_date"], meta[name="publish_date"], '
            'meta[name="date"], meta[property="og:published_time"], time[datetime]'
        )
        if el:
            value = el.get("content") or el.get("datetime")
            if value:
                try:
                    return dateutil.parser.parse(value).isoformat()
                except Exception:
                    return None
        return None

    def extract_mod_date(self, soup: BeautifulSoup) -> Optional[str]:
        el = soup.select_one(
            'meta[property="article:modified_time"], '
            'meta[name="last_modified"], meta[name="modification_date"], '
            'meta[property="og:updated_time"]'
        )
        if el and el.has_attr("content"):
            try:
                return dateutil.parser.parse(el["content"]).isoformat()
            except Exception:
                return None
        return None

    def extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        kws = []
        el = soup.find("meta", attrs={"name": "keywords"})
        if el and el.get("content"):
            kws += [k.strip() for k in el["content"].split(",")]
        el2 = soup.find("meta", attrs={"name": "news_keywords"})
        if el2 and el2.get("content"):
            kws += [k.strip() for k in el2["content"].split(",")]
        # de-dup while preserving order
        seen = set()
        return [k for k in kws if not (k in seen or seen.add(k))]

    def extract_publisher(self, soup: BeautifulSoup) -> Optional[str]:
        el = soup.select_one('meta[name="publisher"], meta[property="og:site_name"], meta[name="application-name"]')
        return el.get("content").strip() if el and el.has_attr("content") else None

    def extract_language(self, soup: BeautifulSoup) -> Optional[str]:
        el = soup.find("meta", attrs={"http-equiv": "content-language"})
        if el and el.get("content"):
            return el["content"].strip()
        html = soup.find("html")
        if html and html.get("lang"):
            return html["lang"].strip()
        return None

    # ---- serialization helper ----
    def convert_to_json(self, meta: MetaTagData, *, indent: int = 2) -> str:
        def _to_primitive(obj: Any):
            if dataclasses.is_dataclass(obj):
                obj = dataclasses.asdict(obj)
            if isinstance(obj, dict):
                return {k: _to_primitive(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [_to_primitive(v) for v in obj]
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        return json.dumps(_to_primitive(meta), ensure_ascii=False, indent=indent)
