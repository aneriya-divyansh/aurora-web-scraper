import re
import json
import time
import random
from typing import Dict, List, Any, Optional, Generator
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import requests
from bs4 import BeautifulSoup

class PaginationHandler:
    """
    Handles different types of pagination and infinite scrolling
    """
    
    def __init__(self, base_url: str, session: requests.Session = None):
        self.base_url = base_url
        self.session = session or requests.Session()
        self.current_page = 1
        self.has_more = True
    
    def detect_pagination_type(self, html_content: str) -> str:
        """
        Detect the type of pagination used on the page
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for common pagination patterns
        pagination_selectors = [
            '.pagination', '.pager', '.page-numbers', '.paging',
            '[class*="pagination"]', '[class*="pager"]', '[class*="page"]'
        ]
        
        for selector in pagination_selectors:
            if soup.select(selector):
                return 'traditional'
        
        # Check for "Load More" buttons
        load_more_selectors = [
            '[class*="load-more"]', '[class*="loadmore"]', '[class*="show-more"]',
            'button:contains("Load More")', 'a:contains("Load More")',
            '[class*="infinite"]', '[class*="scroll"]'
        ]
        
        for selector in load_more_selectors:
            if soup.select(selector):
                return 'load_more'
        
        # Check for infinite scroll indicators
        infinite_indicators = [
            '[class*="infinite-scroll"]', '[class*="lazy-load"]',
            '[data-infinite]', '[data-lazy]'
        ]
        
        for selector in infinite_indicators:
            if soup.select(selector):
                return 'infinite_scroll'
        
        return 'unknown'
    
    def extract_pagination_links(self, html_content: str) -> List[str]:
        """
        Extract pagination links from HTML content
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        # Common pagination link patterns
        pagination_patterns = [
            'a[href*="page="]',
            'a[href*="p="]',
            'a[href*="offset="]',
            'a[href*="start="]',
            '.pagination a',
            '.pager a',
            '.page-numbers a'
        ]
        
        for pattern in pagination_patterns:
            elements = soup.select(pattern)
            for element in elements:
                href = element.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in links:
                        links.append(full_url)
        
        return links
    
    def generate_page_urls(self, pattern: str, total_pages: int = None) -> Generator[str, None, None]:
        """
        Generate page URLs based on a pattern
        """
        if pattern == 'query_param':
            # URL pattern like ?page=1, ?page=2
            for page in range(1, (total_pages or 100) + 1):
                parsed = urlparse(self.base_url)
                query_dict = parse_qs(parsed.query)
                query_dict['page'] = [str(page)]
                new_query = urlencode(query_dict, doseq=True)
                new_url = urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path,
                    parsed.params, new_query, parsed.fragment
                ))
                yield new_url
                
        elif pattern == 'path_param':
            # URL pattern like /page/1, /page/2
            for page in range(1, (total_pages or 100) + 1):
                if self.base_url.endswith('/'):
                    yield f"{self.base_url}page/{page}"
                else:
                    yield f"{self.base_url}/page/{page}"
                    
        elif pattern == 'offset':
            # URL pattern with offset parameter
            offset = 0
            while offset < (total_pages or 1000):
                parsed = urlparse(self.base_url)
                query_dict = parse_qs(parsed.query)
                query_dict['offset'] = [str(offset)]
                new_query = urlencode(query_dict, doseq=True)
                new_url = urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path,
                    parsed.params, new_query, parsed.fragment
                ))
                yield new_url
                offset += 20  # Common page size
    
    def handle_traditional_pagination(self, html_content: str) -> List[str]:
        """
        Handle traditional pagination with numbered pages
        """
        return self.extract_pagination_links(html_content)
    
    def handle_load_more_pagination(self, html_content: str, api_endpoint: str = None) -> Dict[str, Any]:
        """
        Handle "Load More" button pagination
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find load more button
        load_more_selectors = [
            'button[class*="load-more"]',
            'a[class*="load-more"]',
            'button:contains("Load More")',
            'a:contains("Load More")',
            '[data-load-more]',
            '[data-action="load-more"]'
        ]
        
        load_more_element = None
        for selector in load_more_selectors:
            element = soup.select_one(selector)
            if element:
                load_more_element = element
                break
        
        if not load_more_element:
            return {'type': 'load_more', 'has_more': False, 'next_url': None}
        
        # Extract next page URL or API endpoint
        next_url = load_more_element.get('href') or load_more_element.get('data-url')
        if next_url:
            next_url = urljoin(self.base_url, next_url)
        
        # Check if button is disabled or hidden
        is_disabled = (
            load_more_element.get('disabled') or
            'disabled' in load_more_element.get('class', []) or
            'hidden' in load_more_element.get('class', [])
        )
        
        return {
            'type': 'load_more',
            'has_more': not is_disabled,
            'next_url': next_url,
            'element_selector': self._get_element_selector(load_more_element)
        }
    
    def handle_infinite_scroll_pagination(self, html_content: str) -> Dict[str, Any]:
        """
        Handle infinite scroll pagination
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for infinite scroll indicators
        indicators = []
        
        # Check for data attributes
        data_attrs = ['data-infinite', 'data-lazy', 'data-scroll', 'data-load']
        for attr in data_attrs:
            elements = soup.select(f'[{attr}]')
            for element in elements:
                indicators.append({
                    'element': element,
                    'attribute': attr,
                    'value': element.get(attr)
                })
        
        # Check for common infinite scroll classes
        infinite_classes = ['infinite-scroll', 'lazy-load', 'scroll-load', 'auto-load']
        for class_name in infinite_classes:
            elements = soup.select(f'.{class_name}')
            for element in elements:
                indicators.append({
                    'element': element,
                    'type': 'class',
                    'class': class_name
                })
        
        return {
            'type': 'infinite_scroll',
            'has_more': len(indicators) > 0,
            'indicators': indicators
        }
    
    def handle_api_pagination(self, api_url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle API-based pagination
        """
        if not params:
            params = {}
        
        # Common API pagination parameters
        api_params = {
            'page': self.current_page,
            'limit': 20,
            'offset': (self.current_page - 1) * 20,
            **params
        }
        
        try:
            response = self.session.get(api_url, params=api_params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for common pagination fields in API response
            pagination_info = {}
            
            if 'pagination' in data:
                pagination_info = data['pagination']
            elif 'meta' in data and 'pagination' in data['meta']:
                pagination_info = data['meta']['pagination']
            elif 'page' in data:
                pagination_info = data['page']
            
            # Determine if there are more pages
            has_more = False
            if pagination_info:
                current_page = pagination_info.get('current_page', self.current_page)
                total_pages = pagination_info.get('total_pages', 1)
                has_more = current_page < total_pages
                
                # Update current page
                self.current_page = current_page + 1 if has_more else current_page
            
            return {
                'type': 'api',
                'has_more': has_more,
                'data': data,
                'pagination_info': pagination_info,
                'next_params': api_params if has_more else None
            }
            
        except Exception as e:
            return {
                'type': 'api',
                'has_more': False,
                'error': str(e),
                'data': None
            }
    
    def _get_element_selector(self, element) -> str:
        """
        Generate a CSS selector for an element
        """
        if element.get('id'):
            return f"#{element['id']}"
        elif element.get('class'):
            classes = ' '.join(element['class'])
            return f".{classes.replace(' ', '.')}"
        else:
            return element.name
    
    def extract_content_from_page(self, html_content: str, content_selectors: List[str] = None) -> List[Dict[str, Any]]:
        """
        Extract content items from a page
        """
        if not content_selectors:
            content_selectors = [
                'article', '.post', '.item', '.product', '.card',
                '[class*="item"]', '[class*="card"]', '[class*="post"]'
            ]
        
        soup = BeautifulSoup(html_content, 'html.parser')
        items = []
        
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                item = {
                    'text': element.get_text(strip=True),
                    'html': str(element),
                    'links': [a.get('href') for a in element.find_all('a', href=True)],
                    'images': [img.get('src') for img in element.find_all('img', src=True)],
                    'selector': selector
                }
                items.append(item)
        
        return items
    
    def simulate_scroll(self, scroll_distance: int = 1000, delay: float = 2.0) -> Dict[str, Any]:
        """
        Simulate scrolling for infinite scroll pages
        """
        return {
            'action': 'scroll',
            'distance': scroll_distance,
            'delay': delay,
            'timestamp': time.time()
        }
    
    def get_pagination_summary(self) -> Dict[str, Any]:
        """
        Get summary of pagination state
        """
        return {
            'current_page': self.current_page,
            'has_more': self.has_more,
            'base_url': self.base_url,
            'total_processed': self.current_page - 1
        } 