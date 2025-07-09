import requests
import json
import time
from typing import Dict, Any, List
from bs4 import BeautifulSoup
import re
import pandas as pd
from urllib.parse import urlparse

class UniversalScraper:
    def __init__(self):
        """Initialize the universal scraper"""
        self.backend_url = "http://localhost:8000/api/scrape"
        self.current_url = ""
    
    def scrape_and_extract(self, url: str, requirements: str) -> Dict[str, Any]:
        """
        Universal scraping and extraction system
        
        Args:
            url: URL to scrape
            requirements: What data to extract (e.g., "product names and prices")
            
        Returns:
            Dictionary with extracted data and formatted tables
        """
        
        print(f"🌐 Scraping: {url}")
        print(f"📋 Extracting: {requirements}")
        print("-" * 50)
        
        # Store current URL for site-specific parsing
        self.current_url = url
        
        # Step 1: Scrape the URL
        print("🔄 Scraping webpage...")
        scrape_result = self._scrape_url(url)
        
        if not scrape_result.get('success'):
            return {
                'error': 'Scraping failed',
                'details': scrape_result.get('error', 'Unknown error')
            }
        
        # Step 2: Extract data using universal methods
        print("🔍 Extracting requested data...")
        html_content = scrape_result['content']
        extracted_data = self._extract_data_universal(html_content, requirements)
        
        # Step 3: Create clean tables
        print("📊 Creating clean tables...")
        tables = self._create_tables(extracted_data)
        
        # Step 4: Format results
        results = {
            'url': url,
            'requirements': requirements,
            'page_title': scrape_result.get('title', ''),
            'extracted_data': extracted_data,
            'tables': tables,
            'summary': {
                'total_items': sum(len(data) for data in extracted_data.values()),
                'data_types': list(extracted_data.keys())
            }
        }
        
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
                        'content': data.get('content', '')
                    }
                else:
                    return {
                        'success': False,
                        'error': data.get('error', 'Unknown error')
                    }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }
                
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timed out'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Connection error - check if backend is running'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _extract_data_universal(self, html_content: str, requirements: str) -> Dict[str, list]:
        """Universal data extraction using multiple strategies"""
        soup = BeautifulSoup(html_content, 'html.parser')
        extracted = {}
        
        requirements_lower = requirements.lower()
        
        # Extract prices if requested
        if any(word in requirements_lower for word in ['price', 'cost', 'amount']):
            extracted['prices'] = self._extract_prices_universal(soup)
        
        # Extract product names if requested
        if any(word in requirements_lower for word in ['product', 'name', 'title', 'item']):
            extracted['products'] = self._extract_products_universal(soup)
        
        # Extract ratings if requested
        if any(word in requirements_lower for word in ['rating', 'review', 'score']):
            extracted['ratings'] = self._extract_ratings_universal(soup)
        
        # Extract locations if requested
        if any(word in requirements_lower for word in ['location', 'address', 'place', 'area']):
            extracted['locations'] = self._extract_locations_universal(soup)
        
        # Extract years if requested
        if any(word in requirements_lower for word in ['year', 'date', 'model']):
            extracted['years'] = self._extract_years_universal(soup)
        
        # Extract descriptions if requested
        if any(word in requirements_lower for word in ['description', 'details', 'info']):
            extracted['descriptions'] = self._extract_descriptions_universal(soup)
        
        # If no specific requirements or "all" requested, extract everything
        if not extracted or 'all' in requirements_lower:
            extracted = {
                'prices': self._extract_prices_universal(soup),
                'products': self._extract_products_universal(soup),
                'ratings': self._extract_ratings_universal(soup),
                'locations': self._extract_locations_universal(soup),
                'years': self._extract_years_universal(soup),
                'descriptions': self._extract_descriptions_universal(soup)
            }
        
        return extracted
    
    def _extract_products_universal(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Universal product extraction using multiple strategies"""
        products = []
        
        # Strategy 1: Common semantic selectors
        semantic_selectors = [
            'h1', 'h2', 'h3', 'h4',
            '[class*="title"]', '[class*="name"]', '[class*="product"]',
            '[class*="item"]', '[class*="card"]',
            '[data-testid*="title"]', '[data-testid*="name"]',
            '[aria-label*="product"]', '[aria-label*="title"]'
        ]
        
        for selector in semantic_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if self._is_valid_product_text(text):
                    cleaned_text = self._clean_text_universal(text)
                    if cleaned_text and cleaned_text not in [p['value'] for p in products]:
                        products.append({'value': cleaned_text})
        
        # Strategy 2: Link-based extraction (common in e-commerce)
        links = soup.find_all('a', href=True)
        for link in links:
            text = link.get_text(strip=True)
            if self._is_valid_product_text(text):
                cleaned_text = self._clean_text_universal(text)
                if cleaned_text and cleaned_text not in [p['value'] for p in products]:
                    products.append({'value': cleaned_text})
        
        # Strategy 3: Look for product containers and extract titles
        container_selectors = [
            '[class*="product"]', '[class*="item"]', '[class*="card"]',
            '[class*="listing"]', '[class*="result"]'
        ]
        
        for container_selector in container_selectors:
            containers = soup.select(container_selector)
            for container in containers:
                # Look for title elements within containers
                title_elements = container.select('h1, h2, h3, h4, [class*="title"], [class*="name"]')
                for title_elem in title_elements:
                    text = title_elem.get_text(strip=True)
                    if self._is_valid_product_text(text):
                        cleaned_text = self._clean_text_universal(text)
                        if cleaned_text and cleaned_text not in [p['value'] for p in products]:
                            products.append({'value': cleaned_text})
        
        # Strategy 4: Extract from structured data (JSON-LD, microdata)
        structured_data = self._extract_structured_data(soup)
        for item in structured_data:
            if 'name' in item and self._is_valid_product_text(item['name']):
                cleaned_text = self._clean_text_universal(item['name'])
                if cleaned_text and cleaned_text not in [p['value'] for p in products]:
                    products.append({'value': cleaned_text})
        
        return products[:30]  # Limit to 30 products
    
    def _extract_prices_universal(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Universal price extraction"""
        prices = []
        text = soup.get_text()
        
        # Multiple currency patterns
        price_patterns = [
            r'₹[\d,]+(?:\.\d{2})?',  # Indian Rupees
            r'£[\d,]+(?:\.\d{2})?',  # British Pounds
            r'\$[\d,]+(?:\.\d{2})?',  # US Dollars
            r'€[\d,]+(?:\.\d{2})?',  # Euros
            r'[\d,]+(?:\.\d{2})?\s*(?:INR|USD|GBP|EUR)',  # Currency codes
            r'[\d,]+(?:\.\d{2})?\s*(?:rupees?|dollars?|pounds?|euros?)',  # Currency words
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match not in [p['value'] for p in prices]:
                    prices.append({
                        'value': match,
                        'currency': self._detect_currency_universal(match)
                    })
        
        return prices[:30]  # Limit to 30 prices
    
    def _extract_ratings_universal(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Universal rating extraction"""
        ratings = []
        text = soup.get_text()
        
        # Rating patterns
        rating_patterns = [
            r'(\d+(?:\.\d+)?)\s*\/\s*5',
            r'(\d+(?:\.\d+)?)\s*stars?',
            r'Rating:\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*out\s*of\s*5',
            r'(\d+(?:\.\d+)?)\s*\/\s*10',
            r'(\d+(?:\.\d+)?)\s*out\s*of\s*10'
        ]
        
        for pattern in rating_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    rating_value = float(match)
                    if 0 <= rating_value <= 10:
                        scale = 10 if rating_value > 5 else 5
                        ratings.append({
                            'value': rating_value,
                            'scale': scale
                        })
                except ValueError:
                    continue
        
        return ratings[:20]  # Limit to 20 ratings
    
    def _extract_locations_universal(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Universal location extraction"""
        locations = []
        text = soup.get_text()
        
        # Location patterns
        location_patterns = [
            r'[A-Z][a-z]+,\s*[A-Z][a-z]+',  # City, State
            r'[A-Z][a-z]+\s+Layout',  # Area Layout
            r'[A-Z][a-z]+\s+Block',  # Area Block
            r'[A-Z][a-z]+\s+[A-Z][a-z]+',  # Two word locations
            r'\d+\s+[A-Z][a-z]+\s+Street',  # Street addresses
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match not in [l['value'] for l in locations]:
                    locations.append({'value': match})
        
        return locations[:20]  # Limit to 20 locations
    
    def _extract_years_universal(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Universal year extraction"""
        years = []
        text = soup.get_text()
        
        # Year patterns
        year_patterns = [
            r'(20[12]\d)',  # 2010-2029
            r'(19[89]\d)',  # 1980-1999
            r'(\d{4})',  # Any 4-digit year
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                year = int(match)
                if 1980 <= year <= 2030:  # Reasonable year range
                    if match not in [y['value'] for y in years]:
                        years.append({'value': match})
        
        return years[:15]  # Limit to 15 years
    
    def _extract_descriptions_universal(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Universal description extraction"""
        descriptions = []
        
        # Look for description-like elements
        desc_selectors = [
            'p', '.description', '.desc', '.details',
            '[class*="description"]', '[class*="details"]',
            '[class*="info"]', '[class*="summary"]'
        ]
        
        for selector in desc_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if self._is_valid_description_text(text):
                    cleaned_text = self._clean_text_universal(text)
                    if cleaned_text and cleaned_text not in [d['value'] for d in descriptions]:
                        descriptions.append({'value': cleaned_text})
        
        return descriptions[:15]  # Limit to 15 descriptions
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract structured data from JSON-LD and microdata"""
        structured_items = []
        
        # Extract JSON-LD structured data
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    structured_items.append(data)
                elif isinstance(data, list):
                    structured_items.extend(data)
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Extract microdata
        microdata_items = soup.find_all(attrs={'itemtype': True})
        for item in microdata_items:
            item_data = {}
            properties = item.find_all(attrs={'itemprop': True})
            for prop in properties:
                prop_name = prop.get('itemprop')
                prop_value = prop.get_text(strip=True) or prop.get('content', '')
                if prop_name and prop_value:
                    item_data[prop_name] = prop_value
            if item_data:
                structured_items.append(item_data)
        
        return structured_items
    
    def _is_valid_product_text(self, text: str) -> bool:
        """Check if text is likely a valid product name"""
        if not text or len(text) < 3 or len(text) > 200:
            return False
        
        # Skip if it's just numbers or symbols
        if re.match(r'^[\d\s\-\.]+$', text):
            return False
        
        # Skip common navigation/UI text
        ui_patterns = [
            r'^(Home|Shop|Buy|Sale|Deal|Offer|Discount|Free|Shipping|Delivery)$',
            r'^(Click|View|See|More|Details|Info|Specifications)$',
            r'^(Add|Cart|Wishlist|Compare|Share|Review|Rating)$',
            r'^(Login|Sign|Register|Account|Profile)$',
            r'^(Search|Filter|Sort|Price|Name|Date)$'
        ]
        
        for pattern in ui_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return False
        
        return True
    
    def _is_valid_description_text(self, text: str) -> bool:
        """Check if text is likely a valid description"""
        if not text or len(text) < 20 or len(text) > 500:
            return False
        
        # Skip if it's mostly links or navigation
        if text.count('http') > 2 or text.count('www') > 2:
            return False
        
        return True
    
    def _clean_text_universal(self, text: str) -> str:
        """Universal text cleaning"""
        # Remove price patterns that might be mixed in
        price_patterns = [
            r'₹[\d,]+(?:\.\d{2})?',
            r'£[\d,]+(?:\.\d{2})?', 
            r'\$[\d,]+(?:\.\d{2})?',
            r'€[\d,]+(?:\.\d{2})?',
            r'[\d,]+(?:\.\d{2})?\s*(?:INR|USD|GBP|EUR)',
            r'[\d,]+% off',
            r'[\d,]+% discount'
        ]
        
        for pattern in price_patterns:
            text = re.sub(pattern, '', text)
        
        # Remove common noise words and patterns
        noise_patterns = [
            r'\b(Home|Shop|Buy|Sale|Deal|Offer|Discount|Free|Shipping|Delivery)\b',
            r'\b(Click|View|See|More|Details|Info|Specifications)\b',
            r'\b(Add|Cart|Wishlist|Compare|Share|Review|Rating)\b',
            r'\b(Login|Sign|Register|Account|Profile)\b',
            r'\b(Search|Filter|Sort|Price|Name|Date)\b',
            r'^\s*[0-9]+\s*$',  # Just numbers
            r'^\s*[A-Z]+\s*$',  # Just uppercase letters
            r'^\s*[a-z]+\s*$',  # Just lowercase letters
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Clean up extra whitespace and special characters
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'[^\w\s\-\.]', '', text)  # Remove special chars except hyphens and dots
        
        # Remove if too short or too long
        if len(text) < 3 or len(text) > 200:
            return ''
        
        # Remove if it's just a price or percentage
        if re.match(r'^[\d,]+$', text) or re.match(r'^[\d,]+%$', text):
            return ''
        
        return text
    
    def _detect_currency_universal(self, price_str: str) -> str:
        """Detect currency from price string"""
        if '₹' in price_str:
            return 'INR'
        elif '£' in price_str:
            return 'GBP'
        elif '$' in price_str:
            return 'USD'
        elif '€' in price_str:
            return 'EUR'
        elif 'INR' in price_str.upper():
            return 'INR'
        elif 'USD' in price_str.upper():
            return 'USD'
        elif 'GBP' in price_str.upper():
            return 'GBP'
        elif 'EUR' in price_str.upper():
            return 'EUR'
        else:
            return 'Unknown'
    
    def _create_tables(self, extracted_data: Dict[str, list]) -> Dict[str, str]:
        """Create clean tables from extracted data"""
        tables = {}
        
        for data_type, items in extracted_data.items():
            if not items:
                continue
                
            # Create DataFrame
            rows = []
            for i, item in enumerate(items, 1):
                row = {'ID': i}
                
                if data_type == 'prices':
                    row.update({
                        'Price': item.get('value', 'N/A'),
                        'Currency': item.get('currency', 'Unknown')
                    })
                elif data_type == 'ratings':
                    row.update({
                        'Rating': item.get('value', 'N/A'),
                        'Scale': item.get('scale', 'N/A')
                    })
                else:
                    # For other types, just show the value
                    row['Value'] = item.get('value', 'N/A')
                
                rows.append(row)
            
            df = pd.DataFrame(rows)
            tables[data_type] = df.to_string(index=False)
        
        return tables

def main():
    """Main interactive scraper"""
    
    print("🚀 Universal Web Scraper")
    print("=" * 50)
    print("This tool will scrape any webpage and extract clean data tables.")
    print("No raw HTML will be shown - just clean, organized results.")
    print()
    
    # Initialize scraper
    scraper = UniversalScraper()
    
    # Get URL
    print("Enter the URL to scrape:")
    print("Examples:")
    print("- https://www.amazon.in/s?k=laptop")
    print("- https://www.flipkart.com/search?q=mobile")
    print("- https://www.autotrader.co.uk/car-search")
    print("- https://www.ebay.com/sch/i.html?_nkw=laptop")
    print("- https://www.craigslist.org/search/sss?query=car")
    print()
    
    url = input("URL: ").strip()
    
    if not url:
        print("❌ No URL provided")
        return
    
    # Get requirements
    print("\nWhat data would you like to extract?")
    print("Examples:")
    print("- 'product names and prices'")
    print("- 'prices only'")
    print("- 'ratings and reviews'")
    print("- 'locations and addresses'")
    print("- 'all available information'")
    print()
    
    requirements = input("Requirements: ").strip()
    
    if not requirements:
        requirements = "all available information"
    
    # Run scraping and extraction
    print("\n" + "="*50)
    print("🚀 STARTING UNIVERSAL SCRAPING")
    print("="*50)
    
    results = scraper.scrape_and_extract(url, requirements)
    
    if 'error' in results:
        print(f"\n❌ Error: {results['error']}")
        if 'details' in results:
            print(f"Details: {results['details']}")
    else:
        print("\n" + "="*50)
        print("✅ EXTRACTION COMPLETED")
        print("="*50)
        
        # Show summary
        summary = results['summary']
        print(f"📊 Summary:")
        print(f"   - Page: {results['page_title']}")
        print(f"   - Total items extracted: {summary['total_items']}")
        print(f"   - Data types: {', '.join(summary['data_types'])}")
        
        # Show tables
        tables = results['tables']
        if tables:
            print(f"\n📋 EXTRACTED DATA TABLES:")
            print("="*50)
            
            for data_type, table in tables.items():
                print(f"\n🔹 {data_type.upper()}:")
                print("-" * 40)
                print(table)
                print()
        else:
            print("\n⚠️ No data was extracted. Try different requirements.")
        
        # Save results
        timestamp = int(time.time())
        output_file = f"universal_results_{timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {output_file}")

if __name__ == "__main__":
    main() 