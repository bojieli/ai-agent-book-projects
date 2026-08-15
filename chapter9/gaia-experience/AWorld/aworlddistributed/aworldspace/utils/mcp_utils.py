import os


def load_all_mcp_config():
    return {
        "mcpServers": {
            "e2b-server": {
                "command": "npx",
                "args": [
                    "-y",
                    "@e2b/mcp-server"
                ],
                "env": {
                    "E2B_API_KEY": os.environ["E2B_API_KEY"],
                    "SESSION_REQUEST_CONNECT_TIMEOUT": "60"
                }
            },
            "filesystem": {
                "command": "npx",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    "${FILESYSTEM_SERVER_WORKDIR}"
                ]
            },
            "terminal-controller": {
                "command": "python",
                "args": [
                    "-m",
                    "terminal_controller"
                ],
                "env": {
                    "SESSION_REQUEST_CONNECT_TIMEOUT": "300"
                }
            },
            "calculator": {
                "command": "python",
                "args": [
                    "-m",
                    "mcp_server_calculator"
                ],
                "env": {
                    "SESSION_REQUEST_CONNECT_TIMEOUT": "20"
                }
            },
            "excel": {
                "command": "uvx",
                "args": ["excel-mcp-server", "stdio"],
                "env": {
                    "EXCEL_MCP_PAGING_CELLS_LIMIT": "4000",
                    "SESSION_REQUEST_CONNECT_TIMEOUT": "120"
                }
            },
            "google-search": {
                "command": "npx",
                "args": [
                    "-y",
                    "@adenot/mcp-google-search"
                ],
                "env": {
                    "GOOGLE_API_KEY": os.environ["GOOGLE_API_KEY"],
                    "GOOGLE_SEARCH_ENGINE_ID": os.environ["GOOGLE_CSE_ID"],
                    "SESSION_REQUEST_CONNECT_TIMEOUT": "60"
                }
            },
            "ms-playwright": {
                "command": "npx",
                "args": [
                    "@playwright/mcp@latest",
                    "--no-sandbox",
                    "--headless",
                    "--isolated"
                ],
                "env": {
                    "PLAYWRIGHT_TIMEOUT": "120000",
                    "SESSION_REQUEST_CONNECT_TIMEOUT": "120"
                }
            },
            "audio_server": {
                "command": "python",
                "args": [
                    "-m",
                    "mcp_servers.audio_server"
                ],
                "env": {
                    "AUDIO_LLM_API_KEY": os.environ["AUDIO_LLM_API_KEY"],
                    "AUDIO_LLM_BASE_URL": os.environ["AUDIO_LLM_BASE_URL"],
                    "AUDIO_LLM_MODEL_NAME": os.environ["AUDIO_LLM_MODEL_NAME"],
                    "SESSION_REQUEST_CONNECT_TIMEOUT": "60"
                }
            },
            "image_server": {
                "command": "python",
                "args": [
                    "-m",
                    "mcp_servers.image_server"
                ],
                "env": {
                    "LLM_API_KEY": os.environ.get("LLM_API_KEY"),
                    "LLM_MODEL_NAME": os.environ.get("LLM_MODEL_NAME"),
                    "LLM_BASE_URL": os.environ.get("LLM_BASE_URL"),
                    "SESSION_REQUEST_CONNECT_TIMEOUT": "60"
                }
            },
            "youtube_server": {
                "command": "python",
                "args": [
                    "-m",
                    "mcp_servers.youtube_server"
                ],
                "env": {
                    "CHROME_DRIVER_PATH": os.environ['CHROME_DRIVER_PATH'],
                    "SESSION_REQUEST_CONNECT_TIMEOUT": "120"
                }
            },
            "video_server": {
                "command": "python",
                "args": [
                    "-m",
                    "mcp_servers.video_server"
                ],
                "env": {
                    "LLM_API_KEY": os.environ.get("LLM_API_KEY"),
                    "LLM_MODEL_NAME": os.environ.get("LLM_MODEL_NAME"),
                    "LLM_BASE_URL": os.environ.get("LLM_BASE_URL"),
                    "SESSION_REQUEST_CONNECT_TIMEOUT": "60"
                }
            },
            "search_server": {
                "command": "python",
                "args": [
                    "-m",
                    "mcp_servers.search_server"
                ],
                "env": {
                    "GOOGLE_API_KEY": os.environ["GOOGLE_API_KEY"],
                    "GOOGLE_CSE_ID": os.environ["GOOGLE_CSE_ID"],
                    "SESSION_REQUEST_CONNECT_TIMEOUT": "60"
                }
            },
            "download_server": {
                "command": "python",
                "args": [
                    "-m",
                    "mcp_servers.download_server"
                ],
                "env": {
                    "SESSION_REQUEST_CONNECT_TIMEOUT": "120"
                }
            },
            "document_server": {
                "command": "python",
                "args": [
                    "-m",
                    "mcp_servers.document_server"
                ],
                "env": {
                    "SESSION_REQUEST_CONNECT_TIMEOUT": "120"
                }
            },
            "browser_server": {
                "command": "python",
                "args": [
                    "-m",
                    "mcp_servers.browser_server"
                ],
                "env": {
                    "LLM_API_KEY": os.environ.get("LLM_API_KEY"),
                    "LLM_MODEL_NAME": os.environ.get("LLM_MODEL_NAME"),
                    "LLM_BASE_URL": os.environ.get("LLM_BASE_URL"),
                    "SESSION_REQUEST_CONNECT_TIMEOUT": "120"
                }
            },
            "reasoning_server": {
                "command": "python",
                "args": [
                    "-m",
                    "mcp_servers.reasoning_server"
                ],
                "env": {
                    "LLM_API_KEY": os.environ.get("LLM_API_KEY"),
                    "LLM_MODEL_NAME": os.environ.get("LLM_MODEL_NAME"),
                    "LLM_BASE_URL": os.environ.get("LLM_BASE_URL"),
                    "SESSION_REQUEST_CONNECT_TIMEOUT": "120"
                }
            },
            "e2b-code-server": {
                "command": "python",
                "args": [
                    "-m",
                    "mcp_servers.e2b_code_server"
                ],
                "env": {
                    "E2B_API_KEY": os.environ["E2B_API_KEY"],
                    "SESSION_REQUEST_CONNECT_TIMEOUT": "120"
                }
            },
        }
    }
