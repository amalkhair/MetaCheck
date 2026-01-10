from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup
import dateutil.parser
import dataclasses
import json
from typing import Any
from urllib.parse import unquote, quote
import requests
import os
from urllib.parse import urlparse
from src.backend.craap.processing.check_reputation import resolve_ips, reputation_summary
from src.backend.craap.model.data_model import MetaTagData


class MetaTagExtractor:
    """Extracts metadata from HTML meta tags"""

    async def extract(self, html_content: str, url: str) -> MetaTagData:
        """Extract metadata from HTML meta tags"""
        soup = BeautifulSoup(html_content, 'html.parser')

        # First, extract from HTML/meta tags as before
        extracted = MetaTagData(
            publication_date=self.extract_publication_date(soup),
            last_modification_date=self.extract_modification_date(soup),
            author=self.extract_author(soup),
            authors=self.extract_authors(soup),
            description=self.extract_description(soup),
            keywords=self.extract_keywords(soup),
            publisher=self.extract_publisher(soup),
            title=self.extract_title(soup),
            url=url,
            doi=self.extract_doi(soup, url),
            language=self.extract_language(soup),
            content_type=self.extract_content_type(soup),
            generator=self.extract_generator(soup),
            viewport=self.extract_viewport(soup),
            robots=self.extract_robots(soup),
            refresh=self.extract_refresh(soup)
        )

        # If we have a DOI, prefer authoritative metadata from DataCite API and overwrite fields
        doi_val = extracted.doi
        if doi_val:
            # normalize doi for API path (strip leading doi: if present)
            norm = doi_val
            if norm.lower().startswith('doi:'):
                norm = norm.split(':', 1)[1]
            # protect slashes while still keeping them (DataCite expects slashes unencoded)
            api_path = quote(norm, safe='/:')
            api_url = f'https://api.datacite.org/dois/{api_path}'
            try:
                resp = requests.get(api_url, timeout=6)
                if resp.status_code == 200:
                    j = resp.json()
                    # traverse to attributes if present
                    attrs = j.get('data', {}).get('attributes', {}) if isinstance(j, dict) else {}
                    # Titles -> title (take first)
                    titles = attrs.get('titles') or []
                    if titles and isinstance(titles, list):
                        first = titles[0]
                        if isinstance(first, dict) and first.get('title'):
                            extracted.title = first.get('title')
                        elif isinstance(first, str):
                            extracted.title = first

                    # Descriptions -> description (prefer Abstract/first descriptionType)
                    descs = attrs.get('descriptions') or []
                    if descs and isinstance(descs, list):
                        # prefer descriptionType == 'Abstract'
                        picked = None
                        for d in descs:
                            if isinstance(d, dict) and d.get('descriptionType', '').lower() == 'abstract' and d.get('description'):
                                picked = d.get('description'); break
                        if not picked and isinstance(descs[0], dict):
                            picked = descs[0].get('description')
                        if picked:
                            extracted.description = picked

                    # Publisher
                    if attrs.get('publisher'):
                        extracted.publisher = attrs.get('publisher')

                    # Dates: map Issued -> publication_date, Updated -> last_modification_date, Available -> publication_date if missing
                    dates = attrs.get('dates') or []
                    for d in dates:
                        if not isinstance(d, dict):
                            continue
                        dt = d.get('date')
                        dtype = d.get('dateType', '').lower()
                        if dt and dtype:
                            if dtype == 'issued':
                                extracted.publication_date = dt
                            elif dtype == 'updated':
                                extracted.last_modification_date = dt
                            elif dtype == 'available' and not extracted.publication_date:
                                extracted.publication_date = dt

                    # Creators -> authors list
                    creators = attrs.get('creators') or []
                    if creators and isinstance(creators, list):
                        names = []
                        for c in creators:
                            if isinstance(c, dict):
                                name = c.get('name')
                                if not name:
                                    gn = c.get('givenName') or ''
                                    fn = c.get('familyName') or ''
                                    name = (gn + ' ' + fn).strip() if (gn or fn) else None
                                if name:
                                    names.append(name)
                            elif isinstance(c, str):
                                names.append(c)
                        if names:
                            extracted.authors = names
                            extracted.author = names[0]

                    # Subjects -> keywords
                    subjects = attrs.get('subjects') or []
                    if subjects and isinstance(subjects, list):
                        kw = []
                        for s in subjects:
                            if isinstance(s, dict):
                                subj = s.get('subject')
                            else:
                                subj = s
                            if subj:
                                kw.append(subj)
                        if kw:
                            extracted.keywords = kw

                    # Language
                    if attrs.get('language'):
                        extracted.language = attrs.get('language')

                    # DOI canonical
                    if attrs.get('doi'):
                        extracted.doi = 'doi:' + attrs.get('doi')

                    # Related identifiers: prefer URL or DOI related identifiers to set url/doi
                    related = attrs.get('relatedIdentifiers') or []
                    if related and isinstance(related, list):
                        for r in related:
                            if not isinstance(r, dict):
                                continue
                            rtype = (r.get('relatedIdentifierType') or '').upper()
                            rel = r.get('relatedIdentifier')
                            if rel and rtype == 'URL' and (not extracted.url or extracted.url == url):
                                extracted.url = rel
                            if rel and rtype == 'DOI' and not extracted.doi:
                                # ensure canonical doi: prefix
                                val = rel.strip()
                                if val.lower().startswith('doi:'):
                                    extracted.doi = val
                                else:
                                    extracted.doi = 'doi:' + val

                    # Locations / canonical URL: DataCite sometimes exposes locations/associatedLocations or landingPage-like fields
                    # prefer attrs['url'] or attrs['locations'] if present
                    if not extracted.url:
                        # try a few common fields
                        url_field = attrs.get('url') or attrs.get('landingPage') or None
                        if url_field and isinstance(url_field, str):
                            extracted.url = url_field
                        else:
                            locs = attrs.get('locations') or []
                            if isinstance(locs, list) and locs:
                                # try to pick the first location with a 'url' key
                                for loc in locs:
                                    if isinstance(loc, dict) and loc.get('url'):
                                        extracted.url = loc.get('url')
                                        break

                    # Publication year fallback
                    if not extracted.publication_date and attrs.get('publicationYear'):
                        extracted.publication_date = str(attrs.get('publicationYear'))

                    # Types -> content_type or resource type general
                    types = attrs.get('types') or {}
                    if isinstance(types, dict):
                        extracted.content_type = types.get('resourceTypeGeneral') or types.get('citeproc') or types.get('ris')

                    # Contributors -> could be added to keywords or ignored; here we append their names to keywords as informative data
                    contributors = attrs.get('contributors') or []
                    if contributors and isinstance(contributors, list):
                        contrib_names = []
                        for c in contributors:
                            if isinstance(c, dict):
                                n = c.get('name')
                                if n:
                                    contrib_names.append(n)
                        if contrib_names:
                            extracted.keywords = (extracted.keywords or []) + contrib_names
            except Exception:
                # On network errors or parsing errors, fall back to extracted HTML metadata
                pass

        # After enrichment, attempt to get IP reputation using IPQualityScore (if API key configured)
        try:
            api_key = os.environ.get('ipqualityscore_api_key')
            if api_key:
                # derive hostname from the original URL
                parsed = urlparse(url)
                host = parsed.hostname if parsed else None
                if host:
                    try:
                        ips = resolve_ips(host, prefer_ipv4=True)
                        if ips:
                            # store the primary IP on the meta object
                            extracted.ip_address = ips[0]
                            # query the first IP for a compact summary; do not raise on failure
                            try:
                                rep = reputation_summary(api_key, ips[0], strict=False, timeout=6)
                                extracted.reputation = rep
                            except Exception:
                                extracted.reputation = None
                    except Exception:
                        extracted.reputation = None
        except Exception:
            # ensure extractor never raises due to reputation lookup
            extracted.reputation = None

        return extracted

    def extract_publication_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publication date from meta tags"""
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publication_date"]',
            'meta[name="publish_date"]',
            'meta[name="date"]',
            'meta[property="og:published_time"]',
            'meta[name="publish-date"]',
            'meta[name="article:published_time"]',
            'time[datetime]'
        ]

        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date_value = element.get('content') or element.get('datetime')
                if date_value:
                    parsed_date = self.parse_date(date_value)
                    if parsed_date:
                        return parsed_date.isoformat()
        return None

    def extract_modification_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract last modification date from meta tags"""
        date_selectors = [
            'meta[property="article:modified_time"]',
            'meta[name="last_modified"]',
            'meta[name="modification_date"]',
            'meta[property="og:updated_time"]'
        ]

        for selector in date_selectors:
            element = soup.select_one(selector)
            if element and (date_value := element.get('content')):
                parsed_date = self.parse_date(date_value)
                if parsed_date:
                    return parsed_date.isoformat()
        return None

    def extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract primary author from meta tags"""
        author_selectors = [
            'meta[name="author"]',
            'meta[property="article:author"]',
            'meta[property="og:author"]',
            'meta[name="twitter:creator"]'
        ]

        for selector in author_selectors:
            element = soup.select_one(selector)
            if element and (author := element.get('content')):
                return author.strip()
        return None

    def extract_authors(self, soup: BeautifulSoup) -> List[str]:
        """Extract multiple authors from meta tags and content"""
        authors = []

        # From meta tags
        author_elements = soup.select('meta[name="author"], meta[property="article:author"]')
        for element in author_elements:
            if author := element.get('content'):
                authors.extend([a.strip() for a in author.split(',')])

        # Remove duplicates while preserving order
        seen = set()
        return [a for a in authors if not (a in seen or seen.add(a))]

    def extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from meta tags"""
        description_selectors = [
            'meta[name="description"]',
            'meta[property="og:description"]',
            'meta[name="twitter:description"]'
        ]

        for selector in description_selectors:
            element = soup.select_one(selector)
            if element and (description := element.get('content')):
                return description.strip()
        return None

    def extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract keywords from meta tags"""
        keywords = []

        # Standard keywords meta tag
        keywords_element = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_element and (keywords_content := keywords_element.get('content')):
            keywords.extend([k.strip() for k in keywords_content.split(',')])

        # News keywords
        news_keywords = soup.find('meta', attrs={'name': 'news_keywords'})
        if news_keywords and (news_content := news_keywords.get('content')):
            keywords.extend([k.strip() for k in news_content.split(',')])

        return keywords

    def extract_publisher(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publisher from meta tags"""
        publisher_selectors = [
            'meta[name="publisher"]',
            'meta[property="og:site_name"]',
            'meta[name="application-name"]'
        ]

        for selector in publisher_selectors:
            element = soup.select_one(selector)
            if element and (publisher := element.get('content')):
                return publisher.strip()
        return None

    def extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract title from meta tags and page title"""
        title_selectors = [
            'meta[property="og:title"]',
            'meta[name="twitter:title"]',
            'title'
        ]

        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get('content') or element.get_text()
                if title and title.strip():
                    return title.strip()
        return None

    def extract_language(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract language from meta tags and html lang attribute"""
        # From meta tags
        lang_element = soup.find('meta', attrs={'http-equiv': 'content-language'})
        if lang_element and (lang := lang_element.get('content')):
            return lang.strip()

        # From html lang attribute
        html_element = soup.find('html')
        if html_element and (lang := html_element.get('lang')):
            return lang.strip()

        return None

    def extract_content_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract content type from meta tags"""
        content_type_element = soup.find('meta', attrs={'http-equiv': 'content-type'})
        if content_type_element and (content_type := content_type_element.get('content')):
            return content_type.strip()
        return None

    def extract_generator(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract generator from meta tags"""
        generator_element = soup.find('meta', attrs={'name': 'generator'})
        if generator_element and (generator := generator_element.get('content')):
            return generator.strip()
        return None

    def extract_viewport(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract viewport from meta tags"""
        viewport_element = soup.find('meta', attrs={'name': 'viewport'})
        if viewport_element and (viewport := viewport_element.get('content')):
            return viewport.strip()
        return None

    def extract_robots(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract robots directive from meta tags"""
        robots_element = soup.find('meta', attrs={'name': 'robots'})
        if robots_element and (robots := robots_element.get('content')):
            return robots.strip()
        return None

    def extract_refresh(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract refresh directive from meta tags"""
        refresh_element = soup.find('meta', attrs={'http-equiv': 'refresh'})
        if refresh_element and (refresh := refresh_element.get('content')):
            return refresh.strip()
        return None

    def parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse various date formats into datetime object"""
        try:
            return dateutil.parser.parse(date_string)
        except (ValueError, TypeError):
            return None

    def extract_doi(self, soup: BeautifulSoup, page_url: str) -> Optional[str]:
        """Attempt to extract a DOI from meta tags, links, or page text.

        Returns a canonical DOI string like '10.1234/abcde' when found, or None.
        """
        # If the page URL contains an embedded DOI (e.g. ?persistentId=doi:10...),
        # return a value prefixed with 'doi:' as requested (note: this will produce
        # 'doi:doi:10.1234/...' as the user asked).
        try:
            decoded_url = unquote(page_url or '')
        except Exception:
            decoded_url = page_url or ''
        lower_decoded = decoded_url.lower()
        idx = lower_decoded.find('doi:')
        if idx != -1:
            # extract from the first occurrence of 'doi:' until &, # or end
            doi_fragment = decoded_url[idx:]
            for sep in ('&', '#'):
                pos = doi_fragment.find(sep)
                if pos != -1:
                    doi_fragment = doi_fragment[:pos]
                    break
            doi_fragment = doi_fragment.strip()
            if doi_fragment:
                # Normalize the fragment so we don't return 'doi:doi:...'
                # If the fragment already starts with 'doi:' (case-insensitive), return it as-is.
                if doi_fragment.lower().startswith('doi:'):
                    return doi_fragment
                # Otherwise prefix a single 'doi:'
                return 'doi:' + doi_fragment

        # Common meta tags for DOI
        doi_selectors = [
            'meta[name="citation_doi"]',
            'meta[name="dc.identifier"]',
            'meta[name="dc.identifier.doi"]',
            'meta[name="doi"]',
            'meta[property="og:doi"]'
        ]

        for sel in doi_selectors:
            el = soup.select_one(sel)
            if el:
                val = el.get('content') or el.get('value')
                if val:
                    v = val.strip()
                    if v:
                        # normalize if it's a DOI URL
                        if 'doi.org' in v:
                            # extract part after the domain
                            parts = v.split('/')
                            doi_candidate = '/'.join(parts[3:]) if len(parts) > 3 else parts[-1]
                            return doi_candidate
                        # strip leading 'doi:' if present
                        if v.lower().startswith('doi:'):
                            return v.split(':', 1)[1].strip()
                        return v

        # look for links to doi.org
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'doi.org' in href:
                try:
                    parts = href.split('/')
                    doi_candidate = '/'.join(parts[3:]) if len(parts) > 3 else parts[-1]
                    doi_candidate = doi_candidate.strip()
                    if doi_candidate:
                        return doi_candidate
                except Exception:
                    continue

        # fallback: search page text for DOI pattern 10.<digits>/<suffix>
        # build a whitespace-joined, stripped text using stripped_strings to avoid signature issues
        text = ' '.join(soup.stripped_strings)
        import re
        # basic DOI regex (not exhaustive but practical)
        m = re.search(r'\b(10\.\d{4,9}/\S+?)\b', text)
        if m:
            return m.group(1).rstrip('.,;')

        # If no DOI found, return the page URL as a fallback
        return None

    def convert_to_json(self, meta: MetaTagData, *, indent: int = 2) -> str:
        """
        Convert a MetaTagData instance to a JSON string.
        - Supports dataclasses or objects with `__dict__`.
        - Converts datetime objects to ISO 8601 strings.
        """
        def _to_primitive(obj: Any) -> Any:
            if obj is None or isinstance(obj, (str, int, float, bool)):
                return obj
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, dict):
                return {k: _to_primitive(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple, set)):
                return [_to_primitive(v) for v in obj]
            if dataclasses.is_dataclass(obj):
                return _to_primitive(dataclasses.asdict(obj))
            if hasattr(obj, "__dict__"):
                return _to_primitive(vars(obj))
            return str(obj)

        primitive = _to_primitive(meta)
        return json.dumps(primitive, ensure_ascii=False, indent=indent)