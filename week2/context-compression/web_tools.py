"""
Web tools for searching and fetching web pages
"""

import json
import logging
import requests
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import html2text
from urllib.parse import urlparse, urljoin
import time
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format=Config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class WebTools:
    """Tools for web search and page fetching"""
    
    def __init__(self):
        """Initialize web tools"""
        self.serper_api_key = Config.SERPER_API_KEY
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.ignore_emphasis = False
        self.html_converter.body_width = 0  # Don't wrap lines
        self.html_converter.single_line_break = True
        
        # Cache for fetched pages to avoid redundant fetches
        self.page_cache = {}
    
    def search_web(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        Search the web using Serper API
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            Dictionary containing search results with crawled content
        """
        try:
            if not self.serper_api_key:
                # Fallback to mock results for demo
                logger.warning("No Serper API key, using mock results")
                return self._get_mock_search_results(query)
            
            logger.info(f"Searching web for: {query}")
            
            # Call Serper API
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'q': query,
                'num': num_results
            }
            
            response = requests.post(
                f"{Config.SERPER_BASE_URL}/search",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Serper API error: {response.status_code}")
                return self._get_mock_search_results(query)
            
            data = response.json()
            
            # Process organic results
            results = []
            organic_results = data.get('organic', [])[:num_results]
            
            for result in organic_results:
                # Fetch and convert each page
                url = result.get('link', '')
                if url:
                    page_content = self.fetch_webpage(url)
                    
                    results.append({
                        'title': result.get('title', ''),
                        'url': url,
                        'snippet': result.get('snippet', ''),
                        'content': page_content.get('content', ''),
                        'content_length': len(page_content.get('content', '')),
                        'fetch_success': page_content.get('success', False)
                    })
                    
                    # Small delay to be respectful
                    time.sleep(0.5)
            
            return {
                'query': query,
                'num_results': len(results),
                'results': results,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error searching web: {str(e)}")
            return self._get_mock_search_results(query)
    
    def fetch_webpage(self, url: str) -> Dict[str, Any]:
        """
        Fetch a webpage and convert HTML to text
        
        Args:
            url: URL of the webpage to fetch
            
        Returns:
            Dictionary containing the converted text content
        """
        try:
            # Check cache first
            if url in self.page_cache:
                logger.info(f"Using cached content for: {url}")
                return self.page_cache[url]
            
            logger.info(f"Fetching webpage: {url}")
            
            # Fetch the page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Convert to text
            text_content = self.html_converter.handle(str(soup))
            
            # Clean up the text
            lines = text_content.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):  # Remove empty lines and navigation markers
                    cleaned_lines.append(line)
            
            cleaned_text = '\n'.join(cleaned_lines)
            
            # Truncate if too long
            if len(cleaned_text) > Config.MAX_WEBPAGE_LENGTH:
                cleaned_text = cleaned_text[:Config.MAX_WEBPAGE_LENGTH] + "\n\n[Content truncated...]"
            
            result = {
                'url': url,
                'title': soup.title.string if soup.title else 'No title',
                'content': cleaned_text,
                'content_length': len(cleaned_text),
                'success': True,
                'timestamp': time.time()
            }
            
            # Cache the result
            self.page_cache[url] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching webpage {url}: {str(e)}")
            
            error_result = {
                'url': url,
                'title': 'Error',
                'content': f"Failed to fetch webpage: {str(e)}",
                'content_length': 0,
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }
            
            # Cache even failed results to avoid retrying
            self.page_cache[url] = error_result
            
            return error_result
    
    def _get_mock_search_results(self, query: str) -> Dict[str, Any]:
        """
        Get mock search results for testing without API key
        
        Args:
            query: Search query
            
        Returns:
            Mock search results
        """
        # Mock results for OpenAI co-founders
        mock_data = {
            "openai": [
                {
                    'title': 'OpenAI - Wikipedia',
                    'url': 'https://en.wikipedia.org/wiki/OpenAI',
                    'snippet': 'OpenAI was founded in 2015 by Sam Altman, Elon Musk, Ilya Sutskever, Greg Brockman, Wojciech Zaremba, and John Schulman...',
                    'content': '''OpenAI was founded in December 2015 by Sam Altman, Elon Musk, Ilya Sutskever, Greg Brockman, Wojciech Zaremba, and John Schulman.
                    
The organization was founded with the goal of advancing digital intelligence in a way that benefits humanity. 

Current Status of Co-founders (as of 2024):
- Sam Altman: CEO of OpenAI (returned after brief departure in November 2023)
- Elon Musk: Left OpenAI board in 2018, founded xAI in 2023
- Ilya Sutskever: Former Chief Scientist, left OpenAI in May 2024, co-founded Safe Superintelligence Inc.
- Greg Brockman: President and Chairman of OpenAI
- Wojciech Zaremba: Head of Language and Code Generation at OpenAI
- John Schulman: Co-founder, left OpenAI in August 2024 to join Anthropic

Additional early members:
- Andrej Karpathy: Former Director of AI at Tesla, briefly returned to OpenAI, now independent
- Dario Amodei: Left to co-found Anthropic in 2021
- Daniela Amodei: Left to co-found Anthropic in 2021'''
                }
            ],
            "sam altman": [
                {
                    'title': 'Sam Altman - CEO of OpenAI',
                    'url': 'https://example.com/sam-altman',
                    'snippet': 'Sam Altman is the CEO of OpenAI...',
                    'content': 'Sam Altman is currently the CEO of OpenAI. He briefly left the company in November 2023 but returned after employee protests. He is also known for his work at Y Combinator and various investments in startups.'
                }
            ],
            "elon musk": [
                {
                    'title': 'Elon Musk launches xAI',
                    'url': 'https://example.com/elon-musk-ai',
                    'snippet': 'Elon Musk founded xAI in 2023...',
                    'content': 'Elon Musk, who co-founded OpenAI in 2015, left the board in 2018 citing conflicts of interest with Tesla\'s AI development. In 2023, he founded xAI, a new AI company focused on understanding the universe. He is also CEO of Tesla, SpaceX, and owner of X (formerly Twitter).'
                }
            ],
            "ilya sutskever": [
                {
                    'title': 'Ilya Sutskever launches Safe Superintelligence',
                    'url': 'https://example.com/ilya-sutskever',
                    'snippet': 'Ilya Sutskever left OpenAI to start SSI...',
                    'content': 'Ilya Sutskever, former Chief Scientist at OpenAI, left the company in May 2024 after nearly a decade. He co-founded Safe Superintelligence Inc. (SSI) with Daniel Gross and Daniel Levy, focusing on building safe AGI.'
                }
            ]
        }
        
        # Find matching mock data
        query_lower = query.lower()
        for key in mock_data:
            if key in query_lower:
                results = []
                for item in mock_data[key]:
                    results.append({
                        'title': item['title'],
                        'url': item['url'],
                        'snippet': item['snippet'],
                        'content': item['content'],
                        'content_length': len(item['content']),
                        'fetch_success': True
                    })
                
                return {
                    'query': query,
                    'num_results': len(results),
                    'results': results,
                    'timestamp': time.time(),
                    'mock': True
                }
        
        # Default mock result
        return {
            'query': query,
            'num_results': 1,
            'results': [{
                'title': 'Mock Search Result',
                'url': 'https://example.com',
                'snippet': 'This is a mock search result for testing',
                'content': 'Mock content for testing when no API key is available.',
                'content_length': 50,
                'fetch_success': True
            }],
            'timestamp': time.time(),
            'mock': True
        }
    
    def clear_cache(self):
        """Clear the page cache"""
        self.page_cache.clear()
        logger.info("Page cache cleared")
