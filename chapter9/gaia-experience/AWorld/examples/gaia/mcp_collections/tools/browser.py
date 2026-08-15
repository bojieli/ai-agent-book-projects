"""
Browser MCP Server

This module provides MCP server functionality for browser automation and interaction.
It handles tasks such as web scraping, form submission, and automated browsing using browser-use package.

Main functions:
- mcp_browser_use: Performs browser automation tasks with LLM-friendly output
"""

import json
import os
import re
import sys
import time
import traceback

try:
    from browser_use import Agent, AgentHistoryList, BrowserProfile
    from browser_use.llm import ChatOpenAI
    from dotenv import load_dotenv
    from pydantic import BaseModel, Field

    from aworld.logs.util import Color

    from ..base import ActionArguments, ActionCollection, ActionResponse
except Exception as e:
    print(f"Failed to import browser tool: {traceback.format_exc()}")
    raise e


print(f"Browser tool sys.path: {sys.path}")


class BrowserMetadata(BaseModel):
    """Metadata for browser automation results."""

    task: str
    execution_successful: bool
    steps_taken: int | None = None
    downloaded_files: list[str] = Field(default_factory=list)
    visited_urls: list[str] = Field(default_factory=list)
    execution_time: float | None = None
    error_type: str | None = None
    trace_log_path: str | None = None


class BrowserActionCollection(ActionCollection):
    """MCP service for browser automation using browser-use package.

    Provides comprehensive web automation capabilities including:
    - Web scraping and content extraction
    - Form submission and interaction
    - File downloads and media handling
    - LLM-enhanced browsing with memory
    - Robot detection and paywall handling
    """

    def __init__(self, arguments: ActionArguments) -> None:
        super().__init__(arguments)

        # Load environment variables
        load_dotenv()

        # Extended system prompt for browser automation
        self.extended_browser_system_prompt = """
10. URL ends with .pdf
- If the go_to_url function with `https://any_url/any_file_name.pdf` as the parameter, just report the url link and hint the user to download using `download` mcp tool or `curl`, then execute `done` action.

11. Robot Detection:
- If the page is a robot detection page, abort immediately. Then navigate to the most authoritative source for similar information instead

# Efficiency Guidelines
0. if download option is available, always **DOWNLOAD** as possible! Also, report the download url link in your result.
1. Use specific search queries with key terms from the task
2. Avoid getting distracted by tangential information
3. If blocked by paywalls, try archive.org or similar alternatives
4. Document each significant finding clearly and concisely
5. Precisely extract the necessary information with minimal browsing steps.
"""

        # Initialize LLM configuration
        self.llm_config = ChatOpenAI(
            model=os.getenv("LLM_MODEL_NAME"),
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            temperature=1.0,
        )
        self._color_log(f"Browser llm_config: {self.llm_config}", Color.green)

        # Browser profile configuration
        self.browser_profile = BrowserProfile(
            cookies_file=os.getenv("COOKIES_FILE_PATH"),
            downloads_dir=str(self.workspace),
            downloads_path=str(self.workspace),
            save_recording_path=str(self.workspace),
            save_downloads_path=str(self.workspace),
            chromium_sandbox=False,
            headless=True,
        )
        self._color_log(f"Browser browser_profile: {self.browser_profile}", Color.green)

        # Log configuration
        self.trace_log_dir = str(self.workspace / "logs")
        os.makedirs(f"{self.trace_log_dir}/browser_log", exist_ok=True)

        self._color_log("Browser automation service initialized", Color.green)
        self._color_log(
            f"Downloads directory: {self.browser_profile.downloads_path}", Color.blue
        )
        self._color_log(
            f"Trace logs directory: {self.trace_log_dir}/browser_log", Color.blue
        )

    def _create_browser_agent(self, task: str) -> Agent:
        """Create a browser agent instance with configured settings.

        Args:
            task: The task description for the browser agent

        Returns:
            Configured Agent instance
        """
        return Agent(
            task=task,
            llm=self.llm_config,
            extend_system_message=self.extended_browser_system_prompt,
            use_vision=True,
            enable_memory=False,
            browser_profile=self.browser_profile,
            save_conversation_path=f"{self.trace_log_dir}/browser_log/trace.log",
        )

    def _extract_visited_urls(self, extracted_content: list[str]) -> list[str]:
        """Inner method to extract URLs from content using regex.

        Args:
            content_list: List of content strings to search for URLs

        Returns:
            List of unique URLs found in the content
        """
        url_pattern = r'https?://[^\s<>"\[\]{}|\\^`]+'
        visited_urls = set()

        for content in extracted_content:
            if content and isinstance(content, str):
                urls = re.findall(url_pattern, content)
                visited_urls.update(urls)

        return list(visited_urls)

    def _format_extracted_content(self, extracted_content: list[str]) -> str:
        """Format extracted content to be LLM-friendly.

        Args:
            extracted_content: List of extracted content strings from browser execution

        Returns:
            Formatted string suitable for LLM consumption
        """
        if not extracted_content:
            return "No content extracted from browser execution."

        # Handle list of strings
        if len(extracted_content) == 1:
            # Single item - return it directly with formatting
            return f"**Extracted Content:**\n{extracted_content[0]}"
        else:
            # Multiple items - format as numbered list
            formatted_parts = ["**Extracted Content:**"]
            for i, content in enumerate(extracted_content, 1):
                if content.strip():  # Only include non-empty content
                    formatted_parts.append(f"{i}. {content}")

            return (
                "\n".join(formatted_parts)
                if len(formatted_parts) > 1
                else "No meaningful content extracted from browser execution."
            )

    async def mcp_browser_use(
        self,
        task: str = Field(
            description="The task to perform using the browser automation agent"
        ),
        max_steps: int = Field(
            default=50, description="Maximum number of steps for browser execution"
        ),
        extract_format: str = Field(
            default="markdown",
            description="Format for extracted content: 'markdown', 'json', or 'text'",
        ),
    ) -> ActionResponse:
        """Perform browser automation tasks using the browser-use package.

        This tool provides comprehensive browser automation capabilities including:
        - Web scraping and content extraction
        - Form submission and automated interactions
        - File downloads and media handling
        - LLM-enhanced browsing with memory and vision
        - Automatic handling of robot detection and paywalls

        Args:
            task: Description of the browser automation task to perform
            max_steps: Maximum number of execution steps (default: 50)
            extract_format: Output format for extracted content

        Returns:
            ActionResponse with LLM-friendly extracted content and execution metadata
        """
        try:
            self._color_log(f"🎯 Starting browser task: {task}", Color.cyan)

            # Create browser agent
            agent = self._create_browser_agent(task)

            start_time = time.time()

            browser_execution: AgentHistoryList = await agent.run(max_steps=max_steps)

            execution_time = time.time() - start_time

            if (
                browser_execution is not None
                and browser_execution.is_done()
                and browser_execution.is_successful()
            ):
                # Extract and format content
                extracted_content = browser_execution.extracted_content()
                final_result = browser_execution.final_result()

                # Format content based on requested format
                if extract_format.lower() == "json":
                    formatted_content = json.dumps(
                        {"summary": final_result, "extracted_data": extracted_content},
                        indent=2,
                    )
                elif extract_format.lower() == "text":
                    formatted_content = f"{final_result}\n\n{self._format_extracted_content(extracted_content)}"
                else:  # markdown (default)
                    formatted_content = (
                        f"## Browser Automation Result\n\n**Summary:** {final_result}\n\n"
                        f"{self._format_extracted_content(extracted_content)}"
                    )

                # Prepare metadata
                metadata = BrowserMetadata(
                    task=task,
                    execution_successful=True,
                    steps_taken=(
                        len(browser_execution.history)
                        if hasattr(browser_execution, "history")
                        else None
                    ),
                    downloaded_files=[],
                    visited_urls=self._extract_visited_urls(extracted_content),
                    execution_time=execution_time,
                    trace_log_path=f"{self.trace_log_dir}/browser_log/trace.log",
                )

                self._color_log(f"🗒️ Detail: {extracted_content}", Color.lightgrey)
                self._color_log(f"🌏 Result: {final_result}", Color.green)

                return ActionResponse(
                    success=True,
                    message=formatted_content,
                    metadata=metadata.model_dump(),
                )

            else:
                # Handle execution failure
                error_msg = "Browser execution failed or was not completed successfully"

                metadata = BrowserMetadata(
                    task=task,
                    execution_successful=False,
                    execution_time=execution_time,
                    error_type="execution_failure",
                    trace_log_path=f"{self.trace_log_dir}/browser_log/trace.log",
                )

                self._color_log(f"❌ {error_msg}", Color.red)

                return ActionResponse(
                    success=False, message=error_msg, metadata=metadata.model_dump()
                )

        except Exception as e:
            error_msg = f"Browser automation failed: {str(e)}"
            error_trace = traceback.format_exc()

            self.logger.error(f"Browser execution error: {error_trace}")

            metadata = BrowserMetadata(
                task=task,
                execution_successful=False,
                error_type="exception",
                trace_log_path=f"{self.trace_log_dir}/browser_log/trace.log",
            )

            self._color_log(f"❌ {error_msg}", Color.red)

            return ActionResponse(
                success=False,
                message=f"{error_msg}\n\nError details: {error_trace}",
                metadata=metadata.model_dump(),
            )

    def mcp_get_browser_capabilities(self) -> ActionResponse:
        """Get information about browser automation capabilities and configuration.

        Returns:
            ActionResponse with browser service capabilities and current configuration
        """
        capabilities = {
            "automation_features": [
                "Web scraping and content extraction",
                "Form submission and interaction",
                "File downloads and media handling",
                "LLM-enhanced browsing with vision",
                "Memory-enabled browsing sessions",
                "Robot detection and paywall handling",
            ],
            "supported_formats": ["markdown", "json", "text"],
            "configuration": {
                "llm_model": os.getenv("LLM_MODEL_NAME", "Not configured"),
                "downloads_directory": self.browser_profile.downloads_path,
                "cookies_enabled": bool(os.getenv("COOKIES_FILE_PATH")),
                "trace_logging": True,
                "vision_enabled": True,
                "headless": True,
            },
        }

        formatted_info = f"""# Browser Automation Service Capabilities

        ## Features
        {chr(10).join(f"- {feature}" for feature in capabilities["automation_features"])}

        ## Supported Output Formats
        {chr(10).join(f"- {fmt}" for fmt in capabilities["supported_formats"])}

        ## Current Configuration
        - **LLM Model:** {capabilities["configuration"]["llm_model"]}
        - **Downloads Directory:** {capabilities["configuration"]["downloads_directory"]}
        - **Cookies Enabled:** {capabilities["configuration"]["cookies_enabled"]}
        - **Vision Enabled:** {capabilities["configuration"]["vision_enabled"]}
        - **Memory Enabled:** {capabilities["configuration"]["memory_enabled"]}
        - **Trace Logging:** {capabilities["configuration"]["trace_logging"]}
        """

        return ActionResponse(
            success=True, message=formatted_info, metadata=capabilities
        )


# Example usage and entry point
if __name__ == "__main__":
    load_dotenv()

    # Default arguments for testing
    args = ActionArguments(
        name="browser_automation_service",
        transport="stdio",
        workspace=os.getenv("AWORLD_WORKSPACE", "~"),
    )

    # Initialize and run the browser automation service
    try:
        service = BrowserActionCollection(args)
        service.run()
    except Exception as e:
        print(f"An error occurred: {e}: {traceback.format_exc()}")
