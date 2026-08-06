# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MCP Client (e.g., Claude)                    │
└───────────────────────────────┬─────────────────────────────────┘
                                │ stdio
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                       main.py (MCPServer)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Tool Registration (@mcp.tool)                │   │
│  └──────────────────────────────────────────────────────────┘   │
└───┬──────┬──────────┬──────────┬────────────┬──────────────┬───┘
    │      │          │          │            │              │
┌───▼──┐ ┌─▼────┐ ┌──▼──┐ ┌─────▼────┐ ┌────▼─────┐ ┌──────▼────┐
│Search│ │Multi │ │File │ │  Public  │ │ Private  │ │   Base    │
│Tools │ │modal │ │Sys  │ │   Data   │ │   Data   │ │ Utilities │
│  (3) │ │Tools │ │Tools│ │Tools (6) │ │Tools (2) │ │           │
│      │ │  (4) │ │ (3) │ │          │ │          │ │           │
└───┬──┘ └─┬────┘ └──┬──┘ └─────┬────┘ └────┬─────┘ └──────┬────┘
    │      │         │          │            │              │
    │      │         │          │            │              │
    └──────┴─────────┴──────────┴────────────┴──────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  ActionResponse Model  │
                    │  (Standardized Output) │
                    └───────────────────────┘
```

## Module Dependencies

```
main.py
├── search_tools.py
│   ├── base.py (ActionResponse, is_url, download_file_from_url)
│   ├── requests
│   └── mcp.types (TextContent)
│
├── multimodal_tools.py
│   ├── base.py (ActionResponse, validate_file_path, download_file_from_url)
│   ├── beautifulsoup4
│   ├── PyPDF2
│   ├── python-docx
│   ├── python-pptx
│   ├── Pillow
│   └── opencv-python
│
├── filesystem_tools.py
│   ├── base.py (ActionResponse, validate_file_path)
│   └── re (standard library)
│
├── public_data_tools.py
│   ├── base.py (ActionResponse)
│   ├── requests
│   ├── wikipedia
│   └── arxiv
│
├── private_data_tools.py
│   ├── base.py (ActionResponse)
│   ├── google-api-python-client (optional)
│   └── notion-client (optional)
│
└── base.py
    ├── pydantic (BaseModel, Field)
    └── requests
```

## Data Flow

### Request Flow
```
1. MCP Client sends tool request via stdio
   ↓
2. MCPServer receives and validates the request
   ↓
3. Appropriate tool function is called
   ↓
4. Tool function processes request
   ↓
5. External API calls (if needed)
   ↓
6. Data processing and transformation
   ↓
7. ActionResponse object created
   ↓
8. Wrapped in TextContent
   ↓
9. JSON serialized and returned via stdio
   ↓
10. MCP Client receives and processes response
```

### Error Flow
```
1. Exception occurs in tool function
   ↓
2. Exception caught in try-except block
   ↓
3. Error logged with traceback
   ↓
4. ActionResponse created with success=False
   ↓
5. Error details in message and metadata
   ↓
6. Returned to client (no crashes)
```

## Component Responsibilities

### main.py
- **Role**: MCP server initialization and tool registration
- **Responsibilities**:
  - Construct the MCPServer
  - Register all tool functions with decorators
  - Provide server-level instructions
  - Run stdio transport loop
- **Dependencies**: All tool modules

### base.py
- **Role**: Shared utilities and models
- **Responsibilities**:
  - Define ActionResponse model
  - Define DocumentMetadata model
  - Provide URL validation (is_url)
  - Provide file validation (validate_file_path)
  - Provide file download utility (download_file_from_url)
- **Dependencies**: pydantic, requests

### search_tools.py
- **Role**: Search and retrieval operations
- **Tools**:
  - web_search: Google Custom Search API
  - download_file: HTTP/HTTPS file downloads
  - search_knowledge_base: Local file search
- **External APIs**: Google Custom Search
- **Dependencies**: requests, base

### multimodal_tools.py
- **Role**: Content extraction from various media
- **Tools**:
  - read_webpage: HTML parsing
  - read_document: Document extraction (PDF/DOCX/PPTX)
  - parse_image: Image metadata and analysis
  - parse_video: Video metadata extraction
- **File Formats**: HTML, PDF, DOCX, PPTX, JPG, PNG, MP4, etc.
- **Dependencies**: beautifulsoup4, PyPDF2, python-docx, python-pptx, Pillow, opencv-python, base

### filesystem_tools.py
- **Role**: File system operations
- **Tools**:
  - read_file: Read file contents
  - grep_search: Pattern search in files
  - summarize_text: Text summarization
- **Dependencies**: re (stdlib), base

### public_data_tools.py
- **Role**: Public API integrations
- **Tools**:
  - get_weather: OpenWeather API
  - get_stock_price: Yahoo Finance
  - convert_currency: Exchange rate API
  - search_wikipedia: Wikipedia API
  - search_arxiv: ArXiv API
  - search_wayback: Wayback Machine API
- **External APIs**: 6 different public APIs
- **Dependencies**: requests, wikipedia, arxiv, base

### private_data_tools.py
- **Role**: Private data source integrations
- **Tools**:
  - get_calendar_events: Google Calendar OAuth2
  - search_notion: Notion API
- **External APIs**: Google Calendar, Notion
- **Dependencies**: google-api-python-client (optional), notion-client (optional), base

## Configuration Management

```
Environment Variables (.env)
├── GOOGLE_API_KEY (required for web search)
├── GOOGLE_CSE_ID (required for web search)
├── OPENWEATHER_API_KEY (required for weather)
├── NOTION_API_KEY (optional for Notion)
└── Google OAuth2 Credentials (optional for Calendar)
```

## Error Handling Strategy

### Levels of Error Handling

1. **Input Validation**
   - Parameter validation
   - File existence checks
   - URL format validation

2. **External API Errors**
   - Network timeouts
   - HTTP errors
   - API quota limits
   - Authentication failures

3. **Processing Errors**
   - File parsing errors
   - Encoding errors
   - Memory limits

4. **Graceful Degradation**
   - Return partial results when possible
   - Clear error messages
   - Suggest remediation steps

### Error Response Format
```json
{
  "success": false,
  "message": "Human-readable error description",
  "metadata": {
    "error_type": "category_of_error",
    "additional_context": "more details"
  }
}
```

## Performance Characteristics

### Timeouts
- Web requests: 10-30 seconds
- File downloads: 180 seconds
- Long operations: 300 seconds

### Limits
- File download size: 100 MB
- Video download size: 500 MB
- Text read limit: 50,000 characters
- Search results: 5-100 items

### Concurrency
- Async/await throughout
- Single-threaded stdio transport
- Non-blocking external API calls

## Security Considerations

### Input Validation
- Path traversal prevention
- URL scheme restrictions (HTTP/HTTPS only)
- File size limits
- Timeout enforcement

### API Security
- API keys via environment variables
- OAuth2 for Google Calendar
- Token-based auth for Notion
- No hardcoded credentials

### Output Sanitization
- JSON encoding for all responses
- Base64 encoding for binary data
- Length limits on returned data

## Extensibility Points

### Adding New Tools
1. Create function in appropriate module
2. Follow async pattern
3. Use ActionResponse format
4. Add error handling
5. Register in main.py
6. Update documentation

### Adding New Categories
1. Create new module in src/
2. Import base utilities
3. Implement tools following patterns
4. Import in main.py
5. Register tools
6. Update documentation

### Adding New Data Sources
1. Add to public_data_tools.py or private_data_tools.py
2. Implement API client
3. Follow error handling patterns
4. Document API requirements
5. Update env.example

## Testing Strategy

### Unit Testing (Future)
- Test each tool function
- Mock external APIs
- Test error conditions
- Validate response format

### Integration Testing
- test_imports.py: Verify all imports
- quickstart.py: Test actual functionality
- Manual testing via MCP client

### Production Monitoring
- Logging throughout
- Error tracking
- Performance metrics (timing)
- API quota monitoring

## Deployment Considerations

### Requirements
- Python 3.10+
- All dependencies in requirements.txt
- Environment variables configured
- Network access for external APIs

### Running in Production
- Use process manager (systemd, supervisor)
- Configure appropriate timeouts
- Monitor logs
- Set up API key rotation
- Implement rate limiting if needed

### Scaling
- Current: Single process, stdio transport
- Future: Could add HTTP transport for multiple clients
- Future: Could implement caching layer
- Future: Could add request queuing
