"""
Browser automation agent for DeepResearch system.
Provides web scraping and browser automation capabilities.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from utils.logger import LoggerMixin


class BrowserAction(Enum):
    """Types of browser actions."""
    VISIT = "visit"
    CLICK = "click"
    EXTRACT_TEXT = "extract_text"
    EXTRACT_LINKS = "extract_links"
    SCREENSHOT = "screenshot"
    SCROLL = "scroll"
    WAIT = "wait"
    SEARCH = "search"


@dataclass
class BrowserResult:
    """Result of browser operation."""
    success: bool
    action: BrowserAction
    url: str
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class BrowserAgent(LoggerMixin):
    """
    Browser automation agent using Playwright.
    Provides web scraping and automation capabilities.
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize browser agent.
        
        Args:
            headless: Whether to run browser in headless mode
            timeout: Default timeout for operations in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.context = None
        self.page = None
        
        # Try to import playwright
        try:
            import playwright
            self.playwright_available = True
        except ImportError:
            self.playwright_available = False
            self.log_warning("Playwright not available. Browser automation will use fallback mode.")
    
    async def start_browser(self) -> bool:
        """
        Start browser instance.
        
        Returns:
            True if browser started successfully
        """
        if not self.playwright_available:
            self.log_warning("Cannot start browser: Playwright not available")
            return False
        
        try:
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            self.page = await self.context.new_page()
            
            # Set default timeout
            self.page.set_default_timeout(self.timeout)
            
            self.log_info("Browser started successfully")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to start browser: {e}")
            return False
    
    async def stop_browser(self):
        """Stop browser instance."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            
            self.log_info("Browser stopped")
            
        except Exception as e:
            self.log_error(f"Error stopping browser: {e}")
    
    async def visit_url(self, url: str, wait_for: Optional[str] = None) -> BrowserResult:
        """
        Visit a URL.
        
        Args:
            url: URL to visit
            wait_for: Optional selector to wait for
        
        Returns:
            Browser operation result
        """
        start_time = time.time()
        
        if not self.playwright_available:
            return self._fallback_visit_url(url)
        
        if not self.page:
            if not await self.start_browser():
                return BrowserResult(
                    success=False,
                    action=BrowserAction.VISIT,
                    url=url,
                    error="Failed to start browser"
                )
        
        try:
            self.log_info(f"Visiting URL: {url}")
            
            # Navigate to URL
            response = await self.page.goto(url, wait_until="domcontentloaded")
            
            # Wait for specific element if requested
            if wait_for:
                await self.page.wait_for_selector(wait_for, timeout=10000)
            
            # Get page title and basic info
            title = await self.page.title()
            current_url = self.page.url
            
            execution_time = time.time() - start_time
            
            return BrowserResult(
                success=True,
                action=BrowserAction.VISIT,
                url=current_url,
                data={
                    "title": title,
                    "status_code": response.status if response else None,
                    "final_url": current_url
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_error(f"Failed to visit URL {url}: {e}")
            
            return BrowserResult(
                success=False,
                action=BrowserAction.VISIT,
                url=url,
                error=str(e),
                execution_time=execution_time
            )
    
    async def extract_text(self, selector: Optional[str] = None) -> BrowserResult:
        """
        Extract text from page.
        
        Args:
            selector: CSS selector to extract text from (optional)
        
        Returns:
            Browser operation result with extracted text
        """
        start_time = time.time()
        
        if not self.playwright_available:
            return self._fallback_extract_text()
        
        if not self.page:
            return BrowserResult(
                success=False,
                action=BrowserAction.EXTRACT_TEXT,
                url="",
                error="No active page"
            )
        
        try:
            if selector:
                # Extract text from specific element
                element = await self.page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                else:
                    text = ""
            else:
                # Extract all text from page
                text = await self.page.inner_text("body")
            
            execution_time = time.time() - start_time
            
            return BrowserResult(
                success=True,
                action=BrowserAction.EXTRACT_TEXT,
                url=self.page.url,
                data={"text": text, "selector": selector},
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_error(f"Failed to extract text: {e}")
            
            return BrowserResult(
                success=False,
                action=BrowserAction.EXTRACT_TEXT,
                url=self.page.url if self.page else "",
                error=str(e),
                execution_time=execution_time
            )
    
    async def extract_links(self, selector: str = "a") -> BrowserResult:
        """
        Extract links from page.
        
        Args:
            selector: CSS selector for link elements
        
        Returns:
            Browser operation result with extracted links
        """
        start_time = time.time()
        
        if not self.playwright_available:
            return self._fallback_extract_links()
        
        if not self.page:
            return BrowserResult(
                success=False,
                action=BrowserAction.EXTRACT_LINKS,
                url="",
                error="No active page"
            )
        
        try:
            # Get all link elements
            links = await self.page.query_selector_all(selector)
            
            extracted_links = []
            for link in links:
                href = await link.get_attribute("href")
                text = await link.inner_text()
                
                if href:
                    # Convert relative URLs to absolute
                    if href.startswith("/"):
                        base_url = f"{self.page.url.split('/')[0]}//{self.page.url.split('/')[2]}"
                        href = base_url + href
                    elif not href.startswith("http"):
                        continue  # Skip invalid links
                    
                    extracted_links.append({
                        "url": href,
                        "text": text.strip(),
                        "title": await link.get_attribute("title") or ""
                    })
            
            execution_time = time.time() - start_time
            
            return BrowserResult(
                success=True,
                action=BrowserAction.EXTRACT_LINKS,
                url=self.page.url,
                data={"links": extracted_links, "count": len(extracted_links)},
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_error(f"Failed to extract links: {e}")
            
            return BrowserResult(
                success=False,
                action=BrowserAction.EXTRACT_LINKS,
                url=self.page.url if self.page else "",
                error=str(e),
                execution_time=execution_time
            )
    
    async def click_element(self, selector: str) -> BrowserResult:
        """
        Click an element on the page.
        
        Args:
            selector: CSS selector for element to click
        
        Returns:
            Browser operation result
        """
        start_time = time.time()
        
        if not self.playwright_available:
            return BrowserResult(
                success=False,
                action=BrowserAction.CLICK,
                url="",
                error="Playwright not available"
            )
        
        if not self.page:
            return BrowserResult(
                success=False,
                action=BrowserAction.CLICK,
                url="",
                error="No active page"
            )
        
        try:
            # Wait for element to be visible
            await self.page.wait_for_selector(selector, state="visible", timeout=5000)
            
            # Click the element
            await self.page.click(selector)
            
            # Wait a bit for any navigation or changes
            await asyncio.sleep(1)
            
            execution_time = time.time() - start_time
            
            return BrowserResult(
                success=True,
                action=BrowserAction.CLICK,
                url=self.page.url,
                data={"selector": selector},
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_error(f"Failed to click element {selector}: {e}")
            
            return BrowserResult(
                success=False,
                action=BrowserAction.CLICK,
                url=self.page.url if self.page else "",
                error=str(e),
                execution_time=execution_time
            )
    
    async def search_on_page(self, query: str, search_selector: str = "input[type='search'], input[name*='search'], input[name*='q']") -> BrowserResult:
        """
        Perform search on current page.
        
        Args:
            query: Search query
            search_selector: CSS selector for search input
        
        Returns:
            Browser operation result
        """
        start_time = time.time()
        
        if not self.playwright_available:
            return BrowserResult(
                success=False,
                action=BrowserAction.SEARCH,
                url="",
                error="Playwright not available"
            )
        
        if not self.page:
            return BrowserResult(
                success=False,
                action=BrowserAction.SEARCH,
                url="",
                error="No active page"
            )
        
        try:
            # Find search input
            search_input = await self.page.query_selector(search_selector)
            if not search_input:
                raise Exception(f"Search input not found with selector: {search_selector}")
            
            # Clear and type query
            await search_input.clear()
            await search_input.type(query)
            
            # Submit search (try Enter key first, then look for submit button)
            await search_input.press("Enter")
            
            # Wait for results to load
            await asyncio.sleep(2)
            
            execution_time = time.time() - start_time
            
            return BrowserResult(
                success=True,
                action=BrowserAction.SEARCH,
                url=self.page.url,
                data={"query": query, "search_selector": search_selector},
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_error(f"Failed to search for '{query}': {e}")
            
            return BrowserResult(
                success=False,
                action=BrowserAction.SEARCH,
                url=self.page.url if self.page else "",
                error=str(e),
                execution_time=execution_time
            )
    
    async def take_screenshot(self, path: Optional[str] = None) -> BrowserResult:
        """
        Take screenshot of current page.
        
        Args:
            path: Optional path to save screenshot
        
        Returns:
            Browser operation result
        """
        start_time = time.time()
        
        if not self.playwright_available:
            return BrowserResult(
                success=False,
                action=BrowserAction.SCREENSHOT,
                url="",
                error="Playwright not available"
            )
        
        if not self.page:
            return BrowserResult(
                success=False,
                action=BrowserAction.SCREENSHOT,
                url="",
                error="No active page"
            )
        
        try:
            if not path:
                path = f"screenshot_{int(time.time())}.png"
            
            await self.page.screenshot(path=path, full_page=True)
            
            execution_time = time.time() - start_time
            
            return BrowserResult(
                success=True,
                action=BrowserAction.SCREENSHOT,
                url=self.page.url,
                data={"screenshot_path": path},
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_error(f"Failed to take screenshot: {e}")
            
            return BrowserResult(
                success=False,
                action=BrowserAction.SCREENSHOT,
                url=self.page.url if self.page else "",
                error=str(e),
                execution_time=execution_time
            )
    
    def _fallback_visit_url(self, url: str) -> BrowserResult:
        """Fallback method for visiting URL using requests."""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            start_time = time.time()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.title.string if soup.title else ""
            
            execution_time = time.time() - start_time
            
            return BrowserResult(
                success=True,
                action=BrowserAction.VISIT,
                url=url,
                data={
                    "title": title.strip(),
                    "status_code": response.status_code,
                    "content": response.text,
                    "soup": soup
                },
                execution_time=execution_time,
                metadata={"fallback_mode": True}
            )
            
        except Exception as e:
            return BrowserResult(
                success=False,
                action=BrowserAction.VISIT,
                url=url,
                error=f"Fallback visit failed: {str(e)}",
                metadata={"fallback_mode": True}
            )
    
    def _fallback_extract_text(self) -> BrowserResult:
        """Fallback method for text extraction."""
        return BrowserResult(
            success=False,
            action=BrowserAction.EXTRACT_TEXT,
            url="",
            error="Text extraction not available in fallback mode",
            metadata={"fallback_mode": True}
        )
    
    def _fallback_extract_links(self) -> BrowserResult:
        """Fallback method for link extraction."""
        return BrowserResult(
            success=False,
            action=BrowserAction.EXTRACT_LINKS,
            url="",
            error="Link extraction not available in fallback mode",
            metadata={"fallback_mode": True}
        )
    
    async def execute_action(self, action_data: Dict[str, Any]) -> BrowserResult:
        """
        Execute browser action based on action data.
        
        Args:
            action_data: Dictionary containing action details
        
        Returns:
            Browser operation result
        """
        action_type = action_data.get("action", "visit")
        
        try:
            if action_type == "visit":
                url = action_data.get("url", "")
                wait_for = action_data.get("wait_for")
                return await self.visit_url(url, wait_for)
            
            elif action_type == "extract_text":
                selector = action_data.get("selector")
                return await self.extract_text(selector)
            
            elif action_type == "extract_links":
                selector = action_data.get("selector", "a")
                return await self.extract_links(selector)
            
            elif action_type == "click":
                selector = action_data.get("selector", "")
                return await self.click_element(selector)
            
            elif action_type == "search":
                query = action_data.get("query", "")
                search_selector = action_data.get("search_selector", "input[type='search'], input[name*='search'], input[name*='q']")
                return await self.search_on_page(query, search_selector)
            
            elif action_type == "screenshot":
                path = action_data.get("path")
                return await self.take_screenshot(path)
            
            else:
                return BrowserResult(
                    success=False,
                    action=BrowserAction.VISIT,
                    url="",
                    error=f"Unknown action type: {action_type}"
                )
                
        except Exception as e:
            self.log_error(f"Browser action execution failed: {e}")
            return BrowserResult(
                success=False,
                action=BrowserAction.VISIT,
                url="",
                error=str(e)
            )
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_browser() 