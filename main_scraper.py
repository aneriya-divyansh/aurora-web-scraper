import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from scraper_core import WebScraper
from openai_processor import OpenAIProcessor
from pagination_handler import PaginationHandler

class AuroraScraper:
    """
    Main scraper class that combines web scraping, pagination handling, and OpenAI processing
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, headless: bool = True):
        self.scraper = WebScraper(headless=headless)
        self.openai_processor = OpenAIProcessor(api_key=openai_api_key)
        self.pagination_handler = None
        
    async def scrape_site(self, url: str, 
                         method: str = 'auto',
                         pagination_type: str = 'auto',
                         max_pages: int = 10,
                         scroll_pages: int = 0,
                         wait_for: str = None,
                         table_columns: List[str] = None) -> Dict[str, Any]:
        """
        Main method to scrape a site with pagination and OpenAI processing
        """
        print(f"Starting to scrape: {url}")
        
        all_content = []
        all_structured_data = []
        pagination_info = {}
        
        # Initialize pagination handler
        self.pagination_handler = PaginationHandler(url, self.scraper.session)
        
        current_url = url
        page_count = 0
        
        while current_url and page_count < max_pages:
            print(f"Scraping page {page_count + 1}: {current_url}")
            
            try:
                # Scrape the current page
                page_data = await self.scraper.scrape_url(
                    current_url, 
                    method=method,
                    wait_for=wait_for,
                    scroll_pages=scroll_pages
                )
                
                # Extract content items
                content_items = self.pagination_handler.extract_content_from_page(
                    page_data['content']
                )
                
                all_content.extend(content_items)
                
                # Process with OpenAI for structured data
                if content_items:
                    combined_content = "\n\n".join([item['text'] for item in content_items])
                    
                    # Generate table data
                    table_result = self.openai_processor.generate_table_data(
                        combined_content, 
                        table_columns
                    )
                    
                    if table_result.get('table_data'):
                        all_structured_data.extend(table_result['table_data'])
                
                # Handle pagination
                if page_count == 0:  # First page
                    if pagination_type == 'auto':
                        pagination_type = self.pagination_handler.detect_pagination_type(
                            page_data['content']
                        )
                
                # Get next page URL based on pagination type
                current_url = await self._get_next_page_url(
                    page_data['content'], 
                    pagination_type,
                    current_url
                )
                
                page_count += 1
                
                # Add delay between requests
                if current_url:
                    await asyncio.sleep(2)
                    
            except Exception as e:
                print(f"Error scraping page {page_count + 1}: {str(e)}")
                break
        
        # Final processing with OpenAI
        final_result = await self._process_final_data(all_content, all_structured_data)
        
        return {
            'url': url,
            'total_pages_scraped': page_count,
            'total_content_items': len(all_content),
            'total_structured_items': len(all_structured_data),
            'pagination_type': pagination_type,
            'content': all_content,
            'structured_data': all_structured_data,
            'final_analysis': final_result,
            'pagination_summary': self.pagination_handler.get_pagination_summary()
        }
    
    async def _get_next_page_url(self, html_content: str, pagination_type: str, current_url: str) -> Optional[str]:
        """
        Get the next page URL based on pagination type
        """
        if pagination_type == 'traditional':
            links = self.pagination_handler.handle_traditional_pagination(html_content)
            # Find the next page link
            for link in links:
                if self._is_next_page_link(link, current_url):
                    return link
            return None
            
        elif pagination_type == 'load_more':
            load_more_info = self.pagination_handler.handle_load_more_pagination(html_content)
            return load_more_info.get('next_url')
            
        elif pagination_type == 'infinite_scroll':
            # For infinite scroll, we need to simulate scrolling
            scroll_info = self.pagination_handler.simulate_scroll()
            # Return the same URL to continue scrolling
            return current_url if self.pagination_handler.has_more else None
            
        elif pagination_type == 'api':
            # Handle API pagination
            api_info = self.pagination_handler.handle_api_pagination(current_url)
            if api_info.get('has_more'):
                return current_url  # Continue with same URL but different params
            return None
            
        return None
    
    def _is_next_page_link(self, link: str, current_url: str) -> bool:
        """
        Check if a link is the next page link
        """
        # Simple heuristic - look for page numbers
        import re
        
        # Extract page numbers from URLs
        current_page_match = re.search(r'page[=/](\d+)', current_url)
        link_page_match = re.search(r'page[=/](\d+)', link)
        
        if current_page_match and link_page_match:
            current_page = int(current_page_match.group(1))
            link_page = int(link_page_match.group(1))
            return link_page == current_page + 1
        
        # Check for "next" in link text or class
        return 'next' in link.lower()
    
    async def _process_final_data(self, content: List[Dict[str, Any]], 
                                structured_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process final data with OpenAI for comprehensive analysis
        """
        if not content:
            return {'error': 'No content to process'}
        
        # Combine all content for analysis
        combined_text = "\n\n".join([item['text'] for item in content])
        
        # Get comprehensive analysis
        analysis_result = self.openai_processor.analyze_content(combined_text)
        
        # Get structured data extraction
        structured_result = self.openai_processor.extract_structured_data(combined_text)
        
        return {
            'analysis': analysis_result.get('analysis'),
            'structured_extraction': structured_result.get('structured_data'),
            'content_summary': {
                'total_items': len(content),
                'total_characters': len(combined_text),
                'average_item_length': len(combined_text) / len(content) if content else 0
            },
            'openai_usage': {
                'analysis_usage': analysis_result.get('usage'),
                'structured_usage': structured_result.get('usage')
            }
        }
    
    def save_results(self, results: Dict[str, Any], 
                    save_csv: bool = True, 
                    save_json: bool = True,
                    filename_prefix: str = "scraped_data") -> Dict[str, str]:
        """
        Save scraping results to files
        """
        save_results = {}
        
        if save_csv and results.get('structured_data'):
            csv_filename = f"{filename_prefix}.csv"
            csv_result = self.openai_processor.save_to_csv(
                results['structured_data'], 
                csv_filename
            )
            save_results['csv'] = csv_result
        
        if save_json:
            json_filename = f"{filename_prefix}.json"
            json_result = self.openai_processor.save_to_json(results, json_filename)
            save_results['json'] = json_result
        
        return save_results
    
    async def scrape_multiple_sites(self, urls: List[str], 
                                  **kwargs) -> Dict[str, Any]:
        """
        Scrape multiple sites and compare results
        """
        results = {}
        
        for url in urls:
            try:
                site_result = await self.scrape_site(url, **kwargs)
                results[url] = site_result
                
                # Add delay between sites
                await asyncio.sleep(3)
                
            except Exception as e:
                results[url] = {'error': str(e)}
        
        # Compare results if multiple sites
        if len(urls) > 1:
            comparison_results = {}
            for i, url1 in enumerate(urls):
                for url2 in urls[i+1:]:
                    if url1 in results and url2 in results:
                        content1 = results[url1].get('content', [])
                        content2 = results[url2].get('content', [])
                        
                        if content1 and content2:
                            text1 = "\n".join([item['text'] for item in content1])
                            text2 = "\n".join([item['text'] for item in content2])
                            
                            comparison = self.openai_processor.compare_content(text1, text2)
                            comparison_results[f"{url1}_vs_{url2}"] = comparison
            
            results['comparisons'] = comparison_results
        
        return results

# Example usage
async def main():
    """
    Example usage of the Aurora Scraper
    """
    # Initialize scraper
    scraper = AuroraScraper(headless=True)
    
    # Example 1: Scrape a single site
    result = await scraper.scrape_site(
        url="https://example.com",
        method="auto",
        max_pages=5,
        table_columns=["Title", "Description", "Category", "Keywords"]
    )
    
    # Save results
    save_results = scraper.save_results(result)
    print("Save results:", save_results)
    
    # Example 2: Scrape multiple sites
    urls = [
        "https://site1.com",
        "https://site2.com"
    ]
    
    multi_results = await scraper.scrape_multiple_sites(
        urls=urls,
        max_pages=3
    )
    
    print("Multi-site results:", multi_results)

if __name__ == "__main__":
    asyncio.run(main()) 