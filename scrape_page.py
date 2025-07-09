#!/usr/bin/env python3
"""
Simple Page Scraper with Structured Product Extraction
"""

import sys
from universal_product_extractor import UniversalProductExtractor

def main():
    """Simple page scraper"""
    
    print("🌐 Simple Page Scraper")
    print("=" * 40)
    print("Scrapes any page and extracts structured product data")
    print("=" * 40)
    
    # Get URL from command line or user input
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter URL to scrape: ").strip()
    
    if not url:
        print("❌ No URL provided")
        return
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        print(f"Added https:// prefix: {url}")
    
    # Initialize extractor
    extractor = UniversalProductExtractor()
    
    print(f"\n🔄 Scraping: {url}")
    print("=" * 50)
    
    # Extract products
    result = extractor.extract_products(url)
    
    if result:
        print(f"\n✅ SUCCESS!")
        print(f"📊 Found {result['total_products']} products")
        print(f"⏱️ Scraping time: {result['scraping_time']:.2f} seconds")
        print(f"📄 Page title: {result['page_title']}")
        
        # Show first few products
        if result['products']:
            print(f"\n🛍️ First 3 products:")
            for i, product in enumerate(result['products'][:3], 1):
                print(f"\n--- Product {i} ---")
                if product['title']:
                    print(f"Title: {product['title'][:60]}...")
                if product['price']:
                    print(f"Price: {product['price']}")
                if product['rating']:
                    print(f"Rating: {product['rating']} stars")
                if product['brand']:
                    print(f"Brand: {product['brand']}")
        
        print(f"\n💾 Data saved to JSON and CSV files")
        
    else:
        print(f"\n❌ FAILED to extract products")
        print("This might be due to:")
        print("- Page not loading properly")
        print("- No products found on the page")
        print("- Anti-bot protection")
        print("- JavaScript rendering issues")

if __name__ == "__main__":
    main() 