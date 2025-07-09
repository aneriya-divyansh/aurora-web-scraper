import requests
import json
import time
from typing import Dict, Any
from ai_parser import AIContentParser
from table_formatter import TableFormatter

class UnifiedScraper:
    def __init__(self, api_key: str = None):
        """Initialize the unified scraper system"""
        self.backend_url = "http://localhost:8000/api/scrape"
        self.ai_parser = AIContentParser(api_key)
        self.table_formatter = TableFormatter()
    
    def scrape_and_parse(self, url: str, extraction_requirements: str, output_format: str = "console") -> Dict[str, Any]:
        """
        Complete workflow: scrape URL, parse with AI, format as table
        
        Args:
            url: URL to scrape
            extraction_requirements: What data to extract
            output_format: "console", "csv", or "html"
            
        Returns:
            Complete results dictionary
        """
        
        print(f"🌐 Scraping: {url}")
        print(f"📋 Requirements: {extraction_requirements}")
        print(f"📊 Output format: {output_format}")
        print("-" * 60)
        
        # Step 1: Scrape the URL
        print("🔄 Step 1: Scraping webpage...")
        scrape_result = self._scrape_url(url)
        
        if not scrape_result.get('success'):
            return {
                'error': 'Scraping failed',
                'details': scrape_result.get('error', 'Unknown error')
            }
        
        # Step 2: Parse with AI
        print("🤖 Step 2: Parsing content with AI...")
        html_content = scrape_result['content']
        parsed_data = self.ai_parser.analyze_content(html_content, extraction_requirements)
        
        # Step 3: Format as table
        print("📊 Step 3: Formatting as table...")
        formatted_output = self.table_formatter.format_extracted_data(parsed_data, output_format)
        
        # Step 4: Save results
        timestamp = int(time.time())
        results = {
            'url': url,
            'requirements': extraction_requirements,
            'scrape_result': scrape_result,
            'parsed_data': parsed_data,
            'formatted_output': formatted_output,
            'output_format': output_format,
            'timestamp': timestamp
        }
        
        # Save complete results
        output_file = f"unified_results_{timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Save formatted output separately
        if output_format != "console":
            formatted_file = f"formatted_output_{timestamp}.{output_format}"
            with open(formatted_file, 'w', encoding='utf-8') as f:
                f.write(formatted_output)
            print(f"💾 Formatted output saved to: {formatted_file}")
        
        print(f"💾 Complete results saved to: {output_file}")
        
        return results
    
    def _scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrape URL using backend proxy"""
        try:
            params = {"url": url}
            response = requests.get(self.backend_url, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'success': True,
                        'title': data.get('title', ''),
                        'content': data.get('content', ''),
                        'content_length': len(data.get('content', ''))
                    }
                else:
                    return {
                        'success': False,
                        'error': data.get('error', 'Unknown error'),
                        'status': data.get('status', 'unknown')
                    }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timed out'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Connection error - check if backend is running'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

def interactive_unified_scraper():
    """Interactive unified scraper"""
    
    print("🚀 Unified Web Scraper & AI Parser")
    print("=" * 60)
    
    # Initialize scraper
    scraper = UnifiedScraper()
    
    # Get URL
    print("\nEnter the URL to scrape:")
    print("Examples:")
    print("- https://www.amazon.in/s?k=laptop")
    print("- https://www.flipkart.com/search?q=mobile")
    print("- https://www.autotrader.co.uk/car-search")
    
    url = input("\nURL: ").strip()
    
    if not url:
        print("❌ No URL provided")
        return
    
    # Get extraction requirements
    print("\nWhat data would you like to extract?")
    print("Examples:")
    print("- 'product names and prices'")
    print("- 'car listings with prices and years'")
    print("- 'all available information'")
    print("- 'prices only'")
    
    requirements = input("\nRequirements: ").strip()
    
    if not requirements:
        requirements = "all available information"
    
    # Get output format
    print("\nOutput format:")
    print("1. Console (default)")
    print("2. CSV")
    print("3. HTML")
    
    format_choice = input("\nSelect format (1-3, default=1): ").strip()
    
    if format_choice == "2":
        output_format = "csv"
    elif format_choice == "3":
        output_format = "html"
    else:
        output_format = "console"
    
    # Run the complete workflow
    print("\n" + "="*60)
    print("🚀 STARTING UNIFIED SCRAPING WORKFLOW")
    print("="*60)
    
    results = scraper.scrape_and_parse(url, requirements, output_format)
    
    if 'error' in results:
        print(f"\n❌ Error: {results['error']}")
        if 'details' in results:
            print(f"Details: {results['details']}")
    else:
        print("\n" + "="*60)
        print("✅ WORKFLOW COMPLETED SUCCESSFULLY")
        print("="*60)
        
        # Display summary
        scrape_result = results['scrape_result']
        parsed_data = results['parsed_data']
        
        print(f"📊 Summary:")
        print(f"   - URL: {results['url']}")
        print(f"   - Page title: {scrape_result.get('title', 'N/A')}")
        print(f"   - Content size: {scrape_result.get('content_length', 0):,} characters")
        print(f"   - Items extracted: {parsed_data.get('summary', {}).get('total_items', 0)}")
        print(f"   - Extraction method: {parsed_data.get('summary', {}).get('extraction_method', 'unknown')}")
        print(f"   - Fields extracted: {', '.join(parsed_data.get('fields', []))}")
        
        # Show formatted output if console
        if output_format == "console":
            print("\n📋 EXTRACTED DATA:")
            print("-" * 60)
            print(results['formatted_output'])
        else:
            print(f"\n📋 Formatted data saved to file (see above for filename)")

if __name__ == "__main__":
    interactive_unified_scraper() 