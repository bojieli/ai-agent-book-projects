# coding: utf-8

import json
import os

import requests

from typing import Tuple, Any, List, Dict

from examples.common.tools.tool_action import SearchAction
from aworld.core.tool.action_factory import ActionFactory
from aworld.core.common import ActionModel, ActionResult
from aworld.logs.util import logger
from aworld.utils import import_package
from aworld.core.tool.action import ExecutableAction


# @ActionFactory.register(name=SearchAction.WIKI.value.name,
#                         desc=SearchAction.WIKI.value.desc,
#                         tool_name='search_api')
class SearchWiki(ExecutableAction):
    def __init__(self):
        import_package("wikipedia")

    def act(self, action: ActionModel, **kwargs) -> Tuple[ActionResult, Any]:
        import wikipedia

        query = action.params.get("query")
        logger.info(f"Calling search_wiki api with query: {query}")

        result: str = ''
        try:
            page = wikipedia.page(query)
            result_dict = {
                'url': page.url,
                'title': page.title,
                'content': page.content,
            }
            result = str(result_dict)
        except wikipedia.exceptions.DisambiguationError as e:
            result = wikipedia.summary(
                e.options[0], sentences=5, auto_suggest=False
            )
        except wikipedia.exceptions.PageError:
            result = (
                "There is no page in Wikipedia corresponding to entity "
                f"{query}, please specify another word to describe the"
                " entity to be searched."
            )
        except Exception as e:
            logger.error(f"An exception occurred during the search: {e}")
            result = f"An exception occurred during the search: {e}"
        logger.debug(f"wiki result: {result}")
        return ActionResult(content=result, keep=True, is_done=True), None


# @ActionFactory.register(name=SearchAction.DUCK_GO.value.name,
#                         desc=SearchAction.DUCK_GO.value.desc,
#                         tool_name="search_api")
class Duckduckgo(ExecutableAction):
    def __init__(self):
        import_package("duckduckgo_search")

    def act(self, action: ActionModel, **kwargs) -> Tuple[ActionResult, Any]:
        r"""Use DuckDuckGo search engine to search information for
        the given query.

        This function queries the DuckDuckGo API for related topics to
        the given search term. The results are formatted into a list of
        dictionaries, each representing a search result.

        Args:
            query (str): The query to be searched.
            source (str): The type of information to query (e.g., "text",
                "images", "videos"). Defaults to "text".
            max_results (int): Max number of results, defaults to `5`.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries where each dictionary
                represents a search result.
        """

        from duckduckgo_search import DDGS

        params = action.params
        query = params.get("query")
        max_results = params.get("max_results", 5)
        source = params.get("source", "text")

        logger.debug(f"Calling search_duckduckgo function with query: {query}")

        ddgs = DDGS()
        responses: List[Dict[str, Any]] = []

        if source == "text":
            try:
                results = ddgs.text(keywords=query, max_results=max_results)
            except Exception as e:
                # Handle specific exceptions or general request exceptions
                responses.append({"error": f"duckduckgo search failed.{e}"})
                return ActionResult(content="duckduckgo search failed", keep=True), responses

            for i, result in enumerate(results, start=1):
                # Creating a response object with a similar structure
                response = {
                    "result_id": i,
                    "title": result["title"],
                    "description": result["body"],
                    "url": result["href"],
                }
                responses.append(response)
        elif source == "images":
            try:
                results = ddgs.images(keywords=query, max_results=max_results)
            except Exception as e:
                # Handle specific exceptions or general request exceptions
                responses.append({"error": f"duckduckgo search failed.{e}"})
                return ActionResult(content="duckduckgo search failed", keep=True), responses

            # Iterate over results found
            for i, result in enumerate(results, start=1):
                # Creating a response object with a similar structure
                response = {
                    "result_id": i,
                    "title": result["title"],
                    "image": result["image"],
                    "url": result["url"],
                    "source": result["source"],
                }
                responses.append(response)
        elif source == "videos":
            try:
                results = ddgs.videos(keywords=query, max_results=max_results)
            except Exception as e:
                # Handle specific exceptions or general request exceptions
                responses.append({"error": f"duckduckgo search failed.{e}"})
                return ActionResult(content="duckduckgo search failed", keep=True), responses

            # Iterate over results found
            for i, result in enumerate(results, start=1):
                # Creating a response object with a similar structure
                response = {
                    "result_id": i,
                    "title": result["title"],
                    "description": result["description"],
                    "embed_url": result["embed_url"],
                    "publisher": result["publisher"],
                    "duration": result["duration"],
                    "published": result["published"],
                }
                responses.append(response)
        logger.debug(f"Search results: {responses}")
        return ActionResult(content=json.dumps(responses), keep=True, is_done=True), None


# @ActionFactory.register(name=SearchAction.GOOGLE.value.name,
#                         desc=SearchAction.GOOGLE.value.desc,
#                         tool_name="search_api")
class SearchGoogle(ExecutableAction):
    def act(self, action: ActionModel, **kwargs) -> Tuple[ActionResult, Any]:
        query = action.params.get("query")
        num_result_pages = action.params.get("num_result_pages", 6)
        # https://developers.google.com/custom-search/v1/overview
        api_key = action.params.get("api_key", os.environ.get("GOOGLE_API_KEY"))
        # https://cse.google.com/cse/all
        engine_id = action.params.get("engine_id", os.environ.get("GOOGLE_ENGINE_ID"))
        logger.debug(f"Calling search_google function with query: {query}")

        # Using the first page
        start_page_idx = 1
        # Different language may get different result
        search_language = "en"
        # How many pages to return
        num_result_pages = num_result_pages
        # Constructing the URL
        # Doc: https://developers.google.com/custom-search/v1/using_rest
        url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={engine_id}&q={query}&start={start_page_idx}&lr={search_language}&num={num_result_pages}"
        responses = []
        try:
            result = requests.get(url)
            result.raise_for_status()
            data = result.json()

            # Get the result items
            if "items" in data:
                search_items = data.get("items")

                for i, search_item in enumerate(search_items, start=1):
                    # Check metatags are present
                    if "pagemap" not in search_item:
                        continue
                    if "metatags" not in search_item["pagemap"]:
                        continue
                    if "og:description" in search_item["pagemap"]["metatags"][0]:
                        long_description = search_item["pagemap"]["metatags"][0]["og:description"]
                    else:
                        long_description = "N/A"
                    # Get the page title
                    title = search_item.get("title")
                    # Page snippet
                    snippet = search_item.get("snippet")

                    # Extract the page url
                    link = search_item.get("link")
                    response = {
                        "result_id": i,
                        "title": title,
                        "description": snippet,
                        "long_description": long_description,
                        "url": link,
                    }
                    if "huggingface.co" in link:
                        logger.warning(f"Filter out the link: {link}")
                        continue
                    responses.append(response)
            else:
                responses.append({"error": f"google search failed with response: {data}"})
        except Exception as e:
            logger.error(f"Google search failed with error: {e}")
            responses.append({"error": f"google search failed with error: {e}"})

        if len(responses) == 0:
            responses.append(
                "No relevant webpages found. Please simplify your query and expand the search space as much as you can, then try again.")
        logger.debug(f"search result: {responses}")
        responses.append(
            "If the search result does not contain the information you want, please make reflection on your query: what went well, what didn't, then refine your search plan.")
        return ActionResult(content=json.dumps(responses), keep=True, is_done=True), None


@ActionFactory.register(name=SearchAction.BAIDU.value.name,
                        desc=SearchAction.BAIDU.value.desc,
                        tool_name="search_api")
class SearchBaidu(ExecutableAction):
    def __init__(self):
        import_package("baidusearch")

    def act(self, action: ActionModel, **kwargs) -> Tuple[ActionResult, Any]:
        from baidusearch.baidusearch import search

        query = action.params.get("query")
        num_results = action.params.get("num_results", 6)
        num_results = int(num_results)
        logger.debug(f"Calling search_baidu with query: {query}")

        responses = []
        try:
            responses = search(query, num_results=num_results)
        except Exception as e:
            logger.error(f"Baidu search failed with error: {e}")
            responses.append({"error": f"baidu search failed with error: {e}"})

        if len(responses) == 0:
            responses.append(
                "No relevant webpages found. Please simplify your query and expand the search space as much as you can, then try again.")
        logger.debug(f"search result: {responses}")
        responses.append(
            "If the search result does not contain the information you want, please make reflection on your query: what went well, what didn't, then refine your search plan.")
        return ActionResult(content=json.dumps(responses), keep=True, is_done=True), None
