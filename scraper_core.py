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
                viewport={'width': 1366, 'height': 768},
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
    
    async def _handle_infinite_scroll(self, page, scroll_pages: int = 0):
        """
        Handle infinite scroll with screenshot capture:
        - Take screenshot
        - Scroll one page at a time
        - Take screenshot after each scroll
        - Wait 10 seconds only after the last scroll to check for new content
        """
        print("🔄 Starting intelligent infinite scroll with screenshots...")
        
        # Wait 5 seconds after initial load
        await page.wait_for_timeout(5000)
        # Initialize counters
        scroll_count = 0
        screenshots_taken = 0
        # Take initial screenshot
        screenshot_path = f"scroll_screenshot_{screenshots_taken:03d}.png"
        await page.screenshot(path=screenshot_path, full_page=False)
        print(f"📸 Screenshot {screenshots_taken}: {screenshot_path}")
        screenshots_taken += 1
        
        while True:
            # Scroll down by one viewport height (one page)
            viewport_height = await page.evaluate("window.innerHeight")
            current_scroll_position = await page.evaluate("window.pageYOffset")
            new_scroll_position = current_scroll_position + viewport_height
            await page.evaluate(f"window.scrollTo(0, {new_scroll_position})")
            scroll_count += 1
            print(f"📜 Scroll {scroll_count}: Scrolled to position {new_scroll_position}px")
            # Wait 5 seconds for new content to load
            await page.wait_for_timeout(5000)
            # Take screenshot after scroll
            screenshot_path = f"scroll_screenshot_{screenshots_taken:03d}.png"
            await page.screenshot(path=screenshot_path, full_page=False)
            print(f"📸 Screenshot {screenshots_taken}: {screenshot_path}")
            screenshots_taken += 1
            # Check if we've reached the bottom
            new_height = await page.evaluate("document.body.scrollHeight")
            current_scroll_y = await page.evaluate("window.pageYOffset")
            viewport_height = await page.evaluate("window.innerHeight")
            if current_scroll_y + viewport_height >= new_height:
                print("⏳ Reached bottom of page, waiting 10 seconds for new content...")
                await page.wait_for_timeout(10000)  # 10 seconds
                # Check if new content has loaded
                final_height = await page.evaluate("document.body.scrollHeight")
                if final_height > new_height:
                    print(f"✅ New content detected! Height increased from {new_height}px to {final_height}px")
                    # Take one more screenshot of the new content
                    screenshot_path = f"scroll_screenshot_{screenshots_taken:03d}.png"
                    await page.screenshot(path=screenshot_path, full_page=False)
                    print(f"📸 Screenshot {screenshots_taken}: {screenshot_path}")
                    screenshots_taken += 1
                else:
                    print(f"🛑 No new content detected after 10-second wait")
                    break
            # Additional safety check - if we've scrolled too many times, stop
            if scroll_count >= 50:  # Maximum 50 scrolls to prevent infinite loops
                print("🛑 Stopping scroll: Reached maximum scroll limit (50)")
                break
        print(f"🎉 Scroll complete! Total scrolls: {scroll_count}")
        print(f"📸 Total screenshots taken: {screenshots_taken}")
        print(f"📏 Final page height: {await page.evaluate('document.body.scrollHeight')}px")
    
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
    
    def _handle_selenium_scroll(self, driver, scroll_pages: int = 0):
        """
        Handle infinite scroll with Selenium using screenshot capture:
        - Take screenshot
        - Scroll one page at a time
        - Take screenshot after each scroll
        - Wait 10 seconds only after the last scroll to check for new content
        """
        print("🔄 Starting intelligent infinite scroll with Selenium screenshots...")
        
        # Get initial page height
        initial_height = driver.execute_script("return document.body.scrollHeight")
        print(f"📏 Initial page height: {initial_height}px")
        
        scroll_count = 0
        screenshots_taken = 0
        
        # Take initial screenshot
        screenshot_path = f"scroll_screenshot_{screenshots_taken:03d}.png"
        driver.save_screenshot(screenshot_path)
        print(f"📸 Screenshot {screenshots_taken}: {screenshot_path}")
        screenshots_taken += 1
        
        while True:
            # Get viewport height and current scroll position
            viewport_height = driver.execute_script("return window.innerHeight")
            current_scroll_position = driver.execute_script("return window.pageYOffset")
            
            # Scroll down by one viewport height
            new_scroll_position = current_scroll_position + viewport_height
            driver.execute_script(f"window.scrollTo(0, {new_scroll_position});")
            
            scroll_count += 1
            print(f"📜 Scroll {scroll_count}: Scrolled to position {new_scroll_position}px")
            
            # Take screenshot after scroll
            screenshot_path = f"scroll_screenshot_{screenshots_taken:03d}.png"
            driver.save_screenshot(screenshot_path)
            print(f"📸 Screenshot {screenshots_taken}: {screenshot_path}")
            screenshots_taken += 1
            
            # Check if we've reached the bottom
            new_height = driver.execute_script("return document.body.scrollHeight")
            current_scroll_y = driver.execute_script("return window.pageYOffset")
            viewport_height = driver.execute_script("return window.innerHeight")
            
            # If we're at the bottom, wait 10 seconds to see if new content loads
            if current_scroll_y + viewport_height >= new_height:
                print("⏳ Reached bottom of page, waiting 10 seconds for new content...")
                time.sleep(10)  # 10 seconds
                
                # Check if new content has loaded
                final_height = driver.execute_script("return document.body.scrollHeight")
                
                if final_height > new_height:
                    print(f"✅ New content detected! Height increased from {new_height}px to {final_height}px")
                    # Take one more screenshot of the new content
                    screenshot_path = f"scroll_screenshot_{screenshots_taken:03d}.png"
                    driver.save_screenshot(screenshot_path)
                    print(f"📸 Screenshot {screenshots_taken}: {screenshot_path}")
                    screenshots_taken += 1
                else:
                    print(f"🛑 No new content detected after 10-second wait")
                    break
            else:
                # Not at bottom yet, continue scrolling
                print("📜 Continuing to next page...")
            
            # Additional safety check - if we've scrolled too many times, stop
            if scroll_count >= 50:  # Maximum 50 scrolls to prevent infinite loops
                print("🛑 Stopping scroll: Reached maximum scroll limit (50)")
                break
        
        print(f"🎉 Scroll complete! Total scrolls: {scroll_count}")
        print(f"📸 Total screenshots taken: {screenshots_taken}")
        print(f"📏 Final page height: {driver.execute_script('return document.body.scrollHeight')}px")
    
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