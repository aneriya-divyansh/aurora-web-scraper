#!/usr/bin/env python3
"""
OCR-Enabled Web Scraper with Intelligent Scrolling and ChatGPT Integration
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from scraper_core import WebScraper
from openai_processor import OpenAIProcessor
import pandas as pd
import os

class OCRScraper:
    """
    OCR-enabled scraper with intelligent scrolling and ChatGPT table generation
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, headless: bool = True):
        self.scraper = WebScraper(headless=headless)
        self.openai_processor = OpenAIProcessor(api_key=openai_api_key)
        
    async def scrape_with_ocr(self, url: str, 
                             table_columns: List[str] = None,
                             wait_for: str = None) -> Dict[str, Any]:
        """
        Scrape a site with intelligent scrolling and generate tables with ChatGPT
        """
        print(f"🔍 Starting OCR-enabled scraping: {url}")
        
        try:
            # Scrape with intelligent scrolling enabled
            page_data = await self.scraper.scrape_url(
                url=url,
                method="playwright",  # Use Playwright for better JavaScript handling
                wait_for=wait_for,
                scroll_pages=1  # Enable intelligent scrolling
            )
            
            print(f"✅ Page scraped successfully!")
            print(f"📏 Content length: {len(page_data['content'])} characters")
            
            # Extract text content for OCR processing
            text_content = self._extract_text_content(page_data['content'])
            
            if not text_content:
                return {
                    'error': 'No text content found to process',
                    'url': url
                }
            
            print(f"📝 Extracted {len(text_content)} characters of text content")
            
            # Generate table with ChatGPT
            table_result = await self._generate_table_with_chatgpt(text_content, table_columns)
            
            return {
                'url': url,
                'content_length': len(page_data['content']),
                'text_content_length': len(text_content),
                'table_data': table_result.get('table_data', []),
                'table_columns': table_result.get('columns', []),
                'row_count': table_result.get('row_count', 0),
                'error': table_result.get('error'),
                'usage': table_result.get('usage'),
                'screenshots_taken': self._count_screenshots()
            }
            
        except Exception as e:
            return {
                'error': f"Scraping failed: {str(e)}",
                'url': url
            }
    
    def _extract_text_content(self, html_content: str) -> str:
        """
        Extract clean text content from HTML for OCR processing
        """
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            print(f"⚠️  Error extracting text content: {str(e)}")
            return ""
    
    async def _generate_table_with_chatgpt(self, text_content: str, 
                                         table_columns: List[str] = None) -> Dict[str, Any]:
        """
        Generate table data using ChatGPT from text content
        """
        if not table_columns:
            table_columns = ["Title", "Description", "Category", "Price", "Rating", "Features"]
        
        print(f"🤖 Generating table with ChatGPT using columns: {table_columns}")
        
        try:
            # Use the existing OpenAI processor to generate table data
            table_result = self.openai_processor.generate_table_data(text_content, table_columns)
            
            if table_result.get('error'):
                print(f"❌ ChatGPT table generation failed: {table_result['error']}")
                return table_result
            
            print(f"✅ Table generated successfully! {table_result.get('row_count', 0)} rows found")
            return table_result
            
        except Exception as e:
            print(f"❌ Error generating table: {str(e)}")
            return {
                'error': f"Table generation failed: {str(e)}",
                'table_data': None
            }
    
    def save_table_results(self, results: Dict[str, Any], 
                          filename_prefix: str = "ocr_scraped_data") -> Dict[str, str]:
        """
        Save table results to CSV and JSON files
        """
        save_results = {}
        
        if results.get('table_data'):
            # Save as CSV
            try:
                df = pd.DataFrame(results['table_data'])
                csv_filename = f"{filename_prefix}.csv"
                df.to_csv(csv_filename, index=False)
                save_results['csv'] = csv_filename
                print(f"💾 CSV saved: {csv_filename}")
            except Exception as e:
                print(f"⚠️  Failed to save CSV: {str(e)}")
            
            # Save as JSON
            try:
                json_filename = f"{filename_prefix}.json"
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                save_results['json'] = json_filename
                print(f"💾 JSON saved: {json_filename}")
            except Exception as e:
                print(f"⚠️  Failed to save JSON: {str(e)}")
        
        return save_results
    
    def _count_screenshots(self) -> int:
        """
        Count the number of screenshot files created during scraping
        """
        import glob
        import os
        
        screenshot_files = glob.glob("scroll_screenshot_*.png")
        return len(screenshot_files)
    
    async def scrape_multiple_sites(self, urls: List[str], 
                                  table_columns: List[str] = None) -> List[Dict[str, Any]]:
        """
        Scrape multiple sites with OCR and table generation
        """
        results = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n{'='*60}")
            print(f"🌐 Scraping site {i}/{len(urls)}: {url}")
            print(f"{'='*60}")
            
            result = await self.scrape_with_ocr(url, table_columns)
            results.append(result)
            
            # Add delay between requests
            if i < len(urls):
                print("⏳ Waiting 3 seconds before next site...")
                await asyncio.sleep(3)
        
        return results

async def main():
    """
    Main function to test the OCR scraper
    """
    print("🚀 Starting OCR-Enabled Web Scraper Test")
    print("=" * 60)
    
    # Initialize scraper
    scraper = OCRScraper(headless=False)  # Set to False to see scrolling in action
    
    # Test URLs
    test_urls = [
        {
            "name": "Amazon Product Search",
            "url": "https://www.amazon.com/s?k=laptop",
            "table_columns": ["Product Name", "Price", "Rating", "Reviews", "Availability", "Features"]
        },
        {
            "name": "Autotrader Car Listings",
            "url": "https://www.autotrader.co.uk/car-search?channel=cars&postcode=SW1W+0NY&latLong=&distance=&make=Alfa+Romeo&model=156&homeDeliveryAdverts=include&advertising-location=at_cars&year-to=2025",
            "table_columns": ["Title", "Price", "Year", "Mileage", "Location", "Description"]
        }
    ]
    
    for test in test_urls:
        print(f"\n🧪 Testing: {test['name']}")
        print(f"🔗 URL: {test['url']}")
        
        try:
            # Scrape with OCR and table generation
            result = await scraper.scrape_with_ocr(
                url=test['url'],
                table_columns=test['table_columns']
            )
            
            if result.get('error'):
                print(f"❌ {test['name']} failed: {result['error']}")
                continue
            
            print(f"✅ {test['name']} completed successfully!")
            print(f"📊 Rows found: {result.get('row_count', 0)}")
            print(f"📋 Columns: {result.get('table_columns', [])}")
            
            # Save results
            save_results = scraper.save_table_results(
                result, 
                filename_prefix=f"{test['name'].lower().replace(' ', '_')}_ocr_results"
            )
            
            # Show sample data
            if result.get('table_data'):
                print(f"\n📋 Sample data (first 2 rows):")
                for i, row in enumerate(result['table_data'][:2]):
                    print(f"   Row {i+1}: {row}")
            
        except Exception as e:
            print(f"❌ {test['name']} failed with exception: {str(e)}")
    
    print(f"\n🎉 OCR scraper test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 