# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import os

from aworld.config.conf import ToolConfig, ModelConfig


class BrowserToolConfig(ToolConfig):
    headless: bool = False
    keep_browser_open: bool = True
    private: bool = True
    browse_name: str = "chromium"
    custom_executor: bool = False
    width: int = 1280
    height: int = 720
    slow_mo: int = 0
    disable_security: bool = False
    dom_js_path: str = None
    locale: str = None
    geolocation: str = None
    storage_state: str = None
    do_highlight: bool = True
    focus_highlight: int = -1
    viewport_expansion: int = 0
    cdp_url: str = None
    wss_url: str = None
    proxy: str = None
    cookies_file: str = None
    working_dir: str = None
    enable_recording: bool = False
    sleep_after_init: float = 0
    max_retry: int = 3
    llm_config: ModelConfig = ModelConfig()
    max_extract_content_input_tokens: int = 64000
    max_extract_content_output_tokens: int = 5000
    reuse: bool = True


class AndroidToolConfig(ToolConfig):
    avd_name: str | None = None
    adb_path: str | None = os.path.expanduser('~') + "/Library/Android/sdk/platform-tools/adb"
    emulator_path: str | None = os.path.expanduser('~') + "/Library/Android/sdk/emulator/emulator"
    headless: bool | None = None
