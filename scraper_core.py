import asyncio
import json
import time
import random
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

class WebScraper:
    """
    Comprehensive web scraper that handles JavaScript, pagination, infinite scroll,
    and anti-bot detection measures.
    """
    
    def __init__(self, headless: bool = True, use_proxy: bool = False):
        self.headless = headless
        self.use_proxy = use_proxy
        self.ua = UserAgent()
        self.session = requests.Session()
        self.setup_session()
        
    def setup_session(self):
        """Setup requests session with anti-detection measures"""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        if self.use_proxy and os.getenv('PROXY_URL'):
            self.session.proxies = {
                'http': os.getenv('PROXY_URL'),
                'https': os.getenv('PROXY_URL')
            }
    
    async def scrape_with_playwright(self, url: str, wait_for: str = None, 
                                   scroll_pages: int = 0) -> Dict[str, Any]:
        """
        Scrape using Playwright for JavaScript-heavy sites
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-default-apps',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',
                    '--disable-javascript-harmony-shipping',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                ]
            )
            
            context = await browser.new_context(
                user_agent=self.ua.random,
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                }
            )
            
            page = await context.new_page()
            
            # Add stealth scripts
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            try:
                await page.goto(url, wait_until='networkidle')
                
                if wait_for:
                    await page.wait_for_selector(wait_for, timeout=10000)
                
                # Handle infinite scroll
                if scroll_pages > 0:
                    await self._handle_infinite_scroll(page, scroll_pages)
                
                # Get page content
                content = await page.content()
                title = await page.title()
                
                # Extract structured data if available
                structured_data = await self._extract_structured_data(page)
                
                await browser.close()
                
                return {
                    'url': url,
                    'title': title,
                    'content': content,
                    'structured_data': structured_data,
                    'method': 'playwright'
                }
                
            except Exception as e:
                await browser.close()
                raise Exception(f"Playwright scraping failed: {str(e)}")
    
    async def _handle_infinite_scroll(self, page, scroll_pages: int):
        """Handle infinite scroll by scrolling down multiple times"""
        for i in range(scroll_pages):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(random.randint(2000, 4000))  # Random delay
            
            # Wait for new content to load
            try:
                await page.wait_for_function(
                    "document.body.scrollHeight > arguments[0]",
                    arg=await page.evaluate("document.body.scrollHeight"),
                    timeout=5000
                )
            except:
                break  # No more content to load
    
    async def _extract_structured_data(self, page) -> Dict[str, Any]:
        """Extract JSON-LD and other structured data"""
        try:
            # Extract JSON-LD
            json_ld = await page.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    return Array.from(scripts).map(script => JSON.parse(script.textContent));
                }
            """)
            
            # Extract meta tags
            meta_data = await page.evaluate("""
                () => {
                    const meta = {};
                    document.querySelectorAll('meta').forEach(tag => {
                        const name = tag.getAttribute('name') || tag.getAttribute('property');
                        const content = tag.getAttribute('content');
                        if (name && content) {
                            meta[name] = content;
                        }
                    });
                    return meta;
                }
            """)
            
            return {
                'json_ld': json_ld,
                'meta_data': meta_data
            }
        except:
            return {}
    
    def scrape_with_selenium(self, url: str, wait_for: str = None,
                           scroll_pages: int = 0) -> Dict[str, Any]:
        """
        Scrape using Selenium with undetected-chromedriver for anti-detection
        """
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument(f'--user-agent={self.ua.random}')
        
        if self.headless:
            options.add_argument('--headless')
        
        driver = uc.Chrome(options=options)
        
        try:
            driver.get(url)
            
            if wait_for:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
                )
            
            # Handle infinite scroll
            if scroll_pages > 0:
                self._handle_selenium_scroll(driver, scroll_pages)
            
            content = driver.page_source
            title = driver.title
            
            # Extract structured data
            structured_data = self._extract_selenium_structured_data(driver)
            
            driver.quit()
            
            return {
                'url': url,
                'title': title,
                'content': content,
                'structured_data': structured_data,
                'method': 'selenium'
            }
            
        except Exception as e:
            driver.quit()
            raise Exception(f"Selenium scraping failed: {str(e)}")
    
    def _handle_selenium_scroll(self, driver, scroll_pages: int):
        """Handle infinite scroll with Selenium"""
        for i in range(scroll_pages):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4))
            
            # Check if new content loaded
            old_height = driver.execute_script("return document.body.scrollHeight")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == old_height:
                break
    
    def _extract_selenium_structured_data(self, driver) -> Dict[str, Any]:
        """Extract structured data with Selenium"""
        try:
            # Extract JSON-LD
            json_ld_scripts = driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
            json_ld = []
            for script in json_ld_scripts:
                try:
                    json_ld.append(json.loads(script.get_attribute('innerHTML')))
                except:
                    continue
            
            # Extract meta tags
            meta_data = {}
            meta_tags = driver.find_elements(By.TAG_NAME, 'meta')
            for tag in meta_tags:
                name = tag.get_attribute('name') or tag.get_attribute('property')
                content = tag.get_attribute('content')
                if name and content:
                    meta_data[name] = content
            
            return {
                'json_ld': json_ld,
                'meta_data': meta_data
            }
        except:
            return {}
    
    def scrape_with_requests(self, url: str) -> Dict[str, Any]:
        """
        Simple scraping with requests and BeautifulSoup for static HTML
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract structured data
            structured_data = self._extract_bs4_structured_data(soup)
            
            return {
                'url': url,
                'title': soup.title.string if soup.title else '',
                'content': response.text,
                'structured_data': structured_data,
                'method': 'requests'
            }
            
        except Exception as e:
            raise Exception(f"Requests scraping failed: {str(e)}")
    
    def _extract_bs4_structured_data(self, soup) -> Dict[str, Any]:
        """Extract structured data with BeautifulSoup"""
        try:
            # Extract JSON-LD
            json_ld = []
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    json_ld.append(json.loads(script.string))
                except:
                    continue
            
            # Extract meta tags
            meta_data = {}
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property')
                content = meta.get('content')
                if name and content:
                    meta_data[name] = content
            
            return {
                'json_ld': json_ld,
                'meta_data': meta_data
            }
        except:
            return {}
    
    def detect_scraping_method(self, url: str) -> str:
        """
        Detect the best scraping method based on URL patterns or initial test
        """
        # You can implement logic to detect if a site needs JavaScript
        # For now, we'll use a simple heuristic
        js_heavy_domains = [
            'react', 'vue', 'angular', 'spa', 'app', 'dashboard',
            'facebook', 'twitter', 'instagram', 'linkedin', 'youtube'
        ]
        
        domain = urlparse(url).netloc.lower()
        if any(keyword in domain for keyword in js_heavy_domains):
            return 'playwright'
        
        return 'requests'  # Default to simple requests
    
    async def scrape_url(self, url: str, method: str = 'auto', 
                        wait_for: str = None, scroll_pages: int = 0) -> Dict[str, Any]:
        """
        Main scraping method that chooses the best approach
        """
        if method == 'auto':
            method = self.detect_scraping_method(url)
        
        if method == 'playwright':
            return await self.scrape_with_playwright(url, wait_for, scroll_pages)
        elif method == 'selenium':
            return self.scrape_with_selenium(url, wait_for, scroll_pages)
        elif method == 'requests':
            return self.scrape_with_requests(url)
        else:
            raise ValueError(f"Unknown scraping method: {method}") 