
from examples.multi_agents.collaborative.debate.agent.search.search_engine import SearchEngine


class TavilySearchEngine(SearchEngine):
    """Tavily"""
    async def async_search(self, query: str, max_results=5, include_raw_content=False, **kwargs) -> dict:
        """
            Performs concurrent web searches using the Tavily API.

            Args:
                query (Str): str

            Returns:
                    dict:  search responses from Tavily API, one per query. Each response has format:
                        {
                            'query': str, # The original search query
                            'follow_up_questions': None,
                            'answer': None,
                            'images': list,
                            'results': [                     # List of search results
                                {
                                    'title': str,            # Title of the webpage
                                    'url': str,              # URL of the result
                                    'content': str,          # Summary/snippet of content
                                    'score': float,          # Relevance score
                                    'raw_content': str|None  # Full page content if available
                                },
                                ...
                            ]
                        }
            """
        try:
            from tavily import AsyncTavilyClient
        except ImportError:
            # install mistune
            import subprocess
            subprocess.run(["pip", "install", "tavily-python>=0.5.1"], check=True)
            from tavily import AsyncTavilyClient
        tavily_async_client = AsyncTavilyClient()
        return await tavily_async_client.search(
            query,
            max_results=5,
            include_raw_content=True,
            topic="general"
        )
