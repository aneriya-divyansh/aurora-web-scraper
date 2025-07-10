# Aurora Web Scraper

A comprehensive web scraping solution that combines multiple tools to handle JavaScript-based content, pagination, infinite scrolling, and bot detection. It integrates OpenAI for intelligent content analysis and structured output generation, with a backend proxy server for server-side scraping and OCR fallback capabilities.

## 🚀 Features

### Core Capabilities
- **Multi-Method Scraping**: Supports Playwright, Selenium, and Requests
- **JavaScript Rendering**: Handles dynamic content and SPAs
- **Anti-Detection**: Bypasses bot detection with stealth techniques
- **Pagination Support**: Traditional, load-more, infinite scroll, and API pagination
- **OpenAI Integration**: Intelligent content analysis and structured output
- **Table Generation**: Converts scraped content to structured table format
- **Backend Proxy Server**: Server-side scraping with FastAPI
- **Universal Product Extractor**: Platform-agnostic product data extraction
- **OCR Fallback**: Screenshot-based content extraction when parsing fails
- **Automatic Timeout Handling**: Smart fallback to OCR for slow extractions

### Advanced Features
- **Automatic Method Detection**: Chooses the best scraping method for each site
- **Content Comparison**: Compare multiple sites and find similarities
- **Custom Analysis**: Define custom prompts for specific analysis needs
- **Multiple Output Formats**: CSV, JSON, and structured data
- **Rate Limiting**: Built-in delays and retry mechanisms
- **Proxy Support**: Optional proxy configuration for anonymity
- **User-Configurable Pagination**: Choose number of pages to scrape
- **Intelligent Fallback**: Automatic OCR prompting on failures or zero results
- **Web Interface**: Modern, responsive web UI for easy configuration and monitoring
- **Real-time Status Updates**: Live progress tracking and task management
- **Task History**: View and manage previous scraping jobs
- **Download Results**: Direct download of JSON results with timestamps

## 🛠️ Tools Combined

1. **Playwright** - Modern browser automation for JavaScript-heavy sites
2. **Selenium + Undetected ChromeDriver** - Anti-detection browser automation
3. **Requests + BeautifulSoup** - Fast static HTML scraping
4. **OpenAI API** - Intelligent content analysis and structuring
5. **FastAPI Backend Proxy** - Server-side scraping with Playwright
6. **Pagination Handlers** - Multiple pagination strategies
7. **Anti-Detection Libraries** - Stealth techniques and user agent rotation
8. **OCR Integration** - Screenshot-based content extraction

## 📦 Installation

### Prerequisites
- Python 3.8+
- Chrome/Chromium browser
- OpenAI API key

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd aurora
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers**
```bash
playwright install
```

4. **Set up environment variables**
```bash
cp config.env.example .env
# Edit .env with your OpenAI API key and other settings
```

5. **Install ChromeDriver (for Selenium)**
```bash
# On macOS
brew install chromedriver

# On Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# Or use webdriver-manager (included in requirements)
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file with the following variables:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Proxy Configuration (optional)
PROXY_URL=http://username:password@proxy-server:port

# Browser Configuration
HEADLESS=true
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

# Rate Limiting
REQUEST_DELAY=2
MAX_RETRIES=3

# Output Configuration
OUTPUT_FORMAT=json
SAVE_SCREENSHOTS=false

# Backend Proxy Configuration
BACKEND_PROXY_URL=http://localhost:8000
```

## 📖 Usage

### Web Interface (Recommended)

The easiest way to use Aurora Web Scraper is through the web interface:

```bash
python start_aurora.py
```

This will start both the backend proxy server and the web interface:
- **Frontend**: http://localhost:8080 - Modern web interface
- **Backend**: http://localhost:8000 - API server

### Starting the Backend Proxy Server (Manual)

If you prefer to run components separately, start the backend proxy server:

```bash
python backend_proxy.py
```

The server will run on `http://localhost:8000` and provide endpoints for:
- `/scrape` - Scrape HTML content
- `/screenshot` - Take screenshots with OCR capabilities

### Basic Usage

```python
import asyncio
from universal_product_extractor import UniversalProductExtractor

async def main():
    # Initialize extractor
    extractor = UniversalProductExtractor()
    
    # Extract products from a single site
    result = await extractor.extract_products(
        url="https://example.com/products",
        max_pages=5,
        use_ocr_fallback=True
    )
    
    # Save results
    extractor.save_results(result)
    print("Results saved successfully!")

asyncio.run(main())
```

### Advanced Usage with Pagination

```python
# Extract products with custom pagination
result = await extractor.extract_products(
    url="https://flipkart.com/dupattas",
    max_pages=3,  # User-configurable pagination
    use_ocr_fallback=True,
    delay_between_pages=2
)

# The system will automatically:
# - Handle different pagination types
# - Track page numbers in output
# - Prompt for OCR fallback if extraction fails or takes >45 seconds
```

### OCR Fallback Usage

The system automatically prompts for OCR fallback when:
- Zero products are found
- Extraction takes more than 45 seconds
- Any error occurs during extraction

```python
# Manual OCR fallback
ocr_result = await extractor.ocr_fallback(
    url="https://example.com",
    prompt="Extract all product information from this page"
)
```

## 🎯 Scraping Methods

### 1. Universal Product Extractor (Recommended)
- Platform-agnostic product detection
- Automatic method selection
- Built-in OCR fallback
- User-configurable pagination

### 2. Backend Proxy Server
- Server-side scraping with Playwright
- Bypasses frontend restrictions
- Screenshot capabilities
- JSON API endpoints

### 3. Playwright (Direct)
- Full JavaScript rendering
- Anti-detection measures
- Infinite scroll support
- Screenshot capabilities

### 4. Selenium + Undetected ChromeDriver
- Advanced anti-detection
- Real browser automation
- Complex interactions

### 5. Requests + BeautifulSoup
- Fast static HTML scraping
- Lightweight and efficient
- Good for simple sites

## 📄 Pagination Types

### Traditional Pagination
- Numbered pages (1, 2, 3...)
- Next/Previous buttons
- URL patterns like `?page=2`

### Load More Pagination
- "Load More" buttons
- AJAX content loading
- Dynamic content injection

### Infinite Scroll
- Scroll-based loading
- Lazy loading
- Continuous content flow

### API Pagination
- JSON API endpoints
- Offset/limit parameters
- Cursor-based pagination

## 🔍 Anti-Detection Features

- **User Agent Rotation**: Random user agents for each request
- **Stealth Scripts**: Remove automation indicators
- **Request Delays**: Random delays between requests
- **Header Management**: Realistic browser headers
- **Proxy Support**: Optional proxy configuration
- **Session Management**: Persistent sessions with cookies
- **Backend Proxy**: Server-side scraping to bypass frontend restrictions

## 📊 Output Formats

### CSV Output
```csv
Title,Price,Description,Category,Keywords
Example Product,$99.99,Product description,Electronics,keyword1;keyword2
```

### JSON Output
```json
{
  "url": "https://example.com",
  "total_pages_scraped": 5,
  "total_products": 50,
  "products": [...],
  "extraction_method": "universal_extractor",
  "ocr_used": false
}
```

### Structured Product Data
```python
{
  "title": "Product Name",
  "price": "$99.99",
  "description": "Product description",
  "category": "Electronics",
  "keywords": ["keyword1", "keyword2"],
  "image_url": "https://example.com/image.jpg",
  "rating": "4.5",
  "reviews": "123"
}
```

## 🚨 Error Handling & Fallbacks

The scraper includes comprehensive error handling:

- **Network Errors**: Automatic retries with exponential backoff
- **Rate Limiting**: Respects site rate limits
- **Bot Detection**: Falls back to different methods
- **Content Parsing**: Graceful handling of malformed HTML
- **API Errors**: OpenAI API error handling
- **Zero Results**: Automatic OCR fallback prompting
- **Slow Extraction**: OCR fallback for extractions >45 seconds
- **Connection Issues**: Backend proxy restart suggestions

## 📈 Performance Optimization

- **Concurrent Scraping**: Async/await for better performance
- **Content Caching**: Avoid re-scraping same content
- **Selective Loading**: Load only necessary resources
- **Memory Management**: Efficient memory usage for large sites
- **Backend Proxy**: Server-side processing reduces client load
- **Smart Fallbacks**: Automatic method switching for optimal performance

## 🔧 Customization

### Custom Product Selectors
```python
product_selectors = [
    '.product', '.item', '.card', '.listing',
    '[class*="product"]', '[class*="item"]', '[class*="card"]'
]
```

### Custom Pagination Patterns
```python
pagination_patterns = [
    'a[href*="page="]',
    'a[href*="p="]',
    '.pagination a',
    '.pager a'
]
```

### Custom Analysis Schema
```python
schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "price": {"type": "string"},
        "description": {"type": "string"},
        "category": {"type": "string"},
        "rating": {"type": "string"}
    }
}
```

## 🧪 Testing

Run the universal product extractor to test the scraper:

```bash
python universal_product_extractor.py
```

This will prompt for a URL and demonstrate:
1. Universal product extraction
2. Pagination handling
3. OCR fallback capabilities
4. Error handling and recovery

```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes. Always respect:
- Website terms of service
- robots.txt files
- Rate limiting
- Legal requirements
- Privacy policies

Use responsibly and ethically.

## 🆘 Support

For issues and questions:
1. Check the examples in `universal_product_extractor.py`
2. Review the error messages
3. Check your OpenAI API key configuration
4. Ensure all dependencies are installed
5. Verify your internet connection
6. Restart the backend proxy server if needed

## 🔄 Updates

Stay updated with the latest features and improvements by checking the repository regularly.

## 🚀 Quick Start

### Option 1: Web Interface (Recommended)
1. **Install dependencies**: `pip install -r requirements.txt`
2. **Start Aurora Web Scraper**: `python start_aurora.py`
3. **Open browser**: Go to http://localhost:8080
4. **Enter URL and configure settings**
5. **View results and download data**

### Option 2: Command Line
1. **Install dependencies**: `pip install -r requirements.txt`
2. **Start backend proxy**: `python backend_proxy.py`
3. **Run extractor**: `python universal_product_extractor.py`
4. **Enter URL and follow prompts**

The system will automatically handle the rest, including fallbacks and error recovery! 