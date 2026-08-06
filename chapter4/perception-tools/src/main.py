"""
Main MCP server for perception tools.

This MCP server provides comprehensive perception capabilities including:
- Search tools (web search, knowledge base, file download)
- Multimodal understanding (web pages, documents, images, videos)
- File system operations (read, grep, summarization)
- Public data sources (weather, stocks, currency, Wikipedia, ArXiv, Wayback)
- Private data sources (Google Calendar, Notion)
"""
import logging
from dotenv import load_dotenv
from mcp.server import MCPServer
from pydantic import Field

# Import all tool functions
from search_tools import search_web, download_file, search_knowledge_base
from multimodal_tools import read_webpage, read_document, parse_image, parse_video, extract_youtube_transcript, download_youtube_video
from filesystem_tools import (
    copy_path,
    delete_path,
    grep_search,
    move_path,
    read_file,
    summarize_text,
)
from public_data_tools import (
    get_weather, get_stock_price, convert_currency,
    search_wikipedia, search_arxiv, search_wayback,
    get_crypto_price, search_location, search_poi
)
from private_data_tools import get_calendar_events, search_notion
from pubchem_tools import search_compounds, get_compound_properties, get_compound_synonyms, search_similar_compounds
from yahoo_finance_tools import get_stock_quote, get_historical_data, get_company_info, get_financial_statements
from document_processing_tools import extract_pdf_text, extract_docx_content, extract_pptx_content, extract_csv_content
from media_processing_tools import transcribe_audio_whisper, extract_audio_metadata, extract_text_ocr, analyze_image_ai, extract_video_keyframes, analyze_video_ai, trim_audio, get_image_metadata
from google_search_enhanced import google_search_api, read_webpage_content
from wiki_enhanced import get_article_content, get_article_categories, get_article_links, get_article_history
from arxiv_enhanced import get_paper_details, download_paper, get_arxiv_categories
from wayback_enhanced import get_archived_content
from expanded_catalog import enrich_existing_tools, register_expanded_tools


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv()

# Initialize MCP server
mcp = MCPServer(
    "perception-tools",
    instructions="""
Perception Tools MCP Server

A comprehensive MCP server providing various perception and data retrieval capabilities:

## Search Tools
- Web search using DuckDuckGo (free, no API key required)
- Local knowledge base search
- File download from URLs

## Multimodal Understanding
- Web page content extraction
- Document reading (PDF, DOCX, PPTX)
- Image parsing and analysis
- Video metadata extraction

## File System Tools
- File reading with encoding support
- Grep-like pattern search
- Text summarization

## Public Data Sources
- Weather information
- Stock prices and market data
- Cryptocurrency prices (CoinGecko)
- Currency conversion
- Location search / geocoding (Nominatim)
- Points of Interest search (Overpass)
- Wikipedia search
- ArXiv academic papers
- Wayback Machine archives

## Private Data Sources
- Google Calendar events
- Notion workspace search
"""
)


# ============================================================================
# SEARCH TOOLS
# ============================================================================

@mcp.tool(description="Search the web using DuckDuckGo (free, no API key required)")
async def web_search(
    query: str = Field(description="Search query string"),
    num_results: int = Field(default=5, description="Number of results (1-10)"),
    region: str = Field(default="wt-wt", description="Region code (e.g., 'us-en', 'uk-en', 'wt-wt' for worldwide)")
):
    """Search the web and return results."""
    return await search_web(query, num_results, region)


@mcp.tool(description="Download a file from a URL to local storage")
async def download(
    url: str = Field(description="URL to download from"),
    output_path: str = Field(description="Local path to save the file"),
    overwrite: bool = Field(default=False, description="Overwrite existing file"),
    timeout: int = Field(default=180, description="Download timeout in seconds")
):
    """Download a file from URL."""
    return await download_file(url, output_path, overwrite, timeout)


@mcp.tool(description="Search a local knowledge base directory")
async def knowledge_base_search(
    query: str = Field(description="Search query"),
    knowledge_base_path: str = Field(description="Path to knowledge base directory"),
    top_k: int = Field(default=5, description="Number of top results")
):
    """Search local knowledge base."""
    return await search_knowledge_base(query, knowledge_base_path, top_k)


# ============================================================================
# MULTIMODAL UNDERSTANDING TOOLS
# ============================================================================

@mcp.tool(description="Read and extract content from a webpage")
async def webpage_reader(
    url: str = Field(description="URL of the webpage"),
    extract_text: bool = Field(default=True, description="Extract text content"),
    extract_links: bool = Field(default=False, description="Extract links")
):
    """Read webpage content."""
    return await read_webpage(url, extract_text, extract_links)


@mcp.tool(description="Read and extract content from documents (PDF, DOCX, PPTX)")
async def document_reader(
    file_path: str = Field(description="Path to document file or URL"),
    extract_images: bool = Field(default=False, description="Extract images")
):
    """Read document content."""
    return await read_document(file_path, extract_images)


@mcp.tool(description="Parse and analyze image files")
async def image_parser(
    image_path: str = Field(description="Path to image file or URL"),
    use_llm: bool = Field(default=True, description="Use LLM for analysis")
):
    """Parse image content."""
    return await parse_image(image_path, use_llm)


@mcp.tool(description="Parse and extract metadata from video files")
async def video_parser(
    video_path: str = Field(description="Path to video file or URL"),
    extract_frames: bool = Field(default=False, description="Extract sample frames"),
    frame_interval: int = Field(default=30, description="Frame extraction interval")
):
    """Parse video metadata."""
    return await parse_video(video_path, extract_frames, frame_interval)


# ============================================================================
# FILE SYSTEM TOOLS
# ============================================================================

@mcp.tool(description="Read a file and return its contents")
async def file_reader(
    file_path: str = Field(description="Path to the file"),
    encoding: str = Field(default="utf-8", description="File encoding"),
    max_length: int = Field(default=50000, description="Maximum characters to read")
):
    """Read file contents."""
    return await read_file(file_path, encoding, max_length)


@mcp.tool(description="Search for patterns in files (grep-like functionality)")
async def grep(
    pattern: str = Field(description="Regular expression pattern"),
    directory: str = Field(description="Directory to search in"),
    file_pattern: str = Field(default="*", description="File pattern (e.g., *.py)"),
    recursive: bool = Field(default=True, description="Search recursively"),
    case_sensitive: bool = Field(default=False, description="Case-sensitive search"),
    max_results: int = Field(default=100, description="Maximum results")
):
    """Search files for pattern."""
    return await grep_search(pattern, directory, file_pattern, recursive, case_sensitive, max_results)


@mcp.tool(description="Summarize long text content")
async def text_summarizer(
    text: str = Field(description="Text to summarize"),
    max_length: int = Field(default=500, description="Target summary length"),
    use_llm: bool = Field(default=True, description="Use LLM for summarization")
):
    """Summarize text."""
    return await summarize_text(text, max_length, use_llm)


@mcp.tool(description="Move a file or directory inside the configured mutation workspace")
async def filesystem_move(
    source_path: str = Field(description="Relative source path beneath PERCEPTION_MUTATION_ROOT"),
    destination_path: str = Field(description="Relative destination path beneath PERCEPTION_MUTATION_ROOT"),
    overwrite: bool = Field(default=False, description="Quarantine an existing destination before moving"),
):
    """Move one workspace-confined filesystem object."""
    return await move_path(source_path, destination_path, overwrite)


@mcp.tool(description="Copy a file or directory inside the configured mutation workspace")
async def filesystem_copy(
    source_path: str = Field(description="Relative source path beneath PERCEPTION_MUTATION_ROOT"),
    destination_path: str = Field(description="Relative destination path beneath PERCEPTION_MUTATION_ROOT"),
    overwrite: bool = Field(default=False, description="Quarantine an existing destination before copying"),
):
    """Copy one workspace-confined filesystem object."""
    return await copy_path(source_path, destination_path, overwrite)


@mcp.tool(description="Delete a file or directory from the configured mutation workspace using reversible quarantine")
async def filesystem_delete(
    path: str = Field(description="Relative path beneath PERCEPTION_MUTATION_ROOT"),
):
    """Quarantine one workspace-confined filesystem object."""
    return await delete_path(path)


# ============================================================================
# PUBLIC DATA SOURCE TOOLS
# ============================================================================

@mcp.tool(description="Get current weather information for a location (Open-Meteo, free, no API key)")
async def weather(
    location: str = Field(description="City name (automatically geocoded)"),
    latitude: float | None = Field(default=None, description="Latitude coordinate (optional)"),
    longitude: float | None = Field(default=None, description="Longitude coordinate (optional)")
):
    """Get weather data."""
    return await get_weather(location, latitude, longitude)


@mcp.tool(description="Get stock price and market information")
async def stock_price(
    symbol: str = Field(description="Stock ticker symbol (e.g., AAPL)"),
    interval: str = Field(default="1d", description="Data interval")
):
    """Get stock price."""
    return await get_stock_price(symbol, interval)


@mcp.tool(description="Convert between currencies")
async def currency_converter(
    amount: float = Field(description="Amount to convert"),
    from_currency: str = Field(description="Source currency code (e.g., USD)"),
    to_currency: str = Field(description="Target currency code (e.g., EUR)")
):
    """Convert currency."""
    return await convert_currency(amount, from_currency, to_currency)


@mcp.tool(description="Get cryptocurrency price information (CoinGecko, free, no API key)")
async def crypto_price(
    symbol: str = Field(description="Cryptocurrency symbol or ID (e.g., bitcoin, ethereum, btc, eth)"),
    vs_currency: str = Field(default="usd", description="Target currency (usd, eur, gbp, etc.)")
):
    """Get cryptocurrency price."""
    return await get_crypto_price(symbol, vs_currency)


@mcp.tool(description="Search for locations using Nominatim/OpenStreetMap (free, no API key)")
async def location_search(
    query: str = Field(description="Location query (e.g., 'Eiffel Tower', 'New York', 'Tokyo')"),
    limit: int = Field(default=5, description="Maximum number of results (1-50)"),
    country_code: str | None = Field(default=None, description="Country code filter (e.g., 'us', 'gb', 'fr')")
):
    """Search locations (geocoding)."""
    return await search_location(query, limit, country_code)


@mcp.tool(description="Search for Points of Interest near a location using Overpass/OpenStreetMap (free, no API key)")
async def poi_search(
    query: str = Field(description="Type of POI (e.g., 'restaurant', 'cafe', 'hospital', 'atm', 'hotel')"),
    latitude: float = Field(description="Center latitude coordinate"),
    longitude: float = Field(description="Center longitude coordinate"),
    radius: int = Field(default=1000, description="Search radius in meters"),
    limit: int = Field(default=10, description="Maximum number of results")
):
    """Search points of interest."""
    return await search_poi(query, latitude, longitude, radius, limit)


@mcp.tool(description="Search Wikipedia and get article summary")
async def wikipedia_search(
    query: str = Field(description="Search query"),
    language: str = Field(default="en", description="Wikipedia language"),
    sentences: int = Field(default=5, description="Summary sentence count")
):
    """Search Wikipedia."""
    return await search_wikipedia(query, language, sentences)


@mcp.tool(description="Search ArXiv for academic papers")
async def arxiv_search(
    query: str = Field(description="Search query"),
    max_results: int = Field(default=5, description="Maximum results"),
    sort_by: str = Field(default="relevance", description="Sort method")
):
    """Search ArXiv."""
    return await search_arxiv(query, max_results, sort_by)


@mcp.tool(description="Search Wayback Machine for archived web pages")
async def wayback_search(
    url: str = Field(description="URL to search for"),
    year: int | None = Field(default=None, description="Filter by year"),
    limit: int = Field(default=10, description="Maximum snapshots")
):
    """Search Wayback Machine."""
    return await search_wayback(url, year, limit)


# ============================================================================
# YOUTUBE TOOLS
# ============================================================================

@mcp.tool(description="Extract transcript from a YouTube video")
async def youtube_transcript(
    video_id: str = Field(description="YouTube video ID or URL"),
    language_code: str = Field(default="en", description="Language code for transcript"),
    translate_to_language: str | None = Field(default=None, description="Translate to this language")
):
    """Extract YouTube transcript."""
    return await extract_youtube_transcript(video_id, language_code, translate_to_language)


# ============================================================================
# PUBCHEM CHEMICAL DATA TOOLS
# ============================================================================

@mcp.tool(description="Search PubChem for chemical compounds")
async def pubchem_search(
    query: str = Field(description="Search term or identifier"),
    search_type: str = Field(default="name", description="Type: name, cid, smiles, inchi, formula"),
    max_results: int = Field(default=10, description="Maximum results (1-100)")
):
    """Search PubChem compounds."""
    return await search_compounds(query, search_type, max_results)


@mcp.tool(description="Get detailed properties for a PubChem compound")
async def pubchem_properties(
    cid: int = Field(description="PubChem Compound ID"),
    properties: list[str] | None = Field(default=None, description="List of property names")
):
    """Get compound properties."""
    return await get_compound_properties(cid, properties)


@mcp.tool(description="Get synonyms for a PubChem compound")
async def pubchem_synonyms(
    cid: int = Field(description="PubChem Compound ID"),
    max_synonyms: int = Field(default=20, description="Maximum synonyms (1-100)")
):
    """Get compound synonyms."""
    return await get_compound_synonyms(cid, max_synonyms)


@mcp.tool(description="Search for structurally similar compounds in PubChem")
async def pubchem_similar(
    cid: int = Field(description="Reference compound CID"),
    similarity_threshold: float = Field(default=0.9, description="Similarity threshold (0.0-1.0)"),
    max_results: int = Field(default=10, description="Maximum results (1-50)")
):
    """Search similar compounds."""
    return await search_similar_compounds(cid, similarity_threshold, max_results)


# ============================================================================
# YAHOO FINANCE TOOLS
# ============================================================================

@mcp.tool(description="Get current stock quote and market data")
async def yfinance_quote(
    symbol: str = Field(description="Stock ticker symbol (e.g., AAPL, MSFT)")
):
    """Get stock quote."""
    return await get_stock_quote(symbol)


@mcp.tool(description="Get historical stock price data")
async def yfinance_historical(
    symbol: str = Field(description="Stock ticker symbol"),
    start: str = Field(description="Start date (YYYY-MM-DD)"),
    end: str = Field(description="End date (YYYY-MM-DD)"),
    interval: str = Field(default="1d", description="Data interval (1d, 1wk, 1mo)"),
    max_rows_preview: int = Field(default=10, description="Max rows in preview")
):
    """Get historical stock data."""
    return await get_historical_data(symbol, start, end, interval, max_rows_preview)


@mcp.tool(description="Get comprehensive company information")
async def yfinance_company_info(
    symbol: str = Field(description="Stock ticker symbol")
):
    """Get company information."""
    return await get_company_info(symbol)


@mcp.tool(description="Get financial statements (income statement, balance sheet, cash flow)")
async def yfinance_financials(
    symbol: str = Field(description="Stock ticker symbol"),
    statement_type: str = Field(description="Type: income_statement, balance_sheet, cash_flow"),
    period_type: str = Field(default="annual", description="Period: annual or quarterly"),
    max_columns_preview: int = Field(default=4, description="Max periods to show")
):
    """Get financial statements."""
    return await get_financial_statements(symbol, statement_type, period_type, max_columns_preview)


# ============================================================================
# DOCUMENT PROCESSING TOOLS
# ============================================================================

@mcp.tool(description="Extract text from PDF file with optional page range")
async def pdf_extract(
    file_path: str = Field(description="Path to PDF file"),
    page_range: str | None = Field(default=None, description="Page range (e.g., '1-5' or '1,3,5')")
):
    """Extract text from PDF."""
    return await extract_pdf_text(file_path, page_range)


@mcp.tool(description="Extract content from Word document (DOCX)")
async def docx_extract(
    file_path: str = Field(description="Path to DOCX file")
):
    """Extract content from DOCX."""
    return await extract_docx_content(file_path)


@mcp.tool(description="Extract content from PowerPoint presentation (PPTX)")
async def pptx_extract(
    file_path: str = Field(description="Path to PPTX file")
):
    """Extract content from PPTX."""
    return await extract_pptx_content(file_path)


@mcp.tool(description="Extract and parse CSV file data")
async def csv_parse(
    file_path: str = Field(description="Path to CSV file"),
    max_rows: int = Field(default=1000, description="Maximum rows to read")
):
    """Parse CSV data."""
    return await extract_csv_content(file_path, max_rows)


# ============================================================================
# MEDIA PROCESSING TOOLS
# ============================================================================

@mcp.tool(description="Transcribe audio to text using Whisper")
async def audio_transcribe(
    file_path: str = Field(description="Path to audio file"),
    model_size: str = Field(default="base", description="Whisper model size"),
    language: str = Field(default="en", description="Language code")
):
    """Transcribe audio to text."""
    return await transcribe_audio_whisper(file_path, model_size, language)


@mcp.tool(description="Extract audio file metadata")
async def audio_metadata(
    file_path: str = Field(description="Path to audio file")
):
    """Extract audio metadata."""
    return await extract_audio_metadata(file_path)


@mcp.tool(description="Extract text from image using OCR")
async def image_ocr(
    image_path: str = Field(description="Path to image file"),
    language: str = Field(default="eng", description="OCR language")
):
    """Extract text from image using OCR."""
    return await extract_text_ocr(image_path, language)


@mcp.tool(description="Analyze image using AI vision")
async def image_analyze(
    image_path: str = Field(description="Path to image file"),
    prompt: str = Field(default="Describe this image in detail", description="Analysis prompt")
):
    """Analyze image with AI."""
    return await analyze_image_ai(image_path, prompt)


@mcp.tool(description="Extract keyframes from video")
async def video_keyframes(
    video_path: str = Field(description="Path to video file"),
    num_frames: int = Field(default=10, description="Number of keyframes to extract")
):
    """Extract video keyframes."""
    return await extract_video_keyframes(video_path, num_frames)


@mcp.tool(description="Analyze video content using AI vision")
async def video_analyze(
    video_path: str = Field(description="Path to video file"),
    num_frames: int = Field(default=5, description="Number of frames to analyze"),
    prompt: str = Field(default="Analyze this video and describe what's happening", description="Analysis prompt")
):
    """Analyze video with AI."""
    return await analyze_video_ai(video_path, num_frames, prompt)


@mcp.tool(description="Trim audio file to specific time range")
async def audio_trim(
    audio_path: str = Field(description="Path to audio file"),
    start_time: float = Field(description="Start time in seconds"),
    duration: float | None = Field(default=None, description="Duration in seconds"),
    output_path: str | None = Field(default=None, description="Output file path")
):
    """Trim audio file."""
    return await trim_audio(audio_path, start_time, duration, output_path)


@mcp.tool(description="Get detailed image metadata including EXIF")
async def image_metadata(
    image_path: str = Field(description="Path to image file")
):
    """Get image metadata."""
    return await get_image_metadata(image_path)


@mcp.tool(description="Download YouTube video")
async def youtube_download(
    url: str = Field(description="YouTube video URL"),
    output_dir: str = Field(default=".", description="Output directory"),
    max_resolution: str = Field(default="720p", description="Maximum resolution")
):
    """Download YouTube video."""
    return await download_youtube_video(url, output_dir, max_resolution)


# ============================================================================
# GOOGLE SEARCH ENHANCED TOOLS
# ============================================================================

@mcp.tool(description="Search Google with API or DuckDuckGo fallback")
async def google_search_enhanced(
    query: str = Field(description="Search query"),
    num_results: int = Field(default=5, description="Number of results (1-10)"),
    safe_search: bool = Field(default=True, description="Enable safe search"),
    language: str = Field(default="en", description="Language code"),
    country: str = Field(default="us", description="Country code")
):
    """Enhanced Google search."""
    return await google_search_api(query, num_results, safe_search, language, country)


@mcp.tool(description="Read and extract content from webpage")
async def webpage_read_enhanced(
    url: str = Field(description="URL to read"),
    extract_links: bool = Field(default=False, description="Extract links from page")
):
    """Read webpage content."""
    return await read_webpage_content(url, extract_links)


# ============================================================================
# WIKIPEDIA ENHANCED TOOLS
# ============================================================================

@mcp.tool(description="Get full Wikipedia article content")
async def wiki_article_full(
    title: str = Field(description="Article title"),
    language: str = Field(default="en", description="Language code")
):
    """Get full Wikipedia article."""
    return await get_article_content(title, language)


@mcp.tool(description="Get Wikipedia article categories")
async def wiki_article_categories(
    title: str = Field(description="Article title"),
    language: str = Field(default="en", description="Language code")
):
    """Get article categories."""
    return await get_article_categories(title, language)


@mcp.tool(description="Get links from Wikipedia article")
async def wiki_article_links(
    title: str = Field(description="Article title"),
    language: str = Field(default="en", description="Language code")
):
    """Get article links."""
    return await get_article_links(title, language)


@mcp.tool(description="Get historical version of Wikipedia article")
async def wiki_article_history(
    title: str = Field(description="Article title"),
    date: str = Field(description="Date (YYYY/MM/DD)"),
    language: str = Field(default="en", description="Language code")
):
    """Get historical Wikipedia article."""
    return await get_article_history(title, date, language)


# ============================================================================
# ARXIV ENHANCED TOOLS
# ============================================================================

@mcp.tool(description="Get detailed ArXiv paper information")
async def arxiv_paper_details(
    paper_id: str = Field(description="ArXiv paper ID")
):
    """Get paper details."""
    return await get_paper_details(paper_id)


@mcp.tool(description="Download ArXiv paper PDF")
async def arxiv_download(
    paper_id: str = Field(description="ArXiv paper ID"),
    download_dir: str = Field(default=".", description="Download directory")
):
    """Download ArXiv paper."""
    return await download_paper(paper_id, download_dir)


@mcp.tool(description="Get ArXiv subject categories")
async def arxiv_categories():
    """Get ArXiv categories."""
    return await get_arxiv_categories()


# ============================================================================
# WAYBACK ENHANCED TOOLS
# ============================================================================

@mcp.tool(description="Get content from archived webpage")
async def wayback_archived_content(
    url: str = Field(description="URL to retrieve"),
    timestamp: str = Field(description="Timestamp (YYYYMMDDhhmmss)")
):
    """Get archived webpage content."""
    return await get_archived_content(url, timestamp)


# ============================================================================
# PRIVATE DATA SOURCE TOOLS
# ============================================================================

@mcp.tool(description="Get events from Google Calendar")
async def calendar_events(
    start_date: str | None = Field(default=None, description="Start date (ISO format)"),
    end_date: str | None = Field(default=None, description="End date (ISO format)"),
    calendar_id: str = Field(default="primary", description="Calendar ID"),
    max_results: int = Field(default=10, description="Maximum events")
):
    """Get calendar events."""
    return await get_calendar_events(start_date, end_date, calendar_id, max_results)


@mcp.tool(description="Search Notion workspace")
async def notion_search(
    query: str = Field(description="Search query"),
    database_id: str | None = Field(default=None, description="Specific database ID"),
    page_size: int = Field(default=10, description="Results per page")
):
    """Search Notion."""
    return await search_notion(query, database_id, page_size)


# Complete the 56 native schema descriptions before adding the expanded
# catalog. The implementations and native parameter schemas remain unchanged.
enrich_existing_tools(mcp)

# Experiment 4-7 requires 120+ tools from this perception MCP server.  The
# 56 native tools plus 70 additional real-backed, read-mostly tools bring the
# server catalog to 126 tools. Registration is dynamic only to avoid repetitive
# wrapper functions; tools/list still
# returns ordinary full JSON schemas and every tool is callable over MCP.
register_expanded_tools(mcp)


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    logging.info("Starting Perception Tools MCP server!")
    mcp.run(transport="stdio")
