from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright
import uvicorn
import asyncio

app = FastAPI()

@app.get("/api/scrape")
async def scrape_url(url: str = Query(..., description="URL to scrape")):
    async with async_playwright() as p:
        # Launch browser with anti-detection measures
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        # Create context with realistic browser settings
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
        # Add script to remove webdriver property
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        page = await context.new_page()
        
        # Set additional page properties
        await page.evaluate("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
        
        try:
            # Use longer timeout and different wait condition for different sites
            if "amazon." in url:
                wait_until = "domcontentloaded"
                timeout = 60000  # 60 seconds
            elif "flipkart." in url:
                wait_until = "networkidle"
                timeout = 45000  # 45 seconds for Flipkart
            else:
                wait_until = "networkidle"
                timeout = 30000  # 30 seconds
            
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            
            # Wait for dynamic content to load
            await page.wait_for_timeout(6000)
            
            # Enhanced scrolling for infinite scroll sites
            await _handle_infinite_scroll(page, url)
            
            content = await page.content()
            title = await page.title()
            
            # Check if we hit a Cloudflare page
            if "cloudflare" in title.lower() or "attention required" in title.lower():
                await browser.close()
                return JSONResponse({
                    "url": url,
                    "title": title,
                    "content": content,
                    "status": "blocked_by_cloudflare",
                    "message": "Hit Cloudflare protection page"
                })
            
            await browser.close()
            return JSONResponse({
                "url": url,
                "title": title,
                "content": content,
                "status": "success"
            })
            
        except Exception as e:
            await browser.close()
            return JSONResponse({
                "url": url,
                "error": str(e),
                "status": "error"
            })

async def _handle_infinite_scroll(page, url: str):
        """Handle infinite scroll by simulating scrolls"""
        
        # Determine scroll strategy based on URL
        if "housing.com" in url or "infinite" in url.lower():
            # Aggressive scrolling for infinite scroll sites
            scroll_count = 0
            max_scrolls = 20
            
            while scroll_count < max_scrolls:
                # Scroll down
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)  # Wait for content to load
                
                # Check if new content loaded
                new_height = await page.evaluate("document.body.scrollHeight")
                
                # Scroll back up a bit to trigger more loading
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight - 1000)")
                await page.wait_for_timeout(1000)
                
                scroll_count += 1
                
                # Check if we've reached the end (no new content)
                if scroll_count > 5:
                    current_height = await page.evaluate("document.body.scrollHeight")
                    if current_height == new_height:
                        break
        
        elif "flipkart." in url:
            # Flipkart-specific scrolling
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(1000)
        
        elif "amazon." in url:
            # Amazon-specific scrolling
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await page.wait_for_timeout(1000)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)

@app.get("/api/scrape_with_scroll")
async def scrape_with_scroll(url: str = Query(..., description="URL to scrape"), 
                           scroll_count: int = Query(0, description="Number of scrolls to perform")):
    """Enhanced scraping with scroll simulation"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Perform scrolls
            for i in range(scroll_count):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                
                # Scroll back up to trigger more loading
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight - 500)")
                await page.wait_for_timeout(1000)
            
            content = await page.content()
            title = await page.title()
            
            await browser.close()
            return JSONResponse({
                "url": url,
                "title": title,
                "content": content,
                "status": "success",
                "scrolls_performed": scroll_count
            })
            
        except Exception as e:
            await browser.close()
            return JSONResponse({
                "url": url,
                "error": str(e),
                "status": "error"
            })

if __name__ == "__main__":
    uvicorn.run("enhanced_backend_proxy:app", host="0.0.0.0", port=8000, reload=True) 