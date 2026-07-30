"""
Public data source tools: weather, stocks, currency, Wiki, ArXiv, Wayback Machine.
"""
import json
import logging
import os
import time
import traceback
from datetime import datetime
from typing import Union

import requests
from dotenv import load_dotenv
from mcp.types import TextContent
from pydantic import BaseModel, Field
import wikipedia

from base import ActionResponse


load_dotenv()


async def get_weather(
    location: str,
    latitude: float | None = None,
    longitude: float | None = None
) -> Union[str, TextContent]:
    """
    Get current weather information for a location using Open-Meteo API.
    
    Args:
        location: City name for display purposes
        latitude: Latitude coordinate (if not provided, will try to geocode location)
        longitude: Longitude coordinate (if not provided, will try to geocode location)
        
    Returns:
        TextContent with weather data
    """
    try:
        logging.info(f"🌤️ Getting weather for: {location}")
        
        # If coordinates not provided, try to geocode the location
        if latitude is None or longitude is None:
            # Use Open-Meteo's geocoding API
            geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
            geocode_params = {
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json"
            }
            
            geocode_response = requests.get(geocode_url, params=geocode_params, timeout=10)
            geocode_response.raise_for_status()
            geocode_data = geocode_response.json()
            
            if not geocode_data.get("results"):
                raise ValueError(f"Location not found: {location}")
            
            first_result = geocode_data["results"][0]
            latitude = first_result["latitude"]
            longitude = first_result["longitude"]
            location = first_result.get("name", location)
            country = first_result.get("country", "")
        else:
            country = ""
        
        # Get weather data from Open-Meteo
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
            "timezone": "auto"
        }
        
        response = requests.get(weather_url, params=weather_params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        current = data["current"]
        
        # Map weather codes to descriptions
        # Based on WMO Weather interpretation codes
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
            85: "Slight snow showers", 86: "Heavy snow showers",
            95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
        }
        
        weather_code = current["weather_code"]
        description = weather_codes.get(weather_code, "Unknown")
        
        result = {
            "location": location,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "temperature": current["temperature_2m"],
            "feels_like": current["apparent_temperature"],
            "humidity": current["relative_humidity_2m"],
            "precipitation": current["precipitation"],
            "weather_code": weather_code,
            "description": description,
            "wind_speed": current["wind_speed_10m"],
            "wind_direction": current["wind_direction_10m"],
            "units": "metric",
            "timestamp": current["time"],
            "provider": "Open-Meteo"
        }
        
        logging.info(f"✅ Weather: {result['temperature']}°C - {result['description']}")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata={"location": location, "provider": "Open-Meteo", "api_key_required": False}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Weather query failed: {str(e)}"
        logging.error(f"Weather error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "weather_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def get_stock_price(
    symbol: str,
    interval: str = "1d"
) -> Union[str, TextContent]:
    """
    Get stock price information.
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL, TSLA)
        interval: Data interval (1d, 1h, etc.)
        
    Returns:
        TextContent with stock data
    """
    try:
        logging.info(f"📈 Getting stock price for: {symbol}")
        
        # Using Yahoo Finance API (free, no key required)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            "interval": interval,
            "range": "1d"
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "chart" in data and "result" in data["chart"] and data["chart"]["result"]:
            quote = data["chart"]["result"][0]["meta"]
            
            result = {
                "symbol": symbol,
                "currency": quote.get("currency", "USD"),
                "current_price": quote.get("regularMarketPrice"),
                "previous_close": quote.get("previousClose"),
                "open": quote.get("regularMarketOpen"),
                "day_high": quote.get("regularMarketDayHigh"),
                "day_low": quote.get("regularMarketDayLow"),
                "volume": quote.get("regularMarketVolume"),
                "exchange": quote.get("exchangeName")
            }
            
            logging.info(f"✅ Stock price: ${result['current_price']}")
        else:
            raise ValueError(f"Invalid response for symbol: {symbol}")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata={"symbol": symbol}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Stock query failed: {str(e)}"
        logging.error(f"Stock error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "stock_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str
) -> Union[str, TextContent]:
    """
    Convert between currencies.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code (e.g., USD)
        to_currency: Target currency code (e.g., EUR)
        
    Returns:
        TextContent with conversion result
    """
    try:
        logging.info(f"💱 Converting {amount} {from_currency} to {to_currency}")
        
        # Using free exchange rate API
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if to_currency not in data["rates"]:
            raise ValueError(f"Currency not found: {to_currency}")
        
        rate = data["rates"][to_currency]
        converted_amount = amount * rate
        
        result = {
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "exchange_rate": rate,
            "converted_amount": converted_amount,
            "timestamp": data.get("date", datetime.now().isoformat())
        }
        
        logging.info(f"✅ {amount} {from_currency} = {converted_amount:.2f} {to_currency}")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata={"rate": rate}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Currency conversion failed: {str(e)}"
        logging.error(f"Currency error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "currency_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def search_wikipedia(
    query: str,
    language: str = "en",
    sentences: int = 5
) -> Union[str, TextContent]:
    """
    Search Wikipedia and get article summary.
    
    Args:
        query: Search query
        language: Wikipedia language (en, zh, etc.)
        sentences: Number of sentences in summary
        
    Returns:
        TextContent with Wikipedia article
    """
    try:
        wikipedia.set_lang(language)
        
        logging.info(f"📚 Searching Wikipedia for: {query}")
        
        # Search for pages
        search_results = wikipedia.search(query, results=3)
        
        if not search_results:
            raise ValueError(f"No Wikipedia articles found for: {query}")
        
        # Get the first result's page
        page = wikipedia.page(search_results[0], auto_suggest=False)
        
        summary = wikipedia.summary(search_results[0], sentences=sentences, auto_suggest=False)
        
        result = {
            "title": page.title,
            "url": page.url,
            "summary": summary,
            "language": language,
            "search_results": search_results
        }
        
        logging.info(f"✅ Found Wikipedia article: {page.title}")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata={"query": query, "language": language}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Wikipedia search failed: {str(e)}"
        logging.error(f"Wikipedia error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "wikipedia_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def search_arxiv(
    query: str,
    max_results: int = 5,
    sort_by: str = "relevance"
) -> Union[str, TextContent]:
    """
    Search ArXiv for academic papers.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        sort_by: Sort method (relevance, lastUpdatedDate, submittedDate)
        
    Returns:
        TextContent with ArXiv papers
    """
    try:
        import arxiv
        
        logging.info(f"🔬 Searching ArXiv for: {query}")
        
        # Map sort_by to arxiv.SortCriterion
        sort_map = {
            "relevance": arxiv.SortCriterion.Relevance,
            "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
            "submittedDate": arxiv.SortCriterion.SubmittedDate
        }
        
        sort_criterion = sort_map.get(sort_by, arxiv.SortCriterion.Relevance)
        
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_criterion
        )

        # arxiv.Client defaults to page_size=100 even when the caller asks for
        # only a handful of papers.  That needlessly expands the official API
        # request and made paired experiment arms much more susceptible to
        # export.arxiv.org throttling.  Keep the request page bounded by the
        # public MCP argument while retaining the library's documented delay
        # and retry behavior.
        client = arxiv.Client(
            page_size=max(1, min(max_results, 100)),
            delay_seconds=3.0,
            num_retries=3,
        )
        
        papers = []
        for result in client.results(search):
            papers.append({
                "title": result.title,
                "authors": [author.name for author in result.authors],
                "summary": result.summary[:500] + "...",
                "published": result.published.isoformat(),
                "url": result.entry_id,
                "pdf_url": result.pdf_url,
                "categories": result.categories
            })
        
        logging.info(f"✅ Found {len(papers)} papers")
        
        action_response = ActionResponse(
            success=True,
            message={
                "query": query,
                "papers": papers,
                "count": len(papers)
            },
            metadata={"query": query, "max_results": max_results}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"ArXiv search failed: {str(e)}"
        logging.error(f"ArXiv error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "arxiv_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def search_wayback(
    url: str,
    year: int | None = None,
    limit: int = 10
) -> Union[str, TextContent]:
    """
    Search Wayback Machine for archived versions of a URL.
    
    Args:
        url: URL to search for
        year: Optional year to filter results
        limit: Maximum number of snapshots to return
        
    Returns:
        TextContent with archived snapshots
    """
    try:
        logging.info(f"🕰️ Searching Wayback Machine for: {url}")
        
        # CDX API endpoint
        cdx_url = "http://web.archive.org/cdx/search/cdx"
        params = {
            "url": url,
            "output": "json",
            "limit": limit,
            "fl": "timestamp,original,statuscode,mimetype"
        }
        
        if year:
            params["from"] = f"{year}0101"
            params["to"] = f"{year}1231"
        
        response = requests.get(cdx_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # First row is headers
        if len(data) <= 1:
            raise ValueError(f"No archived snapshots found for: {url}")
        
        headers = data[0]
        snapshots = []
        
        for row in data[1:]:
            snapshot = dict(zip(headers, row))
            # Convert timestamp to readable format
            ts = snapshot["timestamp"]
            dt = datetime.strptime(ts, "%Y%m%d%H%M%S")
            
            snapshots.append({
                "timestamp": dt.isoformat(),
                "url": f"https://web.archive.org/web/{ts}/{snapshot['original']}",
                "status_code": snapshot.get("statuscode"),
                "mime_type": snapshot.get("mimetype")
            })
        
        logging.info(f"✅ Found {len(snapshots)} archived snapshots")
        
        action_response = ActionResponse(
            success=True,
            message={
                "url": url,
                "snapshots": snapshots,
                "count": len(snapshots)
            },
            metadata={"url": url, "year": year}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Wayback Machine search failed: {str(e)}"
        logging.error(f"Wayback error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "wayback_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def get_crypto_price(
    symbol: str,
    vs_currency: str = "usd"
) -> Union[str, TextContent]:
    """
    Get cryptocurrency price information using CoinGecko API (free, no API key required).
    
    Args:
        symbol: Cryptocurrency symbol or ID (e.g., bitcoin, ethereum, btc, eth)
        vs_currency: Target currency (usd, eur, gbp, etc.)
        
    Returns:
        TextContent with cryptocurrency data
    """
    try:
        logging.info(f"💰 Getting crypto price for: {symbol}")
        
        # CoinGecko free API
        # First, try to get the coin ID from symbol
        symbol_lower = symbol.lower()
        
        # Map common symbols to CoinGecko IDs
        symbol_map = {
            "btc": "bitcoin",
            "eth": "ethereum",
            "usdt": "tether",
            "bnb": "binancecoin",
            "sol": "solana",
            "xrp": "ripple",
            "usdc": "usd-coin",
            "ada": "cardano",
            "doge": "dogecoin",
            "trx": "tron",
            "dot": "polkadot",
            "matic": "matic-network",
            "dai": "dai",
            "shib": "shiba-inu",
            "avax": "avalanche-2"
        }
        
        # Use mapped ID or try the symbol directly
        coin_id = symbol_map.get(symbol_lower, symbol_lower)
        
        # Get price data from CoinGecko
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": vs_currency,
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
            "include_last_updated_at": "true"
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or coin_id not in data:
            raise ValueError(f"Cryptocurrency not found: {symbol}")
        
        coin_data = data[coin_id]
        
        result = {
            "symbol": symbol.upper(),
            "coin_id": coin_id,
            "currency": vs_currency.upper(),
            "current_price": coin_data.get(vs_currency),
            "market_cap": coin_data.get(f"{vs_currency}_market_cap"),
            "volume_24h": coin_data.get(f"{vs_currency}_24h_vol"),
            "price_change_24h_percent": coin_data.get(f"{vs_currency}_24h_change"),
            "last_updated": datetime.fromtimestamp(coin_data.get("last_updated_at", 0)).isoformat() if coin_data.get("last_updated_at") else None,
            "provider": "CoinGecko"
        }
        
        logging.info(f"✅ Crypto price: {result['current_price']} {vs_currency.upper()}")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata={"symbol": symbol, "provider": "CoinGecko", "api_key_required": False}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Crypto price query failed: {str(e)}"
        logging.error(f"Crypto error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "crypto_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def search_location(
    query: str,
    limit: int = 5,
    country_code: str | None = None
) -> Union[str, TextContent]:
    """
    Search for locations using Nominatim (OpenStreetMap) API (free, no API key required).
    
    Args:
        query: Location query (e.g., "Eiffel Tower", "New York", "coffee shop near me")
        limit: Maximum number of results (1-50)
        country_code: Optional country code filter (e.g., "us", "gb", "fr")
        
    Returns:
        TextContent with location search results
    """
    try:
        logging.info(f"📍 Searching location: {query}")
        
        # Nominatim API (OpenStreetMap)
        url = "https://nominatim.openstreetmap.org/search"
        
        params = {
            "q": query,
            "format": "json",
            "limit": min(limit, 50),
            "addressdetails": 1,
            "extratags": 1
        }
        
        if country_code:
            params["countrycodes"] = country_code.lower()
        
        headers = {
            "User-Agent": "PerceptionToolsMCP/1.0"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            raise ValueError(f"No locations found for: {query}")
        
        locations = []
        for item in data:
            address = item.get("address", {})
            
            locations.append({
                "display_name": item.get("display_name"),
                "latitude": float(item.get("lat")),
                "longitude": float(item.get("lon")),
                "type": item.get("type"),
                "category": item.get("class"),
                "address": {
                    "country": address.get("country"),
                    "country_code": address.get("country_code"),
                    "state": address.get("state"),
                    "city": address.get("city") or address.get("town") or address.get("village"),
                    "postcode": address.get("postcode"),
                    "road": address.get("road")
                },
                "importance": item.get("importance"),
                "osm_id": item.get("osm_id"),
                "osm_type": item.get("osm_type")
            })
        
        logging.info(f"✅ Found {len(locations)} locations")
        
        action_response = ActionResponse(
            success=True,
            message={
                "query": query,
                "locations": locations,
                "count": len(locations)
            },
            metadata={"provider": "Nominatim (OpenStreetMap)", "api_key_required": False}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Location search failed: {str(e)}"
        logging.error(f"Location search error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "location_search_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def search_poi(
    query: str,
    latitude: float,
    longitude: float,
    radius: int = 1000,
    limit: int = 10
) -> Union[str, TextContent]:
    """
    Search for Points of Interest (POI) near a location using Overpass API (OpenStreetMap).
    Free, no API key required.
    
    Args:
        query: Type of POI (e.g., "restaurant", "cafe", "hospital", "atm", "hotel")
        latitude: Center latitude
        longitude: Center longitude
        radius: Search radius in meters (default: 1000)
        limit: Maximum number of results (default: 10)
        
    Returns:
        TextContent with POI search results
    """
    try:
        logging.info(f"🔍 Searching POIs: {query} near ({latitude}, {longitude})")
        
        # Overpass API query
        # Search for amenities, shops, tourism, etc.
        overpass_query = f"""
        [out:json][timeout:10];
        (
          node["amenity"~"{query}",i](around:{radius},{latitude},{longitude});
          node["shop"~"{query}",i](around:{radius},{latitude},{longitude});
          node["tourism"~"{query}",i](around:{radius},{latitude},{longitude});
          node["name"~"{query}",i](around:{radius},{latitude},{longitude});
        );
        out body {limit};
        """
        
        url = "https://overpass-api.de/api/interpreter"
        
        response = requests.post(url, data={"data": overpass_query}, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        elements = data.get("elements", [])
        
        if not elements:
            raise ValueError(f"No POIs found for '{query}' near the specified location")
        
        pois = []
        for element in elements[:limit]:
            tags = element.get("tags", {})
            
            pois.append({
                "name": tags.get("name", "Unnamed"),
                "type": tags.get("amenity") or tags.get("shop") or tags.get("tourism") or "unknown",
                "latitude": element.get("lat"),
                "longitude": element.get("lon"),
                "address": tags.get("addr:street"),
                "city": tags.get("addr:city"),
                "postcode": tags.get("addr:postcode"),
                "phone": tags.get("phone"),
                "website": tags.get("website"),
                "opening_hours": tags.get("opening_hours"),
                "cuisine": tags.get("cuisine"),
                "osm_id": element.get("id"),
                "osm_type": element.get("type")
            })
        
        logging.info(f"✅ Found {len(pois)} POIs")
        
        action_response = ActionResponse(
            success=True,
            message={
                "query": query,
                "center": {"latitude": latitude, "longitude": longitude},
                "radius_meters": radius,
                "pois": pois,
                "count": len(pois)
            },
            metadata={"provider": "Overpass API (OpenStreetMap)", "api_key_required": False}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"POI search failed: {str(e)}"
        logging.error(f"POI search error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "poi_search_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
