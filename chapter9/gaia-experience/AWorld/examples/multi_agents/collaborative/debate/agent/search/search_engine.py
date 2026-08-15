import asyncio
from enum import Enum
from typing import List


class SearchAPI(Enum):
    PERPLEXITY = "perplexity"
    TAVILY = "tavily"
    EXA = "exa"
    ARXIV = "arxiv"
    PUBMED = "pubmed"
    LINKUP = "linkup"


class SearchException(Exception):

    def __init__(self, message, error_code=None):
        super().__init__()
        self.message = message
        self.error_code = error_code

    def __str__(self):
        return f'{self.message}'


class SearchEngine:

    def batch_search(self, queries: List[str], max_results=5, include_raw_content=False, **kwargs):
        try:
            return asyncio.run(
                self.async_batch_search(queries, max_results=max_results, include_raw_content=include_raw_content, **kwargs))
        except Exception as err:
            raise SearchException(f"search queries = {queries} failed.")

    async def async_batch_search(self, queries: List[str], max_results=5, include_raw_content=False, **kwargs):
        search_tasks = []
        for query in queries:
            search_tasks.append(
                self.async_search(query, max_results, include_raw_content, **kwargs)
            )

        # Execute all searches concurrently
        search_docs = await asyncio.gather(*search_tasks)

        return search_docs

    async def async_search(self, query: str, max_results=5, include_raw_content=False, **kwargs) -> dict:
        pass
