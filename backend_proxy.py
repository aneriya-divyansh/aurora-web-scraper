from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright
import uvicorn
import asyncio
import time
import base64

app = FastAPI()

@app.get("/api/scrape")
async def scrape_url(url: str = Query(..., description="URL to scrape")):
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            async with async_playwright() as p:
                # Determine browser configuration based on site characteristics
                if any(keyword in url.lower() for keyword in ["makemytrip", "mmt", "travel", "booking"]):
                    # Use Firefox for travel sites as it handles HTTP2 better
                    browser = await p.firefox.launch(
                        headless=True,
                        args=[
                            '--no-sandbox',
                            '--disable-dev-shm-usage',
                            '--disable-web-security',
                            '--disable-features=VizDisplayCompositor',
                            '--disable-http2',  # Disable HTTP2 for problematic sites
                            '--disable-background-timer-throttling',
                            '--disable-backgrounding-occluded-windows',
                            '--disable-renderer-backgrounding'
                        ]
                    )
                else:
                    # Use Chromium for other sites
                    browser = await p.chromium.launch(
                        headless=True,
                        args=[
                            '--no-sandbox',
                            '--disable-blink-features=AutomationControlled',
                            '--disable-dev-shm-usage',
                            '--disable-web-security',
                            '--disable-features=VizDisplayCompositor',
                            '--disable-http2',  # Disable HTTP2 for problematic sites
                            '--disable-background-timer-throttling',
                            '--disable-backgrounding-occluded-windows',
                            '--disable-renderer-backgrounding'
                        ]
                    )
                
                # Create context with realistic browser settings
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',  # Removed 'br' to avoid HTTP2 issues
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
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
                
                # Use different wait conditions and timeouts based on site characteristics
                if any(keyword in url.lower() for keyword in ["makemytrip", "mmt", "travel", "booking"]):
                    wait_until = "domcontentloaded"  # Use domcontentloaded for travel sites
                    timeout = 45000  # 45 seconds
                    additional_wait = 8000  # 8 seconds additional wait
                elif any(keyword in url.lower() for keyword in ["amazon", "ecommerce", "shop"]):
                    wait_until = "domcontentloaded"
                    timeout = 60000
                    additional_wait = 6000
                elif any(keyword in url.lower() for keyword in ["flipkart", "marketplace"]):
                    wait_until = "networkidle"
                    timeout = 45000
                    additional_wait = 6000
                else:
                    wait_until = "networkidle"
                    timeout = 30000
                    additional_wait = 6000
                
                print(f"[DEBUG] Attempting to scrape {url} (attempt {retry_count + 1}/{max_retries})")
                print(f"[DEBUG] Using wait_until: {wait_until}, timeout: {timeout}ms")
                
                await page.goto(url, wait_until=wait_until, timeout=timeout)
                
                # Wait for dynamic content to load
                await page.wait_for_timeout(additional_wait)

                # Aggressive infinite scroll for sites with dynamic content
                if any(keyword in url.lower() for keyword in ["housing", "infinite", "scroll", "dynamic"]):
                    last_height = await page.evaluate("document.body.scrollHeight")
                    scrolls = 0
                    max_scrolls = 50
                    while scrolls < max_scrolls:
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        try:
                            await page.wait_for_load_state('networkidle', timeout=5000)
                        except Exception:
                            pass
                        await page.wait_for_timeout(2000)
                        new_height = await page.evaluate("document.body.scrollHeight")
                        # Debug: print number of listings/cards after each scroll
                        count = await page.evaluate('document.querySelectorAll("[class*=card], [class*=item]").length')
                        print(f"[DEBUG] Scroll {scrolls+1}: {count} cards/listings detected.")
                        if new_height == last_height:
                            break
                        last_height = new_height
                        scrolls += 1

                # Additional scrolling for marketplace sites
                if any(keyword in url.lower() for keyword in ["flipkart", "marketplace", "ecommerce"]):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                    await page.evaluate("window.scrollTo(0, 0)")
                    await page.wait_for_timeout(1000)
                # Additional scrolling for e-commerce sites
                if any(keyword in url.lower() for keyword in ["amazon", "shop", "store"]):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                    await page.wait_for_timeout(1000)
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1000)
                
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
            error_msg = str(e)
            print(f"[DEBUG] Attempt {retry_count + 1} failed: {error_msg}")
            
            if retry_count < max_retries - 1:
                retry_count += 1
                wait_time = 2 ** retry_count  # Exponential backoff
                print(f"[DEBUG] Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                continue
            else:
                return JSONResponse({
                    "url": url,
                    "error": error_msg,
                    "status": "error",
                    "retries": retry_count
                })

@app.get("/api/screenshot")
async def take_screenshot(url: str = Query(..., description="URL to take screenshot of")):
    """Take a screenshot of the page and return as base64"""
    
    try:
        async with async_playwright() as p:
            # Use Chromium for screenshots
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-http2',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ]
            )
            
            # Create context with realistic browser settings
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
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
            
            print(f"[DEBUG] Taking screenshot of {url}")
            
            # Navigate to the page
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Wait for content to load
            await page.wait_for_timeout(5000)
            
            # Scroll to load more content if needed
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(1000)
            
            # Take full page screenshot
            screenshot_bytes = await page.screenshot(full_page=True)
            
            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            await browser.close()
            
            return JSONResponse({
                "url": url,
                "screenshot_base64": screenshot_base64,
                "status": "success"
            })
            
    except Exception as e:
        error_msg = str(e)
        print(f"[DEBUG] Screenshot failed: {error_msg}")
        
        return JSONResponse({
            "url": url,
            "error": error_msg,
            "status": "error"
        })

if __name__ == "__main__":
    uvicorn.run("backend_proxy:app", host="0.0.0.0", port=8000, reload=True) 