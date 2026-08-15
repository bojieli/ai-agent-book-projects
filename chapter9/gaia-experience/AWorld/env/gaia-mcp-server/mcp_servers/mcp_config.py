import os

import dotenv

dotenv.load_dotenv(verbose=True, override=True, interpolate=True)

mcp_config = {
    "mcpServers": {
        "readweb-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/main.py"],
            "cwd": "readweb_server",
            "env": {
                "PIC_SEARCH_URL": os.getenv("PIC_SEARCH_URL"),
                "PIC_SEARCH_TOTAL_NUM": os.getenv("PIC_SEARCH_TOTAL_NUM"),
                "PIC_SEARCH_SLICE_NUM": os.getenv("PIC_SEARCH_SLICE_NUM"),
                "PIC_SEARCH_DOMAIN": os.getenv("PIC_SEARCH_DOMAIN"),
                "PIC_SEARCH_SEARCHMODE": os.getenv("PIC_SEARCH_SEARCHMODE"),
                "PIC_SEARCH_SOURCE": os.getenv("PIC_SEARCH_SOURCE"),
                "PIC_SEARCH_UID": os.getenv("PIC_SEARCH_UID"),
                "JINA_API_KEY": os.getenv("JINA_API_KEY"),
                "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY"),
                "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
                "GOOGLE_CSE_ID": os.getenv("GOOGLE_CSE_ID"),
            },
        },
        "browser-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/main.py"],
            "cwd": "browser_server",
            "env": {
                "LLM_BASE_URL": os.getenv("BROWSERUSE_LLM_BASE_URL"),
                "LLM_MODEL_NAME": os.getenv("BROWSERUSE_LLM_MODEL_NAME"),
                "LLM_API_KEY": os.getenv("BROWSERUSE_LLM_API_KEY"),
            },
        },
        "documents-csv-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/csv_server.py"],
            "cwd": "documents_server",
        },
        "documents-docx-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/docx_server.py"],
            "cwd": "documents_server",
        },
        "documents-pptx-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/pptx_server.py"],
            "cwd": "documents_server",
        },
        "documents-pdf-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/pdf_server.py"],
            "cwd": "documents_server",
            "env": {
                "DATALAB_API_KEY": os.getenv("DATALAB_API_KEY"),
            },
        },
        "documents-txt-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/txt_server.py"],
            "cwd": "documents_server",
        },
        "download-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/download.py"],
            "cwd": "download_server",
        },
        "intelligence-code-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/code.py"],
            "cwd": "intelligence_server",
            "env": {
                "CODE_LLM_BASE_URL": os.getenv("CODE_LLM_BASE_URL"),
                "CODE_LLM_MODEL_NAME": os.getenv("CODE_LLM_MODEL_NAME"),
                "CODE_LLM_API_KEY": os.getenv("CODE_LLM_API_KEY"),
            },
        },
        "intelligence-think-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/think.py"],
            "cwd": "intelligence_server",
            "env": {
                "THINK_LLM_BASE_URL": os.getenv("THINK_LLM_BASE_URL"),
                "THINK_LLM_MODEL_NAME": os.getenv("THINK_LLM_MODEL_NAME"),
                "THINK_LLM_API_KEY": os.getenv("THINK_LLM_API_KEY"),
            },
        },
        "intelligence-guard-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/guard.py"],
            "cwd": "intelligence_server",
            "env": {
                "GUARD_LLM_BASE_URL": os.getenv("GUARD_LLM_BASE_URL"),
                "GUARD_LLM_MODEL_NAME": os.getenv("GUARD_LLM_MODEL_NAME"),
                "GUARD_LLM_API_KEY": os.getenv("GUARD_LLM_API_KEY"),
            },
        },
        "media-audio-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/audio.py"],
            "cwd": "media_server",
            "env": {
                "AUDIO_LLM_BASE_URL": os.getenv("AUDIO_LLM_BASE_URL"),
                "AUDIO_LLM_MODEL_NAME": os.getenv("AUDIO_LLM_MODEL_NAME"),
                "AUDIO_LLM_API_KEY": os.getenv("AUDIO_LLM_API_KEY"),
            },
        },
        "media-image-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/image.py"],
            "cwd": "media_server",
            "env": {
                "IMAGE_LLM_BASE_URL": os.getenv("IMAGE_LLM_BASE_URL"),
                "IMAGE_LLM_MODEL_NAME": os.getenv("IMAGE_LLM_MODEL_NAME"),
                "IMAGE_LLM_API_KEY": os.getenv("IMAGE_LLM_API_KEY"),
            },
        },
        "media-video-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/video.py"],
            "cwd": "media_server",
            "env": {
                "VIDEO_LLM_BASE_URL": os.getenv("VIDEO_LLM_BASE_URL"),
                "VIDEO_LLM_MODEL_NAME": os.getenv("VIDEO_LLM_MODEL_NAME"),
                "VIDEO_LLM_API_KEY": os.getenv("VIDEO_LLM_API_KEY"),
            },
        },
        "parxiv-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/parxiv.py"],
            "cwd": "parxiv_server",
        },
        "terminal-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/terminal.py"],
            "cwd": "terminal_server",
        },
        "wayback-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/wayback.py"],
            "cwd": "wayback_server",
        },
        "wiki-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/wiki.py"],
            "cwd": "wiki_server",
        },
        "googlesearch-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/googlesearch.py"],
            "cwd": "googlesearch_server",
            "env": {
                "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
                "GOOGLE_CSE_ID": os.getenv("GOOGLE_CSE_ID"),
            },
        },
        "filesystem-server": {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "~/workspace"],
        },
        "terminal-controller": {
            "command": "uvx",
            "args": ["terminal_controller"],
            "env": {"SESSION_REQUEST_CONNECT_TIMEOUT": "300"},
        },
        "excel": {
            "command": "uvx",
            "args": ["excel-mcp-server", "stdio"],
            "env": {
                "EXCEL_MCP_PAGING_CELLS_LIMIT": "4000",
                "SESSION_REQUEST_CONNECT_TIMEOUT": "120",
            },
        },
        "google-search": {
            "command": "npx",
            "args": ["-y", "@adenot/mcp-google-search"],
            "env": {
                "GOOGLE_API_KEY": os.environ["GOOGLE_API_KEY"],
                "GOOGLE_SEARCH_ENGINE_ID": os.environ["GOOGLE_CSE_ID"],
                "SESSION_REQUEST_CONNECT_TIMEOUT": "60",
            },
        },
        "audio-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/main.py"],
            "cwd": "audio_server",
            "env": {
                "AUDIO_LLM_API_KEY": os.environ["AUDIO_LLM_API_KEY"],
                "AUDIO_LLM_BASE_URL": os.environ["AUDIO_LLM_BASE_URL"],
                "AUDIO_LLM_MODEL_NAME": os.environ["AUDIO_LLM_MODEL_NAME"],
                "SESSION_REQUEST_CONNECT_TIMEOUT": "60",
            },
        },
        "image-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/main.py"],
            "cwd": "image_server",
            "env": {
                "IMAGE_LLM_API_KEY": os.environ.get("IMAGE_LLM_API_KEY"),
                "IMAGE_LLM_MODEL_NAME": os.environ.get("IMAGE_LLM_MODEL_NAME"),
                "IMAGE_LLM_BASE_URL": os.environ.get("IMAGE_LLM_BASE_URL"),
                "SESSION_REQUEST_CONNECT_TIMEOUT": "60",
            },
        },
        "e2b-code-server": {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "src/main.py"],
            "cwd": "e2b_code_server",
            "env": {
                "E2B_API_KEY": os.environ["E2B_API_KEY"],
                "SESSION_REQUEST_CONNECT_TIMEOUT": "120",
            },
        },
        "ms-playwright": {
            "command": "npx",
            "args": [
                "@playwright/mcp@latest",
                "--no-sandbox",
                "--headless",
                "--isolated",
            ],
            "env": {
                "PLAYWRIGHT_TIMEOUT": "120000",
                "SESSION_REQUEST_CONNECT_TIMEOUT": "120",
            },
        },
        # "calculator": {
        #     "command": "uvx",
        #     "args": [
        #         "mcp_server_calculator"
        #     ],
        #     "env": {
        #         "SESSION_REQUEST_CONNECT_TIMEOUT": "20"
        #     }
        # },
    }
}
