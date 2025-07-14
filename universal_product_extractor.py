#!/usr/bin/env python3
"""
Universal Product Extractor - Works across different e-commerce and travel booking websites
Enhanced version with better JavaScript and HTML handling, including travel booking sites
"""

import requests
import json
import re
import time
import base64
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Any, Optional
import openai

class UniversalProductExtractor:
    """Universal product data extractor for any e-commerce or travel booking site"""
    
    def __init__(self):
        self.proxy_url = "http://localhost:8000/api/scrape"
        self.openai_client = None
        self.setup_openai()
        
    def setup_openai(self):
        """Setup OpenAI client if API key is available"""
        try:
            import openai
            # You can set your OpenAI API key here or use environment variable
            # openai.api_key = "your-api-key-here"
            # Try both old and new API formats
            try:
                self.openai_client = openai.OpenAI()
            except (AttributeError, Exception):
                # Fallback to old API format or handle missing API key
                try:
                    self.openai_client = openai
                except Exception:
                    print("⚠️ OpenAI not available. OCR fallback will not work.")
                    self.openai_client = None
        except ImportError:
            print("⚠️ OpenAI not available. OCR fallback will not work.")
            self.openai_client = None
    
    def extract_products(self, url: str, num_pages: int = 1) -> Optional[Dict[str, Any]]:
        """Extract structured product data from any e-commerce or travel booking site"""
        
        print(f"\n🛒 Universal Product Extractor")
        print(f"URL: {url}")
        print(f"Pages to scrape: {num_pages}")
        print("=" * 60)
        
        all_products = []
        total_scraping_time = 0
        page_titles = []
        ocr_prompted = False
        
        try:
            for page_num in range(1, num_pages + 1):
                print(f"\n📄 Scraping page {page_num}/{num_pages}...")
                
                # Generate page URL
                page_url = self._get_page_url(url, page_num)
                
                # Get HTML content via JavaScript rendering
                start_time = time.time()
                try:
                    response = requests.get(self.proxy_url, params={"url": page_url}, timeout=60)
                except requests.exceptions.Timeout:
                    print(f"❌ Timeout after 60 seconds on page {page_num}")
                    ocr_prompted = True
                    use_ocr = input("Extraction is taking too long. Would you like to try OCR method (screenshot + OpenAI parsing)? (y/n): ").strip().lower()
                    if use_ocr in ['y', 'yes']:
                        print("\n🔄 Trying OCR fallback method...")
                        return self.extract_with_ocr_fallback(url, num_pages)
                    else:
                        print("Skipping OCR fallback.")
                        return None
                end_time = time.time()
                
                page_time = end_time - start_time
                total_scraping_time += page_time
                
                if page_time > 45 and not ocr_prompted:
                    ocr_prompted = True
                    use_ocr = input("Extraction is taking longer than expected (>45s). Would you like to try OCR method (screenshot + OpenAI parsing)? (y/n): ").strip().lower()
                    if use_ocr in ['y', 'yes']:
                        print("\n🔄 Trying OCR fallback method...")
                        return self.extract_with_ocr_fallback(url, num_pages)
                    else:
                        print("Skipping OCR fallback.")
                        return None
                
                print(f"✅ Response Status: {response.status_code}")
                print(f"⏱️ Page Time: {page_time:.2f} seconds")
                
                if response.status_code == 200:
                    data = response.json()
                    html_content = data.get('content', '')
                    page_titles.append(data.get('title', ''))
                    
                    # Parse with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Determine site type and extract accordingly
                    domain = urlparse(url).netloc.lower()
                    if self._is_travel_site(domain):
                        print("✈️ Detected travel booking site - using travel-specific extraction")
                        products = self._parse_travel_products(soup, page_url)
                    else:
                        print("🛍️ Detected e-commerce site - using product-specific extraction")
                        products = self._parse_products(soup, page_url)
                    
                    # Add page number to each product
                    for product in products:
                        product['page_number'] = page_num
                    
                    all_products.extend(products)
                    print(f"📊 Found {len(products)} products on page {page_num}")
                    
                    # If 0 products found, prompt for OCR fallback
                    if len(products) == 0 and not ocr_prompted:
                        ocr_prompted = True
                        use_ocr = input("No products found. Would you like to try OCR method (screenshot + OpenAI parsing)? (y/n): ").strip().lower()
                        if use_ocr in ['y', 'yes']:
                            print("\n🔄 Trying OCR fallback method...")
                            return self.extract_with_ocr_fallback(url, num_pages)
                        else:
                            print("Skipping OCR fallback.")
                            return None
                else:
                    print(f"❌ Error on page {page_num}: {response.text}")
                    ocr_prompted = True
                    use_ocr = input("Extraction failed. Would you like to try OCR method (screenshot + OpenAI parsing)? (y/n): ").strip().lower()
                    if use_ocr in ['y', 'yes']:
                        print("\n🔄 Trying OCR fallback method...")
                        return self.extract_with_ocr_fallback(url, num_pages)
                    else:
                        print("Skipping OCR fallback.")
                        return None
                
                # Add delay between pages to be respectful
                if page_num < num_pages:
                    print("⏳ Waiting 2 seconds before next page...")
                    time.sleep(2)
            
            # Generate summary
            summary = {
                'total_products': len(all_products),
                'total_pages': num_pages,
                'scraping_time': total_scraping_time,
                'page_titles': page_titles,
                'products': all_products,
                'site_type': 'travel' if self._is_travel_site(urlparse(url).netloc.lower()) else 'ecommerce'
            }
            
            # Display results
            self._display_results(summary)
            
            # Save structured data
            self._save_structured_data(summary, url)
            
            return summary
                
        except Exception as e:
            print(f"❌ Exception occurred: {e}")
            use_ocr = input("Extraction failed due to an error. Would you like to try OCR method (screenshot + OpenAI parsing)? (y/n): ").strip().lower()
            if use_ocr in ['y', 'yes']:
                print("\n🔄 Trying OCR fallback method...")
                return self.extract_with_ocr_fallback(url, num_pages)
            else:
                print("Skipping OCR fallback.")
                return None
    
    def extract_with_ocr_fallback(self, url: str, num_pages: int = 1) -> Optional[Dict[str, Any]]:
        """Extract data using OCR fallback when regular extraction fails"""
        
        print(f"\n🔍 OCR Fallback Method")
        print(f"URL: {url}")
        print(f"Pages to scrape: {num_pages}")
        print("=" * 60)
        
        all_products = []
        total_scraping_time = 0
        
        try:
            for page_num in range(1, num_pages + 1):
                print(f"\n📸 Taking screenshot of page {page_num}/{num_pages}...")
                
                # Generate page URL
                page_url = self._get_page_url(url, page_num)
                
                # Take screenshot using Playwright
                start_time = time.time()
                screenshot_data = self._take_screenshot(page_url)
                end_time = time.time()
                
                page_time = end_time - start_time
                total_scraping_time += page_time
                
                if screenshot_data:
                    print(f"✅ Screenshot captured in {page_time:.2f} seconds")
                    
                    # Use OpenAI to parse the screenshot
                    products = self._parse_screenshot_with_openai(screenshot_data, page_url, page_num)
                    
                    if products:
                        all_products.extend(products)
                        print(f"📊 Found {len(products)} products on page {page_num}")
                    else:
                        print(f"❌ No products found on page {page_num}")
                else:
                    print(f"❌ Failed to capture screenshot for page {page_num}")
                    if page_num == 1:  # If first page fails, stop
                        return None
                
                # Add delay between pages
                if page_num < num_pages:
                    print("⏳ Waiting 2 seconds before next page...")
                    time.sleep(2)
            
            # Generate summary
            summary = {
                'total_products': len(all_products),
                'total_pages': num_pages,
                'scraping_time': total_scraping_time,
                'products': all_products,
                'extraction_method': 'ocr',
                'site_type': 'travel' if self._is_travel_site(urlparse(url).netloc.lower()) else 'ecommerce'
            }
            
            # Display results
            self._display_results(summary)
            
            # Save structured data
            self._save_structured_data(summary, url)
            
            return summary
                
        except Exception as e:
            print(f"❌ OCR fallback failed: {e}")
            return None
    
    def _take_screenshot(self, url: str) -> Optional[str]:
        """Take screenshot using Playwright via backend proxy"""
        
        try:
            # Use the backend proxy to take screenshot
            # Use base URL for screenshot endpoint
            base_url = self.proxy_url.replace('/api/scrape', '')
            response = requests.get(
                f"{base_url}/api/screenshot", 
                params={"url": url}, 
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('screenshot_base64')
            else:
                print(f"❌ Screenshot failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Screenshot error: {e}")
            return None
    
    def _parse_screenshot_with_openai(self, screenshot_base64: str, url: str, page_num: int) -> List[Dict[str, Any]]:
        """Parse screenshot using OpenAI Vision API"""
        
        if not self.openai_client:
            print("❌ OpenAI not available for OCR parsing")
            return []
        
        try:
            # Determine site type for better prompting
            domain = urlparse(url).netloc.lower()
            is_travel = self._is_travel_site(domain)
            
            if is_travel:
                system_prompt = """You are an expert at extracting travel booking information from screenshots. 
                Extract structured data about bus tickets, flights, hotels, etc. Include:
                - Type (bus, flight, hotel)
                - Title/Route
                - Price
                - Departure/Arrival times
                - Duration
                - Operator/Airline
                - Stops
                Return as JSON array of objects."""
            else:
                system_prompt = """You are an expert at extracting product information from e-commerce screenshots. 
                Extract structured data about products including:
                - Title
                - Price
                - Original price
                - Discount
                - Rating
                - Brand
                Return as JSON array of objects."""
            
            # Try new API format first, then fallback to old format
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Extract all product/travel information from this screenshot. Return as JSON array."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{screenshot_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=2000
                )
            except AttributeError:
                # Fallback to old API format
                response = self.openai_client.ChatCompletion.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Extract all product/travel information from this screenshot. Return as JSON array."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{screenshot_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=2000
                )
            
            # Parse the response
            content = response.choices[0].message.content
            
            # Extract JSON from response
            try:
                # Find JSON array in the response
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    products_data = json.loads(json_match.group(0))
                    
                    # Convert to our standard format
                    products = []
                    for i, product_data in enumerate(products_data):
                        product = {
                            'index': i + 1,
                            'page_number': page_num,
                            'title': product_data.get('title', ''),
                            'price': product_data.get('price', ''),
                            'original_price': product_data.get('original_price', ''),
                            'discount': product_data.get('discount', ''),
                            'rating': product_data.get('rating', ''),
                            'brand': product_data.get('brand', ''),
                            'platform': urlparse(url).netloc
                        }
                        
                        # Add travel-specific fields if it's a travel site
                        if is_travel:
                            product.update({
                                'type': product_data.get('type', ''),
                                'departure_time': product_data.get('departure_time', ''),
                                'arrival_time': product_data.get('arrival_time', ''),
                                'duration': product_data.get('duration', ''),
                                'operator': product_data.get('operator', ''),
                                'route': product_data.get('route', ''),
                                'stops': product_data.get('stops', '')
                            })
                        
                        products.append(product)
                    
                    return products
                else:
                    print("❌ No JSON array found in OpenAI response")
                    return []
                    
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse OpenAI response as JSON: {e}")
                return []
                
        except Exception as e:
            print(f"❌ OpenAI parsing error: {e}")
            return []
    
    def _get_page_url(self, base_url: str, page_num: int) -> str:
        """Generate page URL based on common pagination patterns"""
        
        if page_num == 1:
            return base_url
        
        # Common pagination patterns
        if '?' in base_url:
            # URL already has parameters
            if 'page=' in base_url:
                # Replace existing page parameter
                return re.sub(r'page=\d+', f'page={page_num}', base_url)
            else:
                # Add page parameter
                return f"{base_url}&page={page_num}"
        else:
            # URL has no parameters
            return f"{base_url}?page={page_num}"
    
    def _is_travel_site(self, domain: str) -> bool:
        """Check if the domain is a travel booking site"""
        travel_keywords = [
            'makemytrip', 'mmt', 'booking', 'hotels', 'expedia',
            'airbnb', 'tripadvisor', 'goibibo', 'yatra', 'cleartrip',
            'redbus', 'abhibus', 'irctc', 'railway', 'skyscanner', 
            'kayak', 'momondo', 'travel', 'trip', 'journey'
        ]
        return any(keyword in domain.lower() for keyword in travel_keywords)
    
    def _parse_travel_products(self, soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
        """Parse travel booking products (buses, flights, hotels, etc.)"""
        
        products = []
        
        # Travel-specific container patterns
        travel_selectors = [
            # Bus ticket patterns
            '[class*="bus"]', '[class*="ticket"]', '[class*="route"]',
            '[class*="journey"]', '[class*="departure"]', '[class*="arrival"]',
            '[class*="operator"]', '[class*="fare"]', '[class*="seat"]',
            
            # Flight patterns
            '[class*="flight"]', '[class*="airline"]', '[class*="depart"]',
            '[class*="arrive"]', '[class*="duration"]', '[class*="stops"]',
            
            # Hotel patterns
            '[class*="hotel"]', '[class*="property"]', '[class*="room"]',
            '[class*="accommodation"]', '[class*="amenity"]',
            
            # Generic travel patterns
            '[class*="card"]', '[class*="item"]', '[class*="listing"]',
            '[class*="result"]', '[class*="option"]', '[class*="choice"]',
            
            # Data attributes for travel sites
            '[data-testid*="bus"]', '[data-testid*="flight"]', '[data-testid*="hotel"]',
            '[data-id*="bus"]', '[data-id*="flight"]', '[data-id*="hotel"]',
            
            # Travel site specific patterns
            '[class*="makeMyTrip"]', '[class*="mmt"]',
            'div[class*="bus"]', 'div[class*="ticket"]',
            
            # Generic containers with travel-related content
            'div:has(span:contains("₹"))',  # Price indicators
            'div:has(span:contains("Bus"))', 'div:has(span:contains("Flight"))',
            'div:has(span:contains("Hotel"))', 'div:has(span:contains("Route"))',
        ]
        
        # Find travel product containers
        travel_containers = []
        
        # Strategy 1: Try specific travel selectors
        for selector in travel_selectors:
            try:
                containers = soup.select(selector)
                if containers:
                    print(f"🔍 Found {len(containers)} travel containers with selector: {selector}")
                    travel_containers.extend(containers)
                    if len(containers) > 3:  # If we found a good number, use this selector
                        break
            except Exception as e:
                continue
        
        # Strategy 2: Look for price patterns in travel context
        if not travel_containers:
            print("🔍 No travel containers found with specific selectors, trying price patterns...")
            
            # Look for any div with travel-related price patterns
            all_divs = soup.find_all('div')
            for div in all_divs:
                div_text = div.get_text()
                # Look for travel-specific price patterns
                if (re.search(r'₹[\d,]+|\$[\d,]+\.?\d*|£[\d,]+\.?\d*', div_text) and
                    any(keyword in div_text.lower() for keyword in 
                        ['bus', 'flight', 'hotel', 'route', 'departure', 'arrival', 
                         'operator', 'duration', 'seat', 'fare', 'ticket'])):
                    travel_containers.append(div)
            
            print(f"🔍 Found {len(travel_containers)} potential travel containers with price patterns")
        
        # Strategy 3: Look for time patterns (common in travel)
        if not travel_containers:
            print("🔍 No travel containers found with price patterns, trying time patterns...")
            
            all_divs = soup.find_all('div')
            for div in all_divs:
                div_text = div.get_text()
                # Look for time patterns common in travel
                if re.search(r'\d{1,2}:\d{2}\s*(?:AM|PM)?', div_text):
                    if any(keyword in div_text.lower() for keyword in 
                          ['bus', 'flight', 'departure', 'arrival', 'route']):
                        travel_containers.append(div)
            
            print(f"🔍 Found {len(travel_containers)} potential travel containers with time patterns")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_containers = []
        for container in travel_containers:
            container_id = str(container)
            if container_id not in seen:
                seen.add(container_id)
                unique_containers.append(container)
        
        print(f"📊 Total unique travel containers: {len(unique_containers)}")
        
        # Extract data from each container
        for i, container in enumerate(unique_containers[:20]):  # Limit to first 20
            travel_data = self._extract_travel_data(container, i + 1, url)
            if travel_data:
                products.append(travel_data)
        
        return products
    
    def _extract_travel_data(self, container, index: int, base_url: str) -> Optional[Dict[str, Any]]:
        """Extract structured data from a travel booking container"""
        
        travel_item = {
            'index': index,
            'type': '',  # bus, flight, hotel, etc.
            'title': '',
            'price': '',
            'original_price': '',
            'departure_time': '',
            'arrival_time': '',
            'duration': '',
            'operator': '',
            'route': '',
            'stops': '',
            'amenities': [],
            'rating': '',
            'reviews_count': '',
            'image_url': '',
            'booking_url': '',
            'platform': urlparse(base_url).netloc
        }
        
        container_text = container.get_text()
        
        # Determine travel type
        if any(word in container_text.lower() for word in ['bus', 'route', 'operator']):
            travel_item['type'] = 'bus'
        elif any(word in container_text.lower() for word in ['flight', 'airline', 'departure']):
            travel_item['type'] = 'flight'
        elif any(word in container_text.lower() for word in ['hotel', 'property', 'room']):
            travel_item['type'] = 'hotel'
        else:
            travel_item['type'] = 'travel'
        
        # Enhanced title extraction for travel
        title_selectors = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            '[class*="title"]', '[class*="name"]', '[class*="route"]',
            '[class*="operator"]', '[class*="airline"]', '[class*="hotel"]',
            'a[title]', 'a[alt]',
            '[title]', '[alt]',
        ]
        
        for selector in title_selectors:
            title_elem = container.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text().strip()
                title_attr = title_elem.get('title', '').strip() or title_elem.get('alt', '').strip()
                
                if title_attr and len(title_attr) > len(title_text):
                    travel_item['title'] = title_attr
                elif title_text:
                    travel_item['title'] = title_text
                
                if travel_item['title']:
                    break
        
        # Enhanced price extraction for travel
        price_patterns = [
            r'₹[\d,]+(?:\.\d{2})?',  # Indian Rupees
            r'\$[\d,]+\.?\d*',       # US Dollars
            r'£[\d,]+\.?\d*',        # British Pounds
            r'€[\d,]+\.?\d*',        # Euros
            r'[\d,]+\.?\d*\s*(?:USD|INR|GBP|EUR)',
            r'Price:\s*₹[\d,]+',
            r'Fare:\s*₹[\d,]+',
            r'Cost:\s*₹[\d,]+',
        ]
        
        for pattern in price_patterns:
            prices = re.findall(pattern, container_text)
            if prices:
                for price in prices:
                    if not any(word in price.lower() for word in ['mrp', 'was', 'original']):
                        travel_item['price'] = price
                        break
                if travel_item['price']:
                    break
        
        # Time extraction for travel
        time_patterns = [
            r'(\d{1,2}:\d{2})\s*(?:AM|PM)?',
            r'(\d{1,2}:\d{2})\s*(?:am|pm)?',
            r'Departure:\s*(\d{1,2}:\d{2})',
            r'Arrival:\s*(\d{1,2}:\d{2})',
        ]
        
        times = []
        for pattern in time_patterns:
            times.extend(re.findall(pattern, container_text))
        
        if len(times) >= 2:
            travel_item['departure_time'] = times[0]
            travel_item['arrival_time'] = times[1]
        elif len(times) == 1:
            travel_item['departure_time'] = times[0]
        
        # Duration extraction
        duration_patterns = [
            r'(\d+h\s*\d*m)',  # 2h 30m format
            r'(\d+:\d+)',      # 2:30 format
            r'Duration:\s*(\d+h\s*\d*m)',
            r'(\d+)\s*hours?',
        ]
        
        for pattern in duration_patterns:
            durations = re.findall(pattern, container_text)
            if durations:
                travel_item['duration'] = durations[0]
                break
        
        # Operator/Airline extraction
        operator_patterns = [
            r'Operator:\s*(.*?)(?:\s|$)',
            r'Airline:\s*(.*?)(?:\s|$)',
            r'by\s+(.*?)(?:\s|$)',
            r'Operated by\s+(.*?)(?:\s|$)',
        ]
        
        for pattern in operator_patterns:
            operators = re.findall(pattern, container_text)
            if operators:
                travel_item['operator'] = operators[0].strip()
                break
        
        # Route extraction
        route_patterns = [
            r'(.*?)\s*to\s*(.*?)(?:\s|$)',
            r'Route:\s*(.*?)(?:\s|$)',
            r'From\s+(.*?)\s+to\s+(.*?)(?:\s|$)',
        ]
        
        for pattern in route_patterns:
            routes = re.findall(pattern, container_text)
            if routes:
                if isinstance(routes[0], tuple):
                    travel_item['route'] = f"{routes[0][0]} to {routes[0][1]}"
                else:
                    travel_item['route'] = routes[0]
                break
        
        # Stops extraction
        stops_patterns = [
            r'(\d+)\s*stops?',
            r'Non-stop',
            r'Direct',
        ]
        
        for pattern in stops_patterns:
            stops = re.findall(pattern, container_text)
            if stops:
                travel_item['stops'] = stops[0] if stops[0] != '0' else 'Non-stop'
                break
        
        # Enhanced image URL extraction
        img_selectors = ['img', '[data-src]', '[data-lazy-src]']
        for selector in img_selectors:
            img_elem = container.select_one(selector)
            if img_elem:
                img_src = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src')
                if img_src:
                    if not img_src.startswith('http'):
                        img_src = urljoin(base_url, img_src)
                    travel_item['image_url'] = img_src
                    break
        
        # Enhanced booking URL extraction
        link_selectors = ['a[href]', 'a[data-href]', 'button[onclick]']
        for selector in link_selectors:
            link_elem = container.select_one(selector)
            if link_elem:
                href = link_elem.get('href') or link_elem.get('data-href')
                if href:
                    if not href.startswith('http'):
                        href = urljoin(base_url, href)
                    travel_item['booking_url'] = href
                    break
        
        # Only return if we have at least a title, price, or route
        if travel_item['title'] or travel_item['price'] or travel_item['route']:
            return travel_item
        
            return None
    
    def _parse_products(self, soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
        """Parse products using universal patterns with enhanced selectors"""
        
        products = []
        
        # Enhanced product container patterns for better coverage
        product_selectors = [
            # Generic container patterns
            '[data-id]',  # Common for product IDs
            '[data-product-id]',
            '[data-item-id]',
            '[data-asin]',  # Amazon specific
            '[data-component-type="s-search-result"]',  # Amazon search results
            
            # Class-based patterns
            '.product',
            '.item',
            '.card',
            '.listing',
            '.product-item',
            '.product-card',
            '.item-card',
            '.listing-item',
            
            # Pattern-based class matching
            '[class*="product"]',
            '[class*="item"]',
            '[class*="card"]',
            '[class*="listing"]',
            '[class*="result"]',
            '[class*="search-result"]',
            
            # Grid and list items
            'li[class*="product"]',
            'li[class*="item"]',
            'div[class*="product"]',
            'div[class*="item"]',
            'div[class*="card"]',
            
            # Specific e-commerce patterns
            '.s-result-item',  # Search result items
            '.sg-col-inner',   # Grid containers
            '[data-tkid]',     # Product IDs
            'div[style*="width: 25%"]',  # Grid layouts
            '.product-tile',    # Generic
            '.product-container',
            
            # Fallback: any div with product-like content
            'div:has(img)',
            'div:has(a[href*="/product"])',
            'div:has(a[href*="/item"])',
        ]
        
        # Find product containers with multiple strategies
        product_containers = []
        
        # Strategy 1: Try specific selectors
        for selector in product_selectors:
            try:
                containers = soup.select(selector)
                if containers:
                    print(f"🔍 Found {len(containers)} containers with selector: {selector}")
                    product_containers.extend(containers)
                    if len(containers) > 5:  # If we found a good number, use this selector
                        break
            except Exception as e:
                continue
        
        # Strategy 2: If no products found, try broader patterns
        if not product_containers:
            print("🔍 No products found with specific selectors, trying broader patterns...")
            
            # Look for any div with price patterns
            all_divs = soup.find_all('div')
            for div in all_divs:
                div_text = div.get_text()
                if re.search(r'₹[\d,]+|\$[\d,]+\.?\d*|£[\d,]+\.?\d*', div_text):
                    # Check if it has some product-like structure
                    if div.find('img') or div.find('a'):
                        product_containers.append(div)
            
            print(f"🔍 Found {len(product_containers)} potential product containers with price patterns")
        
        # Strategy 3: If still no products, try OCR fallback
        if not product_containers:
            print("🔍 No products found with HTML parsing, suggesting OCR fallback...")
            return []
        
        # Remove duplicates while preserving order
        seen = set()
        unique_containers = []
        for container in product_containers:
            container_id = str(container)
            if container_id not in seen:
                seen.add(container_id)
                unique_containers.append(container)
        
        print(f"📊 Total unique product containers: {len(unique_containers)}")
        
        # Extract data from each container
        for i, container in enumerate(unique_containers[:30]):  # Limit to first 30 products
            product_data = self._extract_product_data(container, i + 1, url)
            if product_data:
                products.append(product_data)
        
        return products
    
    def _extract_product_data(self, container, index: int, base_url: str) -> Optional[Dict[str, Any]]:
        """Extract structured data from a product container with enhanced parsing"""
        
        product = {
            'index': index,
            'title': '',
            'price': '',
            'original_price': '',
            'discount': '',
            'rating': '',
            'reviews_count': '',
            'image_url': '',
            'product_url': '',
            'availability': '',
            'brand': '',
            'features': [],
            'platform': urlparse(base_url).netloc
        }
        
        container_text = container.get_text()
        
        # Enhanced title extraction
        title_selectors = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            '[class*="title"]', '[class*="name"]', '[class*="product-name"]',
            '[class*="heading"]', '[class*="product-title"]',
            'a[title]', 'a[alt]',  # Links with title/alt attributes
            '[title]', '[alt]',    # Any element with title/alt
        ]
        
        for selector in title_selectors:
            title_elem = container.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text().strip()
                title_attr = title_elem.get('title', '').strip() or title_elem.get('alt', '').strip()
                
                # Use the longer/better title
                if title_attr and len(title_attr) > len(title_text):
                    product['title'] = title_attr
                elif title_text:
                    product['title'] = title_text
                
                if product['title']:
                    break
        
        # Enhanced price extraction with multiple patterns
        price_patterns = [
            r'₹[\d,]+(?:\.\d{2})?',  # Indian Rupees
            r'\$[\d,]+\.?\d*',       # US Dollars
            r'£[\d,]+\.?\d*',        # British Pounds
            r'€[\d,]+\.?\d*',        # Euros
            r'[\d,]+\.?\d*\s*(?:USD|INR|GBP|EUR)',  # Currency codes
            r'Price:\s*₹[\d,]+',     # Labeled prices
            r'MRP:\s*₹[\d,]+',       # MRP prices
        ]
        
        for pattern in price_patterns:
            prices = re.findall(pattern, container_text)
            if prices:
                # Get the first price that looks like a current price
                for price in prices:
                    if not any(word in price.lower() for word in ['mrp', 'was', 'original']):
                        product['price'] = price
                        break
                if product['price']:
                    break
        
        # Enhanced original price extraction - look for separate original price elements
        original_price_selectors = [
            '[class*="original"]',
            '[class*="was"]',
            '[class*="mrp"]',
            'span[class*="strike"]',
            'del',
            's',  # Strikethrough elements
        ]
        
        for selector in original_price_selectors:
            original_elem = container.select_one(selector)
            if original_elem:
                original_text = original_elem.get_text().strip()
                # Extract price from the text
                price_match = re.search(r'₹[\d,]+(?:\.\d{2})?', original_text)
                if price_match:
                    product['original_price'] = price_match.group(0)
                    break
        
        # If no original price found with selectors, try regex patterns
        if not product['original_price']:
            original_price_patterns = [
                r'M\.R\.P:\s*₹[\d,]+',
                r'Original Price:\s*₹[\d,]+',
                r'Was:\s*₹[\d,]+',
                r'List Price:\s*₹[\d,]+',
            ]
            
            for pattern in original_price_patterns:
                original_prices = re.findall(pattern, container_text)
                if original_prices:
                    product['original_price'] = original_prices[0]
                    break
        
        # Enhanced discount extraction - look for discount elements first
        discount_selectors = [
            '[class*="discount"]',
            '[class*="off"]',
            'span[class*="save"]',
        ]
        
        for selector in discount_selectors:
            discount_elem = container.select_one(selector)
            if discount_elem:
                discount_text = discount_elem.get_text().strip()
                # Extract percentage from discount text
                discount_match = re.search(r'(\d+)%', discount_text)
                if discount_match:
                    product['discount'] = f"{discount_match.group(1)}% off"
                    break
        
        # If no discount found with selectors, try regex patterns
        if not product['discount']:
            discount_patterns = [
                r'(\d+)%\s*off',
                r'(\d+)%\s*discount',
                r'Save\s*(\d+)%',
                r'(\d+)%\s*less',
                r'Up\s*to\s*(\d+)%\s*off',
            ]
            
            for pattern in discount_patterns:
                discounts = re.findall(pattern, container_text)
                if discounts:
                    product['discount'] = f"{discounts[0]}% off"
                    break
        
        # Enhanced rating extraction
        rating_patterns = [
            r'(\d+\.?\d*)\s*out\s*of\s*5\s*stars',
            r'(\d+\.?\d*)\s*stars',
            r'Rating:\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)/5',
            r'(\d+\.?\d*)\s*★',
        ]
        
        for pattern in rating_patterns:
            ratings = re.findall(pattern, container_text)
            if ratings:
                product['rating'] = ratings[0]
                break
        
        # Enhanced review count extraction
        review_patterns = [
            r'(\d+(?:,\d+)*)\s*reviews?',
            r'(\d+(?:,\d+)*)\s*ratings?',
            r'(\d+(?:,\d+)*)\s*customers?',
            r'(\d+(?:,\d+)*)\s*people',
        ]
        
        for pattern in review_patterns:
            reviews = re.findall(pattern, container_text)
            if reviews:
                product['reviews_count'] = reviews[0]
                break
        
        # Enhanced image URL extraction
        img_selectors = ['img', '[data-src]', '[data-lazy-src]']
        for selector in img_selectors:
            img_elem = container.select_one(selector)
            if img_elem:
                img_src = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src')
                if img_src:
                    if not img_src.startswith('http'):
                        img_src = urljoin(base_url, img_src)
                    product['image_url'] = img_src
                    break
        
        # Enhanced product URL extraction
        link_selectors = ['a[href]', 'a[data-href]']
        for selector in link_selectors:
            link_elem = container.select_one(selector)
            if link_elem:
                href = link_elem.get('href') or link_elem.get('data-href')
                if href:
                    if not href.startswith('http'):
                        href = urljoin(base_url, href)
                    product['product_url'] = href
                    break
        
        # Enhanced brand extraction
        brand_patterns = [
            r'^(.*?)\s+',  # First word of title
            r'Brand:\s*(.*?)(?:\s|$)',
            r'by\s+(.*?)(?:\s|$)',
            r'from\s+(.*?)(?:\s|$)',
        ]
        
        if product['title']:
            for pattern in brand_patterns:
                brands = re.findall(pattern, product['title'])
                if brands:
                    product['brand'] = brands[0].strip()
                    break
        
        # Enhanced features extraction
        feature_elements = container.find_all(['li', 'span', 'div'], 
                                           string=re.compile(r'[A-Z][^.]*'))
        for elem in feature_elements[:5]:  # Limit to 5 features
            text = elem.get_text().strip()
            if len(text) > 10 and len(text) < 200:  # Reasonable feature length
                product['features'].append(text)
        
        # Only return if we have at least a title or price
        if product['title'] or product['price']:
            return product
        
        return None
    
    def _display_results(self, summary: Dict[str, Any]):
        """Display structured results"""
        
        print(f"\n📊 EXTRACTION RESULTS:")
        print(f"Total Products Found: {summary['total_products']}")
        print(f"Pages Scraped: {summary.get('total_pages', 1)}")
        print(f"Total Scraping Time: {summary['scraping_time']:.2f} seconds")
        print(f"Site Type: {summary.get('site_type', 'unknown')}")
        
        if summary.get('page_titles'):
            print(f"Page Titles: {', '.join(summary['page_titles'][:3])}{'...' if len(summary['page_titles']) > 3 else ''}")
        
        if summary.get('site_type') == 'travel':
            print(f"\n✈️ TRAVEL DETAILS:")
            for i, travel_item in enumerate(summary['products'][:10], 1):  # Show first 10
                print(f"\n--- Travel Item {i} ---")
                if travel_item['type']:
                    print(f"Type: {travel_item['type']}")
                if travel_item['title']:
                    print(f"Title: {travel_item['title'][:80]}...")
                if travel_item['price']:
                    print(f"Price: {travel_item['price']}")
                if travel_item['departure_time']:
                    print(f"Departure: {travel_item['departure_time']}")
                if travel_item['arrival_time']:
                    print(f"Arrival: {travel_item['arrival_time']}")
                if travel_item['duration']:
                    print(f"Duration: {travel_item['duration']}")
                if travel_item['operator']:
                    print(f"Operator: {travel_item['operator']}")
                if travel_item['route']:
                    print(f"Route: {travel_item['route']}")
                if travel_item['stops']:
                    print(f"Stops: {travel_item['stops']}")
        else:
            print(f"\n🛍️ PRODUCT DETAILS:")
            for i, product in enumerate(summary['products'][:10], 1):  # Show first 10
                print(f"\n--- Product {i} ---")
                if product['title']:
                    print(f"Title: {product['title'][:80]}...")
                if product['price']:
                    print(f"Price: {product['price']}")
                if product['original_price']:
                    print(f"Original Price: {product['original_price']}")
                if product['discount']:
                    print(f"Discount: {product['discount']}")
                if product['rating']:
                    print(f"Rating: {product['rating']} stars")
                if product['reviews_count']:
                    print(f"Reviews: {product['reviews_count']}")
                if product['brand']:
                    print(f"Brand: {product['brand']}")
    
    def _save_structured_data(self, summary: Dict[str, Any], url: str):
        """Save structured data to files"""
        
        domain = urlparse(url).netloc.replace('.', '_')
        
        # Save as JSON
        json_filename = f"structured_products_{domain}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Structured JSON saved to: {json_filename}")
        
        # Save as CSV
        csv_filename = f"products_{domain}.csv"
        with open(csv_filename, 'w', encoding='utf-8') as f:
            if summary.get('site_type') == 'travel':
                f.write("Page,Index,Type,Title,Price,Departure Time,Arrival Time,Duration,Operator,Route,Stops,Image URL,Booking URL\n")
                for product in summary['products']:
                    f.write(f"{product.get('page_number', 1)},")
                    f.write(f"{product['index']},")
                    f.write(f"\"{product['type']}\",")
                    f.write(f"\"{product['title']}\",")
                    f.write(f"\"{product['price']}\",")
                    f.write(f"\"{product['departure_time']}\",")
                    f.write(f"\"{product['arrival_time']}\",")
                    f.write(f"\"{product['duration']}\",")
                    f.write(f"\"{product['operator']}\",")
                    f.write(f"\"{product['route']}\",")
                    f.write(f"\"{product['stops']}\",")
                    f.write(f"\"{product['image_url']}\",")
                    f.write(f"\"{product['booking_url']}\"\n")
            else:
                f.write("Page,Index,Title,Price,Original Price,Discount,Rating,Reviews,Brand,Image URL,Product URL\n")
                for product in summary['products']:
                    f.write(f"{product.get('page_number', 1)},")
                    f.write(f"{product['index']},")
                    f.write(f"\"{product['title']}\",")
                    f.write(f"\"{product['price']}\",")
                    f.write(f"\"{product['original_price']}\",")
                    f.write(f"\"{product['discount']}\",")
                    f.write(f"\"{product['rating']}\",")
                    f.write(f"\"{product['reviews_count']}\",")
                    f.write(f"\"{product['brand']}\",")
                    f.write(f"\"{product['image_url']}\",")
                    f.write(f"\"{product['product_url']}\"\n")
        print(f"📄 CSV data saved to: {csv_filename}")

def main():
    """Test universal product extraction"""
    
    print("🛒 Universal Product Extractor")
    print("=" * 50)
    
    extractor = UniversalProductExtractor()
    
    while True:
        url = input("\nEnter URL to extract products (or 'quit' to exit): ").strip()
        
        if url.lower() in ['quit', 'exit', 'q']:
            print("Goodbye! 👋")
            break
            
        if not url:
            print("Please enter a valid URL")
            continue
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            print(f"Added https:// prefix: {url}")
        
        # Ask for number of pages
        while True:
            try:
                num_pages_input = input("Enter number of pages to scrape (default: 1): ").strip()
                if not num_pages_input:
                    num_pages = 1
                    break
                num_pages = int(num_pages_input)
                if num_pages < 1 or num_pages > 50:
                    print("Please enter a number between 1 and 50")
                    continue
                break
            except ValueError:
                print("Please enter a valid number")
                continue
        
        # Extract products
        result = extractor.extract_products(url, num_pages)
        
        if result is not None and result['total_products'] > 0:
            print(f"\n🎉 Successfully extracted {result['total_products']} products from {result['total_pages']} pages!")
        else:
            print(f"\n❌ Failed to extract products from: {url}")
            
            # Offer OCR fallback option
            if result is not None and result['total_products'] == 0:
                print("\n🔍 No products found with regular extraction.")
                use_ocr = input("Would you like to try OCR method (screenshot + OpenAI parsing)? (y/n): ").strip().lower()
                
                if use_ocr in ['y', 'yes']:
                    print("\n🔄 Trying OCR fallback method...")
                    ocr_result = extractor.extract_with_ocr_fallback(url, num_pages)
                    
                    if ocr_result is not None and ocr_result['total_products'] > 0:
                        print(f"\n🎉 OCR method successfully extracted {ocr_result['total_products']} products from {ocr_result['total_pages']} pages!")
                    else:
                        print(f"\n❌ OCR method also failed to extract products from: {url}")
                else:
                    print("Skipping OCR fallback.")
            else:
                print("Regular extraction failed completely.")
        
        continue_extracting = input("\nExtract from another URL? (y/n): ").strip().lower()
        if continue_extracting not in ['y', 'yes']:
            print("Thanks for using the Universal Product Extractor! 👋")
            break

if __name__ == "__main__":
    main() 