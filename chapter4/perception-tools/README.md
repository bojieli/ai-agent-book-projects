# Perception Tools MCP Server / 感知工具 MCP 服务器

> Companion code for *AI Agents in Depth*, Chapter 4 — **Experiment 4-1 ★★**. MCP perception tools: search, multimodal, filesystem, public/private data. Most free APIs need no key.  
> 配套《深入理解 AI Agent》第 4 章 **实验 4-1 ★★**。感知 MCP 工具：搜索、多模态、文件系统、公开/私有数据。多数免费 API 无需 Key。

← [Chapter 4 index / 返回第 4 章目录](../README.md)

---

## English

A comprehensive MCP (Model Context Protocol) server providing various perception and data retrieval capabilities for AI agents.

### Features

> **✨ No API Keys Required!** Most features work out-of-the-box with free, open APIs.

#### Search Tools
- **Web Search**: DuckDuckGo search (free, no API key required)
- **Knowledge Base Search**: Search local document collections
- **File Download**: Download files from URLs with safety checks

#### Multimodal Understanding Tools
- **Web Page Reader**: Extract text and links from web pages
- **Document Reader**: Extract content from PDF, DOCX, PPTX files
- **Image Parser**: Parse and analyze image files
- **Video Parser**: Extract metadata from video files

#### File System Tools
- **File Reader**: Read files with encoding support
- **Grep Search**: Search for patterns in files (regex support)
- **Text Summarization**: Summarize long text content

#### Public Data Sources
- **Weather**: Current weather via [Open-Meteo](https://open-meteo.com/) (free, no API key)
- **Stock Prices**: Real-time stock data from Yahoo Finance (free, no API key)
- **Crypto Prices**: Cryptocurrency prices via [CoinGecko](https://www.coingecko.com/) (free, no API key)
- **Currency Conversion**: Convert between currencies (free, no API key)
- **Location Search**: Geocoding via [Nominatim (OpenStreetMap)](https://nominatim.openstreetmap.org/) (free, no API key)
- **POI Search**: Points of Interest via [Overpass API (OpenStreetMap)](https://overpass-api.de/) (free, no API key)
- **Wikipedia**: Search and retrieve Wikipedia articles (free, no API key)
- **ArXiv**: Search academic papers on ArXiv (free, no API key)
- **Wayback Machine**: Access archived web pages (free, no API key)

#### Private Data Sources
- **Google Calendar**: Query calendar events
- **Notion**: Search Notion workspace

### Installation

1. Clone the repository and navigate to the project directory:

```bash
cd chapter4/perception-tools
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. **No additional configuration required!** The server works out-of-the-box with free APIs.

### Configuration

#### Default Free APIs (No Setup Required)

The following features work immediately without any API keys:
- **Web Search**: DuckDuckGo
- **Weather**: Open-Meteo  
- **Stock Prices**: Yahoo Finance
- **Crypto Prices**: CoinGecko
- **Currency Conversion**: ExchangeRate-API
- **Location Search**: Nominatim (OpenStreetMap)
- **POI Search**: Overpass API (OpenStreetMap)
- **Wikipedia**: Wikipedia API
- **ArXiv**: ArXiv API
- **Wayback Machine**: Internet Archive

#### Optional Private Data Integrations

##### Google Calendar
For Google Calendar integration, you need to set up OAuth2:

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Follow the [Google Calendar API quickstart](https://developers.google.com/calendar/api/quickstart/python) to set up OAuth2 credentials.

##### Notion
1. Create a Notion integration at [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Get your integration token
3. Share your databases/pages with the integration
4. Add `NOTION_API_KEY` to `.env`

```bash
pip install notion-client
```

### Usage

#### Running the MCP Server

```bash
cd src
python main.py
```

The server runs using stdio transport, suitable for integration with MCP clients.

#### Command-Line Interface (`cli.py`)

Besides serving over MCP stdio, the repo root provides a unified CLI `cli.py` to list, inspect, call, and demo perception tools without an MCP client. Tools are organized by the five Chapter 4 perception scenarios: search / multimodal / filesystem / public data / private data (**53 tools** currently).

```bash
# Help (Chinese)
python cli.py --help

# List all perception tools by five categories (--category for one class)
python cli.py list
python cli.py list --category filesystem

# Parameter signature and call example for a tool
python cli.py info weather

# Call a tool; args as key=value; result is standard ActionResponse JSON
python cli.py run grep 'pattern=async def' directory=src 'file_pattern=*.py'
python cli.py run currency_converter amount=100 from_currency=USD to_currency=CNY

# End-to-end demo: research-assistant perception flow (local + external info)
python cli.py demo            # full demo (includes network steps)
python cli.py demo --offline  # offline (filesystem / local KB only)
```

Notes:

- Each tool is async and returns a unified `ActionResponse` (JSON); the CLI runs the event loop, parses JSON, and prints friendly output.
- Tools are lazy-imported: `list` / `info` / offline `demo` still work if optional deps (e.g. `whisper`, `waybackpy`) are missing; modules load only when those tools are actually called.
- Network tools are marked「联网」in `list`; tools needing auth/API keys are annotated accordingly.

#### Using with MCP Clients

Configure your MCP client (e.g., Claude Desktop) to connect to this server:

```json
{
  "mcpServers": {
    "perception-tools": {
      "command": "python",
      "args": ["/path/to/perception-tools/src/main.py"]
    }
  }
}
```

### Available Tools

#### Search Tools

##### `web_search`
Search the web using DuckDuckGo (free, no API key required).

Parameters:
- `query` (str): Search query string
- `num_results` (int, default=5): Number of results (1-10)
- `region` (str, default="wt-wt"): Region code (e.g., "us-en", "uk-en", "wt-wt" for worldwide)

##### `download`
Download a file from a URL.

Parameters:
- `url` (str): URL to download from
- `output_path` (str): Local path to save the file
- `overwrite` (bool, default=False): Overwrite existing file
- `timeout` (int, default=180): Download timeout in seconds

##### `knowledge_base_search`
Search a local knowledge base directory.

Parameters:
- `query` (str): Search query
- `knowledge_base_path` (str): Path to knowledge base directory
- `top_k` (int, default=5): Number of top results

#### Multimodal Understanding Tools

##### `webpage_reader`
Read and extract content from a webpage.

Parameters:
- `url` (str): URL of the webpage
- `extract_text` (bool, default=True): Extract text content
- `extract_links` (bool, default=False): Extract links

##### `document_reader`
Read and extract content from documents (PDF, DOCX, PPTX).

Parameters:
- `file_path` (str): Path to document file or URL
- `extract_images` (bool, default=False): Extract images

##### `image_parser`
Parse and analyze image files.

Parameters:
- `image_path` (str): Path to image file or URL
- `use_llm` (bool, default=True): Use LLM for analysis

> **Vision LLM keys / OpenRouter fallback**: AI image/video analysis
> (`analyze_image_ai` / `analyze_video_ai`) use `OPENAI_API_KEY` when set.
> If it is absent but `OPENROUTER_API_KEY` is set, they transparently route
> through OpenRouter (`base_url=https://openrouter.ai/api/v1`, model mapped to
> `provider/model` form). Override the model via `PERCEPTION_VISION_MODEL`.
> (Local Whisper transcription still needs `OPENAI_API_KEY` — OpenRouter has no
> audio-transcription API.)

##### `video_parser`
Parse and extract metadata from video files.

Parameters:
- `video_path` (str): Path to video file or URL
- `extract_frames` (bool, default=False): Extract sample frames
- `frame_interval` (int, default=30): Frame extraction interval

#### File System Tools

##### `file_reader`
Read a file and return its contents.

Parameters:
- `file_path` (str): Path to the file
- `encoding` (str, default="utf-8"): File encoding
- `max_length` (int, default=50000): Maximum characters to read

##### `grep`
Search for patterns in files (grep-like functionality).

Parameters:
- `pattern` (str): Regular expression pattern
- `directory` (str): Directory to search in
- `file_pattern` (str, default="*"): File pattern (e.g., *.py)
- `recursive` (bool, default=True): Search recursively
- `case_sensitive` (bool, default=False): Case-sensitive search
- `max_results` (int, default=100): Maximum results

##### `text_summarizer`
Summarize long text content.

Parameters:
- `text` (str): Text to summarize
- `max_length` (int, default=500): Target summary length
- `use_llm` (bool, default=True): Use LLM for summarization

#### Public Data Source Tools

##### `weather`
Get current weather information using Open-Meteo API (free, no API key required).

Parameters:
- `location` (str): City name (automatically geocoded)
- `latitude` (float, optional): Latitude coordinate
- `longitude` (float, optional): Longitude coordinate

##### `stock_price`
Get stock price and market information using Yahoo Finance (free, no API key required).

Parameters:
- `symbol` (str): Stock ticker symbol (e.g., AAPL, TSLA, GOOGL)
- `interval` (str, default="1d"): Data interval

##### `crypto_price`
Get cryptocurrency price information using CoinGecko API (free, no API key required).

Parameters:
- `symbol` (str): Cryptocurrency symbol or ID (e.g., bitcoin, ethereum, btc, eth)
- `vs_currency` (str, default="usd"): Target currency (usd, eur, gbp, etc.)

##### `currency_converter`
Convert between currencies.

Parameters:
- `amount` (float): Amount to convert
- `from_currency` (str): Source currency code (e.g., USD)
- `to_currency` (str): Target currency code (e.g., EUR)

##### `wikipedia_search`
Search Wikipedia and get article summary.

Parameters:
- `query` (str): Search query
- `language` (str, default="en"): Wikipedia language
- `sentences` (int, default=5): Summary sentence count

##### `arxiv_search`
Search ArXiv for academic papers.

Parameters:
- `query` (str): Search query
- `max_results` (int, default=5): Maximum results
- `sort_by` (str, default="relevance"): Sort method

##### `wayback_search`
Search Wayback Machine for archived web pages.

Parameters:
- `url` (str): URL to search for
- `year` (int, optional): Filter by year
- `limit` (int, default=10): Maximum snapshots

##### `location_search`
Search for locations using Nominatim (OpenStreetMap) API (free, no API key required).

Parameters:
- `query` (str): Location query (e.g., "Eiffel Tower", "New York", "Tokyo")
- `limit` (int, default=5): Maximum number of results (1-50)
- `country_code` (str, optional): Country code filter (e.g., "us", "gb", "fr")

##### `poi_search`
Search for Points of Interest near a location using Overpass API (free, no API key required).

Parameters:
- `query` (str): Type of POI (e.g., "restaurant", "cafe", "hospital", "atm", "hotel")
- `latitude` (float): Center latitude coordinate
- `longitude` (float): Center longitude coordinate
- `radius` (int, default=1000): Search radius in meters
- `limit` (int, default=10): Maximum number of results

#### Private Data Source Tools

##### `calendar_events`
Get events from Google Calendar.

Parameters:
- `start_date` (str, optional): Start date (ISO format)
- `end_date` (str, optional): End date (ISO format)
- `calendar_id` (str, default="primary"): Calendar ID
- `max_results` (int, default=10): Maximum events

##### `notion_search`
Search Notion workspace.

Parameters:
- `query` (str): Search query
- `database_id` (str, optional): Specific database ID
- `page_size` (int, default=10): Results per page

### Architecture

The project follows SOLID principles with a modular architecture:

```
perception-tools/
├── src/
│   ├── main.py                  # MCP server entry point
│   ├── base.py                  # Base models and utilities
│   ├── search_tools.py          # Search functionality
│   ├── multimodal_tools.py      # Document/media processing
│   ├── filesystem_tools.py      # File operations
│   ├── public_data_tools.py     # Public APIs
│   └── private_data_tools.py    # Private data sources
├── requirements.txt             # Python dependencies
├── env.example                  # Environment variables template
└── README.md                    # This file
```

### Error Handling

All tools return a standardized `ActionResponse` format:

```json
{
  "success": true/false,
  "message": "Result data or error message",
  "metadata": {
    "additional": "context information"
  }
}
```

### Contributing

Contributions are welcome! Please ensure:
1. Code follows KISS, DRY, and SOLID principles
2. All tools return standardized ActionResponse format
3. Proper error handling and logging
4. Documentation for new tools

### License

This project is part of the AI Agent training camp materials.

---

## 中文

为 AI Agent 提供多种感知与数据获取能力的综合 MCP（Model Context Protocol）服务器。

### 功能

> **✨ 多数功能无需 API Key！** 基于免费开放 API，开箱即用。

#### 搜索工具
- **网络搜索**：DuckDuckGo（免费，无需 API Key）
- **知识库搜索**：搜索本地文档集合
- **文件下载**：从 URL 下载，带安全检查

#### 多模态理解工具
- **网页阅读**：抽取文本与链接
- **文档阅读**：PDF、DOCX、PPTX
- **图像解析**：解析与分析图像
- **视频解析**：抽取视频元数据

#### 文件系统工具
- **文件阅读**：支持编码
- **Grep 搜索**：正则匹配文件内容
- **文本摘要**：总结长文本

#### 公开数据源
- **天气**：[Open-Meteo](https://open-meteo.com/)（免费，无需 Key）
- **股价**：Yahoo Finance（免费，无需 Key）
- **加密货币**：[CoinGecko](https://www.coingecko.com/)（免费，无需 Key）
- **汇率换算**：货币转换（免费，无需 Key）
- **地点搜索**：[Nominatim (OpenStreetMap)](https://nominatim.openstreetmap.org/)（免费，无需 Key）
- **POI 搜索**：[Overpass API (OpenStreetMap)](https://overpass-api.de/)（免费，无需 Key）
- **Wikipedia**：检索维基条目（免费，无需 Key）
- **ArXiv**：学术论文检索（免费，无需 Key）
- **Wayback Machine**：历史网页存档（免费，无需 Key）

#### 私有数据源
- **Google Calendar**：查询日历事件
- **Notion**：搜索 Notion 工作区

### 安装

1. 进入项目目录：

```bash
cd chapter4/perception-tools
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. **无需额外配置！** 服务器默认即可用免费 API 工作。

### 配置

#### 默认免费 API（无需配置）

以下功能立即可用，无需任何 API Key：
- **网络搜索**：DuckDuckGo
- **天气**：Open-Meteo  
- **股价**：Yahoo Finance
- **加密货币**：CoinGecko
- **汇率换算**：ExchangeRate-API
- **地点搜索**：Nominatim（OpenStreetMap）
- **POI 搜索**：Overpass API（OpenStreetMap）
- **Wikipedia**：Wikipedia API
- **ArXiv**：ArXiv API
- **Wayback Machine**：Internet Archive

#### 可选私有数据集成

##### Google Calendar
需要配置 OAuth2：

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

按 [Google Calendar API quickstart](https://developers.google.com/calendar/api/quickstart/python) 配置凭据。

##### Notion
1. 在 [notion.so/my-integrations](https://www.notion.so/my-integrations) 创建集成
2. 获取 integration token
3. 将数据库/页面共享给该集成
4. 在 `.env` 中加入 `NOTION_API_KEY`

```bash
pip install notion-client
```

### 使用

#### 运行 MCP 服务器

```bash
cd src
python main.py
```

服务器使用 stdio 传输，适合接入 MCP 客户端。

#### 命令行接口（`cli.py`）

除了以 MCP stdio 协议对外服务，仓库根目录提供了一个统一的命令行入口
`cli.py`，无需 MCP 客户端即可直接列出、查看、调用和演示各类感知工具。
工具按第四章「感知工具」的五类场景组织：搜索 / 多模态理解 / 文件系统 /
公开数据源 / 私有数据源（当前共 53 个工具）。

```bash
# 查看帮助（中文）
python cli.py --help

# 按五类列出全部感知工具（可用 --category 只看某一类）
python cli.py list
python cli.py list --category filesystem

# 查看某个工具的参数签名与调用示例
python cli.py info weather

# 直接调用某个工具，参数以 key=value 形式传入，结果为标准 ActionResponse JSON
python cli.py run grep 'pattern=async def' directory=src 'file_pattern=*.py'
python cli.py run currency_converter amount=100 from_currency=USD to_currency=CNY

# 运行端到端演示：串联「本地资料 + 外部信息」的研究助手 Agent 感知流程
python cli.py demo            # 完整演示（含联网步骤）
python cli.py demo --offline  # 离线演示（只跑文件系统 / 本地知识库等不联网步骤）
```

说明：

- 每个工具都是异步函数，返回统一的 `ActionResponse`（JSON）；CLI 负责运行事件
  循环、解析 JSON 并友好打印。
- 工具按需惰性导入：`list` / `info` / 离线 `demo` 在缺少可选依赖（如 `whisper`、
  `waybackpy`）时仍可正常工作，只有真正调用相关工具时才导入对应模块。
- 需要联网的工具在 `list` 中标注「联网」，需要授权/API Key 的工具标注了对应说明。

#### 与 MCP 客户端联用

在 MCP 客户端（如 Claude Desktop）中配置：

```json
{
  "mcpServers": {
    "perception-tools": {
      "command": "python",
      "args": ["/path/to/perception-tools/src/main.py"]
    }
  }
}
```

### 可用工具

#### 搜索工具

##### `web_search`
使用 DuckDuckGo 搜索（免费，无需 API Key）。

参数：
- `query` (str)：搜索查询
- `num_results` (int, default=5)：结果数（1-10）
- `region` (str, default="wt-wt")：区域代码（如 `"us-en"`、`"uk-en"`、全球 `"wt-wt"`）

##### `download`
从 URL 下载文件。

参数：
- `url` (str)：下载地址
- `output_path` (str)：本地保存路径
- `overwrite` (bool, default=False)：是否覆盖已有文件
- `timeout` (int, default=180)：超时秒数

##### `knowledge_base_search`
搜索本地知识库目录。

参数：
- `query` (str)：搜索查询
- `knowledge_base_path` (str)：知识库目录路径
- `top_k` (int, default=5)：返回条数

#### 多模态理解工具

##### `webpage_reader`
读取并抽取网页内容。

参数：
- `url` (str)：网页 URL
- `extract_text` (bool, default=True)：是否抽取文本
- `extract_links` (bool, default=False)：是否抽取链接

##### `document_reader`
读取文档（PDF、DOCX、PPTX）。

参数：
- `file_path` (str)：文件路径或 URL
- `extract_images` (bool, default=False)：是否抽取图片

##### `image_parser`
解析与分析图像。

参数：
- `image_path` (str)：图像路径或 URL
- `use_llm` (bool, default=True)：是否用 LLM 分析

> **视觉 LLM Key / OpenRouter 兜底**：AI 图像/视频分析
> （`analyze_image_ai` / `analyze_video_ai`）在设置了 `OPENAI_API_KEY` 时使用它。
> 若缺失但设置了 `OPENROUTER_API_KEY`，则透明走 OpenRouter
> （`base_url=https://openrouter.ai/api/v1`，模型映射为 `provider/model`）。
> 可用 `PERCEPTION_VISION_MODEL` 覆盖模型。
> （本地 Whisper 转写仍需 `OPENAI_API_KEY`——OpenRouter 无音频转写 API。）

##### `video_parser`
解析并抽取视频元数据。

参数：
- `video_path` (str)：视频路径或 URL
- `extract_frames` (bool, default=False)：是否抽取样帧
- `frame_interval` (int, default=30)：抽帧间隔

#### 文件系统工具

##### `file_reader`
读取文件内容。

参数：
- `file_path` (str)：文件路径
- `encoding` (str, default="utf-8")：编码
- `max_length` (int, default=50000)：最大字符数

##### `grep`
在文件中搜索模式（类 grep）。

参数：
- `pattern` (str)：正则表达式
- `directory` (str)：搜索目录
- `file_pattern` (str, default="*")：文件模式（如 `*.py`）
- `recursive` (bool, default=True)：是否递归
- `case_sensitive` (bool, default=False)：是否区分大小写
- `max_results` (int, default=100)：最大结果数

##### `text_summarizer`
总结长文本。

参数：
- `text` (str)：待总结文本
- `max_length` (int, default=500)：目标摘要长度
- `use_llm` (bool, default=True)：是否用 LLM 总结

#### 公开数据源工具

##### `weather`
Open-Meteo 当前天气（免费，无需 Key）。

参数：
- `location` (str)：城市名（自动地理编码）
- `latitude` (float, optional)：纬度
- `longitude` (float, optional)：经度

##### `stock_price`
Yahoo Finance 股价与行情（免费，无需 Key）。

参数：
- `symbol` (str)：股票代码（如 AAPL、TSLA、GOOGL）
- `interval` (str, default="1d")：数据间隔

##### `crypto_price`
CoinGecko 加密货币价格（免费，无需 Key）。

参数：
- `symbol` (str)：符号或 ID（如 bitcoin、ethereum、btc、eth）
- `vs_currency` (str, default="usd")：目标货币

##### `currency_converter`
货币换算。

参数：
- `amount` (float)：金额
- `from_currency` (str)：源货币（如 USD）
- `to_currency` (str)：目标货币（如 EUR）

##### `wikipedia_search`
搜索 Wikipedia 并取摘要。

参数：
- `query` (str)：搜索查询
- `language` (str, default="en")：语言
- `sentences` (int, default=5)：摘要句数

##### `arxiv_search`
搜索 ArXiv 论文。

参数：
- `query` (str)：搜索查询
- `max_results` (int, default=5)：最大条数
- `sort_by` (str, default="relevance")：排序方式

##### `wayback_search`
搜索 Wayback Machine 历史快照。

参数：
- `url` (str)：目标 URL
- `year` (int, optional)：按年过滤
- `limit` (int, default=10)：最大快照数

##### `location_search`
Nominatim（OpenStreetMap）地点搜索（免费，无需 Key）。

参数：
- `query` (str)：地点查询（如 "Eiffel Tower"、"New York"、"Tokyo"）
- `limit` (int, default=5)：最大结果数（1-50）
- `country_code` (str, optional)：国家代码过滤（如 "us"、"gb"、"fr"）

##### `poi_search`
Overpass API 附近 POI 搜索（免费，无需 Key）。

参数：
- `query` (str)：POI 类型（如 "restaurant"、"cafe"、"hospital"、"atm"、"hotel"）
- `latitude` (float)：中心纬度
- `longitude` (float)：中心经度
- `radius` (int, default=1000)：搜索半径（米）
- `limit` (int, default=10)：最大结果数

#### 私有数据源工具

##### `calendar_events`
从 Google Calendar 获取事件。

参数：
- `start_date` (str, optional)：开始日期（ISO）
- `end_date` (str, optional)：结束日期（ISO）
- `calendar_id` (str, default="primary")：日历 ID
- `max_results` (int, default=10)：最大事件数

##### `notion_search`
搜索 Notion 工作区。

参数：
- `query` (str)：搜索查询
- `database_id` (str, optional)：指定数据库 ID
- `page_size` (int, default=10)：每页条数

### 架构

项目遵循 SOLID，模块化组织：

```
perception-tools/
├── src/
│   ├── main.py                  # MCP server entry point
│   ├── base.py                  # Base models and utilities
│   ├── search_tools.py          # Search functionality
│   ├── multimodal_tools.py      # Document/media processing
│   ├── filesystem_tools.py      # File operations
│   ├── public_data_tools.py     # Public APIs
│   └── private_data_tools.py    # Private data sources
├── requirements.txt             # Python dependencies
├── env.example                  # Environment variables template
└── README.md                    # This file
```

### 错误处理

所有工具返回统一的 `ActionResponse`：

```json
{
  "success": true/false,
  "message": "Result data or error message",
  "metadata": {
    "additional": "context information"
  }
}
```

### 贡献

欢迎贡献。请确保：
1. 代码遵循 KISS、DRY、SOLID
2. 工具返回统一 ActionResponse
3. 妥善错误处理与日志
4. 为新工具补充文档

### 许可证

本项目为 AI Agent 训练营材料的一部分。

---

## Notes / 说明

- Prefer `python cli.py demo --offline` for a first run without network-heavy steps.  
- 首次可先跑 `python cli.py demo --offline`，避免重度联网步骤。  
- Most public-data tools need no API key; vision LLM and Whisper paths may need keys.  
- 多数公开数据工具无需 Key；视觉 LLM 与 Whisper 路径可能需要 Key。
