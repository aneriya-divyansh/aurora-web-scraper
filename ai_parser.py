import requests
import json
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Any
import openai
import os

class AIContentParser:
    def __init__(self, api_key: str = None):
        """Initialize the AI parser with OpenAI API key"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
        else:
            print("⚠️ Warning: No OpenAI API key found. Using fallback parsing methods.")
    
    def analyze_content(self, html_content: str, extraction_requirements: str) -> Dict[str, Any]:
        """
        Analyze HTML content and extract data based on requirements
        
        Args:
            html_content: Raw HTML content from scraping
            extraction_requirements: User's requirements for data extraction
            
        Returns:
            Dictionary containing extracted data and metadata
        """
        
        # First, try AI-powered extraction if API key is available
        if self.api_key:
            return self._ai_extract(html_content, extraction_requirements)
        else:
            return self._fallback_extract(html_content, extraction_requirements)
    
    def _ai_extract(self, html_content: str, requirements: str) -> Dict[str, Any]:
        """Use OpenAI to intelligently extract data"""
        
        # Clean HTML for better AI processing
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove scripts, styles, and other non-content elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Extract text content
        text_content = soup.get_text(separator=' ', strip=True)
        
        # Limit content size for API
        if len(text_content) > 8000:
            text_content = text_content[:8000] + "..."
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a web scraping data extraction expert. 
                        Analyze the provided HTML content and extract the requested information.
                        Return the data in a structured JSON format with clear field names.
                        Focus on extracting: product names, prices, ratings, descriptions, 
                        specifications, availability, and any other relevant information."""
                    },
                    {
                        "role": "user", 
                        "content": f"""
                        Requirements: {requirements}
                        
                        HTML Content:
                        {text_content}
                        
                        Please extract the requested data and return it as a JSON object with:
                        1. A 'data' array containing the extracted items
                        2. A 'summary' object with counts and metadata
                        3. A 'fields' array listing what was extracted
                        """
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            
            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                else:
                    # If no JSON found, create structured response
                    extracted_data = {
                        "data": [],
                        "summary": {"total_items": 0, "extraction_method": "ai_fallback"},
                        "fields": [],
                        "raw_ai_response": ai_response
                    }
                
                return extracted_data
                
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "data": [],
                    "summary": {"total_items": 0, "extraction_method": "ai_json_error"},
                    "fields": [],
                    "raw_ai_response": ai_response
                }
                
        except Exception as e:
            print(f"AI extraction failed: {e}")
            return self._fallback_extract(html_content, requirements)
    
    def _fallback_extract(self, html_content: str, requirements: str) -> Dict[str, Any]:
        """Fallback extraction using traditional methods"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        extracted_data = {
            "data": [],
            "summary": {"total_items": 0, "extraction_method": "fallback"},
            "fields": []
        }
        
        # Extract common patterns based on requirements
        if "price" in requirements.lower():
            prices = self._extract_prices(soup)
            extracted_data["data"].extend(prices)
            extracted_data["fields"].append("prices")
            
        if "product" in requirements.lower() or "name" in requirements.lower():
            products = self._extract_product_names(soup)
            extracted_data["data"].extend(products)
            extracted_data["fields"].append("product_names")
            
        if "rating" in requirements.lower():
            ratings = self._extract_ratings(soup)
            extracted_data["data"].extend(ratings)
            extracted_data["fields"].append("ratings")
            
        if "location" in requirements.lower() or "address" in requirements.lower():
            locations = self._extract_locations(soup)
            extracted_data["data"].extend(locations)
            extracted_data["fields"].append("locations")
        
        extracted_data["summary"]["total_items"] = len(extracted_data["data"])
        return extracted_data
    
    def _extract_prices(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract price information"""
        prices = []
        
        # Look for price patterns
        price_patterns = [
            r'₹[\d,]+',
            r'£[\d,]+', 
            r'\$[\d,]+',
            r'[\d,]+ INR',
            r'[\d,]+ USD'
        ]
        
        text = soup.get_text()
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                prices.append({
                    "type": "price",
                    "value": match,
                    "currency": self._detect_currency(match)
                })
        
        return prices
    
    def _extract_product_names(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract product names"""
        products = []
        
        # Look for common product name selectors
        selectors = [
            'h1', 'h2', 'h3', '.product-title', '.product-name',
            '[class*="title"]', '[class*="name"]', '[class*="product"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 3 and len(text) < 200:
                    products.append({
                        "type": "product_name",
                        "value": text
                    })
        
        return products
    
    def _extract_ratings(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract rating information"""
        ratings = []
        
        # Look for rating patterns
        rating_patterns = [
            r'(\d+(?:\.\d+)?)\s*\/\s*5',
            r'(\d+(?:\.\d+)?)\s*stars?',
            r'Rating:\s*(\d+(?:\.\d+)?)'
        ]
        
        text = soup.get_text()
        for pattern in rating_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                ratings.append({
                    "type": "rating",
                    "value": float(match),
                    "scale": 5
                })
        
        return ratings
    
    def _extract_locations(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract location information"""
        locations = []
        
        # Look for address patterns
        address_patterns = [
            r'[A-Z][a-z]+,\s*[A-Z][a-z]+',
            r'[A-Z][a-z]+\s+Layout',
            r'[A-Z][a-z]+\s+Block'
        ]
        
        text = soup.get_text()
        for pattern in address_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                locations.append({
                    "type": "location",
                    "value": match
                })
        
        return locations
    
    def _detect_currency(self, price_str: str) -> str:
        """Detect currency from price string"""
        if '₹' in price_str:
            return 'INR'
        elif '£' in price_str:
            return 'GBP'
        elif '$' in price_str:
            return 'USD'
        else:
            return 'Unknown'

def interactive_parser():
    """Interactive parser that asks user requirements and processes content"""
    
    print("🤖 AI-Powered Web Content Parser")
    print("=" * 50)
    
    # Initialize parser
    parser = AIContentParser()
    
    # Get user requirements
    print("\nWhat type of data would you like to extract?")
    print("Examples:")
    print("- 'product names and prices'")
    print("- 'car listings with prices and years'") 
    print("- 'property listings with locations and prices'")
    print("- 'all available information'")
    
    requirements = input("\nEnter your requirements: ").strip()
    
    if not requirements:
        requirements = "all available information"
    
    # Ask which content file to parse
    print("\nAvailable content files:")
    content_files = [
        "autotrader_content.html",
        "amazon_content.html", 
        "flipkart_content.html",
        "housing_content.html",
        "apple_content.html"
    ]
    
    for i, file in enumerate(content_files, 1):
        print(f"{i}. {file}")
    
    try:
        choice = int(input("\nSelect file number (or 0 to enter custom path): "))
        if choice == 0:
            file_path = input("Enter custom file path: ")
        elif 1 <= choice <= len(content_files):
            file_path = content_files[choice - 1]
        else:
            print("Invalid choice, using autotrader_content.html")
            file_path = "autotrader_content.html"
    except ValueError:
        print("Invalid input, using autotrader_content.html")
        file_path = "autotrader_content.html"
    
    # Read and parse content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"\n📊 Analyzing {file_path}...")
        print(f"📋 Requirements: {requirements}")
        
        # Extract data
        result = parser.analyze_content(html_content, requirements)
        
        # Display results
        print("\n" + "="*50)
        print("📊 EXTRACTION RESULTS")
        print("="*50)
        
        print(f"📈 Summary:")
        print(f"   - Total items extracted: {result['summary']['total_items']}")
        print(f"   - Extraction method: {result['summary']['extraction_method']}")
        print(f"   - Fields extracted: {', '.join(result['fields'])}")
        
        if result['data']:
            print(f"\n📋 Extracted Data:")
            print("-" * 50)
            
            # Group data by type
            grouped_data = {}
            for item in result['data']:
                item_type = item.get('type', 'unknown')
                if item_type not in grouped_data:
                    grouped_data[item_type] = []
                grouped_data[item_type].append(item)
            
            # Display grouped data
            for data_type, items in grouped_data.items():
                print(f"\n🔹 {data_type.upper()}:")
                for i, item in enumerate(items[:10], 1):  # Show first 10 items
                    value = item.get('value', 'N/A')
                    if isinstance(value, float):
                        value = f"{value:.2f}"
                    print(f"   {i}. {value}")
                
                if len(items) > 10:
                    print(f"   ... and {len(items) - 10} more items")
        
        # Save results to JSON
        output_file = f"extracted_data_{file_path.replace('.html', '')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_file}")
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Error processing file: {e}")

if __name__ == "__main__":
    interactive_parser() 