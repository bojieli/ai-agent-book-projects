# MCP Examples

This directory contains examples and demos for using MCP (Model Context Protocol) tools and servers within the AWorld framework. 
These examples showcase how to build, extend, and interact with various MCP-enabled services, including virtual file systems, calculators, media processing, and more.

## Already cases

- **BFCL/**  
  Demonstrates Basic Function Call Learning (BFCL) using a virtual file system (GorillaFileSystem) and MCP tools.  
  - Shows how to synthesize function call samples for model training.
  - Includes a virtual file system agent, MCP tool implementations, and trajectory collection for training data.
  - See `BFCL/README.md` for detailed instructions and architecture diagrams.

- **mcp_demo/**  
  Provides a minimal MCP server and client demo pipeline.  
  - Includes a simple calculator server and example pipeline.
  - Shows how to start an MCP server, configure LLM API keys, and run a sample agent pipeline.
  - See `mcp_demo/README.md` for step-by-step usage.

- **mcp_servers/**  
  A collection of ready-to-use MCP servers for various tasks, such as:
  - Search (text, image, video, document)
  - Reasoning and calculation
  - Audio and browser automation
  - Downloading and file management
  - Each server is implemented as a standalone Python module.
  - Useful for extending agent capabilities with external tools.

- **text_to_audio/**  
  Example of an MCP server and agent for text-to-audio conversion.
  - Includes a sample MCP server and configuration for audio synthesis tasks.

## Usage

- Each subdirectory contains its own entry point (usually `run.py`) and may include additional configuration or requirements files.
- Before running any example, ensure you have installed all required dependencies and set the necessary environment variables (e.g., LLM provider credentials, API keys).
- For detailed instructions, refer to the README or comments within each subdirectory.

## Typical Scenarios

- **Function Call Synthesis:**  
  Generate training data for LLMs by collecting agent trajectories and function call samples (see BFCL).

- **Custom MCP Servers:**  
  Extend agent capabilities by running your own MCP servers for search, reasoning, media, or file operations.

- **Pipeline Demos:**  
  Quickly test agent-server interaction with the provided demo pipelines.

---

If you need more detailed usage instructions or want to add new MCP tools, refer to the documentation and code samples in each subdirectory. 