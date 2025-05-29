"""
Search engine management for DeepResearch system.
Supports multiple search engines with unified interface.
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

import requests
from duckduckgo_search import DDGS

from utils.logger import LoggerMixin
from config import config


def extract_domain_from_url(url: str) -> str:
    """
    Extract domain name from URL for display as source.
    
    Args:
        url: Full URL string
        
    Returns:
        Domain name or 'unknown' if extraction fails
    """
    try:
        if not url:
            return 'unknown'
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Remove 'www.' prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain if domain else 'unknown'
    except Exception:
        return 'unknown'


class SearchEngine(Enum):
    """Supported search engines."""
    TAVILY = "tavily"
    DUCKDUCKGO = "duckduckgo"
    BRAVE = "brave"
    GOOGLE = "google"
    BING = "bing"
    ARXIV = "arxiv"


@dataclass
class SearchResult:
    """Standard search result format."""
    title: str
    url: str
    snippet: str
    source: str
    rank: int = 0
    metadata: Optional[Dict[str, Any]] = None


class BaseSearchEngine(ABC, LoggerMixin):
    """Base class for search engine implementations."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        """
        Initialize search engine.
        
        Args:
            config_dict: Search engine configuration
        """
        self.config = config_dict
        self.timeout = config_dict.get('timeout', 30)
        self.max_results = config_dict.get('max_results', 10)
    
    @abstractmethod
    def search(self, query: str, max_results: Optional[int] = None) -> List[SearchResult]:
        """
        Perform search query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
        
        Returns:
            List of search results
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if search engine is available."""
        pass


class DuckDuckGoSearch(BaseSearchEngine):
    """DuckDuckGo search implementation with rate limiting."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        super().__init__(config_dict)
        self.last_request_time = 0
        self.min_request_interval = 2.0  # Minimum 2 seconds between requests
        self.rate_limit_backoff = 30.0  # 30 seconds backoff for rate limits
        self.max_retries = 3
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[SearchResult]:
        """Perform DuckDuckGo search with rate limiting."""
        max_results = max_results or self.max_results
        
        for attempt in range(self.max_retries):
            try:
                # Rate limiting: ensure minimum interval between requests
                current_time = time.time()
                time_since_last = current_time - self.last_request_time
                if time_since_last < self.min_request_interval:
                    sleep_time = self.min_request_interval - time_since_last
                    self.log_debug(f"Rate limiting: sleeping for {sleep_time:.1f}s")
                    time.sleep(sleep_time)
                
                self.log_info(f"Searching DuckDuckGo for: {query} (attempt {attempt + 1})")
                
                # Initialize DDGS without proxies to avoid compatibility issues
                ddgs = DDGS()
                results = []
                for i, result in enumerate(ddgs.text(query, max_results=max_results)):
                    if i >= max_results:
                        break
                    
                    search_result = SearchResult(
                        title=result.get('title', ''),
                        url=result.get('href', ''),
                        snippet=result.get('body', ''),
                        source=extract_domain_from_url(result.get('href', '')),
                        rank=i + 1
                    )
                    results.append(search_result)
                
                self.last_request_time = time.time()
                self.log_info(f"Found {len(results)} results from DuckDuckGo")
                return results
                    
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check for rate limiting indicators
                if any(indicator in error_msg for indicator in [
                    'rate limit', 'ratelimit', '202', '429', 'too many requests',
                    'blocked', 'throttle', 'quota exceeded'
                ]):
                    backoff_time = self.rate_limit_backoff * (2 ** attempt)  # Exponential backoff
                    self.log_warning(f"DuckDuckGo rate limit detected (attempt {attempt + 1}): {e}")
                    
                    if attempt < self.max_retries - 1:
                        self.log_info(f"Backing off for {backoff_time:.1f}s before retry")
                        time.sleep(backoff_time)
                        continue
                    else:
                        self.log_error(f"DuckDuckGo rate limit exceeded after {self.max_retries} attempts")
                        return []
                
                # Check for temporary network issues
                elif any(indicator in error_msg for indicator in [
                    'timeout', 'connection', 'network', 'dns', 'resolve'
                ]):
                    if attempt < self.max_retries - 1:
                        retry_delay = 5.0 * (attempt + 1)  # Progressive delay
                        self.log_warning(f"DuckDuckGo network error (attempt {attempt + 1}): {e}")
                        self.log_info(f"Retrying in {retry_delay:.1f}s")
                        time.sleep(retry_delay)
                        continue
                    else:
                        self.log_error(f"DuckDuckGo network error after {self.max_retries} attempts: {e}")
                        return []
                
                # Other errors - fail immediately
                else:
                    self.log_error(f"DuckDuckGo search failed: {e}")
                    return []
        
        return []
    
    def is_available(self) -> bool:
        """Check if DuckDuckGo is available."""
        try:
            # Initialize DDGS without proxies to avoid compatibility issues
            ddgs = DDGS()
            # Try a simple search
            list(ddgs.text("test", max_results=1))
            return True
        except Exception as e:
            self.log_warning(f"DuckDuckGo not available: {e}")
            return False


class GoogleSearch(BaseSearchEngine):
    """Google search implementation using SerpAPI."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        super().__init__(config_dict)
        self.api_key = config_dict.get('api_key')
        if not self.api_key:
            raise ValueError("Google search requires SerpAPI key")
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[SearchResult]:
        """Perform Google search via SerpAPI."""
        try:
            max_results = max_results or self.max_results
            
            self.log_info(f"Searching Google for: {query}")
            
            params = {
                'q': query,
                'api_key': self.api_key,
                'engine': 'google',
                'num': min(max_results, 100),  # SerpAPI limit
                'hl': 'zh-cn',  # Chinese language preference
                'gl': 'cn'      # China location
            }
            
            response = requests.get(
                'https://serpapi.com/search',
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            organic_results = data.get('organic_results', [])
            for i, result in enumerate(organic_results[:max_results]):
                search_result = SearchResult(
                    title=result.get('title', ''),
                    url=result.get('link', ''),
                    snippet=result.get('snippet', ''),
                    source=extract_domain_from_url(result.get('link', '')),
                    rank=i + 1,
                    metadata={
                        'position': result.get('position'),
                        'displayed_link': result.get('displayed_link')
                    }
                )
                results.append(search_result)
            
            self.log_info(f"Found {len(results)} results from Google")
            return results
            
        except Exception as e:
            self.log_error(f"Google search failed: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if Google search is available."""
        try:
            if not self.api_key:
                return False
            
            # Test with a simple query
            params = {
                'q': 'test',
                'api_key': self.api_key,
                'engine': 'google',
                'num': 1
            }
            
            response = requests.get(
                'https://serpapi.com/search',
                params=params,
                timeout=5
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            self.log_warning(f"Google search not available: {e}")
            return False


class BingSearch(BaseSearchEngine):
    """Bing search implementation."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        super().__init__(config_dict)
        self.api_key = config_dict.get('api_key')
        if not self.api_key:
            raise ValueError("Bing search requires API key")
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[SearchResult]:
        """Perform Bing search."""
        try:
            max_results = max_results or self.max_results
            
            self.log_info(f"Searching Bing for: {query}")
            
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key
            }
            
            params = {
                'q': query,
                'count': min(max_results, 50),  # Bing limit
                'mkt': 'zh-CN',
                'responseFilter': 'Webpages'
            }
            
            response = requests.get(
                'https://api.bing.microsoft.com/v7.0/search',
                headers=headers,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            web_pages = data.get('webPages', {}).get('value', [])
            for i, result in enumerate(web_pages[:max_results]):
                search_result = SearchResult(
                    title=result.get('name', ''),
                    url=result.get('url', ''),
                    snippet=result.get('snippet', ''),
                    source=extract_domain_from_url(result.get('url', '')),
                    rank=i + 1,
                    metadata={
                        'display_url': result.get('displayUrl'),
                        'date_last_crawled': result.get('dateLastCrawled')
                    }
                )
                results.append(search_result)
            
            self.log_info(f"Found {len(results)} results from Bing")
            return results
            
        except Exception as e:
            self.log_error(f"Bing search failed: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if Bing search is available."""
        try:
            if not self.api_key:
                return False
            
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key
            }
            
            params = {
                'q': 'test',
                'count': 1
            }
            
            response = requests.get(
                'https://api.bing.microsoft.com/v7.0/search',
                headers=headers,
                params=params,
                timeout=5
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            self.log_warning(f"Bing search not available: {e}")
            return False


class GoogleDocsSearch(BaseSearchEngine):
    """Google Docs search implementation using SerpAPI."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        super().__init__(config_dict)
        self.api_key = config_dict.get('api_key')
        if not self.api_key:
            raise ValueError("Google Docs search requires SerpAPI key")
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[SearchResult]:
        """Perform Google Docs search via SerpAPI."""
        try:
            max_results = max_results or self.max_results
            
            self.log_info(f"Searching Google Docs for: {query}")
            
            # 使用 site:docs.google.com 限制搜索范围到 Google Docs
            docs_query = f"site:docs.google.com {query}"
            
            params = {
                'q': docs_query,
                'api_key': self.api_key,
                'engine': 'google',
                'num': min(max_results, 100),
                'hl': 'zh-cn',
                'gl': 'cn'
            }
            
            response = requests.get(
                'https://serpapi.com/search',
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            organic_results = data.get('organic_results', [])
            for i, result in enumerate(organic_results[:max_results]):
                search_result = SearchResult(
                    title=result.get('title', ''),
                    url=result.get('link', ''),
                    snippet=result.get('snippet', ''),
                    source=extract_domain_from_url(result.get('link', '')),
                    rank=i + 1,
                    metadata={
                        'position': result.get('position'),
                        'displayed_link': result.get('displayed_link'),
                        'document_type': 'google_docs'
                    }
                )
                results.append(search_result)
            
            self.log_info(f"Found {len(results)} Google Docs results")
            return results
            
        except Exception as e:
            self.log_error(f"Google Docs search failed: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if Google Docs search is available."""
        try:
            if not self.api_key:
                return False
            
            # Test with a simple query
            params = {
                'q': 'site:docs.google.com test',
                'api_key': self.api_key,
                'engine': 'google',
                'num': 1
            }
            
            response = requests.get(
                'https://serpapi.com/search',
                params=params,
                timeout=5
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            self.log_warning(f"Google Docs search not available: {e}")
            return False


class AuthoritySearch(BaseSearchEngine):
    """Authority websites search implementation."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        super().__init__(config_dict)
        self.api_key = config_dict.get('api_key')
        self.authority_sites = config_dict.get('authority_sites', [])
        if not self.api_key:
            raise ValueError("Authority search requires SerpAPI key")
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[SearchResult]:
        """Perform authority websites search."""
        try:
            max_results = max_results or self.max_results
            
            if not self.authority_sites:
                self.log_warning("No authority sites configured")
                return []
            
            self.log_info(f"Searching authority sites for: {query}")
            
            # 构建站点限制查询
            site_queries = " OR ".join([f"site:{site}" for site in self.authority_sites])
            authority_query = f"({site_queries}) {query}"
            
            params = {
                'q': authority_query,
                'api_key': self.api_key,
                'engine': 'google',
                'num': min(max_results, 100),
                'hl': 'zh-cn',
                'gl': 'cn'
            }
            
            response = requests.get(
                'https://serpapi.com/search',
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            organic_results = data.get('organic_results', [])
            for i, result in enumerate(organic_results[:max_results]):
                # 确定来源网站
                url = result.get('link', '')
                source_site = 'unknown'
                for site in self.authority_sites:
                    if site in url:
                        source_site = site
                        break
                
                search_result = SearchResult(
                    title=result.get('title', ''),
                    url=url,
                    snippet=result.get('snippet', ''),
                    source=extract_domain_from_url(url),
                    rank=i + 1,
                    metadata={
                        'position': result.get('position'),
                        'displayed_link': result.get('displayed_link'),
                        'authority_site': source_site,
                        'search_type': 'authority'
                    }
                )
                results.append(search_result)
            
            self.log_info(f"Found {len(results)} authority site results")
            return results
            
        except Exception as e:
            self.log_error(f"Authority search failed: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if authority search is available."""
        try:
            if not self.api_key or not self.authority_sites:
                return False
            
            # Test with a simple query
            site_query = f"site:{self.authority_sites[0]} test"
            params = {
                'q': site_query,
                'api_key': self.api_key,
                'engine': 'google',
                'num': 1
            }
            
            response = requests.get(
                'https://serpapi.com/search',
                params=params,
                timeout=5
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            self.log_warning(f"Authority search not available: {e}")
            return False


class TavilySearch(BaseSearchEngine):
    """Tavily search implementation - AI-optimized search API."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        super().__init__(config_dict)
        self.api_key = config_dict.get('api_key')
        if not self.api_key:
            raise ValueError("Tavily search requires TAVILY_API_KEY")
        
        self.include_answer = config_dict.get('include_answer', True)
        self.include_raw_content = config_dict.get('include_raw_content', False)
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[SearchResult]:
        """Perform Tavily search."""
        try:
            max_results = max_results or self.max_results
            
            self.log_info(f"Searching Tavily for: {query}")
            
            headers = {
                'Content-Type': 'application/json',
            }
            
            payload = {
                'api_key': self.api_key,
                'query': query,
                'search_depth': 'advanced',
                'include_answer': self.include_answer,
                'include_raw_content': self.include_raw_content,
                'max_results': max_results,
                'include_domains': [],
                'exclude_domains': []
            }
            
            response = requests.post(
                'https://api.tavily.com/search',
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Process search results
            if 'results' in data:
                for i, result in enumerate(data['results'][:max_results]):
                    search_result = SearchResult(
                        title=result.get('title', ''),
                        url=result.get('url', ''),
                        snippet=result.get('content', ''),
                        source=extract_domain_from_url(result.get('url', '')),
                        rank=i + 1,
                        metadata={
                            'score': result.get('score', 0),
                            'published_date': result.get('published_date'),
                            'raw_content': result.get('raw_content') if self.include_raw_content else None
                        }
                    )
                    results.append(search_result)
            
            # Include answer if available
            if data.get('answer') and self.include_answer:
                answer_result = SearchResult(
                    title="AI Generated Answer",
                    url="",
                    snippet=data['answer'],
                    source='tavily_answer',
                    rank=0,
                    metadata={'type': 'answer'}
                )
                results.insert(0, answer_result)
            
            self.log_info(f"Found {len(results)} results from Tavily")
            return results
            
        except Exception as e:
            self.log_error(f"Tavily search failed: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if Tavily is available."""
        try:
            headers = {
                'Content-Type': 'application/json',
            }
            
            payload = {
                'api_key': self.api_key,
                'query': 'test',
                'max_results': 1
            }
            
            response = requests.post(
                'https://api.tavily.com/search',
                json=payload,
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.log_warning(f"Tavily not available: {e}")
            return False


class BraveSearch(BaseSearchEngine):
    """Brave search implementation."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        super().__init__(config_dict)
        self.api_key = config_dict.get('api_key')
        if not self.api_key:
            raise ValueError("Brave search requires BRAVE_SEARCH_API_KEY")
        
        self.country = config_dict.get('country', 'US')
        self.search_lang = config_dict.get('search_lang', 'en')
        self.ui_lang = config_dict.get('ui_lang', 'en-US')
        self.safe_search = config_dict.get('safe_search', 'moderate')
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[SearchResult]:
        """Perform Brave search."""
        try:
            max_results = max_results or self.max_results
            
            self.log_info(f"Searching Brave for: {query}")
            
            headers = {
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip',
                'X-Subscription-Token': self.api_key
            }
            
            params = {
                'q': query,
                'count': min(max_results, 20),  # Brave API limit
                'country': self.country,
                'search_lang': self.search_lang,
                'ui_lang': self.ui_lang,
                'safesearch': self.safe_search,
                'freshness': '',  # Can be 'pd' (past day), 'pw' (past week), 'pm' (past month), 'py' (past year)
                'text_decorations': False,
                'spellcheck': True
            }
            
            response = requests.get(
                'https://api.search.brave.com/res/v1/web/search',
                headers=headers,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Process web results
            if 'web' in data and 'results' in data['web']:
                for i, result in enumerate(data['web']['results'][:max_results]):
                    search_result = SearchResult(
                        title=result.get('title', ''),
                        url=result.get('url', ''),
                        snippet=result.get('description', ''),
                        source=extract_domain_from_url(result.get('url', '')),
                        rank=i + 1,
                        metadata={
                            'age': result.get('age'),
                            'language': result.get('language'),
                            'family_friendly': result.get('family_friendly')
                        }
                    )
                    results.append(search_result)
            
            self.log_info(f"Found {len(results)} results from Brave")
            return results
            
        except Exception as e:
            self.log_error(f"Brave search failed: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if Brave search is available."""
        try:
            headers = {
                'Accept': 'application/json',
                'X-Subscription-Token': self.api_key
            }
            
            params = {
                'q': 'test',
                'count': 1
            }
            
            response = requests.get(
                'https://api.search.brave.com/res/v1/web/search',
                headers=headers,
                params=params,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.log_warning(f"Brave search not available: {e}")
            return False


class ArxivSearch(BaseSearchEngine):
    """ArXiv search implementation for academic papers."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        super().__init__(config_dict)
        self.sort_by = config_dict.get('sort_by', 'relevance')
        self.sort_order = config_dict.get('sort_order', 'descending')
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[SearchResult]:
        """Perform ArXiv search."""
        try:
            import feedparser
        except ImportError:
            self.log_error("feedparser not installed. Install with: pip install feedparser")
            return []
        
        try:
            max_results = max_results or self.max_results
            
            self.log_info(f"Searching ArXiv for: {query}")
            
            # Build ArXiv query URL
            base_url = 'http://export.arxiv.org/api/query'
            
            # Map sort parameters
            sort_by_map = {
                'relevance': 'relevance',
                'lastUpdatedDate': 'lastUpdatedDate',
                'submittedDate': 'submittedDate'
            }
            sort_order_map = {
                'ascending': 'ascending',
                'descending': 'descending'
            }
            
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': max_results,
                'sortBy': sort_by_map.get(self.sort_by, 'relevance'),
                'sortOrder': sort_order_map.get(self.sort_order, 'descending')
            }
            
            response = requests.get(base_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            results = []
            
            for i, entry in enumerate(feed.entries[:max_results]):
                # Extract abstract
                abstract = getattr(entry, 'summary', '')
                if len(abstract) > 300:
                    abstract = abstract[:297] + '...'
                
                # Extract authors
                authors = []
                if hasattr(entry, 'authors'):
                    authors = [author.name for author in entry.authors]
                elif hasattr(entry, 'author'):
                    authors = [entry.author]
                
                # Extract categories
                categories = []
                if hasattr(entry, 'tags'):
                    categories = [tag.term for tag in entry.tags]
                
                search_result = SearchResult(
                    title=getattr(entry, 'title', ''),
                    url=getattr(entry, 'link', ''),
                    snippet=abstract,
                    source=extract_domain_from_url(getattr(entry, 'link', '')),
                    rank=i + 1,
                    metadata={
                        'authors': authors,
                        'published': getattr(entry, 'published', ''),
                        'updated': getattr(entry, 'updated', ''),
                        'categories': categories,
                        'arxiv_id': getattr(entry, 'id', '').split('/')[-1] if hasattr(entry, 'id') else ''
                    }
                )
                results.append(search_result)
            
            self.log_info(f"Found {len(results)} results from ArXiv")
            return results
            
        except Exception as e:
            self.log_error(f"ArXiv search failed: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if ArXiv is available."""
        try:
            import feedparser
            
            response = requests.get(
                'http://export.arxiv.org/api/query',
                params={'search_query': 'all:test', 'max_results': 1},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.log_warning(f"ArXiv not available: {e}")
            return False


class SearchEngineManager(LoggerMixin):
    """
    Manages multiple search engines with fallback support.
    """
    
    def __init__(self):
        """Initialize search engine manager."""
        self.engines = {}
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize available search engines."""
        
        # Tavily (AI-optimized search API)
        if (hasattr(config.search, 'engines') and 
            'tavily' in config.search.engines and 
            getattr(config.search.engines['tavily'], 'enabled', True) and
            config.search.tavily_api_key):
            try:
                tavily_config = config.search.engines['tavily']
                tavily_init_config = {
                    'api_key': config.search.tavily_api_key,
                    'timeout': config.search.timeout,
                    'max_results': getattr(tavily_config, 'max_results', None) or config.search.max_results,
                    'include_answer': getattr(tavily_config, 'include_answer', True),
                    'include_raw_content': getattr(tavily_config, 'include_raw_content', False)
                }
                self.engines['tavily'] = TavilySearch(tavily_init_config)
                self.log_info("Initialized Tavily search")
            except Exception as e:
                self.log_error(f"Failed to initialize Tavily search: {e}")
        
        # DuckDuckGo (free, always available)
        if (not hasattr(config.search, 'engines') or 
            'duckduckgo' not in config.search.engines or
            getattr(config.search.engines.get('duckduckgo'), 'enabled', True)):
            try:
                ddg_config = {
                    'timeout': config.search.timeout,
                    'max_results': config.search.max_results
                }
                if hasattr(config.search, 'engines') and 'duckduckgo' in config.search.engines:
                    engine_config = config.search.engines['duckduckgo']
                    ddg_config.update({
                        'region': getattr(engine_config, 'region', None),
                        'safe_search': getattr(engine_config, 'safe_search', None)
                    })
                self.engines['duckduckgo'] = DuckDuckGoSearch(ddg_config)
                self.log_info("Initialized DuckDuckGo search")
            except Exception as e:
                self.log_error(f"Failed to initialize DuckDuckGo: {e}")
        
        # Brave Search (requires API key)
        if (hasattr(config.search, 'engines') and 
            'brave' in config.search.engines and 
            getattr(config.search.engines['brave'], 'enabled', True) and
            config.search.brave_search_api_key):
            try:
                brave_config = config.search.engines['brave']
                brave_init_config = {
                    'api_key': config.search.brave_search_api_key,
                    'timeout': config.search.timeout,
                    'max_results': getattr(brave_config, 'max_results', None) or config.search.max_results,
                    'country': getattr(brave_config, 'country', 'US'),
                    'search_lang': getattr(brave_config, 'search_lang', 'en'),
                    'ui_lang': getattr(brave_config, 'ui_lang', 'en-US'),
                    'safe_search': getattr(brave_config, 'safe_search', 'moderate')
                }
                self.engines['brave'] = BraveSearch(brave_init_config)
                self.log_info("Initialized Brave search")
            except Exception as e:
                self.log_error(f"Failed to initialize Brave search: {e}")
        
        # Google (requires SerpAPI key)
        if ((not hasattr(config.search, 'engines') or 
             'google' not in config.search.engines or
             getattr(config.search.engines.get('google'), 'enabled', True)) and
            config.search.serpapi_key):
            try:
                google_config = {
                    'api_key': config.search.serpapi_key,
                    'timeout': config.search.timeout,
                    'max_results': config.search.max_results
                }
                if hasattr(config.search, 'engines') and 'google' in config.search.engines:
                    engine_config = config.search.engines['google']
                    google_config.update({
                        'country': getattr(engine_config, 'country', None),
                        'language': getattr(engine_config, 'language', None)
                    })
                self.engines['google'] = GoogleSearch(google_config)
                self.log_info("Initialized Google search")
            except Exception as e:
                self.log_error(f"Failed to initialize Google search: {e}")
        
        # Bing (requires API key)
        if ((not hasattr(config.search, 'engines') or 
             'bing' not in config.search.engines or
             getattr(config.search.engines.get('bing'), 'enabled', True)) and
            config.search.bing_search_key):
            try:
                bing_config = {
                    'api_key': config.search.bing_search_key,
                    'timeout': config.search.timeout,
                    'max_results': config.search.max_results
                }
                if hasattr(config.search, 'engines') and 'bing' in config.search.engines:
                    engine_config = config.search.engines['bing']
                    bing_config.update({
                        'market': getattr(engine_config, 'market', None),
                        'safe_search': getattr(engine_config, 'safe_search', None)
                    })
                self.engines['bing'] = BingSearch(bing_config)
                self.log_info("Initialized Bing search")
            except Exception as e:
                self.log_error(f"Failed to initialize Bing search: {e}")
        
        # ArXiv (free academic search)
        if (hasattr(config.search, 'enable_arxiv_search') and 
            config.search.enable_arxiv_search and
            (not hasattr(config.search, 'engines') or 
             'arxiv' not in config.search.engines or
             getattr(config.search.engines.get('arxiv'), 'enabled', True))):
            try:
                arxiv_config = {
                    'timeout': config.search.timeout,
                    'max_results': config.search.max_results
                }
                if hasattr(config.search, 'engines') and 'arxiv' in config.search.engines:
                    engine_config = config.search.engines['arxiv']
                    arxiv_config.update({
                        'max_results': getattr(engine_config, 'max_results', None) or config.search.max_results,
                        'sort_by': getattr(engine_config, 'sort_by', 'relevance'),
                        'sort_order': getattr(engine_config, 'sort_order', 'descending')
                    })
                self.engines['arxiv'] = ArxivSearch(arxiv_config)
                self.log_info("Initialized ArXiv search")
            except Exception as e:
                self.log_error(f"Failed to initialize ArXiv search: {e}")
        
        # Google Docs (requires SerpAPI key)
        if (config.search.serpapi_key and 
            getattr(config.search, 'enable_google_docs', False)):
            try:
                docs_config = {
                    'api_key': config.search.serpapi_key,
                    'timeout': config.search.timeout,
                    'max_results': config.search.max_results
                }
                self.engines['google_docs'] = GoogleDocsSearch(docs_config)
                self.log_info("Initialized Google Docs search")
            except Exception as e:
                self.log_error(f"Failed to initialize Google Docs search: {e}")
        
        # Authority sites (requires SerpAPI key and authority sites config)
        if (config.search.serpapi_key and 
            hasattr(config.search, 'authority_sites') and 
            config.search.authority_sites and
            getattr(config.search, 'enable_authority_search', False)):
            try:
                authority_config = {
                    'api_key': config.search.serpapi_key,
                    'timeout': config.search.timeout,
                    'max_results': config.search.max_results,
                    'authority_sites': config.search.authority_sites
                }
                self.engines['authority'] = AuthoritySearch(authority_config)
                self.log_info("Initialized Authority sites search")
            except Exception as e:
                self.log_error(f"Failed to initialize Authority search: {e}")
    
    def search(
        self,
        query: str,
        engine: Optional[str] = None,
        max_results: Optional[int] = None,
        use_fallback: bool = True
    ) -> List[SearchResult]:
        """
        Perform search with specified or default engine.
        
        Args:
            query: Search query
            engine: Specific engine to use (optional)
            max_results: Maximum results to return
            use_fallback: Whether to try other engines if primary fails
        
        Returns:
            List of search results
        """
        if not query.strip():
            self.log_warning("Empty search query provided")
            return []
        
        # Determine engine order
        if engine and engine in self.engines:
            engine_order = [engine]
            if use_fallback:
                engine_order.extend([e for e in self.engines.keys() if e != engine])
        else:
            # Use default order
            default_engine = config.search.default_engine
            if default_engine in self.engines:
                engine_order = [default_engine]
                if use_fallback:
                    engine_order.extend([e for e in self.engines.keys() if e != default_engine])
            else:
                engine_order = list(self.engines.keys())
        
        # Try engines in order
        for engine_name in engine_order:
            if engine_name not in self.engines:
                continue
            
            search_engine = self.engines[engine_name]
            
            if not search_engine.is_available():
                self.log_warning(f"Search engine {engine_name} not available")
                continue
            
            try:
                results = search_engine.search(query, max_results)
                if results:
                    self.log_info(f"Successfully searched using {engine_name}")
                    return results
                else:
                    self.log_warning(f"No results from {engine_name}")
            except Exception as e:
                self.log_error(f"Search failed with {engine_name}: {e}")
                continue
        
        self.log_error("All search engines failed")
        return []
    
    def get_available_engines(self) -> List[str]:
        """Get list of available search engines."""
        available = []
        for name, engine in self.engines.items():
            if engine.is_available():
                available.append(name)
        return available
    
    def search_multiple_engines(
        self,
        query: str,
        engines: Optional[List[str]] = None,
        max_results_per_engine: int = 5
    ) -> Dict[str, List[SearchResult]]:
        """
        Search using multiple engines and return combined results.
        
        Args:
            query: Search query
            engines: List of engines to use (optional)
            max_results_per_engine: Max results per engine
        
        Returns:
            Dictionary mapping engine names to results
        """
        if engines is None:
            engines = self.get_available_engines()
        
        results = {}
        
        for engine_name in engines:
            if engine_name not in self.engines:
                continue
            
            try:
                engine_results = self.search(
                    query,
                    engine=engine_name,
                    max_results=max_results_per_engine,
                    use_fallback=False
                )
                results[engine_name] = engine_results
                
                # Add delay between requests to be respectful
                time.sleep(1)
                
            except Exception as e:
                self.log_error(f"Failed to search with {engine_name}: {e}")
                results[engine_name] = []
        
        return results
    
    def deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Remove duplicate results based on URL.
        
        Args:
            results: List of search results
        
        Returns:
            Deduplicated results
        """
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        return unique_results 