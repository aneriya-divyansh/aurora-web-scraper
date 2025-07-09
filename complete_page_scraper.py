#!/usr/bin/env python3
"""
Complete Page Scraper - Handles Pagination and Infinite Scroll
"""

import requests
import json
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, parse_qs, urlencode
from typing import List, Dict, Any, Optional
from universal_product_extractor import UniversalProductExtractor

class CompletePageScraper:
    """Scrapes all pages with pagination and infinite scroll support"""
    
    def __init__(self):
        self.proxy_url = "http://localhost:8000/api/scrape"
        self.extractor = UniversalProductExtractor()
        self.all_products = []
        self.total_pages = 0
        self.current_page = 1
        
    def scrape_all_pages(self, url: str, max_pages: int = 10) -> Dict[str, Any]:
        """Scrape all pages with pagination and infinite scroll"""
        
        print(f"\n🌐 Complete Page Scraper")
        print(f"URL: {url}")
        print(f"Max Pages: {max_pages}")
        print("=" * 60)
        
        # First, determine if it's pagination or infinite scroll
        page_type = self._detect_page_type(url)
        
        if page_type == "pagination":
            return self._scrape_paginated_pages(url, max_pages)
        elif page_type == "infinite_scroll":
            return self._scrape_infinite_scroll(url, max_pages)
        else:
            # Single page
            return self._scrape_single_page(url)
    
    def _detect_page_type(self, url: str) -> str:
        """Detect if page uses pagination or infinite scroll"""
        
        try:
            response = requests.get(self.proxy_url, params={"url": url}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                html_content = data.get('content', '')
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Check for pagination indicators
                pagination_indicators = [
                    'page', 'pagination', 'next', 'previous', 'load more',
                    'show more', 'view more', 'load additional'
                ]
                
                page_text = soup.get_text().lower()
                
                # Check for pagination elements
                pagination_elements = soup.find_all(['a', 'button', 'div'], 
                                                  string=re.compile(r'next|previous|page|load more|show more', re.I))
                
                # Check for infinite scroll indicators
                infinite_indicators = [
                    'infinite scroll', 'auto-load', 'lazy load', 'scroll to load'
                ]
                
                # Check for "Load More" buttons
                load_more_buttons = soup.find_all(string=re.compile(r'load more|show more|view more', re.I))
                
                if pagination_elements or any(indicator in page_text for indicator in pagination_indicators):
                    return "pagination"
                elif load_more_buttons or any(indicator in page_text for indicator in infinite_indicators):
                    return "infinite_scroll"
                else:
                    return "single_page"
                    
        except Exception as e:
            print(f"Error detecting page type: {e}")
        
        return "single_page"
    
    def _scrape_paginated_pages(self, url: str, max_pages: int) -> Dict[str, Any]:
        """Scrape all pages with pagination"""
        
        print("📄 Detected: Pagination")
        print("=" * 40)
        
        all_products = []
        current_page = 1
        base_url = self._get_base_url(url)
        
        while current_page <= max_pages:
            print(f"\n🔄 Scraping Page {current_page}...")
            
            # Construct page URL
            page_url = self._construct_page_url(base_url, current_page)
            
            try:
                # Scrape current page
                result = self.extractor.extract_products(page_url)
                
                if result and result['products']:
                    page_products = result['products']
                    all_products.extend(page_products)
                    
                    print(f"✅ Page {current_page}: Found {len(page_products)} products")
                    print(f"📊 Total products so far: {len(all_products)}")
                    
                    # Check if we've reached the last page
                    if len(page_products) == 0:
                        print(f"📄 No more products found. Stopping at page {current_page}")
                        break
                    
                    current_page += 1
                    
                    # Rate limiting
                    time.sleep(2)
                    
                else:
                    print(f"❌ Page {current_page}: No products found")
                    break
                    
            except Exception as e:
                print(f"❌ Error scraping page {current_page}: {e}")
                break
        
        return {
            'total_pages': current_page - 1,
            'total_products': len(all_products),
            'products': all_products,
            'scraping_type': 'pagination'
        }
    
    def _scrape_infinite_scroll(self, url: str, max_scrolls: int) -> Dict[str, Any]:
        """Scrape infinite scroll pages by simulating scrolls"""
        
        print("♾️ Detected: Infinite Scroll")
        print("=" * 40)
        
        all_products = []
        scroll_count = 0
        
        while scroll_count < max_scrolls:
            print(f"\n🔄 Scroll {scroll_count + 1}/{max_scrolls}...")
            
            try:
                # For infinite scroll, we need to modify the backend to handle scrolling
                # This is a simplified approach - in practice, you'd need to modify the backend
                result = self._scrape_with_scroll(url, scroll_count)
                
                if result and result['products']:
                    new_products = result['products']
                    
                    # Check if we got new products
                    if len(new_products) > len(all_products):
                        all_products = new_products
                        print(f"✅ Scroll {scroll_count + 1}: Found {len(new_products)} total products")
                    else:
                        print(f"📄 No new products found. Stopping at scroll {scroll_count + 1}")
                        break
                    
                    scroll_count += 1
                    time.sleep(3)  # Wait for content to load
                    
                else:
                    print(f"❌ Scroll {scroll_count + 1}: No products found")
                    break
                    
            except Exception as e:
                print(f"❌ Error during scroll {scroll_count + 1}: {e}")
                break
        
        return {
            'total_scrolls': scroll_count,
            'total_products': len(all_products),
            'products': all_products,
            'scraping_type': 'infinite_scroll'
        }
    
    def _scrape_with_scroll(self, url: str, scroll_count: int) -> Optional[Dict[str, Any]]:
        """Scrape with scroll simulation (simplified)"""
        
        # This would need backend modification to handle scrolling
        # For now, we'll use the regular extractor
        return self.extractor.extract_products(url)
    
    def _scrape_single_page(self, url: str) -> Dict[str, Any]:
        """Scrape a single page"""
        
        print("📄 Detected: Single Page")
        print("=" * 40)
        
        result = self.extractor.extract_products(url)
        
        if result:
            return {
                'total_pages': 1,
                'total_products': result['total_products'],
                'products': result['products'],
                'scraping_type': 'single_page'
            }
        else:
            return {
                'total_pages': 0,
                'total_products': 0,
                'products': [],
                'scraping_type': 'single_page'
            }
    
    def _get_base_url(self, url: str) -> str:
        """Extract base URL without page parameters"""
        
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # Remove common pagination parameters
        query_params = parse_qs(parsed.query)
        
        # Remove pagination-related parameters
        pagination_params = ['page', 'p', 'pg', 'offset', 'start', 'from']
        for param in pagination_params:
            query_params.pop(param, None)
        
        # Reconstruct URL
        if query_params:
            query_string = urlencode(query_params, doseq=True)
            base = f"{base}?{query_string}"
        
        return base
    
    def _construct_page_url(self, base_url: str, page_num: int) -> str:
        """Construct URL for specific page number"""
        
        if '?' in base_url:
            return f"{base_url}&page={page_num}"
        else:
            return f"{base_url}?page={page_num}"
    
    def save_complete_results(self, results: Dict[str, Any], url: str):
        """Save complete scraping results"""
        
        domain = urlparse(url).netloc.replace('.', '_')
        
        # Save as JSON
        json_filename = f"complete_scrape_{domain}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Complete results saved to: {json_filename}")
        
        # Save as CSV
        csv_filename = f"complete_products_{domain}.csv"
        with open(csv_filename, 'w', encoding='utf-8') as f:
            f.write("Page,Index,Title,Price,Original Price,Discount,Rating,Reviews,Brand,Image URL,Product URL\n")
            
            for i, product in enumerate(results['products'], 1):
                f.write(f"{results.get('total_pages', 1)},")
                f.write(f"{i},")
                f.write(f"\"{product.get('title', '')}\",")
                f.write(f"\"{product.get('price', '')}\",")
                f.write(f"\"{product.get('original_price', '')}\",")
                f.write(f"\"{product.get('discount', '')}\",")
                f.write(f"\"{product.get('rating', '')}\",")
                f.write(f"\"{product.get('reviews_count', '')}\",")
                f.write(f"\"{product.get('brand', '')}\",")
                f.write(f"\"{product.get('image_url', '')}\",")
                f.write(f"\"{product.get('product_url', '')}\"\n")
        
        print(f"📄 Complete CSV saved to: {csv_filename}")

def main():
    """Main function to scrape all pages"""
    
    print("🌐 Complete Page Scraper")
    print("=" * 50)
    print("Scrapes all pages with pagination and infinite scroll")
    print("=" * 50)
    
    scraper = CompletePageScraper()
    
    # Get URL from user
    url = input("Enter URL to scrape all pages: ").strip()
    
    if not url:
        print("❌ No URL provided")
        return
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        print(f"Added https:// prefix: {url}")
    
    # Get max pages
    try:
        max_pages = int(input("Enter max pages to scrape (default 10): ") or "10")
    except ValueError:
        max_pages = 10
    
    print(f"\n🔄 Starting complete scrape...")
    print(f"URL: {url}")
    print(f"Max Pages: {max_pages}")
    print("=" * 50)
    
    # Scrape all pages
    results = scraper.scrape_all_pages(url, max_pages)
    
    # Display results
    print(f"\n🎉 SCRAPING COMPLETED!")
    print(f"📊 Scraping Type: {results['scraping_type']}")
    print(f"📄 Total Pages/Scrolls: {results.get('total_pages', results.get('total_scrolls', 1))}")
    print(f"🛍️ Total Products: {results['total_products']}")
    
    if results['products']:
        print(f"\n🏆 TOP 5 PRODUCTS:")
        for i, product in enumerate(results['products'][:5], 1):
            print(f"\n--- Product {i} ---")
            if product.get('title'):
                print(f"Title: {product['title'][:60]}...")
            if product.get('price'):
                print(f"Price: {product['price']}")
            if product.get('rating'):
                print(f"Rating: {product['rating']} stars")
    
    # Save results
    scraper.save_complete_results(results, url)
    
    print(f"\n✅ Complete scraping finished!")

if __name__ == "__main__":
    main() 